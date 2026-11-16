"""Speech-to-text for microphone input. Uses SpeechRecognition's free Google web endpoint (needs internet)."""
import io


class VoiceError(Exception):
    """Message is safe to show to the user (Thai)."""


def transcribe(wav_bytes: bytes, language: str = "th-TH") -> str:
    try:
        import speech_recognition as sr
    except ImportError:
        raise VoiceError("ยังไม่ได้ติดตั้งแพ็กเกจ SpeechRecognition")
    rec = sr.Recognizer()
    try:
        with sr.AudioFile(io.BytesIO(wav_bytes)) as src:
            audio = rec.record(src)
    except Exception:
        raise VoiceError("อ่านไฟล์เสียงไม่ได้ ลองอัดใหม่")
    try:
        text = rec.recognize_google(audio, language=language)
    except sr.UnknownValueError:
        raise VoiceError("ฟังไม่ออก ลองพูดให้ชัดขึ้นหรือใกล้ไมค์ขึ้น")
    except sr.RequestError:
        raise VoiceError("บริการแปลงเสียงเป็นข้อความใช้ไม่ได้ในตอนนี้ (ตรวจสอบอินเทอร์เน็ต) — พิมพ์แทนได้")
    return " ".join(text.split())
