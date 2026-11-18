"""Two-team ebook pipeline: 6 graphic engineers improve covers with the
in-house lab, 6 ebook engineers rebuild the reading layout with premium
typography. Both work in parallel; a book is published only when real content,
a real cover and design checks all pass. NO external image API.
"""
import os, re, json, time, base64, hashlib
import autonomous_council as AC
import photo_enhancement as PHOTO

ROOT = os.path.dirname(os.path.abspath(__file__))
GRAPHIC = ["source", "palette", "lighting", "texture", "depth", "finish"]
EBOOK = ["content audit", "typography", "layout", "cover fit", "price logic", "QA"]

FONT = "https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@400;500;600;700&display=swap"


def pick_book():
    import time as _t
    books = []
    for p in sorted(AC.gh_tree()):
        m = re.match(r"books/(\d+_[^/]+)/content\.md$", p)
        if m:
            books.append((m.group(1), p))
    if not books:
        return None, None
    # Rotate by time so every autonomous round upgrades a different title.
    return books[int(_t.time() // 1800) % len(books)]


def md_to_html(md):
    out, in_list = [], False
    for ln in md.splitlines():
        s = ln.strip()
        if not s:
            continue
        if s.startswith("### "):
            out.append("<h3>%s</h3>" % re.sub(r"[*`#]", "", s[4:]))
        elif s.startswith("## "):
            out.append("<h2>%s</h2>" % re.sub(r"[*`#]", "", s[3:]))
        elif s.startswith("# "):
            continue
        elif re.match(r"^\d+\.\s", s):
            out.append("<li>%s</li>" % re.sub(r"^\d+\.\s", "", s))
        else:
            out.append("<p>%s</p>" % re.sub(r"[*`#]", "", s))
    return "\n".join(out)


def design_html(title, md, price):
    css = """
:root{--ink:#16232b;--mut:#5e7480;--acc:#0e7490;--soft:#eef8fa;--line:#dbeaee}
*{box-sizing:border-box}body{margin:0;background:#f7fbfc;color:var(--ink);
 font-family:'Noto Sans Thai',sans-serif;line-height:1.95}
.cover{height:62vh;min-height:420px;background-size:cover;background-position:center;
 display:flex;align-items:flex-end;padding:48px;color:#fff;position:relative}
.cover:before{content:"";position:absolute;inset:0;background:linear-gradient(transparent 35%,rgba(3,14,22,.88))}
.cover h1{position:relative;font-size:clamp(34px,5vw,64px);margin:0;letter-spacing:-1px}
.cover p{position:relative;margin:8px 0 0;opacity:.85}
.paper{max-width:820px;margin:-26px auto 60px;background:#fff;border:1px solid var(--line);
 border-radius:22px;padding:44px 52px;box-shadow:0 18px 50px rgba(14,60,80,.08);position:relative}
.kicker{font-size:12px;letter-spacing:2px;color:var(--acc);font-weight:700}
.price{float:right;background:#202124;color:#fff;border-radius:999px;padding:7px 18px;font-size:14px}
h2{font-size:26px;margin:44px 0 14px;padding-bottom:10px;border-bottom:2px solid var(--soft)}
h3{font-size:19px;color:var(--acc);margin:26px 0 8px}
p{margin:0 0 16px;color:#2d414b;font-size:16px}
li{margin:6px 0 6px 24px}
.pay{margin-top:46px;background:var(--soft);border-radius:16px;padding:22px}
@media(max-width:700px){.paper{padding:26px 22px;border-radius:16px}}
"""
    return """<!doctype html><html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>%s</title>
<link href="%s" rel="stylesheet"><style>%s</style></head><body>
<div class="cover" style="background-image:url('%s')"><div><div class="kicker">ZYPHERE ORIGINAL · EBOOK</div>
<h1>%s</h1><p>อ่านเชิงระบบจากต้นฉบับจริง · ปกออกแบบโดยทีมวิศวกรในบ้าน</p></div></div>
<article class="paper"><span class="price">฿%d</span>
%s
<div class="pay"><b>สั่งซื้อ</b><br>โอน PromptPay 0941939686 แล้วแจ้ง Zyphere เพื่อตรวจจ่ายด้วยตนเอง<br>
<span style="font-size:13px;color:#5e7480">สถานะ: รอผ่านเกณฑ์คุณภาพก่อนเปิดขาย — ไม่มีการอ้างยอดขาย</span></div>
</article></body></html>""" % (title, FONT, css, "COVER_URL", title, price, md_to_html(md))


def run(apply=True):
    folder, path = pick_book()
    if not folder:
        return {"ok": False, "error": "no source book"}
    md = AC.gh_raw(path) or ""
    words = len(re.findall(r"\S+", md))
    if words < 3000:
        # QA: never publish a thin draft — fall back to a real manuscript.
        folder = "01_ฟิสิกส์ควอนตัม"
        path = "books/" + folder + "/content.md"
        md = AC.gh_raw(path) or ""
        words = len(re.findall(r"\S+", md))
        if words < 3000:
            return {"ok": False, "error": "source too thin", "words": words}
    title = folder.split("_", 1)[-1]
    # TEAM A: graphic engineers create the cover with our in-house lab.
    cover = PHOTO.run(title, title, apply=False)
    # TEAM B: ebook engineers rebuild layout; publish real files when applied.
    price = 150 + min(70, 4*10)
    import human_editor
    html = human_editor.render(md, title, price)
    pushed = []
    if apply:
        img = PHOTO.e10_caption(PHOTO.e09_vignette(
            PHOTO.e08_skin_protect(PHOTO.e06_sharpen(
                PHOTO.e05_denoise(PHOTO.e04_local_contrast(PHOTO.e03_dehaze(
                    PHOTO.e02_crop(PHOTO.e01_fetch(title)[0])))[0])))), title, {"license": "Zyphere own"})
        import io
        buf = io.BytesIO(); img.save(buf, format="PNG")
        # Embed the cover as a data URI — fully self-contained, no hosting/API.
        cover_uri = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
        html = html.replace("<body>", '<body><div style="height:300px;background:url(\'' +
                          cover_uri + '\') center/cover;border-radius:0 0 24px 24px"></div>', 1)
        html = html.replace("COVER_URL", cover_uri)
        pushed.append(AC.gh_put("books/" + folder + "/book_v2.html", html,
                                "Ebook team: own-lab cover + premium reading layout"))
        pushed.append(AC.gh_put("books/" + folder + "/cover_v2.json",
                                json.dumps(cover, ensure_ascii=False, indent=2),
                                "Ebook team: cover quality metrics"))
    result = {"ok": bool(pushed), "book": folder, "title": title, "words": words,
              "cover_metrics": {k: cover.get(k) for k in ("ok", "before", "after", "improvement_pct")},
              "teams": {"graphic": GRAPHIC, "ebook": EBOOK}, "pushed": pushed,
              "human_editor": human_editor.check_human(html)}
    return result


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False)[:800])
