"""Text-to-speech, offline after a one-time model download. Returns WAV bytes.

Order: Meta MMS-TTS (torch + transformers; Thai and English) -> system voice via pyttsx3 -> None.
Set ZYPHERE_TTS=system to skip MMS.
"""
import io
import os
import re
import tempfile
import threading
import wave
from typing import Optional

THAI = re.compile(r"[\u0E00-\u0E7F]")
_models = {}
_lock = threading.Lock()


def _mms(text: str) -> bytes:
    import numpy as np
    import torch
    from transformers import AutoTokenizer, VitsModel
    name = "facebook/mms-tts-tha" if THAI.search(text) else "facebook/mms-tts-eng"
    with _lock:
        if name not in _models:
            _models[name] = (AutoTokenizer.from_pretrained(name), VitsModel.from_pretrained(name).eval())
    tok, model = _models[name]
    sr = model.config.sampling_rate
    parts = []
    for sent in [s for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()]:
        torch.manual_seed(0)
        with torch.no_grad():
            parts.append(model(**tok(sent, return_tensors="pt")).waveform[0].numpy())
        parts.append(np.zeros(sr // 8, dtype="float32"))
    wav = np.concatenate(parts)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(wav, -1, 1) * 32767).astype("<i2").tobytes())
    return buf.getvalue()


def _system(text: str) -> bytes:
    import pyttsx3
    eng = pyttsx3.init()
    fd, path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    try:
        eng.save_to_file(text, path)
        eng.runAndWait()
        with open(path, "rb") as fh:
            return fh.read()
    finally:
        os.unlink(path)


def synthesize(text: str) -> Optional[bytes]:
    text = text.strip()
    if not text:
        return None
    backends = [_system] if os.environ.get("ZYPHERE_TTS") == "system" else [_mms, _system]
    for fn in backends:
        try:
            data = fn(text)
            if data:
                return data
        except Exception as e:
            print(f"tts backend {fn.__name__} failed: {type(e).__name__}")
    return None
