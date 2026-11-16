"""Sensors: turn the camera frame (and optional serial devices) into plain-text observations for the AI.

Camera analysis is classical OpenCV (faces, people, light, motion): fast, offline, CPU-only. It detects
that a face exists; it never identifies who it is.
"""
import os
from typing import Optional

import cv2
import numpy as np

_det = None


def _detectors():
    """(face, hog) detectors, or (None, None). OpenCV 5 dropped the classic cascade/HOG classes, so pin opencv 4.x."""
    global _det
    if _det is None:
        try:
            face = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
            hog = cv2.HOGDescriptor()
            hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
            _det = (face, hog)
        except AttributeError:
            _det = (None, None)
    return _det


def _decode(data: bytes):
    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("อ่านภาพจากกล้องไม่ได้")
    return img


def analyze_image(data: bytes, prev: Optional[bytes] = None) -> dict:
    img = _decode(data)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    face, hog = _detectors()
    faces = people = None  # None = detector unavailable
    if face is not None:
        faces = int(len(face.detectMultiScale(gray, 1.1, 5, minSize=(40, 40))))
        small = cv2.resize(img, (480, max(1, int(480 * img.shape[0] / img.shape[1]))))
        people = int(len(hog.detectMultiScale(small, winStride=(8, 8))[0]))
    motion = None
    if prev:
        try:
            p = cv2.cvtColor(_decode(prev), cv2.COLOR_BGR2GRAY)
            if p.shape == gray.shape:
                motion = float(np.mean(cv2.absdiff(p, gray)) / 255 * 100)
        except ValueError:
            pass
    return {"faces": faces, "people": people,
            "brightness": float(gray.mean() / 255 * 100), "motion_pct": motion}


def summarize(r: dict) -> str:
    parts = ([f"ตรวจพบใบหน้า {r['faces']}", f"ตรวจพบคนทั้งตัว {r['people']}"] if r["faces"] is not None
             else ["ตัวตรวจจับใบหน้าใช้ไม่ได้ (ต้องติดตั้ง opencv 4.x)"])
    parts += ["แสงสว่างพอ" if r["brightness"] > 35 else "แสงน้อย/มืด"]
    if r["motion_pct"] is not None:
        parts.append("มีการเคลื่อนไหวจากภาพก่อนหน้า" if r["motion_pct"] > 3 else "ภาพนิ่งเหมือนก่อนหน้า")
    return "[SENSOR:camera] " + " · ".join(parts)


def read_serial(port: Optional[str] = None, baud: int = 9600, timeout: float = 2.0) -> str:
    """Read-only: latest line from an Arduino/ESP32 over USB serial (needs `pip install pyserial`).
    Port from argument or env ZYPHERE_SERIAL (e.g. COM3 or /dev/ttyUSB0). Returns "" if unavailable."""
    port = port or os.environ.get("ZYPHERE_SERIAL")
    if not port:
        return ""
    try:
        import serial
        with serial.Serial(port, baud, timeout=timeout) as s:
            s.reset_input_buffer()
            line = s.readline().decode("utf-8", "replace").strip()
        return f"[SENSOR:serial {port}] {line[:200]}" if line else ""
    except Exception:
        return ""
