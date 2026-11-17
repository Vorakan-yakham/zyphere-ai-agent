"""Zyphere Film Director - storyboard, camera angles, shot planning.

Turns a topic into a cinematic shot list. Honest limits: Zyphere uses licensed
stock images + Ken Burns motion + AI narration; it cannot render real human
actors speaking (needs paid AI-avatar services). But it CAN plan shots,
choose framing/composition, and produce a coherent, beautiful film.

Quality presets map to FFmpeg output sizes.
"""
import re

QUALITY = {
    "hd": {"w": 1280, "h": 720, "label": "HD 720p", "crf": 23},
    "fhd": {"w": 1920, "h": 1080, "label": "Full HD 1080p", "crf": 22},
    "4k": {"w": 3840, "h": 2160, "label": "4K UHD", "crf": 20},
}

ANGLES = {
    "establishing": {"th": "ภาพเปิดเรื่อง มุมกว้าง", "q": "wide landscape establishing shot"},
    "wide": {"th": "ภาพกว้าง", "q": "wide shot"},
    "medium": {"th": "ภาพกลาง", "q": "medium shot"},
    "close": {"th": "ภาพClose-up", "q": "close-up portrait detail"},
    "overhead": {"th": "มุมสูง", "q": "aerial overhead top view"},
    "low": {"th": "มุมต่ำ", "q": "low angle dramatic"},
}

TEMPLATE = [
    ("establishing", "เปิดเรื่อง: ทำความรู้จัก {topic}"),
    ("medium", "จุดสำคัญแรกของ {topic}"),
    ("close", "รายละเอียดที่น่าสนใจของ {topic}"),
    ("wide", "ภาพรวมและบริบทของ {topic}"),
    ("medium", "การนำ {topic} ไปใช้งานจริง"),
    ("close", "สรุปความประทับใจเกี่ยวกับ {topic}"),
]


def plan(topic, scenes=6, lang="th"):
    """Build a storyboard with camera angles for each shot."""
    topic = str(topic or "Zyphere")[:160]
    out = []
    for i in range(max(2, min(scenes, 12))):
        angle, desc = TEMPLATE[i % len(TEMPLATE)]
        a = ANGLES[angle]
        out.append({
            "shot": i + 1,
            "angle": angle,
            "angle_th": a["th"],
            "description": desc.format(topic=topic),
            "image_query": (a["q"] + " " + topic)[:160],
            "camera_note": ("zoom in ช้า ๆ" if angle == "close" else
                            "zoom out เผยบริบท" if angle == "wide" else
                            "pan ตามแนวนอน" if angle == "establishing" else " Ken Burns เบา ๆ"),
        })
    return {"ok": True, "topic": topic, "shots": out,
            "note": "นักแสดง: ใช้ภาพสต็อกที่มีลิขสิทธิ์ + เสียงบรรยาย AI (ไม่มีคนจริงพูดได้ — ต้องบริการ AI avatar แบบเสียเงิน)"}


def quality(name="fhd"):
    q = QUALITY.get(str(name).lower(), QUALITY["fhd"])
    return {"ok": True, "preset": name, **q}
