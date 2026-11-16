"""ข้อความ -> เสียงพูด แบบออฟไลน์ คืนค่าเป็น bytes ของไฟล์ WAV (เล่นด้วย st.audio)."""
import io
import os
import tempfile

_mms = {}


def _mms_tts(text):
    """เสียงไทย/อังกฤษคุณภาพดีจาก Meta MMS-TTS (ต้อง pip install transformers torch scipy)"""
    import numpy as np
    import torch
    from scipy.io import wavfile
    from transformers import AutoTokenizer, VitsModel
    name = "facebook/mms-tts-tha"
    if name not in _mms:
        _mms[name] = (AutoTokenizer.from_pretrained(name), VitsModel.from_pretrained(name))
    tok, model = _mms[name]
    with torch.no_grad():
        wav = model(**tok(text, return_tensors="pt")).waveform[0].numpy()
    buf = io.BytesIO()
    wavfile.write(buf, model.config.sampling_rate, (np.clip(wav, -1, 1) * 32767).astype("int16"))
    return buf.getvalue()


def _pyttsx3_tts(text):
    import pyttsx3
    eng = pyttsx3.init()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        path = f.name
    eng.save_to_file(text, path)
    eng.runAndWait()
    try:
        with open(path, "rb") as fh:
            return fh.read()
    finally:
        os.unlink(path)


def synthesize(text: str, lang: str = "th"):
    text = text.strip()[:600]  # อ่านเฉพาะช่วงต้น เพื่อไม่ให้รอนาน
    if not text:
        return None
    for fn in (_mms_tts, _pyttsx3_tts):
        try:
            return fn(text)
        except Exception:
            continue
    return None
