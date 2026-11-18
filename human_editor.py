"""Human Editor — reshapes real book content into natural, human-paced prose.

In-house rules only: vary sentence length, keep paragraphs short, replace
AI-sounding openers with natural Thai connectors, and render book typography
(drop cap, section ornament, generous spacing). It never invents facts — it
rearranges the concepts already present in the source chapters.
"""
import re, hashlib

AI_CLICHE = ["ในบทนี้", "ดังนั้น", "สรุปแล้ว", "สิ่งสำคัญคือต้อง", "เป็นสิ่งสำคัญที่",
             "ในยุคปัจจุบัน", "บทนี้จะกล่าวถึง"]
CONNECT = ["เมื่อมองให้ใกล้ขึ้น ", "ในอีกมุมหนึ่ง ", "สิ่งที่ควรสังเกตคือ ",
           "ลองพิจารณาดู ", "จากตรงนี้ ", "และนี่คือจุดที่น่าสนใจ — "]


def split_sentences(text):
    t = re.sub(r"\s+", " ", str(text or "")).strip()
    parts = re.split(r"(?<=[.!?。！？])\s+|(?<=[ Koh])", t)
    return [p.strip() for p in parts if len(p.strip()) > 12]


def humanize(text, seed=0):
    sents = split_sentences(text)
    out = []
    for i, s in enumerate(sents):
        for c in AI_CLICHE:
            s = re.sub(re.escape(c), "", s, flags=re.I).strip()
        if i and i % 3 == 0 and not s.startswith(("ใน", "และ", "แต่")):
            s = CONNECT[(i//3 + seed) % len(CONNECT)] + s[0].lower() + s[1:]
        # break overly long sentences at natural Thai/English pauses
        if len(s) > 190:
            cut = s.rfind(", ", 80, 180)
            if cut < 0:
                cut = s.rfind(" ", 80, 180)
            if cut > 0:
                s = s[:cut] + " — " + s[cut+1:].strip()
        out.append(s)
    # group into short, human paragraphs (2-3 sentences)
    paras, cur = [], []
    for s in out:
        cur.append(s)
        if len(cur) >= (2 if len(s) < 80 else 1):
            paras.append(" ".join(cur)); cur = []
    if cur:
        paras.append(" ".join(cur))
    return paras or [str(text or "").strip()]


def md_to_human_paragraphs(md):
    blocks, buf = [], []
    for ln in md.splitlines():
        s = ln.strip()
        if re.match(r"(?m)^#{2,4} ", s):
            if buf:
                blocks.append(("p", " ".join(buf))); buf = []
            blocks.append(("h", re.sub(r"^#+\s*", "", s)))
        elif s and not s.startswith("<!--"):
            buf.append(re.sub(r"[*`#|>]", "", s))
    if buf:
        blocks.append(("p", " ".join(buf)))
    return blocks


CSS = """
:root{--ink:#1b2a32;--mut:#5d7480;--acc:#0e7490;--soft:#eff8fa;--line:#dcebef}
*{box-sizing:border-box}@page{size:A5;margin:24mm 18mm 18mm 24mm}
body{margin:0;background:#f4f7f8;color:var(--ink);
 font-family:'Noto Serif Thai',serif;line-height:1.7}
.book{max-width:660px;margin:0 auto;padding:0 28px 90px;background:#fff;
 box-shadow:0 0 0 1px var(--line);min-height:100vh}
.running{font:600 11px 'Noto Sans Thai',sans-serif;letter-spacing:1.6px;
 color:var(--acc);padding:22px 0 10px;border-bottom:1px solid var(--line);
 display:flex;justify-content:space-between}
.folio{text-align:center;font:500 12px 'Noto Sans Thai',sans-serif;
 color:#8aa0aa;margin:30px 0 0}
.chapter{padding:58px 0 10px;border-bottom:1px solid var(--line)}
.chapter:first-child{padding-top:34px}
.chapter h2{font:700 26px 'Noto Sans Thai',sans-serif;letter-spacing:-.3px;margin:0 0 8px}
.chapter h2:after{content:"";display:block;width:54px;height:3px;background:var(--acc);margin-top:16px}
.eyebrow{font-size:11px;letter-spacing:2.4px;color:var(--acc);font-weight:700}
p{margin:0 0 17px;font-size:16px;color:#2b3f49;text-indent:1.5em;
 max-width:65ch;line-height:1.7}
p.first{text-indent:0}
p.first:first-letter{font-size:58px;line-height:1;float:left;margin:4px 12px 0 0;color:var(--acc)}
.ornament{text-align:center;color:var(--acc);letter-spacing:12px;margin:34px 0 6px;opacity:.55}
.quote{background:var(--soft);border-left:4px solid var(--acc);
 border-radius:0 12px 12px 0;padding:18px 22px;margin:26px 0;color:#30515e}
.pay{background:var(--soft);border-radius:16px;padding:22px;margin-top:46px;font-size:15px}
@media(max-width:700px){.book{padding:0 18px 60px}p{font-size:16px}}
"""


def render(md, title, price=190, cover_uri=""):
    blocks = md_to_human_paragraphs(md)
    parts = []
    ch = 0
    first = False
    for kind, text in blocks:
        if kind == "h":
            ch += 1
            parts.append('<section class="chapter"><div class="eyebrow">บทที่ %02d</div><h2>%s</h2>'
                         % (ch, text))
            first = True
        else:
            paras = humanize(text, seed=ch)
            for p in paras[:8]:
                parts.append('<p class="%s">%s</p>' % ("first" if first else "", p))
                first = False
            parts.append('<div class="ornament">· · ·</div>')
            parts.append('</section>')
    return """<!doctype html><html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>%s</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@500;600;700&family=Noto+Serif+Thai:wght@400;500;600&display=swap" rel="stylesheet">
<style>%s</style></head><body>
<article class="book"><div class="running"><span>ZYPHERE · EBOOK</span><span></span></div><div class="quote"><b>%s</b><br>ทำไมต้องเรียน · สิ่งที่จะได้ · เนื้อหาจากต้นฉบับจริง<br>กรณีศึกษา · คำถามที่พบบ่อย · สรุป</div>
%s
<div class="pay"><b>สั่งซื้อ</b> · ฿%d<br>โอน PromptPay 0941939686 แล้วแจ้ง Zyphere เพื่อตรวจจ่ายด้วยตนเอง
<br><span style="font-size:13px;color:#5d7480">รอผ่านเกณฑ์คุณภาพก่อนเปิดขาย — ไม่มีการอ้างยอดขาย</span></div>
<div class="folio">—  —</div></article></body></html>""" % (title, CSS, title, "\n".join(parts), price)


def check_human(html):
    import re
    issues = []
    if html.count("<p ") < 8:
        issues.append("ย่อหน้าน้อยเกินไป")
    if "ในบทนี้" in html or "บทนี้จะกล่าวถึง" in html:
        issues.append("ยังมีสำนวน AI อยู่")
    lens = [len(x) for x in re.findall(r"<p[^>]*>(.*?)</p>", html, re.S)]
    if lens and max(lens) - min(lens) < 30 and len(lens) > 3:
        issues.append("จังหวะประโยคไม่แปรผัน")
    return issues
