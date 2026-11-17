"""Zyphere Aerospace Design - apply learned physics/thermo/orbital mechanics to
design rockets, spacecraft, saucers, habitats. Produces specs + part lists.

Applied knowledge from curriculum: orbital mechanics, rocket propulsion,
thermodynamics, materials, control systems, space medicine.

HONEST: design/spec/calculation only. Building & launching needs real
engineering, capital, testing, and legal compliance — not possible here.
"""
import math

MU_EARTH = 3.986004418e14  # m^3/s^2
R_EARTH = 6371000  # m

VEHICLES = {
    "rocket": {
        "th": "จรวด", "parts": ["โครงสร้าง (carbon/titanium)", "เครื่องยนต์ (RP-1/LOX หรือ methane/LOX)",
                                "ถังเชื้อเพลิง", "ระบบนำทาง (IMU+GPS)", "ห้องบรรทุก", "ระบบแยกชั้น"],
        "physics": "F=ma · Δv = Isp·g0·ln(m0/mf) · แรงผลักต้องมากกว่าน้ำหนัก (TWR>1)",
    },
    "spacecraft": {
        "th": "ยานอวกาศ", "parts": ["โครงใหม่", "ระบบหล่อเลี้ยงชีวิต (O2/CO2/น้ำ)", "การ์ดกันรังสี",
                                   "แผงโซลาร์เซลล์", "ระบบสื่อสาร", "ระบบควบคุมท่าทาง"],
        "physics": "สุญญากาศ · รังสีคอสมิก · การหมุนเพื่อจำลองแรงโน้มถ่วง (centripetal a=ω²r)",
    },
    "saucer": {
        "th": "จานบิน (UFO concept)", "parts": ["โครงจาน(carbon)", "ระบบขับเคลื่อนแบบสมมติ (antigravity/gravity manipulation)",
                                              "แกนกลาง (reactor concept)", "ระบบควบคุมสนาม", "ระบบลงจอด"],
        "physics": "แนวคิดจากวิทยาศาสตร์ที่ยังไม่พิสูจน์ — anti-gravity ยังอยู่ในระดับสมมติฐาน ไม่มีหลักฐานยืนยัน",
    },
    "habitat": {
        "th": "ฐานอยู่อาศัยอวกาศ", "parts": ["โมดูลอยู่อาศัย", "ระบบปิดลoop (น้ำ/อากาศ recycling)",
                                          "เกราะกันอุกกาบาต (Whipple shield)", "โรงไฟฟ้า", "ท่าจอดยาน"],
        "physics": "แรงดันภายใน ~1 atm · การปิด循环ทรัพยากร · การป้องกันmicro-meteoroid",
    },
}


def orbital_speed(alt_km=400):
    r = R_EARTH + alt_km * 1000
    return math.sqrt(MU_EARTH / r)  # m/s


def design(kind="rocket", payload_kg=1000, altitude_km=400):
    kind = str(kind).lower()
    if kind not in VEHICLES:
        return {"ok": False, "error": "unknown vehicle (rocket|spacecraft|saucer|habitat)"}
    v = VEHICLES[kind]
    speed = orbital_speed(altitude_km)
    return {
        "ok": True, "kind": kind, "thai_name": v["th"],
        "payload_kg": payload_kg, "target_altitude_km": altitude_km,
        "orbital_speed_ms": round(speed, 1),
        "orbital_speed_kms": round(speed / 1000, 2),
        "parts": v["parts"], "physics": v["physics"],
        "formula": ("Δv ≈ Isp·9.81·ln(m0/mf) + ความสูญเสียแรงเสียดทาน/แรงโน้มถ่วง" if kind == "rocket" else "ดูหลักการใน physics"),
        "deliverable": "สเปกยาน + รายการชิ้นส่วน + การคำนวณ → นำเสนอเป็นภาพ/วิดีโอได้",
        "note": "แบบแปลน/คำนวณจากทฤษฎีที่เรียนรู้ — การสร้างจริงต้องวิศวกร ทุน และการทดสอบความปลอดภัย",
    }
