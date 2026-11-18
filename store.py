"""Zyphere Store - generate a REAL, openable HTML storefront with a working
BUY button for every product. Click Buy -> payment page (PromptPay) -> confirm
-> download link. This is what was missing: an actual sellable UI, not text.

Free, static HTML (open directly or GitHub Pages). Owner receives PromptPay.
HONEST: payment confirmation is honest (buyer pays owner, then clicks confirm
and gets download). No fake auto-bank access, no gambling/illegal.
"""
import os, json, time, html, threading

PROMPTPAY = "0941939686"


class Store:
    def __init__(self, out_dir):
        self.out_dir = out_dir
        self.lock = threading.RLock()
        self.orders = []
        self._load()

    def _load(self):
        try:
            self.orders = json.load(open(os.path.join(self.out_dir, "orders.json"), encoding="utf-8")).get("orders", [])
        except Exception:
            pass

    def save(self):
        with self.lock:
            try:
                os.makedirs(self.out_dir, exist_ok=True)
                json.dump({"orders": self.orders[-1000:]}, open(os.path.join(self.out_dir, "orders.json"), "w",
                          encoding="utf-8"), ensure_ascii=False, indent=2)
            except Exception:
                pass

    def build(self, products=None, theme="light"):
        products = products or []
        cards = []
        for p in products[:60]:
            title = html.escape(str(p.get("title", p.get("product", "สินค้า"))))
            price = int(p.get("price", 0) or 0)
            desc = html.escape(str(p.get("desc", p.get("scholar", ""))))[:200]
            url = str(p.get("asset_url", "") or "")
            pid = html.escape(str(p.get("id", ""))[:60])
            cards.append(f'''
<div class="card" data-id="{pid}" data-title="{title}" data-price="{price}" data-url="{html.escape(url)}">
  <div class="ic">📦</div>
  <h3>{title}</h3>
  <p>{desc}</p>
  <div class="row"><span class="price">฿{price}</span><button class="buy" onclick="buy(this)">ซื้อเลย</button></div>
</div>''')
        doc = f'''<!doctype html><html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Zyphere Store — ร้านของ Zyphere</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;font-family:'Noto Sans Thai',system-ui,sans-serif;background:{'#f8fafc'};color:#1f2430}}
header{{background:linear-gradient(135deg,#2563eb,#7c3aed);color:#fff;padding:28px 20px;text-align:center}}
header h1{{margin:0;font-size:28px}}header p{{margin:6px 0 0;opacity:.9}}
.wrap{{max-width:1100px;margin:0 auto;padding:24px 16px;display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:16px}}
.card{{background:#fff;border:1px solid #e5e8ef;border-radius:16px;padding:18px;box-shadow:0 4px 16px rgba(0,0,0,.05)}}
.card h3{{margin:10px 0 6px;font-size:16px}} .card p{{color:#64748b;font-size:13px;min-height:36px}}
.ic{{font-size:28px}} .row{{display:flex;justify-content:space-between;align-items:center;margin-top:12px}}
.price{{font-weight:700;color:#2563eb;font-size:18px}}
.buy{{background:#2563eb;color:#fff;border:0;border-radius:10px;padding:10px 16px;cursor:pointer;font-weight:600}}
.buy:hover{{background:#1d4ed8}}
#modal{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);align-items:center;justify-content:center;z-index:9}}
#box{{background:#fff;border-radius:20px;padding:28px;max-width:420px;width:92%}}
#box h2{{margin:0 0 10px}} .pay{{background:#f1f5f9;border-radius:12px;padding:14px;font-size:20px;text-align:center;letter-spacing:2px;margin:12px 0}}
button.go{{width:100%;background:#16a34a;color:#fff;border:0;border-radius:10px;padding:12px;margin-top:10px;cursor:pointer;font-weight:600}}
button.no{{width:100%;background:#e2e8f0;border:0;border-radius:10px;padding:10px;margin-top:8px;cursor:pointer}}
#done{{display:none;text-align:center}}#done a{{display:block;background:#2563eb;color:#fff;padding:12px;border-radius:10px;text-decoration:none;margin-top:12px}}
</style></head><body>
<header><h1>🛒 Zyphere Store</h1><p>ผลงานจาก 46 นักวิชาการ · จ่าย PromptPay {PROMPTPAY} · ส่งไฟล์ทันที</p></header>
<div class="wrap">{''.join(cards)}</div>
<div id="modal"><div id="box"><div id="payView"><h2>ชำระสินค้า</h2><p id="pTitle"></p>
<div class="pay">PromptPay {PROMPTPAY}</div><p style="color:#64748b;font-size:13px">โอนเงินตามจำนวนด้านล่าง แล้วกด "จ่ายแล้ว / รับลิงก์"</p>
<h3 id="pPrice"></h3><button class="go" onclick="confirmPay()">จ่ายแล้ว / รับลิงก์ดาวน์โหลด</button>
<button class="no" onclick="closeM()">ยกเลิก</button></div>
<div id="done"><h2>✅ ขอบคุณครับ</h2><p>หากโอนเงินแล้ว ระบบ will แสดงลิงก์ไฟล์ด้านล่าง</p><a id="dl" href="#" download>⬇ ดาวน์โหลดสินค้า</a><button class="no" onclick="closeM()">ปิด</button></div>
</div></div>
<script>
let cur={{}};
function buy(b){{const c=b.parentElement.parentElement;cur={{title:c.dataset.title,price:c.dataset.price,url:c.dataset.url,id:c.dataset.id}};
document.getElementById('pTitle').textContent=cur.title;document.getElementById('pPrice').textContent='฿'+cur.price;
document.getElementById('modal').style.display='flex';document.getElementById('payView').style.display='block';document.getElementById('done').style.display='none';}}
function closeM(){{document.getElementById('modal').style.display='none';}}
function confirmPay(){{document.getElementById('payView').style.display='none';document.getElementById('done').style.display='block';
const a=document.getElementById('dl');if(cur.url){{a.href=cur.url;a.style.display='block';}}else{{a.textContent='📦 ผลงานอยู่ใน GitHub — ติดต่อเพื่อรับไฟล์';a.href='https://github.com/Vorakan-yakham/zyphere-scholar-product-pack';}}}}
</script></body></html>'''
        fp = os.path.join(self.out_dir, "STORE.html")
        os.makedirs(self.out_dir, exist_ok=True)
        open(fp, "w", encoding="utf-8").write(doc)
        return {"ok": True, "path": fp, "products": len(products), "url": "/media/STORE.html"}

    def order(self, product="", amount=0, buyer="", status="awaiting_payment"):
        rec = {"ok": True, "id": "or_" + str(int(time.time() * 1000)),
               "product": str(product)[:160], "amount": int(amount or 0),
               "buyer": str(buyer or "")[:120], "promptpay": PROMPTPAY,
               "status": status, "t": int(time.time())}
        with self.lock:
            self.orders.append(rec)
        self.save()
        return rec
