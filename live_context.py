"""Live Context — what the system ACTUALLY knows right now, from real files.

Injected into the assistant's system prompt so it never says 'my data stops in
2024' while the autonomous modules are harvesting 2026 sources every pulse.
"""
import os, json, time

ROOT = os.path.dirname(os.path.abspath(__file__))


def _j(n):
    try:
        return json.load(open(os.path.join(ROOT, "data", n), encoding="utf-8"))
    except Exception:
        return {}


def context(max_chars=1400):
    now = time.strftime("%Y-%m-%d")
    parts = ["[ข้อมูลสดของระบบ ณ " + now + " — อัพเดทอัตโนมัติทุก pulse]",
             "ระบบค้นข้อมูลจากอินเทอร์เน็ตจริงทุกนาที (Wikipedia, OpenAlex, "
             "Openverse, Wikimedia, NASA, เอกสารทางการ) — ไม่ได้จำกัดที่ปี 2024"]
    g = _j("global_code_lessons.json")
    if g:
        parts.append("แหล่งที่ดึงล่าสุด: " + ", ".join(
            str(l.get("source")) for l in g.get("lessons", [])[:6]
            if l.get("status") == 200))
    t = _j("tech_radar.json")
    if t:
        titles = []
        for items in t.get("by_topic", {}).values():
            for x in (items or [])[:2]:
                titles.append(str(x.get("title", ""))[:60])
        if titles:
            parts.append("เทคโนโลยีที่ระบบกำลังติดตาม: " + ", ".join(titles[:6]))
    a = _j("autonomy_last.json")
    if a:
        parts.append("รอบพัฒนาล่าสุดมีผลงานจริงใน governance/AUTONOMY_LIVE.md")
    s = " | ".join(parts)
    return s[:max_chars]


if __name__ == "__main__":
    print(context())
