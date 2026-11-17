"""Zyphere Human Art & Music Learning - study anatomy, skin, hair, lighting,
and music genres so generated work feels human and emotionally believable.

HONEST LIMITS (must be stated to owner):
- Cannot clone Suno.ai (proprietary generative model, huge GPU, ToS).
- Cannot render real human actors from text (needs paid AI avatar services).
- What IS possible: learn the KNOWLEDGE (proportions, skin tones, hair,
  lighting, music theory/genres) and use it to improve locally-generated art
  (Pillow-drawn stylized characters) and original melodies (no copyright).
"""
import math, random

# ---- Human anatomy (learning reference, not a renderer) ----
PROPORTIONS = {
    "head_height_ratio": 7.5,  # average adult = 7.5 head-heights
    "shoulder_width_heads": 2.0,
    "eye_line": 0.5,  # eyes at halfway down the head
    "arm_span_to_height": 1.0,
    "child_head_ratio": 5.0,
    "heroic_head_ratio": 8.0,
}

SKIN_TONES = {
    "very_light": "#f5d6c6", "light": "#e8c1a8", "medium_light": "#d9a57f",
    "medium": "#c68e63", "medium_dark": "#a86b45", "dark": "#7a4a2b", "deep": "#4e2d1a",
}

HAIR_STYLES = ["straight_long", "wavy_medium", "curly_short", "buzz", "ponytail",
               "bob", "bun", "braids", "bald", "side_part"]

LIGHTING = {
    "rembrandt": "แสงสามในสี่ เงาสามเหลี่ยมบนแก้ม (ดราม่า)",
    "butterfly": "แสงบนลงล่าง เงารูปผีเสื้อใต้จมูก (แฟชั่น)",
    "split": "แสงข้างครึ่งหน้า (ปริศนา)",
    "soft": "แสงนุ่มกระจาย (อบอุ่น เป็นธรรมชาติ)",
    "backlight": "แสงหลังตัวแบบ ขอบแสงรอบผม (cinematic)",
}

GENRES = {
    "lofi": {"bpm": (70, 90), "scale": "pentatonic minor", "mood": "ผ่อนคลาย อ่านหนังสือ"},
    "cinematic": {"bpm": (60, 100), "scale": "minor / dorian", "mood": "ยิ่งใหญ่ ดราม่า"},
    "pop": {"bpm": (100, 130), "scale": "major", "mood": "สดใส ติดหู"},
    "ambient": {"bpm": (50, 70), "scale": "pentatonic", "mood": "กว้าง ล่องลอย"},
    "hiphop": {"bpm": (80, 100), "scale": "minor", "mood": "จังหวะหนัก"},
    "thai_pop": {"bpm": (90, 120), "scale": "major / pentatonic", "mood": "อบอุ่น คุ้นเคย"},
}

SCALE_SEMITONES = {
    "major": [0, 2, 4, 5, 7, 9, 11],
    "minor": [0, 2, 3, 5, 7, 8, 10],
    "pentatonic minor": [0, 3, 5, 7, 10],
    "pentatonic": [0, 2, 4, 7, 9],
    "dorian": [0, 2, 3, 5, 7, 9, 10],
}


def character_spec(role="hero", skin="medium", hair="wavy_medium", lighting="soft"):
    """A studied spec for drawing a stylized human character with Pillow."""
    ratio = PROPORTIONS["heroic_head_ratio"] if role == "hero" else PROPORTIONS["head_height_ratio"]
    return {
        "role": role,
        "proportions": {"head_to_body": ratio, "shoulder_heads": PROPORTIONS["shoulder_width_heads"],
                        "eye_line": PROPORTIONS["eye_line"]},
        "skin": SKIN_TONES.get(skin, SKIN_TONES["medium"]),
        "hair": hair if hair in HAIR_STYLES else "wavy_medium",
        "lighting": LIGHTING.get(lighting, LIGHTING["soft"]),
        "note": "สไตล์การ์ตูน/เรื่องเล่า (stylized) — ไม่ใช่คนจริง (ต้องบริการ AI avatar แบบเสียเงิน)",
    }


def melody_spec(genre="lofi", bars=8):
    """Original, royalty-free melody parameters inspired by a genre's theory
    (NOT a copy of Suno or any copyrighted song)."""
    g = GENRES.get(genre, GENRES["lofi"])
    lo, hi = g["bpm"]
    scale = SCALE_SEMITONES.get(g["scale"], SCALE_SEMITONES["pentatonic minor"])
    rnd = random.Random(hash(genre) & 0xffff)
    notes = []
    for _ in range(bars * 4):
        deg = rnd.choice(scale)
        oct_shift = 12 * rnd.choice([0, 0, 0, 1])
        notes.append((deg + oct_shift, rnd.choice([0.5, 0.5, 1.0])))
    return {"ok": True, "genre": genre, "bpm": rnd.randint(lo, hi),
            "scale": g["scale"], "mood": g["mood"], "notes": notes,
            "note": "ทำนองต้นฉบับจากทฤษฎีแนวเพลง — ไม่ก็อปปี้ Suno/เพลงใด"}
