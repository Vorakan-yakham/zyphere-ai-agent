"""Thin wrapper around the Anthropic Messages API (streaming + one-shot)."""
import os
from typing import Generator, List, Optional

MODELS = {
    "claude-sonnet-5-5": "Sonnet 5.5 — balanced",
    "claude-opus-5-5": "Opus 5.5 — deepest reasoning",
    "claude-haiku-5-5": "Haiku 5.5 — fastest",
}
DEFAULT_MODEL = "claude-sonnet-5-5"


class LLMError(Exception):
    """Raised with a user-presentable (Thai) message."""


def get_api_key(secrets=None) -> Optional[str]:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key and secrets is not None:
        try:
            key = secrets.get("ANTHROPIC_API_KEY", None)
        except Exception:
            key = None
    return key or None


class LLM:
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        import anthropic  # imported lazily so the UI still loads without the package

        self._anthropic = anthropic
        self.client = anthropic.Anthropic(api_key=api_key, timeout=120.0, max_retries=2)
        self.model = model
        self.last_usage = (0, 0)

    def _translate(self, e: Exception) -> LLMError:
        a = self._anthropic
        if isinstance(e, a.AuthenticationError):
            return LLMError("API key ไม่ถูกต้อง กรุณาตรวจสอบ ANTHROPIC_API_KEY ใน Secrets")
        if isinstance(e, a.PermissionDeniedError):
            return LLMError("API key นี้ไม่มีสิทธิ์ใช้โมเดลที่เลือก ลองเปลี่ยนโมเดลในแถบข้าง")
        if isinstance(e, a.NotFoundError):
            return LLMError("ไม่พบโมเดลที่เลือก ลองเปลี่ยนโมเดลในแถบข้าง")
        if isinstance(e, a.RateLimitError):
            return LLMError("ใช้งานเกินโควตาชั่วคราว (rate limit) รอสักครู่แล้วลองใหม่")
        if isinstance(e, a.APIConnectionError):
            return LLMError("เชื่อมต่อ Anthropic API ไม่ได้ ตรวจสอบอินเทอร์เน็ตแล้วลองใหม่")
        if isinstance(e, a.BadRequestError):
            return LLMError(f"คำขอไม่ถูกต้อง (อาจเพราะไฟล์ใหญ่หรือชนิดไฟล์ไม่รองรับ): {getattr(e, 'message', e)}")
        if isinstance(e, a.APIStatusError):
            return LLMError(f"Anthropic API ตอบกลับผิดพลาด (HTTP {e.status_code})")
        return LLMError(f"เกิดข้อผิดพลาดที่ไม่คาดคิด: {type(e).__name__}")

    def stream(self, system: str, messages: List[dict], max_tokens: int = 4096) -> Generator[str, None, None]:
        try:
            with self.client.messages.stream(
                model=self.model, max_tokens=max_tokens, system=system, messages=messages
            ) as s:
                for text in s.text_stream:
                    yield text
        except self._anthropic.APIError as e:
            raise self._translate(e) from e

    def complete(self, system: str, messages: List[dict], max_tokens: int = 1024) -> str:
        try:
            r = self.client.messages.create(
                model=self.model, max_tokens=max_tokens, system=system, messages=messages
            )
            u = getattr(r, "usage", None)
            self.last_usage = (getattr(u, "input_tokens", 0) or 0, getattr(u, "output_tokens", 0) or 0)
            return "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
        except self._anthropic.APIError as e:
            raise self._translate(e) from e
