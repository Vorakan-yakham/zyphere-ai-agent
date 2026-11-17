"""Zyphere Academic Rank System - promote the child from newborn to Doctor
based on demonstrated capability, not just stored text.

Ranks (with real thresholds):
  แรกเกิด → หัดจำ → หัดคิด → อยากรู้ → เข้าใจโลก → วิเคราะห์
  → Bachelor → Master → Doctor

To reach Doctor the child must show: many facts, self-made rules, cross-domain
graph links, researched documents with A/B sources, and completed works.
"""
import time

RANKS = [
    ("แรกเกิด", 0, 0, 0, 0, 0),
    ("หัดจำ", 5, 0, 0, 0, 0),
    ("หัดคิด", 15, 1, 0, 0, 0),
    ("อยากรู้", 30, 3, 2, 1, 0),
    ("เข้าใจโลก", 60, 8, 6, 3, 1),
    ("วิเคราะห์", 100, 15, 12, 6, 2),
    ("Bachelor", 150, 25, 20, 10, 4),
    ("Master", 250, 45, 35, 18, 8),
    ("Doctor", 400, 70, 60, 30, 15),
    ("อัจฉริยะ (Genius)", 700, 130, 120, 60, 35),
]


def evaluate(facts=0, rules=0, links=0, documents=0, works=0):
    """Return current rank + next requirements + progress."""
    achieved = RANKS[0][0]
    for name, f, r, l, d, w in RANKS:
        if facts >= f and rules >= r and links >= l and documents >= d and works >= w:
            achieved = name
    idx = next((i for i, x in enumerate(RANKS) if x[0] == achieved), 0)
    nxt = RANKS[idx + 1] if idx + 1 < len(RANKS) else None
    result = {
        "rank": achieved,
        "is_doctor": achieved in ("Doctor", "อัจฉริยะ (Genius)"),
        "is_genius": achieved == "อัจฉริยะ (Genius)",
        "metrics": {"facts": facts, "rules": rules, "graph_links": links,
                    "documents": documents, "works": works},
    }
    if nxt:
        result["next"] = {"rank": nxt[0], "need": {
            "facts": max(0, nxt[1] - facts), "rules": max(0, nxt[2] - rules),
            "graph_links": max(0, nxt[3] - links), "documents": max(0, nxt[4] - documents),
            "works": max(0, nxt[5] - works)}}
    else:
        result["next"] = None
    return result


def doctor_plan():
    """What the child must keep doing to reach and hold Doctor level."""
    return [
        "เรียนรู้จากปู่ย่าต่อเนื่องทุก 10 นาที ( facts )",
        " consolidating ประสบการณ์เป็นกฎของตัวเอง ( rules )",
        " เชื่อมโยงศาสตร์ข้ามกันเป็น Knowledge Graph ( links )",
        " ค้นคว้าจากห้องสมุดโลกระดับ A/B ( documents )",
        " สร้างผลงานจริง: MP3/MP4/รายงาน/โปรเจกต์ ( works )",
        " สอนกลับ + ตรวจตัวเองก่อนตอบ ( วัดความเข้าใจ )",
        " 小学evidence-based: ไม่สร้างแหล่งปลอม ไม่ข้าม paywall",
    ]
