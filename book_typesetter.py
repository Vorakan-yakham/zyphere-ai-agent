"""Book Typesetter — turn the real source manuscript into a BOOK, not a text dump.

- Thai chapter names (translate academic field names; keep English only in a
  small glossary line where no standard Thai term exists — no fabricated facts)
- Real book structure: cover → title page → table of contents (Thai, dotted
  leaders, page numbers) → introduction → chapters with section headings →
  running footer with page numbers.
- Used for BOTH the free sample and the downloadable full book.
"""
import os, re, json, time, hashlib

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "book_typesetter.json")
OUT = os.path.join(ROOT, "governance", "BOOK_TYPESETTER.md")

# Full-phrase translations of real academic field names (localisation of NAMES,
# not invention of facts). Unknown terms fall back to word-level + English.
PHRASE = {
    "Acoustics": "อะคูสติก", "Quantum acoustics": "อะคูสติกควอนตัม",
    "Agrophysics": "ฟิสิกส์การเกษตร", "Aerodynamics": "อากาศพลศาสตร์",
    "Applied physics": "ฟิสิกส์ประยุกต์", "Accelerator physics": "ฟิสิกส์เครื่องเร่งอนุภาค",
    "Communication physics": "ฟิสิกส์การสื่อสาร", "Astrophysics": "ฟิสิกส์ดาราศาสตร์",
    "Atmospheric physics": "ฟิสิกส์บรรยากาศ",
    "Atomic, molecular, and optical physics": "ฟิสิกส์อะตอม โมเลกุล และแสง",
    "Atomic physics": "ฟิสิกส์อะตอม", "Biophysics": "ชีวฟิสิกส์",
    "Neurophysics": "ประสาทฟิสิกส์", "Chemical physics": "ฟิสิกส์เคมี",
    "Classical physics": "ฟิสิกส์คลาสสิก", "Computational physics": "ฟิสิกส์คำนวณ",
    "Condensed matter physics": "ฟิสิกส์สสารควบแน่น", "Cryogenics": "เทคนิคอุณหภูมิต่ำ",
    "Digital physics": "ฟิสิกส์ดิจิทัล", "Dynamics": "พลวัต",
    "Analytical dynamics": "พลวัตเชิงวิเคราะห์", "Astrodynamics": "พลวัตอวกาศ",
    "Brownian dynamics": "พลวัตบราวเนียน", "File dynamics": "พลวัตของไฟล์",
    "Flight dynamics": "พลวัตการบิน", "Fluid dynamics": "พลวัตของไหล",
    "Hydrodynamics": "พลศาสตร์ของไหล", "Fractional dynamics": "พลวัตเศษส่วน",
    "Geodynamics": "พลวัตโลก", "Molecular dynamics": "พลวัตโมเลกุล",
    "Newtonian dynamics": "พลวัตนิวโทเนียน", "Langevin dynamics": "พลวัตล็องฌ์แว็ง",
    "Quantum chromodynamics": "โครโมไดนามิกส์ควอนตัม",
    "Quantum electrodynamics": "อิเล็กโทรไดนามิกส์ควอนตัม",
    "Relativistic dynamics": "พลวัตสัมพัทธภาพ", "Stellar dynamics": "พลวัตดาวฤกษ์",
    "System dynamics": "พลวัตระบบ", "Thermodynamics": "เทอร์โมไดนามิกส์",
    "Vehicle dynamics": "พลวัตยานพาหนะ", "Econophysics": "เศรษฐฟิสิกส์",
    "Electricity": "ไฟฟ้า", "Electromagnetism": "แม่เหล็กไฟฟ้า",
    "Electrostatic": "ไฟฟ้าสถิต", "Magnetism": "แม่เหล็ก",
    "Engineering physics": "ฟิสิกส์วิศวกรรม",
    "Elementary particle physics": "ฟิสิกส์อนุภาคมูลฐาน",
    "Experimental physics": "ฟิสิกส์ทดลอง", "Geophysics": "ธรณีฟิสิกส์",
    "Biogeophysics": "ชีวธรณีฟิสิกส์", "Geomagnetism": "สนามแม่เหล็กโลก",
    "Kinematics": "จลนศาสตร์", "Fluid kinematics": "จลนศาสตร์ของไหล",
    "Relativistic kinematics": "จลนศาสตร์สัมพัทธภาพ", "Kinetics": "จลนพลศาสตร์",
    "Electrokinetics": "อิเล็กโทรจลนพลศาสตร์", "Homeokinetics": "โฮมีโอจลนพลศาสตร์",
    "Laser physics": "ฟิสิกส์เลเซอร์", "Materials physics": "ฟิสิกส์วัสดุ",
    "Mathematical physics": "ฟิสิกส์คณิตศาสตร์", "Mechanics": "กลศาสตร์",
    "Analytical mechanics": "กลศาสตร์เชิงวิเคราะห์", "Applied mechanics": "กลศาสตร์ประยุกต์",
    "Ballistics": "วิทยากระสุน", "Biomechanics": "ชีวกลศาสตร์",
    "Celestial mechanics": "กลศาสตร์ท้องฟ้า", "Classical mechanics": "กลศาสตร์คลาสสิก",
    "Continuum mechanics": "กลศาสตร์สสารต่อเนื่อง", "Fluid mechanics": "กลศาสตร์ของไหล",
    "Fracture mechanics": "กลศาสตร์การแตกร้าว",
    "Hamiltonian mechanics": "กลศาสตร์แฮมิลโทเนียน",
}
WORD = {
    "physics": "ฟิสิกส์", "quantum": "ควอนตัม", "science": "วิทยาศาสตร์",
    "mathematics": "คณิตศาสตร์", "statistics": "สถิติ", "logic": "ตรรกะ",
    "data": "ข้อมูล", "computer": "คอมพิวเตอร์", "software": "ซอฟต์แวร์",
    "biology": "ชีววิทยา", "chemistry": "เคมี", "medicine": "การแพทย์",
    "history": "ประวัติศาสตร์", "economics": "เศรษฐศาสตร์", "finance": "การเงิน",
    "art": "ศิลปะ", "music": "ดนตรี", "language": "ภาษา", "design": "การออกแบบ",
    "engineering": "วิศวกรรม", "electrical": "ไฟฟ้า", "mechanical": "เครื่องกล",
    "civil": "โยธา", "environmental": "สิ่งแวดล้อม", "climate": "ภูมิอากาศ",
    "energy": "พลังงาน", "biology": "ชีววิทยา", "psychology": "จิตวิทยา",
    "philosophy": "ปรัชญา", "ethics": "จริยธรรม", "law": "กฎหมาย",
    "education": "การศึกษา", "business": "ธุรกิจ", "marketing": "การตลาด",
}


def thai_term(en):
    en = (en or "").strip()
    if not en:
        return ""
    # already Thai (book title etc.) — never wrap in a redundant gloss
    if re.search(r"[\u0E00-\u0E7F]", en):
        return en
    if en in PHRASE:
        return PHRASE[en]
    words = re.split(r"\s*,\s*|\s+and\s+|\s+", en, flags=re.I)
    out = [WORD.get(w.strip().lower(), w.strip()) for w in words if w.strip()]
    th = "".join(out)
    # if nothing translated, keep English but mark it honestly as a proper name
    if all(w.lower() not in WORD and w not in PHRASE for w in out):
        return th + " (" + en + ")"
    return th


def inline(text):
    """Minimal markdown inline -> HTML, escaping real HTML first."""
    text = (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    return text


def parse(md):
    lines = (md or "").splitlines()
    title = "หนังสือความรู้ Zyphere"
    toc, chapters, intro = [], [], []
    cur = None
    for ln in lines:
        s = ln.strip()
        if s.startswith("# ") and not s.startswith("## "):
            title = s[2:].strip()
        elif s == "## สารบัญ":
            cur = "toc"
        elif s == "## บทนำ":
            cur = "intro"
        elif s.startswith("## บทที่ "):
            m = re.match(r"## บทที่\s+(\d+)\s+(.+)", s)
            num, name = (m.group(1), m.group(2).strip()) if m else ("?", s[9:])
            cur = {"num": num, "en": name, "th": thai_term(name), "blocks": []}
            chapters.append(cur)
        elif s.startswith("## "):
            cur = "intro" if "นำ" in s else None
        elif s == "---":
            continue
        elif cur == "toc":
            m = re.match(r"(\d+)\.\s*(.+)", s)
            if m:
                toc.append({"n": m.group(1), "en": m.group(2).strip(),
                            "th": thai_term(m.group(2).strip())})
        elif isinstance(cur, dict):
            cur["blocks"].append(ln)
        elif cur == "intro":
            intro.append(ln)
    return {"title": title, "toc": toc, "chapters": chapters, "intro": intro}


def render_blocks(lines):
    out, para, bullets, nums = [], [], [], []

    def flush():
        nonlocal para, bullets, nums
        if para:
            out.append("<p>%s</p>" % inline(" ".join(para)))
            para = []
        if bullets:
            out.append("<ul>%s</ul>" % "".join("<li>%s</li>" % inline(b) for b in bullets))
            bullets = []
        if nums:
            out.append("<ol>%s</ol>" % "".join("<li>%s</li>" % inline(n) for n in nums))
            nums = []

    for ln in lines:
        s = ln.strip()
        if s.startswith("### "):
            flush(); out.append("<h3>%s</h3>" % inline(s[4:]))
        elif s.startswith("- "):
            if para: flush()
            bullets.append(s[2:])
        elif re.match(r"^\d+\.\s", s):
            if para: flush()
            nums.append(re.sub(r"^\d+\.\s", "", s))
        elif not s:
            flush()
        else:
            if bullets or nums: flush()
            para.append(s)
    flush()
    return "\n".join(out)


def typeset(md, sample=False, max_chapters=3):
    b = parse(md)
    chapters = b["chapters"][:max_chapters] if sample else b["chapters"]
    # estimated page numbers from real content length (layout estimate, honest)
    pages, acc = [], 1
    for ch in chapters:
        pages.append(acc)
        acc += max(1, len("\n".join(ch["blocks"])) // 1100)
    toc_rows = []
    for i, ch in enumerate(chapters):
        toc_rows.append(
            '<li><span class="n">%s</span><span class="t">%s</span>'
            '<span class="dots"></span><span class="p">%d</span></li>' %
            (ch["num"], ch["th"], pages[i]))
    if sample and b["toc"]:
        # show the real full TOC names in Thai (first 16) for the sample
        toc_rows = []
        for it in b["toc"][:16]:
            toc_rows.append(
                '<li><span class="n">%s</span><span class="t">%s</span>'
                '<span class="dots"></span><span class="p">—</span></li>' %
                (it["n"], it["th"]))
    chap_html = []
    for i, ch in enumerate(chapters):
        chap_html.append(
            '<article class="page chapter"><div class="chapno">บทที่ %s</div>'
            '<h2>%s</h2><div class="en-name">%s</div>'
            '<div class="rule"></div>%s'
            '<div class="foot">ZYPHERE KNOWLEDGE LIBRARY · %s · หน้า %d</div></article>' %
            (ch["num"], ch["th"], ch["en"], render_blocks(ch["blocks"]),
             b["title"], pages[i]))
    intro = ("<article class='page'><h2>บทนำ</h2><div class='rule'></div>%s"
             "<div class='foot'>ZYPHERE KNOWLEDGE LIBRARY · หน้า 1</div></article>" %
             render_blocks(b["intro"])) if b["intro"] else ""

    note = ("<p class='note'>ตัวอย่างฟรี: สารบัญภาษาไทย + บทนำ + %d บทแรก "
            "จากต้นฉับจริง — <a href='STORE.html'>ดูฉบับเต็มในหน้าร้าน</a></p>" %
            len(chapters)) if sample else ""
    return HTML % {
        "title": b["title"], "thai_title": thai_term(b["title"]),
        "n": len(b["chapters"]), "toc": "\n".join(toc_rows),
        "intro": intro, "chapters": "\n".join(chap_html), "note": note,
        "year": time.strftime("%Y"),
    }


HTML = """<!doctype html><html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%(title)s — Zyphere Knowledge Library</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+Thai:wght@400;600;700&family=Noto+Sans+Thai:wght@400;600;700&display=swap" rel="stylesheet">
<style>
:root{--paper:#fffdf8;--ink:#1c2b33;--acc:#0e7490;--line:#d8e6ea}
*{box-sizing:border-box}body{margin:0;background:#e9eef0;color:var(--ink);
 font-family:'Noto Serif Thai',serif;line-height:1.95}
.page{max-width:760px;margin:26px auto;padding:64px 72px 70px;background:var(--paper);
 box-shadow:0 10px 40px rgba(20,40,50,.13);min-height:980px;position:relative}
.cover{background:linear-gradient(150deg,#08202e 0%%,#0b3a4a 58%%,#0e7490 100%%);
 color:#fff;display:flex;flex-direction:column;justify-content:space-between;min-height:980px}
.cover .top{display:flex;justify-content:space-between;align-items:center;
 font:600 14px 'Noto Sans Thai',sans-serif;letter-spacing:3px;opacity:.85}
.cover h1{font-size:58px;line-height:1.35;margin:0;font-weight:700}
.cover .sub{font:400 20px 'Noto Sans Thai',sans-serif;opacity:.88;margin-top:18px}
.cover .motif{height:250px;position:relative}
.cover .motif i{position:absolute;border:1px solid rgba(255,255,255,.28);border-radius:50%%}
.cover .bottom{font:400 15px 'Noto Sans Thai',sans-serif;opacity:.9;line-height:2}
.titlepage{text-align:center;display:flex;flex-direction:column;justify-content:center}
.titlepage h1{font-size:42px;margin:0 0 10px}
.titlepage .kicker{font:600 13px 'Noto Sans Thai',sans-serif;letter-spacing:4px;color:var(--acc)}
.titlepage .meta{margin-top:60px;font:400 16px 'Noto Sans Thai',sans-serif;color:#5d7380;line-height:2.4}
h2{font-size:30px;color:var(--acc);margin:0 0 6px}
.rule{height:3px;width:72px;background:var(--acc);margin:16px 0 34px}
h3{font-size:19px;color:#114b5e;margin:30px 0 10px;font-weight:700}
p{margin:0 0 16px;text-align:justify}
ul,ol{padding-left:26px;margin:0 0 18px}li{margin:7px 0}
.toc h2{text-align:center;font-size:34px;margin-bottom:8px}
.toc .intro{text-align:center;color:#5d7380;font:400 14px 'Noto Sans Thai',sans-serif;margin-bottom:34px}
.toc ol{list-style:none;padding:0;margin:0}
.toc li{display:flex;align-items:baseline;gap:10px;margin:11px 0;font-size:16px}
.toc .n{color:var(--acc);font:700 13px 'Noto Sans Thai',sans-serif;min-width:26px}
.toc .t{white-space:nowrap}
.toc .dots{flex:1;border-bottom:1px dotted #9fb8c0;transform:translateY(-4px)}
.toc .p{color:#5d7380;font:600 13px 'Noto Sans Thai',sans-serif;min-width:20px;text-align:right}
.chapno{font:700 13px 'Noto Sans Thai',sans-serif;letter-spacing:3px;color:var(--acc)}
.chapter h2{font-size:40px;margin-top:8px}
.en-name{font:400 13px 'Noto Sans Thai',sans-serif;color:#8aa2ab;margin-top:4px}
.foot{position:absolute;bottom:26px;left:72px;right:72px;border-top:1px solid var(--line);
 padding-top:12px;text-align:center;font:400 11px 'Noto Sans Thai',sans-serif;color:#8aa2ab;letter-spacing:1px}
.note{text-align:center;font:400 13px 'Noto Sans Thai',sans-serif;color:#5d7380;padding:18px}
.note a{color:var(--acc)}
@media print{body{background:#fff}.page{box-shadow:none;margin:0;page-break-after:always}}
@media(max-width:640px){.page{padding:38px 26px}.cover h1{font-size:38px}.chapter h2{font-size:30px}}
</style></head><body>
<article class="page cover"><div class="top"><span>ZYPHERE</span><span>KNOWLEDGE LIBRARY</span></div>
<div><div class="motif"><i style="width:260px;height:260px;left:120px;top:10px"></i>
<i style="width:180px;height:180px;left:190px;top:50px"></i>
<i style="width:90px;height:90px;left:235px;top:95px;background:rgba(34,211,238,.25)"></i></div>
<h1>%(thai_title)s</h1><div class="sub">%(title)s</div></div>
<div class="bottom">ชุดหนังสือความรู้ Zyphere · %(n)s บท<br>
เขียนและเรียบเรียงโดยทีมวิศวกร Zyphere · %(year)s<br>
ตัวอย่างอ่านฟรี — อ่านตรวจทานก่อนซื้อ</div></article>
<article class="page titlepage"><div class="kicker">ZYPHERE ORIGINAL</div>
<h1>%(thai_title)s</h1><p style="color:#5d7380">%(title)s</p>
<div class="meta">ชุดหนังสือความรู้ Zyphere<br>ทีมวิศวกร Zyphere<br>%(year)s</div>
<div class="foot">ZYPHERE KNOWLEDGE LIBRARY</div></article>
<article class="page toc"><h2>สารบัญ</h2><div class="intro">%(title)s · %(n)s บท</div>
<ol>%(toc)s</ol><div class="foot">ZYPHERE KNOWLEDGE LIBRARY · สารบัญ</div></article>
%(intro)s
%(chapters)s
<p class="note">%(note)s</p>
</body></html>
"""


def run(apply=True):
    import sample_publisher as SP
    rec = SP.run(apply=apply)
    items = rec.get("items", [])
    folders = SP.source_map()
    made = []
    for it in items:
        # rewrite the published sample into a real book layout
        import autonomous_council as AC
        folder = folders.get(it["title"])
        md = AC.gh_raw("books/%s/content.md" % folder) if folder else ""
        if not md:
            continue
        path = os.path.join(SP.SAMPLES, it["file"])
        if apply:
            open(path, "w", encoding="utf-8").write(typeset(md, sample=True))
        made.append(it["file"])
    out = {"t": int(time.time()), "typeset": len(made),
           "note": "สารบัญ/ชื่อบทภาษาไทย + โครงสร้างหนังสือจริง (ไม่แต่งข้อเท็จจริง)"}
    if apply:
        json.dump(out, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        open(OUT, "w", encoding="utf-8").write(
            "# จัดรูปแบบหนังสือ\n\n- แปลง **%d** เล่มเป็นหนังสือจริง\n" % len(made) +
            "- " + out["note"] + "\n")
    return out


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False))
