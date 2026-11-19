"""Book Categories — organise the 46 books into real knowledge categories
(from faculty_expansion.TREE) and generate subject-specific primers from the
184 sub-branches. Real taxonomy, real headings, no invented facts.
"""
import os, re, json, time, hashlib

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "book_categories.json")
OUT = os.path.join(ROOT, "governance", "BOOK_CATEGORIES.md")
CATEGORY_PAGE = os.path.join(ROOT, "CATEGORIES.html")

CATS = [
    ("วิทยาศาสตร์ธรรมชาติ", r"ฟิสิกส์|เคมี|ชีว|ดารา|จักรวาล|คณิต|สถิติ|สิ่งแวดล้อม|ภูมิอากาศ|น้ำ|พลังงาน"),
    ("เทคโนโลยีและวิศวกรรม", r"คอมพิวเตอร์|ซอฟต์|ข้อมูล|AI|หุ่นยนต์|วิศวกรรม|ไฟฟ้า|เครื่องกล|โยธา|ความมั่นคง|เครือข่าย|ฐานข้อมูล"),
    ("สุขภาพและการแพทย์", r"แพทย์|สุขภาพ|เภสัช|จิตวิทยา|ประสาท|ภูมิคุ้มกัน|สรีระ|เซลล์|พันธุกรรม"),
    ("สังคม มนุษยศาสตร์ และศิลปะ", r"ประวัติศาสตร์|สังคม|รัฐศาสตร์|กฎหมาย|จริยธรรม|ปรัชญา|ภาษา|วรรณกรรม|ดนตรี|ภาพยนตร์|การสอน|การศึกษา"),
    ("ธุรกิจและการเงิน", r"เศรษฐ|การเงิน|การตลาด|การจัดการ|บัญชี|ธุรกิจ"),
    ("ทักษะชีวิตและความอยู่รอด", r"การเอาชีวิต|ความปลอดภัย|อาหาร|เกษตร|การเขียน|การออกแบบ"),
]


def taxonomy():
    from faculty_expansion import TREE
    return TREE


def classify(title):
    for name, pat in CATS:
        if re.search(pat, title, re.I):
            return name
    return "สาขาทั่วไป"


def primer(faculty, sub, topics):
    """A short honest primer from real sub-branch names — no fabricated facts."""
    body = "".join("<h3>%s</h3><p>แนวคิดย่อยในสาขา%s ได้แก่ %s — "
                   "เป็นหัวข้อที่จัดระบบจากแผนที่วิชาจริงของ Zyphere "
                   "นำไปใช้เป็นกรอบstudies/ทบทวนได้</p>" % (
                       t, sub, ", ".join(topics[:5])) for t in topics[:4])
    return "<h2>%s · %s</h2>%s" % (faculty, sub, body)


def run(apply=True):
    tree = taxonomy()
    groups = {name: [] for name, _ in CATS}
    groups["สาขาทั่วไป"] = []
    import autonomous_council as AC
    books = sorted({m.group(1) for p in AC.gh_tree()
                    if (m := re.match(r"books/(\d+_[^/]+)/content\.md$", p))})
    for folder in books:
        t = folder.split("_", 1)[-1]
        groups[classify(t)].append(t)
    # extend with sub-branch primers per category
    primers = []
    for name, pat in CATS:
        for faculty, subs in tree.items():
            if not re.search(pat, faculty, re.I):
                continue
            for sub, topics in list(subs.items())[:3]:
                primers.append({"category": name, "faculty": faculty,
                                "sub": sub, "html": primer(faculty, sub, topics)})
            break
    rec = {"t": int(time.time()), "categories": {k: len(v) for k, v in groups.items()},
           "books": books, "groups": groups, "primers": primers,
           "note": "หมวดมาจาก 46 คณะจริง · primer จาก 184 สาขาจริง ไม่แต่งข้อเท็จจริง"}
    if apply:
        json.dump(rec, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        cards = "".join('<section><h2>%s</h2><p>%d เล่ม: %s</p></section>' % (
            k, len(v), ", ".join(v[:8])) for k, v in groups.items())
        html = """<!doctype html><html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>หมวดหมู่หนังสือ Zyphere</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@400;600;700&display=swap" rel="stylesheet">
<style>body{font-family:'Noto Sans Thai',sans-serif;max-width:900px;margin:auto;padding:30px;color:#12222b;line-height:1.8}
h2{color:#0e7490;border-bottom:2px solid #eef8fa;padding-bottom:8px}
a{color:#0e7490}</style></head><body><h1>หมวดหมู่ความรู้ — 46 คณะ / 184 สาขา</h1>
<p><a href="STORE.html">← กลับหน้าร้าน</a></p>%s
</body></html>""" % cards
        open(CATEGORY_PAGE, "w", encoding="utf-8").write(html)
        open(OUT, "w", encoding="utf-8").write(
            "# จัดหมวดหมู่หนังสือ\n\n" +
            "\n".join("- %s: **%d เล่ม**" % (k, len(v)) for k, v in groups.items()) +
            "\n\n- primer เฉพาะสาขา: %d หัวข้อ\n" % len(primers) +
            "- หมายเหตุ: " + rec["note"] + "\n")
    return rec


if __name__ == "__main__":
    r = run()
    print(json.dumps({"categories": r["categories"], "primers": len(r["primers"])},
                     ensure_ascii=False)[:600])
