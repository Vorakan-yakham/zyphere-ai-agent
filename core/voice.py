"""Speech-to-text for microphone input, fully offline (faster-whisper). The model downloads once, then no internet is needed."""
import io
import os
import threading

_model = None
_lock = threading.Lock()


class VoiceError(Exception):
    """Message is safe to show to the user (Thai)."""


def _get_model():
    global _model
    with _lock:
        if _model is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError:
                raise VoiceError("ยังไม่ได้ติดตั้ง faster-whisper — รัน `pip install faster-whisper`")
            size = os.environ.get("ZYPHERE_STT_MODEL", "small")  # tiny/base/small/medium/large-v3
            try:
                _model = WhisperModel(size, device="auto", compute_type="int8")
            except Exception:
                raise VoiceError(f"โหลดโมเดลเสียง '{size}' ไม่ได้ (ครั้งแรกต้องต่ออินเทอร์เน็ตเพื่อดาวน์โหลด 1 ครั้ง)")
    return _model


def transcribe(wav_bytes: bytes, language: str = "th-TH") -> str:
    code = (language or "th").split("-")[0].lower()
    model = _get_model()
    try:
        segments, _ = model.transcribe(io.BytesIO(wav_bytes), language=code, vad_filter=True,
                                       beam_size=5, condition_on_previous_text=False)
        text = " ".join(s.text.strip() for s in segments)
    except Exception:
        raise VoiceError("อ่านไฟล์เสียงไม่ได้ ลองอัดใหม่")
    text = " ".join(text.split())
    if not text:
        raise VoiceError("ฟังไม่ออก ลองพูดให้ชัดขึ้นหรือใกล้ไมค์ขึ้น")
    return text
