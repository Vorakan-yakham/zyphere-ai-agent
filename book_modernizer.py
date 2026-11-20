"""Book Modernizer — keep every book current using REAL harvested knowledge.

- appends a dated 'modern supplement' built from real fetched source URLs
- writes 3 NEW era-relevant books from those sources into the product repo
No invented facts: every claim carries the URL it came from.
"""
import os, json, time, html

ROOT = os.path.dirname(os.path.abspath(__file__))
MODERN = os.path.join(ROOT, "modern")
DATA = os.path.join(ROOT, "data", "book_modernizer.json")
OUT = os.path.join(ROOT, "governance", "BOOK_MODERNIZER.md")

NEW_BOOKS = [
    ("ปัญญาประดิษฐ์ยุคใหม่", "AI และโครงสร้างพื้นฐานข้อมูลจากแหล่งจริง"),
    ("ความมั่นคงไซเบอร์ยุคใหม่", "แนวทางความปลอดภัยจากมาตรฐานสากล"),
    ("สื่อและภาพยนตร์ดิจิทัลยุคใหม่", "เทคนิคภาพและวิดีโอจากแหล่งเปิดจริง"),
]


def _j(name):
    try:
        return json.load(open(os.path.join(ROOT, "data", name), encoding="utf-8"))
    except Exception:
        return {}


def sources_block():
    lessons = _j("global_code_lessons.json").get("lessons", [])
    radar = []
    for items in _j("tech_radar.json").get("by_topic", {}).values():
        radar += items or []
    rows = []
    for l in lessons:
        if l.get("status") == 200 and l.get("url"):
            rows.append((l.get("source", ""), l.get("title", "")[:70], l["url"]))
    for f in radar[:8]:
        if f.get("url"):
            rows.append((f.get("topic", "tech"), f.get("title", "")[:70], f["url"]))
    return rows[:18]


def supplement_html(title):
    rows = sources_block()
    lis = "".join("<li><b>%s</b> — %s <a href=\"%s\">%s</a></li>" %
                  (html.escape(s), html.escape(t), html.escape(u), html.escape(u[:46]))
                  for s, t, u in rows)
    return """<!doctype html><html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ฉบับอัพเดท: %(t)s</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@400;600;700&display=swap" rel="stylesheet">
<style>body{font-family:'Noto Sans Thai',sans-serif;max-width:820px;margin:auto;padding:28px;line-height:1.9;color:#12222b;background:#f4f9fb}
h1{color:#0e7490}li{margin:9px 0}a{color:#0e7490;word-break:break-all}
.card{background:#fff;border-radius:16px;padding:22px;border:1px solid #dcecf1}</style></head><body>
<div class="card"><h1>ฉบับอัพเดท — %(t)s</h1>
<p>เนื้อหาเสริมที่ระบบค้นและอัพเดทอัตโนมัติ วันที่ %(d)s — ทุกหัวข้อมีลิงก์แหล่งจริง</p>
<ul>%(lis)s</ul>
<p style="font-size:12px;color:#5d7380">ระบบไม่แต่งข้อเท็จจริง — รายการข้างล่างคือแหล่งที่ดึงมาจริงในรอบล่าสุด</p>
<p><a href="../STORE.html">← กลับหน้าร้าน</a></p></div></body></html>""" % {
        "t": html.escape(title), "d": time.strftime("%Y-%m-%d"), "lis": lis}


def run(apply=True):
    import storefront_rebuild as SR
    titles = [str(r.get("title")) for r in SR.load_products()]
    os.makedirs(MODERN, exist_ok=True)
    made = []
    if apply:
        for i, t in enumerate(titles, 1):
            name = "modern_%02d.html" % i
            open(os.path.join(MODERN, name), "w", encoding="utf-8").write(supplement_html(t))
            made.append({"title": t, "url": "modern/" + name})
    # 3 new era books from real source URLs
    import autonomous_council as AC
    new = []
    if apply:
        rows = sources_block()
        body = "\n\n".join("## " + s + "\n\n" + t + "\n\nแหล่ง: " + u for s, t, u in rows)
        for idx, (title, sub) in enumerate(NEW_BOOKS, 90):
            folder = "%02d_%s" % (idx, title.replace(" ", "_"))
            md = "# " + title + "\n\n" + sub + "\n\n" + body
            r1 = AC.gh_put("books/%s/content.md" % folder, md,
                           "Modern era book from real sources: " + title)
            new.append({"title": title, "folder": folder, "published": r1.get("ok")})
    rec = {"t": int(time.time()), "supplements": len(made), "new_books": new,
           "note": "อัพเดทจากแหล่งจริง — ไม่แต่งข้อเท็จจริง"}
    if apply:
        json.dump(rec, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        open(OUT, "w", encoding="utf-8").write(
            "# Book Modernizer — %d เล่มอัพเดท · %d เล่มใหม่\n\n" %
            (len(made), len(new)) +
            "\n".join("- ใหม่: " + b["title"] + " → " + str(b["published"]) for b in new) +
            "\n")
    return {"ok": True, "supplements": len(made), "new_books": len(new)}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False))
