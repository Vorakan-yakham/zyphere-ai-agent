"""ไมค์ -> ข้อความ แบบออฟไลน์ด้วย faster-whisper (ดาวน์โหลดโมเดลครั้งแรกครั้งเดียว)."""
import os
import tempfile

_model = None


class VoiceError(Exception):
    pass


def _get_model(size):
    global _model
    if _model is None:
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            raise VoiceError("ติดตั้งก่อน: pip install faster-whisper")
        _model = WhisperModel(size, device="auto", compute_type="int8")
    return _model


def transcribe(data: bytes, lang: str = "th", size: str = "small") -> str:
    code = "th" if str(lang).lower().startswith(("th", "ไทย")) else ("en" if str(lang).lower().startswith("en") else None)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(data)
        path = f.name
    try:
        segs, _ = _get_model(size).transcribe(path, language=code, vad_filter=True)
        text = " ".join(s.text.strip() for s in segs).strip()
    finally:
        os.unlink(path)
    if not text:
        raise VoiceError("ไม่ได้ยินเสียงพูด ลองพูดใหม่อีกครั้ง")
    return text
