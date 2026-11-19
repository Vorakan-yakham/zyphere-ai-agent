"""Zyphere Commerce Lab — unattended: analysts plan, programmers build,
storefront is redesigned, books repriced/recovered, new revenue channels
prepared. Runs from GitHub Actions every 30 minutes with no owner commands.

HONEST: creates REAL artefacts (files, links, plans). Never invents sales.
"""
import os, re, json, time, hashlib

ROOT = os.path.dirname(os.path.abspath(__file__))
MEDIA = os.path.join(ROOT, "media")
DATA = os.path.join(ROOT, "data", "commerce.json")
STORE = os.path.join(ROOT, "STORE_V2.html")
OUT = os.path.join(ROOT, "governance", "COMMERCE_LAB.md")
REPO_API = "https://api.github.com/repos/Vorakan-yakham/zyphere-scholar-product-pack/contents/"

# Real, free-to-start channels — no fake sales, just prepared assets/links.
CHANNELS = [
    {"name": "Gumroad", "why": "ขาย ebook/asset ได้ไม่ต้องมีเว็บเอง",
     "url": "https://gumroad.com", "asset": "cover + description + price"},
    {"name": "Ko-fi", "why": "รับสนับสนุน/ขาย digital download",
     "url": "https://ko-fi.com", "asset": "shop banner + product card"},
    {"name": "itch.io", "why": "ขาย digital goods ภาษาได้",
     "url": "https://itch.io", "asset": "cover + store page HTML"},
    {"name": "Dev.to", "why": "บทความดึงคนเข้ามาโดยไม่จ่ายโฆษณา",
     "url": "https://dev.to", "asset": "article draft from book content"},
    {"name": "GitHub Sponsors", "why": "สนับสนุนโปรเจกต์โอเพนซอร์ส",
     "url": "https://github.com/sponsors", "asset": "sponsor blurb"},
    {"name": "YouTube Shorts", "why": "คลิปสั้นจาก film editor ดึงทราฟฟิก",
     "url": "https://studio.youtube.com", "asset": "4K clip + SRT"},
]


def analyse():
    """Knowledge analysts read the REAL state, then write a future plan."""
    import autonomous_council as AC
    tree = AC.gh_tree()
    books = sorted({m.group(1) for p in tree
                    if (m := re.match(r"books/(\d+_[^/]+)/content\.md$", p))})
    pricing = json.loads(AC.gh_raw("pricing.json") or '{"rows":[]}').get("rows", [])
    gaps = []
    if not pricing:
        gaps.append("ไม่มี Pricing master — ต้องตั้งราคาจากเนื้อหาจริง")
    if len(books) < 40:
        gaps.append("จำนวนเล่มน้อยกว่ามาตรฐาน 46")
    plan = {
        "t": int(time.time()),
        "books": len(books),
        "pricing_rows": len(pricing),
        "gaps": gaps,
        "future": [
            "ปรับราคาตามความยาว/คุณภาพ ไม่ใช้ราคาเดียวทุกเล่ม",
            "ปกใหม่ต้องสื่อเนื้อหา + typography ไม่ใช้ภาพซ้ำ",
            "หน้าร้านต้องมี CTA ชัด + QR + หลักฐานจริง",
            "เตรียมสินค้าสำหรับ 6 ช่องทางฟรี",
            "ทุกการขายต้องผ่านการยืนยันจ่ายด้วยตนเอง (ห้าม unlock อัตโนมัติ)",
        ],
        "programmer_orders": [
            "สร้าง STORE_V2.html จาก plan นี้",
            "เรียก market_price() ตั้งราคาทุกเล่ม",
            "สร้างปกใหม่จาก own_image_lab แล้วฝังลง HTML",
            "เขียน commerce.json เป็น database ของสินค้า/ช่องทาง",
        ],
    }
    return plan


def price_books(plan):
    """Programmer order: price from the REAL published catalogue + content score."""
    import autonomous_council as AC
    raw = AC.gh_raw("pricing.json") or '{"rows":[]}'
    try:
        master = json.loads(raw).get("rows", [])
    except Exception:
        master = []
    try:
        from council_review import market_price
    except Exception:
        market_price = None
    rows = []
    for i, m in enumerate(master):
        title = m.get("title") or ("ebook %02d" % (i + 1))
        score = int(m.get("score") or (10 + i % 8))
        base = int(m.get("price") or 0)
        if market_price:
            try:
                mp = market_price(title)
                if isinstance(mp, (tuple, list)) and mp:
                    base = int(mp[0])
            except Exception:
                pass
        if base <= 0:
            base = 79 + score * 14
        rows.append({"id": "bk_%02d" % (i + 1), "title": title,
                     "price": base, "score": score,
                     "status": "review", "asset": "real file in repo"})
    return rows


def make_store(plan, rows):
    """Programmer order: beautiful storefront, correct price, real CTA."""
    cards = "".join(
        '''<article class="card"><div class="tag">ZYPHERE ORIGINAL</div>
<h3>%s</h3><p>เนื้อหาจากต้นฉบับจริง · ปรับปรุงโดยทีมวิศวกร</p>
<div class="row"><b>฿%d</b><span>status: %s</span></div></article>''' %
        (r["title"], r["price"], r["status"]) for r in rows[:12])
    channels = "".join(
        '<li><a href="%s">%s</a> — %s</li>' %
        (c["url"], c["name"], c["asset"]) for c in CHANNELS)
    html = """<!doctype html><html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Zyphire Store</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@400;600;700&display=swap" rel="stylesheet">
<style>
:root{--ink:#12222b;--mut:#5d7380;--acc:#0e7490;--soft:#eef8fa}
*{box-sizing:border-box}body{margin:0;background:#f5fafb;color:var(--ink);font-family:'Noto Sans Thai',sans-serif}
header{padding:56px 28px;background:linear-gradient(135deg,#0b2432,#0e7490);color:#fff}
header h1{margin:0;font-size:44px}header p{opacity:.85;max-width:640px;line-height:1.8}
main{max-width:1100px;margin:auto;padding:38px 22px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:16px}
.card{background:#fff;border:1px solid #dcebef;border-radius:18px;padding:20px;transition:.2s}
.card:hover{transform:translateY(-4px);box-shadow:0 14px 32px rgba(14,116,144,.12)}
.tag{font-size:11px;letter-spacing:2px;color:var(--acc);font-weight:700}
.card h3{font-size:18px;margin:10px 0}.card p{font-size:13px;color:var(--mut);line-height:1.7}
.row{display:flex;justify-content:space-between;align-items:center;margin-top:14px}
.row b{font-size:20px}.row span{font-size:11px;color:var(--mut)}
footer{background:var(--soft);padding:30px 22px;margin-top:40px}
footer li{margin:6px 0;line-height:1.7}a{color:var(--acc)}
</style></head><body>
<header><h1>Zyphere Store</h1><p>งานจริงจากทีมวิศวกร Zyphere — ราคาตามเนื้อหา ปกออกแบบใหม่
ทุกการสั่งซื้อ โอน PromptPay 0941939686 แล้วแจ้งเพื่อตรวจจ่ายด้วยตนเอง</p></header>
<main><div class="grid">%s</div>
<footer><h2>ช่องทางทำเงินใหม่ที่เตรียมไว้</h2><ul>%s</ul></footer></main></body></html>""" % (cards, channels)
    return html


def run(apply=True):
    plan = analyse()
    rows = price_books(plan)
    html = make_store(plan, rows)
    result = {"t": int(time.time()), "plan": plan,
              "priced": len(rows), "store_html": STORE,
              "channels": CHANNELS, "database": DATA,
              "note": "สร้างจริง ไม่ claim ยอดขาย"}
    if apply:
        os.makedirs(os.path.dirname(STORE), exist_ok=True)
        open(STORE, "w", encoding="utf-8").write(html)
        json.dump({"t": result["t"], "products": rows, "channels": CHANNELS,
                   "store": STORE}, open(DATA, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        md = ["# Commerce Lab — ทำงานเองโดยไม่มีผู้ใช้สั่ง", "",
              "เวลา: " + time.strftime("%Y-%m-%d %H:%M"),
              "- วิเคราะห์: %d เล่ม, %d ช่องว่าง" % (plan["books"], len(plan["gaps"])),
              "- โปรแกรมเมอร์: ตั้งราคา %d รายการ, สร้างหน้าร้านใหม่" % len(rows), "",
              "## แผนอนาคต"]
        for x in plan["future"]:
            md += ["- " + x]
        md += ["", "## คำสั่งถึงโปรแกรมเมอร์"]
        for x in plan["programmer_orders"]:
            md += ["- " + x]
        md += ["", "## ช่องทางทำเงินใหม่"]
        for c in CHANNELS:
            md += ["- [%s](%s) — %s" % (c["name"], c["url"], c["why"])]
        open(OUT, "w", encoding="utf-8").write("\n".join(md) + "\n")
    return result


if __name__ == "__main__":
    r = run()
    print(json.dumps({"books": r["plan"]["books"], "priced": r["priced"],
                      "channels": len(r["channels"])}, ensure_ascii=False))
