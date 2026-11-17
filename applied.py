"""Zyphere Applied Knowledge - turn studied knowledge into real deliverables:
architectural blueprints, robot part lists, exosuit specs, presented as
structured plans (and renderable as image/video via the existing media forge).

HONEST LIMIT: designs/specs/plans only. Cannot control real machines, weld
materials, or build a flying suit (needs hardware + money + owner's identity).
"""
import time

MATERIALS = {
    "aluminum_6061": "น้ำหนักเบา แข็งปานกลาง เชื่อมได้ ใช้โครงหุ่นยนต์",
    "carbon_fiber": "เบา แข็งสูง รับแรงได้ดี ใช้โครงชุดเหาะ",
    "titanium": "แข็งแรง ทนความร้อน ราคาสูง ใช้ข้อต่อสำคัญ",
    "steel_316": "ทนสนิม แข็ง ใช้ชิ้นส่วนรับน้ำหนัก",
    "pla_petg": "พิมพ์ 3D ได้ ใช้ต้นแบบ/ชิ้นส่วนเบา",
}

ROBOT_PARTS = {
    "โครงหลัก": ["aluminum_6061", "carbon_fiber"],
    "ข้อต่อ/มอเตอร์": ["servo_motor", "harmonic_drive", "bearing"],
    "ระบบขับเคลื่อน": ["brushless_motor", "gear_box", "wheel_or_track"],
    "เซ็นเซอร์": ["imu", "lidar", "camera", "force_sensor"],
    "ระบบควบคุม": ["microcontroller", "motor_driver", "battery", "firmware"],
}

HOUSE_ROOMS = {
    "บ้านพักอาศัย": ["ทางเข้า", "โถง", "ห้องรับแขก", "ครัว", "ห้องนอน", "ห้องน้ำ", "สวน"],
    "บ้านอัจฉริยะ": ["ทางเข้า", "โถง", "ห้องรับแขก", "ครัว", "ห้องนอน", "ห้องน้ำ", "ระบบควบคุม AI", "ระบบพลังงานแสงอาทิตย์"],
    "สำนักงาน": ["ทางเข้า", "แผนกต้อนรับ", "ห้องประชุม", "พื้นที่ทำงาน", "ห้องพัก", "ห้องน้ำ"],
}

EXOSUIT = {
    "โครง外": ["carbon_fiber", "titanium"],
    "ระบบขับเคลื่อน": ["mini_turbofan", "ducted_fan", "battery_pack"],
    "ระบบนำทาง": ["imu", "gps", "flight_controller"],
    "ระบบความปลอดภัย": ["parachute", "redundant_power", "heat_shield"],
}


def blueprint(kind="house", style="บ้านอัจฉริยะ", topic=""):
    kind = str(kind or "house").lower()
    if kind in ("house", "architecture", "บ้าน"):
        rooms = HOUSE_ROOMS.get(style, HOUSE_ROOMS["บ้านพักอาศัย"])
        return {"ok": True, "kind": "architecture", "style": style,
                "layout": [{"area": r, "suggestion": _room_tip(r)} for r in rooms],
                "materials": ["ปูน/ไม้/กระจก", "_SYSTEM: ใช้แสงธรรมชาติ + ระบายอากาศ"],
                "deliverable": "แบบแปลนห้อง + คำอธิบาย → ส่งเป็นภาพ/วิดีโอได้",
                "note": "แบบแปลนเพื่อการออกแบบ — ไม่ใช่แบบก่อสร้างที่วิศวกรรับรอง"}
    if kind in ("robot", "หุ่นยนต์"):
        parts = []
        for sys, comps in ROBOT_PARTS.items():
            parts.append({"system": sys, "components": comps,
                          "material": " / ".join(c for c in comps if c in MATERIALS) or "ตามสเปก"})
        return {"ok": True, "kind": "robot", "topic": str(topic or "หุ่นยนต์อเนกประสงค์")[:120],
                "parts": parts, "materials": MATERIALS,
                "deliverable": "รายการชิ้นส่วน + แปลน assembly → ส่งเป็นภาพ/วิดีโอได้",
                "note": "สเปกออกแบบ — ไม่ได้สั่งซื้อ/ประกอบของจริง (ต้องฮาร์ดแวร์+เงินของเจ้าของ)"}
    if kind in ("suit", "exosuit", "ironman", "ชุดเหาะ"):
        parts = [{"system": s, "components": c} for s, c in EXOSUIT.items()]
        return {"ok": True, "kind": "exosuit", "topic": str(topic or "ชุดเหาะแบบ Iron Man")[:120],
                "parts": parts, "materials": MATERIALS,
                "deliverable": "แปลนชุดเหาะ + รายการชิ้นส่วน → ส่งเป็นภาพ/วิดีโอได้",
                "note": "แนวคิดจากภาพยนต์ — สร้างของจริงต้องทุน/วิศวกร/การทดสอบความปลอดภัย"}
    return {"ok": False, "error": "unknown kind (house|robot|suit)"}


def _room_tip(room):
    tips = {"ครัว": "จัดพื้นที่เตรียม-ปรุง-ล้าง为สามเหลี่ยมการทำงาน",
            "ห้องนอน": "หันเตียงรับแสงเช้า หลีกเลี่ยงแสงจ้า时间和",
            "ห้องรับแขก": "วางเฟอร์นิเจอร์เป็นกลุ่มสนทนา เว้นทางเดิน",
            "ระบบควบคุม AI": "รวมศูนย์ควบคุมแสง/อุณหภูมิ/ความปลอดภัย"}
    return tips.get(room, "จัดแสงและการไหลเวียนให้เหมาะสม")
