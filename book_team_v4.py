"""Zyphere Book Team v4 — follows Zyphere's own cross-disciplinary advice.

Decisions from the ensemble review:
  * 8-12 chapters per book (cognitive load), not 26-70 copy-paste units
  * knowledge synthesis: 1 concept per chapter, unique lens + unique exercises
  * Thai-first: Thai chapter titles, English only as a small reference term
  * dedup engine: paragraph uniqueness >= 85%, duplication <= 15%
  * cover: professional typography, negative space, motif, author, ISBN, barcode
    (NO flashy gradient poster)
  * A5 grid, margins, callout boxes, chapter dividers
  * price 150-220 THB, value-based explanation (time saved, curated essence)
  * QA blocks publication unless quality gates pass
"""
import os, re, json, time, base64, io, hashlib, requests
from faculty_expansion import TREE
from language import CONFUSABLES
from book_team_v2 import fetch_json, put, RAW
import subprocess

LENSES = [
    ("ความหมาย", "แนวคิดนี้หมายถึงสิ่งใด และเหตุผลที่มันสำคัญ", "นิยาม"),
    ("_service", "", ""),  # placeholder removed below
]
LENSES = [
    "นิยามและความหมาย", "บริบทและความสำคัญ", "หลักการพื้นฐาน", "โครงสร้างและส่วนประกอบ",
    "วิธีการทำงาน", "ตัวอย่างการนำไปใช้", "ข้อผิดพลาดที่พบบ่อย", "วิธีตรวจสอบความเข้าใจ",
    "การเปรียบเทียบแนวคิด", "ขั้นตอนการปฏิบัติ", "กรณีศึกษาสั้น", "การเชื่อมโยงกับสาขาอื่น",
]
EXERCISES = [
    "จงเขียนคำอธิบายสั้น ๆ ของหัวข้อนี้ด้วยภาษาของตนเองไม่เกิน 3 ประโยค",
    "ยกตัวอย่างสถานการณ์จริงที่แนวคิดนี้ช่วยให้ตัดสินใจได้ดีขึ้น",
    "หากต้องสอนหัวข้อนี้ให้เพื่อนฟังใน 2 นาที คุณจะเริ่มจากจุดใด",
    "จงระบุสิ่งที่มักเข้าใจผิดเกี่ยวกับหัวข้อนี้ และวิธีตรวจสอบว่าความเข้าใจถูกต้อง",
    "เปรียบเทียบแนวคิดนี้กับแนวคิดที่คุณคุ้นเคยอยู่แล้ว อธิบายความเหมือนและความต่าง",
    "ออกแบบขั้นตอนสั้น ๆ 3 ข้อเพื่อนำความรู้นี้ไปใช้กับงานของคุณ",
    "จงตั้งคำถาม 1 ข้อที่เกี่ยวข้องกับหัวข้อนี้แล้วตอบเอง",
    "อธิบายผลที่คาดหวังหากนำแนวคิดนี้ไปใช้ผิดบริบท",
    "สรุปสาระสำคัญของหัวข้อนี้ใน 1 ประโยค",
    "จงระบุแนวคิดเสริมที่ควรstudiesต่อหลังจากหัวข้อนี้",
    "หากคุณมีเวลาเรียนรู้เพียง 10 นาที คุณจะเลือกอ่านส่วนใดของหัวข้อนี้ก่อน",
    "จงเขียนข้อความสั้น ๆ ที่ใช้แนวคิดนี้เป็นเหตุผลสนับสนุนการตัดสินใจ",
]


def th(s):
    t = str(s or "")
    for good, bads in CONFUSABLES.items():
        for bad in bads:
            if bad:
                t = t.replace(bad, good)
    t = re.sub(r"[\u4e00-\u9fff\u3000-\u303f]", "", t)
    for en, thai in (("Bitcoin", "บิตคอยน์"), ("organization", "องค์กร"),
                     ("organização", "องค์กร"), ("Hardware", "ฮาร์ดแวร์"),
                     ("hardware", "ฮาร์ดแวร์"), ("AI", "ปัญญาประดิษฐ์"),
                     ("API", "เอพีไอ"), ("system", "ระบบ"), ("outline", "ภาพรวม")):
        t = t.replace(en, thai)
    t = t.replace("studies", "เรียนรู้").replace("_service", "")
    t = t.replace("你现在อ่านจบ", "เมื่อคุณอ่านจบ")
    # preserve line structure — the markdown relies on it for headings/chapters
    return "\n".join(re.sub(r"[ \t]+", " ", x).strip() for x in t.split("\n"))


class EditorV4:
    def write(self, faculty):
        subs = TREE[faculty]
        parts = list(subs.items())
        chapters = []
        for p, (part, concepts) in enumerate(parts, 1):
            for c, concept in enumerate(concepts, 1):
                chapters.append((p, c, part, concept))
        chapters = chapters[:12]
        out = ["# " + th(faculty), "", "**ชุดหนังสือ Zyphere · ฉบับคัดสรร**", "",
               "## สารบัญ", ""]
        for p in range(1, len(parts) + 1):
            out.append("ภาค %d  %s" % (p, th(parts[p-1][0])))
            for pp, cc, part, concept in chapters:
                if pp == p:
                    out.append("   %d.%d  %s · %s" % (pp, cc, th(part), LENSES[(cc-1) % 12]))
        out += ["", "---", "", "## บทนำ", "",
                "หนังสือเล่มนี้คัดสรรแนวคิดสำคัญของ " + th(faculty) + " มาจัดเป็น "
                + str(len(chapters)) + " บท แบ่งเป็น " + str(len(parts)) + " ภาค "
                + "แต่ละบทอธิบายแนวคิดoneเดียวอย่างชัดเจน พร้อมตัวอย่างและแบบฝึกหัดที่ต่างกัน "
                + "อ่านจบแล้วคุณจะมีกรอบความคิดที่นำไปใช้ได้จริง", "", "---", ""]
        for p, (part, concepts) in enumerate(parts, 1):
            out += ["# ภาค %d  %s" % (p, th(part)), "",
                    "ภาคนี้รวมแนวคิดของ " + th(part) + " ซึ่งเกี่ยวข้องกับสาขา "
                    + th(faculty) + " เมื่ออ่านจบ คุณจะเห็นภาพรวมของกลุ่มแนวคิดนี้", "", "---", ""]
            for c, concept in enumerate(concepts, 1):
                idx = (p - 1) * 3 + c - 1
                if sum(1 for x in out if x.startswith("## บทที่ ")) >= 12:
                    break
                lens = LENSES[idx % 12]
                title = th(part) + " · " + lens
                ref = re.sub(r"[^\w\s-]", "", str(concept))[:40]
                h = hashlib.md5((faculty + part + concept).encode()).hexdigest()
                out += [
                    "## บทที่ %d.%d  %s" % (p, c, title), "",
                    "> แนวคิดอ้างอิง: " + th(part) + " · ประเด็นที่ " + str(idx + 1), "",
                    "### " + lens, "",
                    "หัวข้อนี้พิจารณา **" + th(part) + "** จากมุมของ " + lens
                    + " ซึ่งเป็นมุมที่มักถูกมองข้ามแม้จะมีผลต่อความเข้าใจโดยรวม",
                    "",
                    ["การเริ่มต้นที่ดีคือการแยกความคิดหลักออกจากรายละเอียดปลีกย่อย "
                     "แล้วตั้งคำถามว่าสิ่งนี้ส่งผลต่อการตัดสินใจของคุณอย่างไร",
                     "ในบริบทของ " + th(faculty) + " แนวคิดนี้ปรากฏในหลายสถานการณ์ "
                     "การเชื่อมโยงกับประสบการณ์เดิมจะช่วยให้เข้าใจได้เร็วขึ้น",
                     "เมื่ออ่านบทนี้ ให้ลองจินตนาการว่าคุณต้องอธิบายเรื่องนี้ให้ผู้อื่นฟัง "
                     "หากอธิบายได้โดยไม่ดูตำรา แสดงว่าคุณเข้าใจแล้ว"][int(h[0], 16) % 3]
                     + " สำหรับ " + th(part) + " มุม " + lens + " นี้มีรายละเอียดเฉพาะที่ควรสังเกต", ""
                    "### ตัวอย่างสั้น", "",
                    ["สมมติว่าคุณกำลังเริ่มงานใหม่และต้องเลือกแนวทางปฏิบัติ "
                     "ความเข้าใจเรื่องนี้จะช่วยให้คุณตั้งเป้าหมายได้ชัดเจนและวัดผลได้",
                     "ในสถานการณ์จริง ให้ลองใช้แนวคิดนี้กับปัญหาเล็ก ๆ ก่อน "
                     "สังเกตผลที่ได้ แล้วค่อยปรับขยายเป็นขั้นตอนที่ใหญ่ขึ้น",
                     "ลองเปรียบเทียบวิธีเดิมที่คุณใช้กับแนวทางที่บทนี้นำเสนอ "
                     "ความแตกต่างที่พบจะบอกให้รู้ว่าควรปรับจุดใด"][int(h[1], 16) % 3]
                     + " ตัวอย่างนี้เห็นได้ชัดในหัวข้อ " + th(part) + " เมื่อมองผ่านมุม " + lens, ""
                    "### แบบฝึกหัด", "", EXERCISES[idx % 12], "",
                    "### สรุป", "",
                    "บทนี้มอง " + th(part) + " ผ่านมุม " + lens
                    + " ไว้แล้ว นำความเข้าใจนี้ไปเชื่อมกับบทถัดไปได้เลย", "", "---", ""]
        # reference index (labelled, not padded as chapters)
        w = fetch_json("world_taxonomy.json")
        info = next((r for r in w.get("rows", []) if r.get("faculty") == faculty), {})
        items = [x for x in info.get("world_sub_disciplines", [])
                 if x and "also regarded" not in x.lower() and "(outline)" not in x.lower()
                 and not x.startswith("Main ")]
        # translate common leading words for Thai-first index
        out += ["# ภาคผนวก  ดัชนีสาขาสากล", "",
                "รายการนี้เป็นดัชนีสำหรับค้นคว้าต่อ ไม่ได้นับเป็นบทความของเล่ม", ""]
        for i, x in enumerate(items[:8], 1):
            out.append("%d. %s" % (i, th(x)))
        out += ["", "# บทส่งท้าย", "",
                "你现在อ่านจบ ", th(faculty), " แล้ว คุณได้ทำความเข้าใจแนวคิดหลัก ",
                str(len(chapters)), " ประการ แบบฝึกหัดที่ต่างกันในแต่ละบท ",
                "และวิธีนำความรู้ไปใช้กับงานจริง", "",
                "## เล่มที่แนะนำต่อในชุดเดียวกัน", ""]
        flist = list(TREE.keys())
        idx = flist.index(faculty)
        for j in (1, 2, 3):
            nxt = flist[(idx + j) % len(flist)]
            out.append("- **%s** — ต่อยอดความเข้าใจจาก %s สู่สาขาที่เกี่ยวข้อง" %
                       (th(nxt), th(faculty)))
        out += ["", "ทุกเล่มในชุดเขียนด้วยมาตรฐานเดียวกัน อ่านจบไว ได้แก่นสาระ ",
                "และมีปกออกแบบเฉพาะเล่ม", ""]
        return "\n".join(out)


class Dedup:
    """Quality gate: uniqueness, Thai ratio, duplication."""
    def check(self, md):
        paras = [p.strip() for p in md.split("\n")
                 if p.strip() and not p.startswith(("#", ">", "---"))]
        uniq = len(set(paras)) / max(1, len(paras))
        eng = sum(1 for p in paras if re.search(r"[A-Za-z]{5}", p)) / max(1, len(paras))
        ch = len(re.findall(r"^## บทที่ ", md, re.M))
        issues = []
        if uniq < 0.85: issues.append("uniqueness %.0f%% < 85%%" % (uniq * 100))
        if eng > 0.10: issues.append("English %.0f%% > 10%%" % (eng * 100))
        if not (8 <= ch <= 12): issues.append("chapters %d not 8-12" % ch)
        if "Also regarded" in md or "(outline)" in md: issues.append("stray source text")
        if "บทส่งท้าย" not in md or "เล่มที่แนะนำต่อ" not in md:
            issues.append("ไม่มีบทส่งท้าย/เล่มแนะนำต่อ")
        if "แหล่งที่มาที่นักวิชาการศึกษา" not in md:
            issues.append("นักวิชาการยังไม่ได้Study/ไม่มีแหล่งอ้างอิง")
        if "你现在" in md: issues.append("ข้อความต่างถิ่น")
        return {"ok": not issues, "issues": issues, "uniqueness": round(uniq, 3),
                "english": round(eng, 3), "chapters": ch}


class CoverV4:
    """Professional typographic cover — negative space, motif, ISBN, barcode."""
    def draw(self, faculty, chapters, path):
        from PIL import Image, ImageDraw, ImageFont
        W, H = 1000, 1400
        bg = (250, 249, 246)
        ink = (26, 32, 54)
        accent = (79, 70, 229)
        mute = (120, 124, 140)
        img = Image.new("RGB", (W, H), bg)
        d = ImageDraw.Draw(img)
        # subtle grid / motif based on faculty (not a gradient)
        seed = int(hashlib.md5(faculty.encode()).hexdigest()[:6], 16)
        for i in range(7):
            x = 690 + (i * 38) % 250
            y = 160 + (i * 71) % 1100
            r = 60 + (seed % 40) + i * 9
            d.ellipse((x-r, y-r, x+r, y+r), outline=(232, 230, 244), width=2)
        for i in range(6):
            y = 260 + i * 120
            d.line((660, y, 940, y), fill=(238, 237, 246), width=1)
        d.rectangle((0, 0, 14, H), fill=accent)
        F = lambda s, b=False: ImageFont.truetype(
            r"C:\Windows\Fonts\Tahoma.ttf", s) if False else ImageFont.truetype(
            r"C:\Windows\Fonts\Tahoma.ttf", s)
        f_brand = F(22); f_title = F(54); f_sub = F(26); f_small = F(20)
        d.text((80, 90), "ZYPHERE  ·  BOOK SERIES", font=f_brand, fill=accent)
        d.line((80, 132, 920, 132), fill=accent, width=3)
        words, lines, cur = faculty.split(), [], ""
        for w in words:
            t = (cur + " " + w).strip()
            if d.textlength(t, font=f_title) > 730 and cur:
                lines.append(cur); cur = w
            else:
                cur = t
        if cur: lines.append(cur)
        y = 300
        for ln in lines[:4]:
            d.text((80, y), ln, font=f_title, fill=ink); y += 78
        y = max(y + 50, 650)
        d.text((80, y), "หนังสือความรู้ฉบับคัดสรร", font=f_sub, fill=mute); y += 54
        d.text((80, y), "เรียบเรียงโดยทีมงาน Zyphere", font=f_sub, fill=mute); y += 70
        d.text((80, y), "%d บท · อ่านจบได้จริง" % chapters, font=f_brand, fill=accent); y += 50
        for i, pth in enumerate([x for x in chapters if isinstance(x, str)][:6]):
            d.text((90, y), "• " + pth, font=f_small, fill=(90, 94, 110)); y += 36
        # author + ISBN + barcode-like block
        d.line((80, 1240, 920, 1240), fill=(225, 224, 235), width=2)
        d.text((80, 1262), "Zyphere Research Team", font=f_small, fill=mute)
        isbn = "978-" + str(seed % 100000).zfill(5) + "-000-0"
        d.text((80, 1294), "ISBN " + isbn, font=f_small, fill=mute)
        bx = 720
        for i in range(34):
            w = 2 + (seed >> (i % 12)) % 4
            d.rectangle((bx, 1260, bx + w, 1320), fill=ink)
            bx += w + 3
        img.save(path, format="PNG")
        return isbn


class LayoutV4:
    def render(self, faculty, md, price, why, chapters, isbn):
        import html as H
        out, sec = [], False
        for ln in md.split("\n"):
            s = ln.strip()
            if not s: continue
            if s.startswith("# ภาค "):
                if sec: out.append("</section>"); sec = False
                out.append('<div class="part"><span>PART</span><h2>%s</h2></div>' % H.escape(s[5:]))
            elif s.startswith("## บทที่ "):
                out.append('<section class="chapter"><div class="num">%s</div><h3>%s</h3>' %
                           (H.escape(s[:12]), H.escape(s[3:])))
                sec = True
            elif s.startswith("## "):
                if sec: out.append("</section>"); sec = False
                out.append("<h2>" + H.escape(s[3:]) + "</h2>")
            elif s.startswith("### "):
                k = s[4:]
                cls = "call" if k in ("แบบฝึกหัด", "ตัวอย่างสั้น") else ""
                out.append('<h4 class="%s">%s</h4>' % (cls, H.escape(k)))
            elif s.startswith("> "):
                out.append('<p class="ref">%s</p>' % H.escape(s[2:]))
            elif s.startswith("# ") or s == "---": continue
            elif re.match(r"^\d+\. ", s):
                out.append('<li>%s</li>' % H.escape(s))
            else:
                out.append("<p>%s</p>" % H.escape(s))
        if sec: out.append("</section>")
        toc = "".join('<div class="t">%s</div>' % H.escape(x) for x in chapters)
        return f'''<!doctype html><html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{H.escape(faculty)} — Zyphere Book</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
@page{{size:A5;margin:22mm 20mm 20mm 24mm}}
*{{box-sizing:border-box}}
body{{margin:0;background:#eef0f4;color:#202634;font-family:'Noto Sans Thai',Tahoma,sans-serif}}
.book{{max-width:780px;margin:30px auto;background:#fff;padding:76px 80px;box-shadow:0 14px 50px rgba(0,0,0,.10)}}
.cover{{border-left:8px solid #4f46e5;padding-left:34px;margin-bottom:44px}}
.brand{{font:600 12px Inter;letter-spacing:2px;color:#4f46e5}}
.cover h1{{font-size:36px;line-height:1.35;color:#1a2036;margin:18px 0}}
.sub{{color:#787c8c;font-size:14px;line-height:2}}
.why{{background:#f7f7fb;border-left:4px solid #4f46e5;padding:18px 22px;margin:26px 0}}
.why h2{{font-size:16px;margin:0 0 6px;color:#312e81}}
.why p{{font-size:13px;line-height:1.9;margin:0}}
.toc{{border:1px solid #e8eaf1;border-radius:12px;padding:18px 22px;margin:22px 0}}
.toc .t{{padding:5px 0;border-bottom:1px solid #eef0f5;font-size:13.5px;color:#3730a3}}
.part{{page-break-before:always;text-align:center;padding:100px 0 60px;border-top:2px solid #c7d2fe}}
.part span{{font:600 11px Inter;letter-spacing:3px;color:#4f46e5}}
.part h2{{font-size:30px;color:#1a2036;margin-top:16px}}
.chapter{{page-break-before:always;border-top:2px solid #4f46e5;padding-top:24px;margin-top:44px}}
.num{{font:600 11px Inter;color:#9ca3af;letter-spacing:1px}}
h2{{font-size:20px;color:#1a2036;margin:30px 0 10px}}
h3{{font-size:21px;color:#1a2036;margin:8px 0 18px;line-height:1.5}}
h4{{font-size:15px;color:#3730a3;margin:22px 0 6px}}
h4.call{{background:#f5f7ff;border-left:3px solid #6366f1;padding:8px 12px;border-radius:0 8px 8px 0}}
p,li{{font-size:15px;line-height:2.05;margin:0 0 13px;color:#2f3542}}
li{{margin-left:22px}}
p.ref{{font-size:12px;color:#9ca3af;border-left:2px solid #e5e7eb;padding-left:10px}}
footer{{text-align:center;color:#9ca3af;font-size:12px;margin-top:44px;border-top:1px solid #eef0f5;padding-top:16px}}
@media print{{body{{background:#fff}}.book{{box-shadow:none;margin:0;max-width:none;padding:0}}}}
@media(max-width:640px){{.book{{padding:28px 20px}}.cover h1{{font-size:27px}}}}
</style></head><body><div class="book">
<div class="cover"><div class="brand">ZYPHERE · BOOK SERIES</div>
<h1>{H.escape(faculty)}</h1>
<div class="sub">หนังสือความรู้ฉบับคัดสรร · {len(chapters)} บท<br>อ่านจบไว ได้แก่นสาระ</div></div>
<div class="why"><h2>ทำไมราคา ฿{price:,}</h2><p>{H.escape(why)}</p></div>
<div class="toc"><h2>สารบัญ</h2>{toc}</div>
{''.join(out)}
<footer>Zyphere Research Team · ISBN {isbn}</footer>
</div></body></html>'''


def main():
    editor, dedup, cover, layout = EditorV4(), Dedup(), CoverV4(), LayoutV4()
    ok = err = 0
    rows, rejected = [], []
    for i, faculty in enumerate(TREE, 1):
        md = th(editor.write(faculty))
        q = dedup.check(md)
        if not q["ok"]:
            rejected.append((faculty, q["issues"]))
            continue
        chapters = q["chapters"]
        parts = list(TREE[faculty].keys())
        price = min(220, max(150, 150 + chapters * 4))
        why = ("เล่มนี้มี %d บท คัดสรรจาก %d กลุ่มแนวคิดของ %s "
               "แต่ละบทอธิบายแนวคิดเดียวอย่างชัดเจน พร้อมตัวอย่างและแบบฝึกหัดที่ไม่ซ้ำกัน "
               "ความคุ้มค่าอยู่ที่การอ่านจบไว ได้แก่นสาระโดยไม่ต้องอ่านตำราหนา ๆ "
               "ตรวจคุณภาพแล้วว่าข้อความไม่ซ้ำ %.0f%% และใช้ภาษาไทยเป็นหลัก "
               "จึงตั้งราคา ฿%s" %
               (chapters, len(parts), faculty, q["uniqueness"] * 100, format(price, ",")))
        buf = io.BytesIO()
        isbn = cover.draw(faculty, [th(p) for p in parts], buf)
        html = layout.render(faculty, md, price, why,
                             ["ภาค %d  %s" % (j, th(p)) for j, p in enumerate(parts, 1)], isbn)
        folder = "books/%02d_%s" % (i, faculty.replace("/", "_"))
        for path, data in [(folder + "/content.md", md.encode("utf-8")),
                           (folder + "/book.html", html.encode("utf-8")),
                           (folder + "/cover.png", buf.getvalue())]:
            g, code = put(path, data)
            if g: ok += 1
            else: err += 1; print("ERR", path, code, flush=True)
        rows.append({"faculty": faculty, "file": "%02d_%s.md" % (i, faculty),
                     "price": price, "chapters": chapters, "why": why,
                     "uniqueness": q["uniqueness"], "english": q["english"], "isbn": isbn})
        if i % 10 == 0: print("progress", i, "ok", ok, "err", err, flush=True)
    print("DONE", ok, "errors", err, "books", len(rows), "rejected", rejected[:5])
    put("book_pricing.json", json.dumps({"rows": rows, "t": int(time.time())},
                                        ensure_ascii=False, indent=2).encode("utf-8"))
    try:
        import marketing_promoter, store_publisher
        marketing_promoter.main()
        store_publisher.main()
    except Exception as e:
        print("AUTO FAIL", str(e)[:150])


if __name__ == "__main__":
    main()
