"""Zyphere Store — honest, admin-verified payment gate.

Flow (no fake 'click I paid = download'):
  BUY -> see PromptPay 0941939686 -> pay -> SUBMIT payment reference
  -> order status 'awaiting_verification'
  -> ADMIN verifies the transfer and APPROVES (admin token required)
  -> only then the gated download endpoint serves the file.

HONEST:
- No claim of automatic bank detection (no bank API access).
- Payment proof is the buyer's transfer reference; owner verifies manually.
- Files are also public in GitHub as a showcase; the PAID product is the
  curated bundle delivered through this gate + support. (Owner can make the
  deliverable repo private later for a hard paywall.)
- No gambling / illegal / spoofing / account or OTP automation.
"""
import os, json, time, html, threading, secrets

PROMPTPAY = "0941939686"
ZIPBALL = ("https://github.com/Vorakan-yakham/zyphere-scholar-product-pack/"
           "archive/refs/heads/main.zip")


class Store:
    def __init__(self, out_dir):
        self.out_dir = out_dir
        self.lock = threading.RLock()
        self.orders = []
        self._load()

    def _load(self):
        try:
            self.orders = json.load(open(os.path.join(self.out_dir, "orders.json"),
                                         encoding="utf-8")).get("orders", [])
        except Exception:
            pass

    def save(self):
        with self.lock:
            try:
                os.makedirs(self.out_dir, exist_ok=True)
                json.dump({"orders": self.orders[-1000:]},
                          open(os.path.join(self.out_dir, "orders.json"), "w", encoding="utf-8"),
                          ensure_ascii=False, indent=2)
            except Exception:
                pass

    # ---------- payment gate state machine ----------
    def create_order(self, product="", amount=0, buyer="", email=""):
        rec = {"id": "or_" + secrets.token_hex(4),
               "token": secrets.token_urlsafe(12),
               "product": str(product)[:160], "amount": int(amount or 0),
               "buyer": str(buyer or "")[:120], "email": str(email or "")[:120],
               "promptpay": PROMPTPAY, "status": "awaiting_payment",
               "ref": "", "t": int(time.time()), "approved_by": "", "approved_t": 0}
        with self.lock:
            self.orders.append(rec)
        self.save()
        return {"ok": True, "id": rec["id"], "token": rec["token"],
                "status": rec["status"], "promptpay": PROMPTPAY, "amount": rec["amount"]}

    def submit_payment(self, order_id="", ref="", token=""):
        with self.lock:
            o = next((x for x in self.orders
                      if x.get("id") == order_id and (not token or x.get("token") == token)), None)
            if not o:
                return {"ok": False, "error": "order not found"}
            if o.get("status") not in ("awaiting_payment", "awaiting_verification"):
                return {"ok": False, "error": "order already resolved", "status": o.get("status")}
            o["ref"] = str(ref or "")[:120]
            o["status"] = "awaiting_verification"
            o["submitted_t"] = int(time.time())
        self.save()
        return {"ok": True, "id": o["id"], "status": o["status"],
                "message": "ส่งหลักฐานการชำระแล้ว รอ Admin ตรวจสอบครับ"}

    def approve(self, order_id="", by="admin"):
        with self.lock:
            o = next((x for x in self.orders if x.get("id") == order_id), None)
            if not o:
                return {"ok": False, "error": "order not found"}
            if o.get("status") == "approved":
                return {"ok": True, "status": "approved", "already": True}
            o["status"] = "approved"
            o["approved_by"] = str(by)[:60]
            o["approved_t"] = int(time.time())
        self.save()
        return {"ok": True, "id": o["id"], "status": "approved"}

    def reject(self, order_id="", by="admin"):
        with self.lock:
            o = next((x for x in self.orders if x.get("id") == order_id), None)
            if not o:
                return {"ok": False, "error": "order not found"}
            o["status"] = "rejected"
            o["approved_by"] = str(by)[:60]
        self.save()
        return {"ok": True, "id": o["id"], "status": "rejected"}

    def status(self, order_id="", token=""):
        with self.lock:
            o = next((x for x in self.orders
                      if x.get("id") == order_id and (not token or x.get("token") == token)), None)
            if not o:
                return {"ok": False, "error": "order not found"}
            return {"ok": True, "id": o["id"], "status": o["status"],
                    "product": o.get("product", ""), "amount": o.get("amount", 0),
                    "ref": o.get("ref", "")}

    def download(self, order_id="", token=""):
        """Gated: serve download only for an APPROVED order."""
        with self.lock:
            o = next((x for x in self.orders
                      if x.get("id") == order_id and x.get("token") == token), None)
            if not o:
                return {"ok": False, "error": "order not found / invalid token"}
            if o.get("status") != "approved":
                return {"ok": False, "error": "payment not verified yet",
                        "status": o.get("status")}
        return {"ok": True, "url": ZIPBALL, "filename": "zyphere-product-pack.zip",
                "product": o.get("product", ""), "status": "approved"}

    def pending(self):
        with self.lock:
            return [dict(o) for o in self.orders if o.get("status") == "awaiting_verification"]

    def all_orders(self):
        with self.lock:
            return [dict(o) for o in self.orders]

    # ---------- backwards-compatible aliases ----------
    def order(self, product="", amount=0, buyer="", status="awaiting_payment"):
        return self.create_order(product, amount, buyer)

    # ---------- storefront HTML ----------
    def build(self, products=None, theme="light"):
        products = products or []
        cards = []
        for p in products[:60]:
            title = html.escape(str(p.get("title", p.get("product", "สินค้า"))))
            price = int(p.get("price", 0) or 0)
            desc = html.escape(str(p.get("desc", p.get("scholar", ""))))[:200]
            cards.append(f'''
<div class="card" data-title="{title}" data-price="{price}" data-url="{html.escape(str(p.get("asset_url","")))}">
  <div class="ic">📦</div>
  <h3>{title}</h3>
  <p>{desc}</p>
  <div class="row"><span class="price">฿{price}</span><button class="buy" onclick="buy(this)">ซื้อเลย</button></div>
</div>''')
        doc = f'''<!doctype html><html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Zyphere Store — ร้านของ Zyphere</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;font-family:'Noto Sans Thai',system-ui,sans-serif;background:#f8fafc;color:#1f2430}}
header{{background:linear-gradient(135deg,#2563eb,#7c3aed);color:#fff;padding:28px 20px;text-align:center}}
header h1{{margin:0;font-size:28px}}header p{{margin:6px 0 0;opacity:.9;font-size:14px}}
.wrap{{max-width:1100px;margin:0 auto;padding:24px 16px;display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:16px}}
.card{{background:#fff;border:1px solid #e5e8ef;border-radius:16px;padding:18px;box-shadow:0 4px 16px rgba(0,0,0,.05)}}
.card h3{{margin:10px 0 6px;font-size:16px}} .card p{{color:#64748b;font-size:13px;min-height:36px}}
.ic{{font-size:28px}} .row{{display:flex;justify-content:space-between;align-items:center;margin-top:12px}}
.price{{font-weight:700;color:#2563eb;font-size:18px}}
.buy{{background:#2563eb;color:#fff;border:0;border-radius:10px;padding:10px 16px;cursor:pointer;font-weight:600}}
.buy:hover{{background:#1d4ed8}}
#modal{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);align-items:center;justify-content:center;z-index:9}}
#box{{background:#fff;border-radius:20px;padding:28px;max-width:440px;width:92%;max-height:90vh;overflow:auto}}
#box h2{{margin:0 0 10px}} .pay{{background:#f1f5f9;border-radius:12px;padding:14px;font-size:20px;text-align:center;letter-spacing:2px;margin:12px 0}}
input{{width:100%;padding:10px;border:1px solid #cbd5e1;border-radius:10px;margin:6px 0}}
button.go{{width:100%;background:#16a34a;color:#fff;border:0;border-radius:10px;padding:12px;margin-top:10px;cursor:pointer;font-weight:600}}
button.no{{width:100%;background:#e2e8f0;border:0;border-radius:10px;padding:10px;margin-top:8px;cursor:pointer}}
.note{{color:#64748b;font-size:12px;line-height:1.6}}
#done{{display:none;text-align:center}}#done a{{display:block;background:#2563eb;color:#fff;padding:12px;border-radius:10px;text-decoration:none;margin-top:12px;word-break:break-all}}
.pill{{display:inline-block;padding:4px 10px;border-radius:99px;background:#fef3c7;color:#92400e;font-size:12px;margin-top:8px}}
</style></head><body>
<header><h1>🛒 Zyphere Store</h1><p>ผลงานจาก 46 นักวิชาการ · ชำระ PromptPay {PROMPTPAY} · Admin ตรวจแล้วส่งไฟล์</p></header>
<div class="wrap">{''.join(cards)}</div>
<div id="modal"><div id="box">
<div id="payView"><h2>ชำระสินค้า</h2><p id="pTitle"></p>
<div style="text-align:center;background:#f8fafc;border-radius:12px;padding:12px;margin:12px 0">
<img id="pQR" src="" alt="PromptPay QR" style="width:190px;height:190px;background:#fff;border:1px solid #e5e8ef;border-radius:10px">
<div style="font-size:11px;color:#64748b;margin-top:8px;letter-spacing:0">PromptPay {PROMPTPAY}</div>
</div>
<p class="note">สแกน QR โอนตามยอด แล้วกรอก "รหัสอ้างอิง/4 ตัวสุดท้าย" ของรายการโอน แอดมินจะตรวจแล้วอนุมัติการดาวน์โหลดครับ<br><b>หมายเหตุ:</b> ระบบไม่มี API ธนาคาร จึงต้องให้แอดมินตรวจรายการโอนด้วยตนเอง — ไม่ใช่กดแล้วได้ไฟล์ทันที</p>
<h3 id="pPrice"></h3>
<input id="pRef" placeholder="รหัสอ้างอิงการโอน (เช่น 4 ตัวสุดท้าย)">
<button class="go" onclick="submitPay()">ส่งหลักฐานชำระ → รอ Admin ตรวจ</button>
<button class="no" onclick="closeM()">ยกเลิก</button></div>
<div id="pending" style="display:none"><h2>⏳ รอ Admin ตรวจสอบ</h2>
<p class="note">ส่งหลักฐานแล้วครับ เก็บรหัส订单นี้ไว้ แล้วกลับมาตรวจสถานะได้เลย</p>
<div class="pay" id="pOrder"></div><span class="pill">awaiting_verification</span>
<button class="go" onclick="checkStatus()">ตรวจสถานะ / รับลิงก์</button>
<button class="no" onclick="closeM()">ปิด</button></div>
<div id="done" style="display:none"><h2>✅ ชำระผ่านแล้ว</h2><p id="dMsg"></p>
<a id="dl" href="#" download>⬇ ดาวน์โหลดแพ็กเกจสินค้า</a>
<button class="no" onclick="closeM()">ปิด</button></div>
</div></div>
<script>
const API='https://zyphere-ai-agent.onrender.com';
let cur={{}},oid='',tk='';
function buy(b){{const c=b.parentElement.parentElement;cur={{title:c.dataset.title,price:c.dataset.price,url:c.dataset.url}};
document.getElementById('pTitle').textContent=cur.title;document.getElementById('pPrice').textContent='฿'+cur.price;
document.getElementById('pQR').src=API+'/api/store/qr?amount='+encodeURIComponent(cur.price)+'&t='+Date.now();
show('payView');}}
function closeM(){{document.getElementById('modal').style.display='none';}}
function show(id){{['payView','pending','done'].forEach(x=>document.getElementById(x).style.display=(x===id?'block':'none'));document.getElementById('modal').style.display='flex';}}
async function submitPay(){{
 try{{const r=await fetch(API+'/api/store/order',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{product:cur.title,amount:cur.price}})}});const o=await r.json();
 if(!o.ok)throw new Error(o.error||'order failed');oid=o.id;tk=o.token;
 const s=await fetch(API+'/api/store/submit',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{order_id:oid,token:tk,ref:document.getElementById('pRef').value}})}});const sj=await s.json();
 if(!sj.ok)throw new Error(sj.error||'submit failed');
 document.getElementById('pOrder').textContent=oid;show('pending');}}
 catch(e){{alert('ส่งหลักฐานไม่ได้: '+e.message)}}
}}
async function checkStatus(){{
 try{{const r=await fetch(API+'/api/store/download?order_id='+encodeURIComponent(oid)+'&token='+encodeURIComponent(tk));const j=await r.json();
 if(j.ok){{document.getElementById('dMsg').textContent='แอดมินอนุมัติแล้ว ขอบคุณครับ';const a=document.getElementById('dl');a.href=j.url;a.download=j.filename||'zyphere-product-pack.zip';show('done');}}
 else{{alert('ยังไม่ได้รับการอนุมัติ: '+(j.error||j.status||'r_pending'));}}
 }}catch(e){{alert('ตรวจสถานะไม่ได้: '+e.message)}}
}}
</script></body></html>'''
        fp = os.path.join(self.out_dir, "STORE.html")
        os.makedirs(self.out_dir, exist_ok=True)
        open(fp, "w", encoding="utf-8").write(doc)
        return {"ok": True, "path": fp, "products": len(products), "url": "/media/STORE.html"}
