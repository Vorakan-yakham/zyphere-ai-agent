"""เซ็นเซอร์: วิเคราะห์ภาพจากกล้อง (st.camera_input) ด้วย OpenCV แล้วแปลงเป็นข้อความให้ AI รับรู้."""
import cv2
import numpy as np

_face = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
_hog = cv2.HOGDescriptor()
_hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())


def _decode(data: bytes):
    return cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)


def analyze_image(data: bytes, prev: bytes | None = None) -> dict:
    img = _decode(data)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = _face.detectMultiScale(gray, 1.1, 5, minSize=(40, 40))
    people, _ = _hog.detectMultiScale(cv2.resize(img, (640, int(640 * img.shape[0] / img.shape[1]))),
                                      winStride=(8, 8))
    motion = None
    if prev is not None:
        p = cv2.cvtColor(_decode(prev), cv2.COLOR_BGR2GRAY)
        if p.shape == gray.shape:
            motion = float(np.mean(cv2.absdiff(p, gray)) / 255 * 100)
    return {"faces": len(faces), "people": len(people),
            "brightness": float(gray.mean() / 255 * 100), "motion_pct": motion}


def summarize(r: dict) -> str:
    parts = [f"พบใบหน้า {r['faces']} ใบหน้า", f"พบคน {r['people']} คน",
             "ห้องสว่าง" if r["brightness"] > 40 else "ห้องค่อนข้างมืด"]
    if r["motion_pct"] is not None:
        parts.append("มีการเคลื่อนไหว" if r["motion_pct"] > 3 else "นิ่งสงบ")
    return "[ข้อมูลเซ็นเซอร์กล้อง] " + ", ".join(parts)
