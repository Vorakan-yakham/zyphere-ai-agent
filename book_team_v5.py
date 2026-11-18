"""Zyphere Book Team v5 — applies the studied book design system.

Uses v4's editor/dedup/cover, and a new typesetter with:
  front matter (half title, title page, copyright, contents, introduction)
  running head + folio, figures from Wikimedia with attribution
  serif body / sans headings, A5 grid, callout boxes
  back matter (conclusion, glossary, colophon with typeface notes)
"""
import io, json, time, html as H, hashlib
from faculty_expansion import TREE
from book_team_v4 import EditorV4, Dedup, th
from book_team_v2 import put
from book_team import GraphicDesigner
from book_design_system import figure, publish_standard

ISO = "https://creativecommons.org/licenses/by-sa/4.0/"


class TypesetterV5:
    def render(self, faculty, md, price, why, chapters, isbn, fig):
        parts, chapters_html, in_ch, sec = [], [], False, False
        for ln in md.split("\n"):
            s = ln.strip()
            if not s:
                continue
            if s.startswith("# ภาค "):
                if in_ch: chapters_html.append("</section>"); in_ch = False
                parts.append(H.escape(s[5:]))
                chapters_html.append('<div class="part"><span>PART</span><h2>%s</h2></div>' %
                                     H.escape(s[5:]))
            elif s.startswith("## บทที่ "):
                chapters_html.append('<section class="chapter"><div class="folio">%s</div><h3>%s</h3>' %
                                     (H.escape(s[:12]), H.escape(s[3:])))
                in_ch = True
            elif s.startswith("## "):
                if in_ch: chapters_html.append("</section>"); in_ch = False
                chapters_html.append("<h2>" + H.escape(s[3:]) + "</h2>")
            elif s.startswith("### "):
                k = s[4:]
                cls = "call" if k in ("แบบฝึกหัด", "ตัวอย่างสั้น", "ตัวอย่างสั้น") else ""
                chapters_html.append('<h4 class="%s">%s</h4>' % (cls, H.escape(k)))
            elif s.startswith("> "):
                chapters_html.append('<p class="ref">%s</p>' % H.escape(s[2:]))
            elif s.startswith("# ") or s == "---":
                continue
            elif s.startswith("- ") or s.startswith("1.") or s[0:2].isdigit():
                chapters_html.append("<li>%s</li>" % H.escape(s))
            else:
                chapters_html.append("<p>%s</p>" % H.escape(s))
        if in_ch: chapters_html.append("</section>")
        toc = "".join('<div class="t">%s</div>' % H.escape(x) for x in parts)
        fig_html = ""
        if fig:
            fig_html = ('''<figure class="fig"><img src="%s" alt="%s">
<figcaption>ภาพ: %s · ที่มา: <a href="%s">Wikimedia / Wikipedia</a>
(CC BY-SA)</figcaption></figure>''' % (H.escape(fig.get("url", "")), H.escape(faculty),
    H.escape(fig.get("caption", "")), H.escape(fig.get("source", ""))))
        return f'''<!doctype html><html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{H.escape(faculty)} — Zyphere Book</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@500;600;700&family=Noto+Serif+Thai:wght@400;500;600&display=swap" rel="stylesheet">
<style>
@page{{size:A5;margin:20mm 18mm 18mm 24mm}}
*{{box-sizing:border-box}}
html{{--body:'Noto Serif Thai',Tahoma,serif;--head:'Noto Sans Thai',sans-serif;--ink:#1f2433;--mut:#737888;--acc:#4f46e5;--line:#e6e8f0}}
body{{margin:0;background:#eceef3;color:var(--ink);font-family:var(--body)}}
.book{{max-width:720px;margin:28px auto;background:#fff;padding:76px 84px 84px;box-shadow:0 14px 48px rgba(0,0,0,.10)}}
.half{{text-align:center;font:600 14px var(--head);letter-spacing:3px;color:var(--acc);padding:40px 0 70px;border-bottom:1px solid var(--line)}}
.title{{text-align:center;padding:80px 0 50px}}
.title h1{{font:700 40px/1.35 var(--head);color:var(--ink);margin:0 0 20px}}
.title .by{{font:500 14px var(--head);color:var(--mut)}}
.copy{{font-size:11px;color:var(--mut);line-height:1.9;border-top:1px solid var(--line);padding-top:18px;margin-bottom:30px}}
.running{{font:500 10px var(--head);color:#b6bac7;border-bottom:1px solid var(--line);padding-bottom:8px;margin-bottom:24px;display:flex;justify-content:space-between}}
.toc{{border:1px solid var(--line);border-radius:10px;padding:20px 24px;margin:24px 0}}
.toc .t{{padding:6px 0;border-bottom:1px solid #eef0f5;font:500 13.5px var(--head);color:#3730a3}}
.why{{background:#f7f8fc;border-left:3px solid var(--acc);padding:16px 20px;margin:24px 0}}
.why h2{{font:600 15px var(--head);margin:0 0 6px;color:#312e81}}
.why p{{font-size:12.5px;line-height:1.9;margin:0}}
.fig{{margin:26px 0;text-align:center}}
.fig img{{max-width:100%;border-radius:8px;box-shadow:0 4px 16px rgba(0,0,0,.08)}}
.fig figcaption{{font-size:11px;color:var(--mut);line-height:1.7;margin-top:8px}}
.fig a{{color:var(--acc)}}
.part{{page-break-before:always;text-align:center;padding:110px 0 60px;border-top:2px solid #c7d2fe}}
.part span{{font:600 11px var(--head);letter-spacing:4px;color:var(--acc)}}
.part h2{{font:700 30px var(--head);margin-top:18px}}
.chapter{{page-break-before:always;border-top:2px solid var(--acc);padding-top:22px;margin-top:44px}}
.folio{{font:600 10px var(--head);color:#b6bac7;letter-spacing:1px}}
h2{{font:700 20px var(--head);color:var(--ink);margin:30px 0 12px}}
h3{{font:700 21px/1.5 var(--head);color:var(--ink);margin:8px 0 18px}}
h4{{font:600 15px var(--head);color:#3730a3;margin:22px 0 6px}}
h4.call{{background:#f5f7ff;border-left:3px solid var(--acc);padding:8px 12px;border-radius:0 8px 8px 0}}
p,li{{font:400 15px/1.75 var(--body);margin:0 0 13px;color:#2d3340}}
li{{margin-left:22px}}
p.ref{{font-size:12px;color:var(--mut);border-left:2px solid var(--line);padding-left:10px}}
.gloss{{background:#f7f8fc;border-radius:10px;padding:18px 22px;margin-top:30px}}
.gloss h2{{margin-top:0}}
.colophon{{font:500 11px var(--head);color:var(--mut);border-top:1px solid var(--line);margin-top:36px;padding-top:14px;line-height:1.9}}
footer{{text-align:center;font-size:11px;color:var(--mut);margin-top:30px}}
@media print{{body{{background:#fff}}.book{{box-shadow:none;margin:0;max-width:none;padding:0}}}}
@media(max-width:640px){{.book{{padding:30px 20px}}.title h1{{font-size:28px}}}}
</style></head><body><div class="book">
<div class="half">ZYPHERE · BOOK SERIES</div>
<div class="title"><h1>{H.escape(faculty)}</h1><div class="by">Zyphere Research Team</div></div>
<div class="copy">© {time.strftime('%Y')} Zyphere · เอกสารเพื่อการเรียนรู้ · ISBN {isbn}<br>
เนื้อหานี้เป็นโครงสร้างความรู้สำหรับการเรียนรู้ด้วยตนเอง มิใช่ตำราที่ผ่านการตรวจสอบโดยผู้เชี่ยวชาญภายนอก</div>
<div class="running"><span>ZYPHERE</span><span>{H.escape(faculty)}</span></div>
<div class="why"><h2>ทำไมราคา ฿{price:,}</h2><p>{H.escape(why)}</p></div>
{fig_html}
<div class="toc"><h2>สารบัญ</h2>{toc}</div>
{''.join(chapters_html)}
<div class="gloss"><h2>อภิธานศัพท์</h2>
<p><b>ภาค (Part)</b> — กลุ่มแนวคิดที่เกี่ยวข้องกัน · <b>บท (Chapter)</b> — หน่วยเรียนรู้หนึ่งแนวคิด</p>
<p><b>แบบฝึกหัด</b> — คำถามเพื่อตรวจสอบความเข้าใจของผู้อ่าน · <b>Colophon</b> — รายละเอียดการจัดทำเล่ม</p></div>
<div class="colophon">จัดหน้าด้วยระบบ Book Design Standard ของ Zyphere · A5 · เนื้อหา Noto Serif Thai 15px leading 1.7 ·
หัวข้อ Noto Sans Thai · ภาพจาก Wikimedia ภายใต้ CC BY-SA · ออกแบบปกโดยฝ่ายกราฟฟิก Zyphere</div>
<footer>ISBN {isbn} · Zyphere Complete Book Series</footer>
</div></body></html>'''


def main():
    publish_standard()
    editor, dedup, cover = EditorV4(), Dedup(), GraphicDesigner()
    typeset = TypesetterV5()
    ok = err = 0
    rows = []
    for i, faculty in enumerate(TREE, 1):
        md = th(editor.write(faculty))
        q = dedup.check(md)
        if not q["ok"]:
            print("QA FAIL", faculty, q["issues"], flush=True)
            continue
        chapters = q["chapters"]
        price = min(220, max(150, 150 + chapters * 4))
        why = ("เล่มนี้มี %d บท แบ่งเป็นภาค คัดสรรแนวคิดจากคณะวิชาจริง "
               "แต่ละบทมีคำอธิบาย ตัวอย่าง และแบบฝึกหัดที่ไม่ซ้ำ "
               "จัดหน้าแบบหนังสือ A5 มีภาพประกอบจากแหล่งสาธารณะพร้อมเครดิต "
               "ความคุ้มค่าคืออ่านจบไว ได้แก่นสาระโดยไม่ต้องอ่านตำราหนา ๆ "
               "ตรวจแล้วว่าข้อความไม่ซ้ำ %.0f%% และใช้ภาษาไทยเป็นหลัก "
               "จึงตั้งราคา ฿%s" % (chapters, q["uniqueness"] * 100, format(price, ",")))
        buf = io.BytesIO()
        isbn = cover.draw(faculty, list(TREE[faculty].keys()), buf)
        f = figure(faculty)
        html = typeset.render(faculty, md, price, why,
                              ["ภาค %d  %s" % (j, th(p)) for j, p in enumerate(TREE[faculty], 1)],
                              isbn, f)
        folder = "books/%02d_%s" % (i, faculty.replace("/", "_"))
        for path, data in [(folder + "/content.md", md.encode("utf-8")),
                           (folder + "/book.html", html.encode("utf-8")),
                           (folder + "/cover.png", buf.getvalue())]:
            g, code = put(path, data)
            if g: ok += 1
            else: err += 1; print("ERR", path, code, flush=True)
        rows.append({"faculty": faculty, "file": "%02d_%s.md" % (i, faculty),
                     "price": price, "chapters": chapters, "why": why,
                     "uniqueness": q["uniqueness"], "figure": bool(f), "isbn": isbn})
        if i % 10 == 0: print("progress", i, "ok", ok, "err", err, flush=True)
    print("DONE", ok, "errors", err, "books", len(rows),
          "with figures", sum(1 for r in rows if r["figure"]))
    put("book_pricing.json", json.dumps({"rows": rows, "t": int(time.time())},
                                        ensure_ascii=False, indent=2).encode("utf-8"))
    try:
        import marketing_promoter, store_publisher
        marketing_promoter.main(); store_publisher.main()
    except Exception as e:
        print("AUTO FAIL", str(e)[:150])


if __name__ == "__main__":
    main()
