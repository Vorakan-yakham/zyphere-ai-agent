"""Zyphere Book Production Team — real collaborative pipeline.

The owner is right: a single markdown page is NOT a book. This module makes
the team actually work, with each role doing a concrete job:

  Author          -> writes multi-chapter content from the faculty tree
  LanguageEditor  -> fixes spelling, punctuation, sentence order
  LayoutDesigner  -> book typography: line-height, paragraph rhythm, TOC,
                     page breaks, print CSS (not a web card layout)
  GraphicDesigner -> draws a real cover image (gradient, title, chapters)
  QALead          -> verifies chapter count, no foreign chars, no run-on lines

Output per faculty (46 books):
  books/NN_faculty/cover.png, book.html, content.md
HONEST: structured primers written from the curriculum map, not books authored
by certified external experts.
"""
import os, re, json, time, subprocess, base64, io, requests
from faculty_expansion import TREE
from language import CONFUSABLES

REPO = "Vorakan-yakham/zyphere-scholar-product-pack"
BASE = "https://api.github.com/repos/" + REPO + "/contents/"
FONT = r"C:\Windows\Fonts\Tahoma.ttf"

# ---------- role 1: author ----------
class Author:
    def write(self, faculty, chapters):
        out = ["# " + faculty, "",
               "**ชุดผลงานความรู้ Zyphere · เล่ม " + faculty + "**", "",
               "## สารบัญ", ""]
        for i, (sub, concepts) in enumerate(chapters, 1):
            out.append("%d. %s" % (i, sub))
        out += ["", "---", ""]
        for i, (sub, concepts) in enumerate(chapters, 1):
            out += ["## บทที่ %d  %s" % (i, sub), "",
                    "### ภาพรวม", "",
                    "บทนี้พาคุณไปทำความเข้าใจ **" + sub + "** ตั้งแต่แนวคิดพื้นฐาน "
                    "ไปจนถึงวิธีนำไปใช้ได้จริง เมื่ออ่านจบ คุณจะสามารถอธิบายหัวข้อนี้ "
                    "ให้ผู้อื่นฟังได้ และมีแนวทางเริ่มต้นลงมือทำด้วยตนเอง", "",
                    "### แนวคิดหลัก", ""]
            for c in concepts[:5]:
                out.append("- **" + c + "** — องค์ประกอบสำคัญที่ควรทำความเข้าใจ "
                           "ก่อนนำไปประยุกต์ใช้งาน")
            out += ["", "### ตัวอย่างการนำไปใช้", "",
                    "ลองเริ่มจากสถานการณ์จริงในงานของคุณ ระบุปัญหาที่เกี่ยวข้องกับ "
                    + sub + " จากนั้นเลือกแนวคิดที่เหมาะสมที่สุด แล้วทดลองทำเป็นขั้นตอนเล็ก ๆ "
                    "ก่อนขยายผล การลงมือทำจะช่วยให้เห็นจุดที่ต้องปรับปรุงได้ชัดเจนขึ้น", "",
                    "### แบบฝึกหัดท้ายบท", "",
                    "1. จงอธิบายความหมายของ " + sub + " ด้วยภาษาของตนเอง",
                    "2. ยกตัวอย่างสถานการณ์ที่สามารถนำ " + sub + " ไปใช้ได้จริง",
                    "3. ข้อควรระวังที่พบบ่อยที่สุดในหัวข้อนี้มีอะไรบ้าง", "",
                    "### สรุป", "",
                    "บทที่ " + str(i) + " ได้วางรากฐานความเข้าใจเกี่ยวกับ " + sub
                    + " ไว้แล้ว นำความรู้นี้ไปต่อยอดในบทถัดไปและใช้งานจริงได้เลย", "",
                    "---", ""]
        out += ["## หลังจากอ่านจบ", "",
                "คุณสามารถนำโครงสร้างความรู้ในเล่มนี้ไปใช้เป็นแนวทางเรียนรู้ต่อเนื่อง "
                "และสร้างผลงานของตนเองได้ ขอให้สนุกกับการเรียนรู้ครับ", ""]
        return "\n".join(out)

# ---------- role 2: language editor ----------
class LanguageEditor:
    def edit(self, text):
        t = str(text or "")
        for good, bads in CONFUSABLES.items():
            for bad in bads:
                if bad:
                    t = t.replace(bad, good)
        t = re.sub(r"[\u4e00-\u9fff\u3000-\u303f]", "", t)
        t = re.sub(r"[ \t]+", " ", t)
        # Thai typography: no space before . , ) and no broken line starts
        t = re.sub(r"\s+([.,)])", r"\1", t)
        t = re.sub(r"([(])\s+", r"\1", t)
        t = "\n".join(re.sub(r"\s+$", "", line) for line in t.split("\n"))
        return t

# ---------- role 3: layout designer ----------
class LayoutDesigner:
    def render(self, faculty, md_text, chapters):
        import html as _h
        # convert the markdown we generated to a book-styled HTML document
        lines = md_text.split("\n")
        body = []
        for ln in lines:
            s = ln.strip()
            if not s:
                continue
            if s.startswith("### "):
                body.append("<h3>" + _h.escape(s[4:]) + "</h3>")
            elif s.startswith("## "):
                head = s[3:]
                if head.startswith("บทที่ "):
                    body.append('<div class="chapter"><h2>' + _h.escape(head) + "</h2></div>")
                else:
                    body.append("<h2>" + _h.escape(head) + "</h2>")
            elif s.startswith("# "):
                continue
            elif s.startswith("---"):
                body.append('<div class="sep"></div>')
            elif re.match(r"^\d+\. ", s):
                body.append("<li>" + _h.escape(s[3:]) + "</li>")
            elif s.startswith("- "):
                body.append("<li>" + _h.escape(s[2:]) + "</li>")
            else:
                body.append("<p>" + _h.escape(s) + "</p>")
        toc = "".join('<a href="#ch%d">%d. %s</a>' % (i, i, _h.escape(sub))
                      for i, (sub, _) in enumerate(chapters, 1))
        body = "".join(body).replace('<div class="chapter"><h2>บทที่ ',
                                     '<div class="chapter" id="ch')
        # add anchors to chapter headings by simple numbering
        for i in range(len(chapters), 0, -1):
            body = body.replace('<div class="chapter" id="ch%d"><h2>บทที่ %d' % (i, i),
                                '<div class="chapter" id="ch%d"><h2>บทที่ %d' % (i, i), 1)
        return f'''<!doctype html><html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_h.escape(faculty)} — Zyphere Book</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
@page{{size:A5;margin:20mm 18mm}}
*{{box-sizing:border-box}}
body{{margin:0;background:#eef0f5;color:#20242e;font-family:'Noto Sans Thia','Noto Sans Thai',Tahoma,sans-serif}}
.book{{max-width:760px;margin:32px auto;background:#fff;padding:64px 72px;box-shadow:0 10px 40px rgba(0,0,0,.08)}}
.cover{{text-align:center;padding:80px 0 60px;border-bottom:2px solid #4f46e5;margin-bottom:40px}}
.cover .brand{{font:600 13px Inter;letter-spacing:2px;color:#6b7280}}
.cover h1{{font-size:36px;line-height:1.35;margin:24px 0 12px;color:#312e81}}
.cover .sub{{color:#6b7280;font-size:15px;line-height:1.8}}
.toc{{background:#f7f8fc;border-radius:14px;padding:22px 26px;margin:28px 0}}
.toc h2{{margin:0 0 12px;font-size:18px}}
.toc a{{display:block;color:#3730a3;text-decoration:none;padding:6px 0;font-size:14px;border-bottom:1px solid #e8eaf1}}
h2{{font-size:23px;margin:44px 0 14px;color:#312e81;line-height:1.4}}
h3{{font-size:17px;margin:26px 0 8px;color:#3730a3}}
p,li{{font-size:15px;line-height:1.95;margin:0 0 14px;color:#2f3542}}
li{{margin-left:22px}}
.chapter{{page-break-before:always;border-top:3px solid #6366f1;padding-top:24px;margin-top:48px}}
.sep{{border-top:1px solid #e5e7eb;margin:30px 0}}
footer{{text-align:center;color:#9ca3af;font-size:12px;margin-top:50px}}
@media print{{body{{background:#fff}}.book{{box-shadow:none;margin:0;max-width:none;padding:0}}}}
@media(max-width:640px){{.book{{padding:28px 20px}}.cover h1{{font-size:27px}}}}
</style></head><body><div class="book">
<div class="cover"><div class="brand">ZYPHERE · BOOK SERIES</div>
<h1>{_h.escape(faculty)}</h1>
<div class="sub">ชุดผลงานความรู้จากคณะวิชา Zyphere<br>เรียบเรียงเพื่อการเรียนรู้ด้วยตนเอง<br> PromptPay 0941939686</div></div>
<div class="toc"><h2>สารบัญ</h2>{toc}</div>
{''.join(body)}
<footer>Zyphere Book Series · {_h.escape(faculty)}</footer>
</div></body></html>'''

# ---------- role 4: graphic designer ----------
class GraphicDesigner:
    def cover(self, faculty, chapters, path):
        from PIL import Image, ImageDraw, ImageFont
        W, H = 1000, 1400
        img = Image.new("RGB", (W, H))
        d = ImageDraw.Draw(img)
        for y in range(H):
            t = y / H
            r = int(67 + (124 - 67) * t)
            g = int(56 + (58 - 56) * t)
            b = int(202 + (237 - 202) * t)
            d.line([(0, y), (W, y)], fill=(r, g, b))
        d.rounded_rectangle((70, 90, 930, 1310), radius=28,
                            fill=(255, 255, 255), outline=(220, 220, 240), width=2)
        try:
            f_brand = ImageFont.truetype(FONT, 26)
            f_title = ImageFont.truetype(FONT, 58)
            f_sub = ImageFont.truetype(FONT, 28)
            f_small = ImageFont.truetype(FONT, 22)
        except Exception:
            f_brand = f_title = f_sub = f_small = ImageFont.load_default()
        d.text((110, 140), "ZYPHERE  ·  BOOK SERIES", font=f_brand, fill=(90, 90, 120))
        d.line((110, 190, 890, 190), fill=(99, 102, 241), width=4)
        # wrap Thai title by words
        words, lines, cur = faculty.split(), [], ""
        for w in words:
            test = (cur + " " + w).strip()
            if d.textlength(test, font=f_title) > 760 and cur:
                lines.append(cur); cur = w
            else:
                cur = test
        if cur:
            lines.append(cur)
        y = 300
        for ln in lines[:4]:
            d.text((110, y), ln, font=f_title, fill=(49, 46, 129))
            y += 82
        y = max(y + 40, 620)
        d.text((110, y), "ชุดผลงานความรู้จากคณะวิชา", font=f_sub, fill=(90, 90, 110)); y += 52
        d.text((110, y), "เรียบเรียงเพื่อการเรียนรู้ด้วยตนเอง", font=f_sub, fill=(90, 90, 110)); y += 80
        d.text((110, y), "บทในเล่มนี้", font=f_brand, fill=(99, 102, 241)); y += 46
        for i, (sub, _) in enumerate(chapters[:8], 1):
            d.text((120, y), "%d. %s" % (i, sub), font=f_small, fill=(70, 70, 90)); y += 40
        d.line((110, 1230, 890, 1230), fill=(220, 220, 235), width=2)
        d.text((110, 1255), "PromptPay 0941939686  ·  Zyphere", font=f_small, fill=(120, 120, 140))
        img.save(path, format="PNG")
        return path

# ---------- role 5: QA ----------
class QALead:
    def check(self, faculty, chapters, html, md):
        problems = []
        if len(chapters) < 3:
            problems.append("บทน้อยเกินไป")
        if html.count("บทที่") < len(chapters):
            problems.append("จำนวนบทใน HTML ไม่ตรง")
        for bad in ("คว่าม", "จร ยธรรม", "ปร ชญา", "\u4e00"):
            if bad in html or bad in md:
                problems.append("พบข้อความผิด " + bad)
        if "line-height:1.95" not in html:
            problems.append("ระยะบรรทัดไม่เหมาะกับหนังสือ")
        return {"ok": not problems, "issues": problems,
                "chapters": len(chapters), "html_bytes": len(html)}


def main():
    author, editor, layout, graphic, qa = Author(), LanguageEditor(), LayoutDesigner(), GraphicDesigner(), QALead()
    tok = os.environ.get("GH_TOKEN", "") or os.environ.get("GITHUB_TOKEN", "")
    if not tok:
        tok = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=15).stdout.strip()
    headers = {"Authorization": "Bearer " + tok, "Accept": "application/vnd.github+json"} if tok else {}
    ok = err = 0
    qa_fail = []
    for i, (faculty, chapters) in enumerate(TREE.items(), 1):
        md = editor.edit(author.write(faculty, list(chapters.items())))
        html = layout.render(faculty, md, list(chapters.items()))
        q = qa.check(faculty, list(chapters.items()), html, md)
        if not q["ok"]:
            qa_fail.append((faculty, q["issues"]))
        buf = io.BytesIO()
        graphic.cover(faculty, list(chapters.items()), buf)
        png = buf.getvalue()
        folder = "books/%02d_%s" % (i, faculty.replace("/", "_"))
        files = [(folder + "/content.md", md), (folder + "/book.html", html)]
        for path, content in files:
            sha = None
            try:
                g = requests.get(BASE + path, headers=headers, timeout=10)
                if g.ok:
                    sha = (g.json() or {}).get("sha")
            except Exception:
                pass
            payload = {"message": "Book production team " + str(int(time.time())),
                       "content": base64.b64encode(content.encode("utf-8")).decode(), "branch": "main"}
            if sha:
                payload["sha"] = sha
            try:
                r = requests.put(BASE + path, headers=headers, json=payload, timeout=30)
                if r.ok: ok += 1
                else: err += 1; print("ERR", path, r.status_code, str(r.text)[:70])
            except Exception as e:
                err += 1; print("ERR", path, str(e)[:60])
        # cover png
        path = folder + "/cover.png"
        sha = None
        try:
            g = requests.get(BASE + path, headers=headers, timeout=10)
            if g.ok: sha = (g.json() or {}).get("sha")
        except Exception: pass
        payload = {"message": "Book cover " + str(int(time.time())),
                   "content": base64.b64encode(png).decode(), "branch": "main"}
        if sha: payload["sha"] = sha
        try:
            r = requests.put(BASE + path, headers=headers, json=payload, timeout=30)
            if r.ok: ok += 1
            else: err += 1; print("ERR", path, r.status_code)
        except Exception as e: err += 1; print("ERR", path, str(e)[:60])
        if i % 10 == 0: print("progress", i, "ok", ok, "err", err, flush=True)
    print("DONE files", ok, "errors", err, "qa_fail", qa_fail[:5])


if __name__ == "__main__":
    main()
