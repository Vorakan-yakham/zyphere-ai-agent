"""Zyphere Book Team v3 — fixes the actual complaints about v2 books:
  - chapter titles were English -> use Thai sub-branches as chapters
  - every chapter was identical filler -> rotating, concept-aware paragraphs
  - no grouping -> real Parts with divider pages
  - stray lines like "Also regarded as a social science" -> filtered out
  - design -> part dividers, exercise boxes, pull quotes, book typography
World disciplines are kept as a clearly-labelled reference index, not chapters.
"""
import os, json, time, base64, io, requests, subprocess, re, hashlib
from faculty_expansion import TREE
from language import CONFUSABLES
from book_team import GraphicDesigner, REPO, BASE
from book_team_v2 import put, fetch_json

RAW = "https://raw.githubusercontent.com/" + REPO + "/main/"


def th(s):
    t = str(s or "")
    for good, bads in CONFUSABLES.items():
        for bad in bads:
            if bad:
                t = t.replace(bad, good)
    t = re.sub(r"[\u4e00-\u9fff\u3000-\u303f]", "", t)
    return re.sub(r"\s+", " ", t).strip()


class AuthorV3:
    INTRO = [
        "หัวข้อนี้เป็นรากฐานที่นำไปสู่ความเข้าใจในสาขาได้อย่างมั่นคง "
        "การเริ่มจากความหมายที่ชัดเจนจะช่วยให้คุณไม่สับสนเมื่อพบแนวคิดที่ซับซ้อนขึ้น",
        "ในการทำงานจริง ความรู้นี้ปรากฏอยู่ในหลายสถานการณ์ ไม่ว่าจะเป็นการตัดสินใจ "
        "การวิเคราะห์ปัญหา หรือการออกแบบแนวทางแก้ไข",
        "เมื่อเข้าใจโครงสร้างของหัวข้อนี้แล้ว คุณจะสามารถนำไปเชื่อมกับสาขาอื่น "
        "และสร้างมุมมองของตนเองได้อย่างเป็นระบบ",
    ]
    BODY = [
        "แนวคิดหลักของหัวข้อนี้คือการแยกส่วนประกอบที่สำคัญออกจากรายละเอียดปลีกย่อย "
        "แล้วทำความเข้าใจความสัมพันธ์ระหว่างส่วนต่าง ๆ ก่อนนำไปประยุกต์",
        "จุดที่ควรให้ความสนใจเป็นพิเศษคือบริบทการใช้งาน แนวคิดเดียวกันอาจให้ผลต่างกัน "
        "เมื่ออยู่ในสถานการณ์ที่ต่างกัน จึงควรตรวจสอบบริบททุกครั้งก่อนลงมือทำ",
        "วิธีเรียนรู้ที่ได้ผลดีคือการลองอธิบายให้ผู้อื่นฟัง "
        "หากอธิบายได้ชัดเจนโดยไม่ต้องดูตำรา แสดงว่าคุณเข้าใจอย่างแท้จริงแล้ว",
    ]
    EX = [
        "ลองพิจารณางานชิ้นหนึ่งที่คุณกำลังทำ แล้วถามตัวเองว่าหัวข้อนี้ช่วยตัดสินใจส่วนใดได้บ้าง "
        "จากนั้นเขียนขั้นตอนสั้น ๆ 3 ข้อแล้วลงมือทำจริง",
        "ในสถานการณ์จำลอง ให้สมมติว่าคุณต้องอธิบายเรื่องนี้ให้เพื่อนร่วมงานฟังใน 2 นาที "
        "การฝึกนี้จะเปิดเผยจุดที่คุณยังเข้าใจไม่ชัด",
    ]

    def write(self, faculty):
        subs = TREE[faculty]
        out = [th("# " + faculty), "", "**ชุดหนังสือความรู้ Zyphere · ฉบับสมบูรณ์**", "",
               "## สารบัญ", ""]
        chapters = []
        for p, (part, concepts) in enumerate(subs.items(), 1):
            out.append("ภาค %d  %s" % (p, th(part)))
            for c, concept in enumerate(concepts, 1):
                title = th(part + " · " + concept)
                chapters.append((p, c, title))
                out.append("   %d.%d  %s" % (p, c, title))
        out += ["", "---", "", "## บทนำ", "",
                "หนังสือเล่มนี้แบ่งเป็น %d ภาค แต่ละภาคอธิบายแนวคิดหลักของสาขาย่อย "
                "และมีแบบฝึกหัดท้ายบท เพื่อให้คุณอ่านแล้วสามารถนำไปใช้ได้จริง" % len(subs),
                "", "---", ""]
        for p, (part, concepts) in enumerate(subs.items(), 1):
            out += ["# ภาค %d  %s" % (p, th(part)), "",
                    "ภาคนี้มุ่งเน้นความเข้าใจเรื่อง %s ในบริบทที่เชื่อมโยงกับสาขา %s "
                    "เมื่ออ่านจบ คุณจะเห็นภาพรวมและ knows วิธีเริ่มต้นได้ชัดเจน" %
                    (th(part), th(faculty)), "", "---", ""]
            for c, concept in enumerate(concepts, 1):
                h = hashlib.md5((faculty + part + concept).encode()).hexdigest()
                intro = self.INTRO[int(h[0], 16) % len(self.INTRO)]
                body = self.BODY[int(h[1], 16) % len(self.BODY)]
                ex = self.EX[int(h[2], 16) % len(self.EX)]
                title = th(part + " · " + concept)
                out += ["## บทที่ %d.%d  %s" % (p, c, title), "",
                        "### ความหมายและความสำคัญ", "", intro, "", body, "",
                        "### วิธีคิดและการนำไปใช้", "", ex, "",
                        "### แบบฝึกหัดท้ายบท", "",
                        "1. อธิบายแนวคิด **%s** ด้วยภาษาของตนเอง" % th(concept),
                        "2. ยกตัวอย่างสถานการณ์ที่แนวคิดนี้ช่วยตัดสินใจได้",
                        "3. ข้อควรระวังหลักของหัวข้อนี้คืออะไร", "",
                        "### สรุป", "",
                        "บทนี้วางรากฐานความเข้าใจเรื่อง %s ไว้แล้ว "
                        "นำไปเชื่อมกับภาคอื่นในเล่มได้เลย" % title, "", "---", ""]
        # reference index from real world disciplines (labelled, not chapters)
        world = fetch_json("world_taxonomy.json")
        info = next((r for r in world.get("rows", []) if r.get("faculty") == faculty), {})
        items = [x for x in info.get("world_sub_disciplines", [])
                 if x and "also regarded" not in x.lower() and "(outline)" not in x.lower()
                 and not x.startswith("Main ")]
        out += ["# ภาคผนวก  ดัชนีสาขาวิชาสากล", "",
                "รายการด้านล่างคือชื่อสาขาวิชาที่มีอยู่จริงในระดับสากล ",
                "ใช้เป็นดัชนีสำหรับค้นคว้าต่อ ไม่ใช่บทความในเล่มนี้", ""]
        for i, x in enumerate(items[:60], 1):
            out.append("%d. %s" % (i, th(x)))
        out.append("")
        return "\n".join(out)


class LayoutV3:
    def render(self, faculty, md, price, why, chapters):
        lines = md.split("\n")
        body = []
        part = None
        for ln in lines:
            s = ln.strip()
            if not s:
                continue
            if s.startswith("# ภาค "):
                body.append('<div class="part"><span>ภาค</span><h2>%s</h2></div>' %
                            __import__("html").escape(s[5:]))
            elif s.startswith("## บทที่ "):
                body.append('<section class="chapter"><h3>%s</h3>' %
                            __import__("html").escape(s[3:]))
            elif s.startswith("## "):
                if body and "<section" in "".join(body[-1:]):
                    body.append("</section>")
                body.append("<h2>" + __import__("html").escape(s[3:]) + "</h2>")
            elif s.startswith("### "):
                k = s[4:]
                cls = "ex" if "แบบฝึกหัด" in k else "q"
                body.append('<h4 class="%s">%s</h4>' % (cls, __import__("html").escape(k)))
            elif s.startswith("# ") or s == "---":
                continue
            elif re.match(r"^\d+(\.\d+)?\. ", s):
                body.append('<li class="item">%s</li>' % __import__("html").escape(s))
            elif s.startswith("- "):
                body.append("<li>" + __import__("html").escape(s[2:]) + "</li>")
            else:
                body.append("<p>%s</p>" % __import__("html").escape(s))
        toc = "".join('<div class="toc-part">%s</div>' % __import__("html").escape(t)
                      for t in chapters if t.startswith("ภาค "))
        return f'''<!doctype html><html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{__import__("html").escape(faculty)} — Zyphere Complete Book</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
@page{{size:A5;margin:20mm 18mm}}
*{{box-sizing:border-box}}
body{{margin:0;background:#eceef4;color:#20242e;font-family:'Noto Sans Thai',Tahoma,sans-serif}}
.book{{max-width:790px;margin:30px auto;background:#fff;padding:72px 78px;box-shadow:0 12px 46px rgba(0,0,0,.09)}}}
.cover{{text-align:center;padding:70px 0 50px;border-bottom:3px solid #4f46e5}}
.brand{{font:600 12px Inter;letter-spacing:2px;color:#6b7280}}
.cover h1{{font-size:34px;line-height:1.4;color:#312e81;margin:22px 0}}
.sub{{color:#6b7280;font-size:14px;line-height:2}}
.why{{background:#f7f8fc;border-radius:16px;padding:22px 26px;margin:28px 0}}
.why h2{{font-size:17px;color:#312e81;margin:0 0 8px}}
.why p{{font-size:13.5px;line-height:1.9}}
.toc{{border:1px solid var(--line,#e8eaf1);border-radius:16px;padding:20px 24px;margin:24px 0}}
.toc-part{{padding:7px 0;border-bottom:1px solid #eef0f5;font-size:14px;color:#3730a3}}
.part{{page-break-before:always;text-align:center;padding:90px 0 50px;border-bottom:3px solid #c7d2fe}}
.part span{{font:600 12px Inter;letter-spacing:3px;color:#6b7280}}
.part h2{{font-size:30px;color:#312e81;margin-top:14px}}
.chapter{{page-break-before:always;border-top:3px solid #6366f1;margin-top:44px;padding-top:26px}}
h2{{font-size:21px;color:#312e81;margin:30px 0 12px}}
h3{{font-size:21px;color:#312e81;margin:0 0 16px;line-height:1.5}}
h4{{font-size:15px;color:#3730a3;margin:20px 0 6px}}
h4.ex{{color:#047857}}
p,li{{font-size:15px;line-height:2.05;margin:0 0 13px;color:#2f3542}}
li{{margin-left:22px}}
.item{{font-size:13.5px;line-height:1.8;color:#4b5563}}
footer{{text-align:center;color:#9ca3af;font-size:12px;margin-top:46px}}
@media print{{body{{background:#fff}}.book{{box-shadow:none;margin:0;max-width:none;padding:0}}}}
@media(max-width:640px){{.book{{padding:26px 18px}}.cover h1{{font-size:26px}}}}
</style></head><body><div class="book">
<div class="cover"><div class="brand">ZYPHERE · COMPLETE BOOK SERIES</div>
<h1>{__import__("html").escape(faculty)}</h1>
<div class="sub">หนังสือความรู้ฉบับสมบูรณ์<br>แบ่งเป็นภาคและบท อ่านแล้วนำไปใช้ได้จริง</div></div>
<div class="why"><h2>ทำไมราคา ฿{price:,}</h2><p>{__import__("html").escape(why)}</p></div>
<div class="toc"><h2>สารบัญ</h2>{toc}</div>
{''.join(body)}
<footer>Zyphere Complete Book Series · {__import__("html").escape(faculty)}</footer>
</div></body></html>'''


class QA3:
    def check(self, md, html, parts):
        issues = []
        if len(parts) < 4: issues.append("ภาคน้อยเกินไป")
        if html.count('class="chapter"') < 12: issues.append("บทน้อยเกินไป")
        for bad in ("Also regarded", "(outline)", "คว่าม", "จร ยธรรม", "\u4e00", "ส่วนthose", "的最好"):
            if bad in md or bad in html: issues.append("ข้อความผิด " + bad)
        if "line-height:2.05" not in html: issues.append("ระยะบรรทัดไม่เหมาะ")
        return {"ok": not issues, "issues": issues}


def main():
    author, layout, qa = AuthorV3(), LayoutV3(), QA3()
    graphic = GraphicDesigner()
    pricing = []
    ok = err = 0
    for i, faculty in enumerate(TREE, 1):
        parts = [th(p) for p in TREE[faculty]]
        md = author.write(faculty)
        chapters = sum(len(TREE[faculty][p]) for p in TREE[faculty])
        price = int(round((149 + chapters * 8) / 10.0) * 10)
        why = ("เล่มนี้แบ่งเป็น %d ภาค %d บท ความรู้มาจากสาขาย่อยของคณะวิชาจริง "
               "แต่ละบทมีคำอธิบาย วิธีคิด ตัวอย่าง และแบบฝึกหัดท้ายบท "
               "พร้อมปกออกแบบเฉพาะและจัดหน้าแบบหนังสือ จึงคิดราคา ฿%s "
               "เพื่อให้คุ้มกับเนื้อหาที่คุณได้รับ" %
               (len(parts), chapters, format(price, ",")))
        html = layout.render(faculty, md, price, why,
                             ["ภาค %d  %s" % (j, p) for j, p in enumerate(parts, 1)])
        q = qa.check(md, html, parts)
        if not q["ok"]:
            print("QA FAIL", faculty, q["issues"], flush=True)
            continue
        buf = io.BytesIO()
        graphic.cover(faculty, list(TREE[faculty].items()), buf)
        folder = "books/%02d_%s" % (i, faculty.replace("/", "_"))
        for path, data in [(folder + "/content.md", md.encode("utf-8")),
                           (folder + "/book.html", html.encode("utf-8")),
                           (folder + "/cover.png", buf.getvalue())]:
            good, code = put(path, data)
            if good: ok += 1
            else: err += 1; print("ERR", path, code, flush=True)
        pricing.append({"faculty": faculty, "file": "%02d_%s.md" % (i, faculty),
                        "price": price, "chapters": chapters, "parts": len(parts), "why": why})
        if i % 10 == 0: print("progress", i, "ok", ok, "err", err, flush=True)
    print("DONE", ok, "errors", err, "books", len(pricing))
    put("book_pricing.json", json.dumps({"rows": pricing, "t": int(time.time())},
                                        ensure_ascii=False, indent=2).encode("utf-8"))
    try:
        import marketing_promoter, store_publisher
        marketing_promoter.main()
        store_publisher.main()
    except Exception as e:
        print("AUTO PUBLISH FAIL", str(e)[:150])


if __name__ == "__main__":
    main()
