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
            if o.get("status") == "paid":
                return {"ok": True, "id": o["id"], "status": "paid", "already": True}
            if o.get("status") not in ("awaiting_payment", "awaiting_verification"):
                return {"ok": False, "error": "order already resolved", "status": o.get("status")}
            o["ref"] = str(ref or "")[:120]
            # A button click is NOT proof of payment. Money is verified only by
            # the Omise webhook (or an explicit admin action) - see mark_paid().
            o["status"] = "awaiting_verification"
            o["submitted_t"] = int(time.time())
        self.save()
        return {"ok": True, "id": o["id"], "status": o["status"],
                "message": "รับรายแล้ว รอระบบตรวจยืนยันการชำระครับ"}

    def mark_paid(self, order_id="", via="omise", charge_id=""):
        """Set paid ONLY after a real payment event (Omise webhook / admin)."""
        with self.lock:
            o = next((x for x in self.orders if x.get("id") == order_id), None)
            if not o:
                return {"ok": False, "error": "order not found"}
            o["status"] = "paid"
            o["paid_via"] = str(via)[:40]
            if charge_id:
                o["charge_id"] = str(charge_id)[:80]
            o["paid_t"] = int(time.time())
        self.save()
        return {"ok": True, "id": o["id"], "status": "paid"}

    def approve(self, order_id="", by="admin"):
        with self.lock:
            o = next((x for x in self.orders if x.get("id") == order_id), None)
            if not o:
                return {"ok": False, "error": "order not found"}
            if o.get("status") == "approved":
                return {"ok": True, "status": "approved", "already": True}
            o["status"] = "paid"
            o["paid_via"] = "admin:" + str(by)[:30]
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
            if o.get("status") not in ("paid", "approved"):
                return {"ok": False, "error": "ยังไม่ยืนยันการชำระ",
                        "status": o.get("status")}
        return {"ok": True, "url": ZIPBALL, "filename": "zyphere-product-pack.zip",
                "product": o.get("product", ""), "status": "approved"}

    def pending(self):
        with self.lock:
            return [dict(o) for o in self.orders if o.get("status") in ("awaiting_verification", "awaiting_payment")]

    def all_orders(self):
        with self.lock:
            return [dict(o) for o in self.orders]

    # ---------- backwards-compatible aliases ----------
    def order(self, product="", amount=0, buyer="", status="awaiting_payment"):
        return self.create_order(product, amount, buyer)

    # ---------- storefront HTML ----------
    def build(self, products=None, theme="light"):
        """Storefront reviewed by the design + language faculties.

        Design: Google AI Studio-inspired — light canvas, soft shadows,
        generous spacing, indigo/violet accent, clear information hierarchy.
        Language: Thai copy checked with LanguageMastery (see REVIEW.md).
        """
        products = products or []
        # Language department: apply the real Thai corrector to every line of copy.
        try:
            from language import LanguageMastery
            _lm = LanguageMastery()
            def th(s):
                return _lm.correct(str(s))["text"]
        except Exception:
            def th(s):
                return str(s)

        cards = []
        for i, p in enumerate(products[:60], 1):
            title = html.escape(th(str(p.get("title", p.get("product", "ผลงาน")))))
            price = int(p.get("price", 0) or 0)
            desc = html.escape(th(str(p.get("desc", p.get("scholar", "เอกสารความรู้จากคณะวิชา Zyphere")))))[:160]
            cards.append(f'''
    <article class="card" data-title="{title}" data-price="{price}">
      <div class="card-top"><span class="num">{i:02d}</span><span class="tag">ดิจิทัล</span></div>
      <div class="ic">✦</div>
      <h3>{title}</h3>
      <p class="desc">{desc}</p>
      <div class="card-foot"><span class="price">฿{price:,}</span><button class="buy" onclick="buy(this)">เลือกซื้อ</button></div>
    </article>''')

        copy = {
            "brand": th("ร้านค้า Zyphere"),
            "hero_h": th("ผลงานจากคณะวิชา ส่งมอบให้คุณ"),
            "hero_p": th("เอกสารความรู้ที่ไซเฟอร์จัดทำขึ้นจากคณะวิชาทั้ง 46 สาขา เลือกหัวข้อที่ต้องการ แล้วชำระผ่านพรีมเพย์ ทีมงานจะตรวจสอบรายการโอนและปลดล็อกไฟล์ให้"),
            "all": th("ผลงานทั้งหมด"),
            "search": th("ค้นหาหัวข้อ..."),
            "orders": th("คำสั่งซื้อของฉัน"),
            "login": th("เข้าสู่ระบบด้วย Google"),
            "pay_title": th("ชำระเงิน"),
            "ref_label": th("หมายเลขอ้างอิงการโอน (หรือตัวเลข 4 ตัวสุดท้าย)"),
            "submit": th("ชำระเงิน / แจ้งชำระ"),
            "note": th("สแกนคิวอาร์โค้ดเพื่อชำระตามยอดที่แสดง ระบบจะปลดล็อกไฟล์เมื่อยืนยันการชำระสำเร็จ"),
            "fine": th("หมายเหตุ: การกดปุ่มเพียงอย่างเดียวไม่อาจดาวน์โหลดไฟล์ได้ ระบบจะยืนยันผ่านประตูชำระเงิน หรือให้แอดมินตรวจรายการโอนก่อนอนุมัติ"),
            "pending_h": th("อยู่ระหว่างการตรวจสอบ"),
            "pending_p": th("ส่งหลักฐานการชำระเรียบร้อยแล้ว กรุณาเก็บหมายเลขคำสั่งซื้อไว้ แล้วกลับมาตรวจสถานะได้ทุกเมื่อ"),
            "check": th("ตรวจสถานะคำสั่งซื้อ"),
            "done_h": th("ชำระเงินเรียบร้อย"),
            "done_p": th("ทีมงานอนุมัติแล้ว ขอบคุณที่สนับสนุนครับ"),
            "dl": th("ดาวน์โหลดแพ็กเกจผลงาน"),
            "empty": th("ยังไม่มีคำสั่งซื้อ เข้าสู่ระบบด้วย Google เพื่อดูคำสั่งซื้อของคุณ"),
            "cancel": th("ยกเลิก"), "close": th("ปิด"),
            "noresult": th("ไม่พบหัวข้อที่ค้นหา"),
            "secure": th("ชำระปลอดภัย · ตรวจสอบโดยทีมงาน · ส่งไฟล์จริง"),
        }
        copy_json = json.dumps(copy, ensure_ascii=False)

        doc = f'''<!doctype html><html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{copy['brand']} — Zyphere</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+Thai:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{{--bg:#f7f8fc;--ink:#1b1f2a;--mut:#6b7280;--line:#e8eaf1;--blue:#4f46e5;--violet:#7c3aed;--ok:#16a34a}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font-family:Inter,'Noto Sans Thai',system-ui,sans-serif;-webkit-font-smoothing:antialiased}}
nav{{position:sticky;top:0;z-index:20;background:rgba(255,255,255,.86);backdrop-filter:blur(14px);border-bottom:1px solid var(--line)}}
.navin{{max-width:1120px;margin:0 auto;padding:14px 22px;display:flex;align-items:center;justify-content:space-between}}
.logo{{display:flex;align-items:center;gap:10px;font-weight:700;font-size:18px;letter-spacing:-.2px}}
.mark{{width:30px;height:30px;border-radius:9px;background:linear-gradient(135deg,#2563eb,#7c3aed);display:grid;place-items:center;color:#fff;font-size:16px}}
.gbtn{{border:1px solid var(--line);background:#fff;color:var(--ink);border-radius:10px;padding:8px 14px;font:600 13px Inter,'Noto Sans Thai';cursor:pointer}}
.gbtn:hover{{border-color:#c7d2fe;background:#f5f7ff}}
.hero{{max-width:1120px;margin:26px auto 0;padding:40px 38px;border-radius:24px;color:#fff;background:linear-gradient(120deg,#4338ca 0%,#6d28d9 55%,#9333ea 100%);box-shadow:0 18px 44px rgba(79,70,229,.22);position:relative;overflow:hidden}}
.hero:after{{content:"";position:absolute;right:-70px;top:-90px;width:320px;height:320px;border-radius:50%;background:rgba(255,255,255,.08)}}
.hero h1{{margin:0;font-size:32px;letter-spacing:-.6px;font-weight:700}}
.hero p{{margin:12px 0 0;max-width:660px;line-height:1.75;opacity:.94;font-size:14px}}
.chips{{display:flex;gap:8px;flex-wrap:wrap;margin-top:20px}}
.chip{{background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.22);border-radius:99px;padding:6px 12px;font-size:12px}}
section{{max-width:1120px;margin:0 auto;padding:30px 22px 60px}}
.shead{{display:flex;align-items:center;justify-content:space-between;gap:14px;margin-bottom:18px;flex-wrap:wrap}}
.shead h2{{margin:0;font-size:20px;letter-spacing:-.3px}}
.search{{border:1px solid var(--line);background:#fff;border-radius:11px;padding:10px 14px;font:14px Inter,'Noto Sans Thai';min-width:230px;outline:none}}
.search:focus{{border-color:#a5b4fc;box-shadow:0 0 0 3px #eef2ff}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(248px,1fr));gap:16px}}
.card{{background:#fff;border:1px solid var(--line);border-radius:18px;padding:18px;display:flex;flex-direction:column;min-height:196px;transition:.18s;box-shadow:0 2px 10px rgba(17,24,39,.03)}}
.card:hover{{transform:translateY(-3px);box-shadow:0 14px 30px rgba(17,24,39,.09);border-color:#dbe2ff}}
.card-top{{display:flex;justify-content:space-between;align-items:center}}
.num{{font:700 12px Inter;color:#a5b4fc;letter-spacing:1px}}
.tag{{font-size:11px;color:var(--blue);background:#eef2ff;border-radius:99px;padding:3px 9px}}
.ic{{font-size:26px;color:var(--violet);margin:12px 0 2px}}
.card h3{{margin:4px 0 8px;font-size:15.5px;font-weight:600;line-height:1.5}}
.desc{{margin:0;color:var(--mut);font-size:12.5px;line-height:1.65;flex:1}}
.card-foot{{display:flex;justify-content:space-between;align-items:center;margin-top:16px;padding-top:14px;border-top:1px solid var(--line)}}
.price{{font:700 18px Inter;color:var(--blue)}}
.buy{{border:0;background:linear-gradient(135deg,#4f46e5,#7c3aed);color:#fff;border-radius:10px;padding:9px 15px;font:600 13px Inter,'Noto Sans Thai';cursor:pointer;box-shadow:0 6px 14px rgba(79,70,229,.22)}}
.buy:hover{{filter:brightness(1.07)}}
.ov{{display:none;position:fixed;inset:0;background:rgba(17,24,39,.52);backdrop-filter:blur(4px);align-items:center;justify-content:center;z-index:30;padding:18px}}
.box{{background:#fff;border-radius:22px;padding:26px;max-width:430px;width:100%;max-height:92vh;overflow:auto;box-shadow:0 30px 70px rgba(0,0,0,.3)}}
.box h2{{margin:0 0 4px;font-size:20px}}
.box .sub{{color:var(--mut);font-size:13px;margin:0 0 14px}}
.qrwrap{{text-align:center;background:#f8f9ff;border:1px solid var(--line);border-radius:16px;padding:16px;margin:14px 0}}
.qrwrap img{{width:186px;height:186px;background:#fff;border-radius:10px}}
.qrnum{{font-size:11px;color:#6b7280;margin-top:10px;letter-spacing:.3px}}
.note{{font-size:12.5px;line-height:1.7;color:#374151;background:#f9fafb;border-radius:12px;padding:12px 14px}}
.fine{{font-size:11.5px;line-height:1.65;color:#9a6a13;background:#fffbeb;border:1px solid #fde68a;border-radius:12px;padding:10px 12px;margin-top:10px}}
.amt{{font:700 22px Inter;color:var(--blue);margin:12px 0 4px}}
input{{width:100%;padding:11px 13px;border:1px solid var(--line);border-radius:11px;font:14px Inter,'Noto Sans Thai';margin-top:8px;outline:none}}
input:focus{{border-color:#a5b4fc;box-shadow:0 0 0 3px #eef2ff}}
.btn{{width:100%;border:0;border-radius:11px;padding:12px;font:600 14px Inter,'Noto Sans Thai';cursor:pointer;margin-top:10px}}
.primary{{background:linear-gradient(135deg,#16a34a,#15803d);color:#fff}}
.ghost{{background:#f3f4f6;color:#374151}}
.pill{{display:inline-block;background:#fef3c7;color:#92400e;border-radius:99px;padding:5px 11px;font-size:11.5px;margin-top:8px}}
.code{{font:600 13px Inter;background:#f1f5f9;border-radius:8px;padding:8px 10px;word-break:break-all;margin:10px 0}}
.dl{{display:block;text-align:center;background:linear-gradient(135deg,#4f46e5,#7c3aed);color:#fff;text-decoration:none;border-radius:11px;padding:12px;margin-top:12px;font-weight:600}}
.my{{background:#fff;border:1px solid var(--line);border-radius:18px;padding:20px;margin-top:8px}}
.myrow{{display:flex;justify-content:space-between;gap:10px;align-items:center;border-bottom:1px solid var(--line);padding:12px 0;flex-wrap:wrap}}
.myrow:last-child{{border-bottom:0}}
.st{{font-size:11.5px;border-radius:99px;padding:4px 10px}}
.st-wait{{background:#fef3c7;color:#92400e}}.st-ok{{background:#dcfce7;color:#166534}}.st-rej{{background:#fee2e2;color:#991b1b}}
.mini{{font-size:12px;color:var(--mut)}}
footer{{text-align:center;color:var(--mut);font-size:12px;padding:26px 16px 40px;border-top:1px solid var(--line)}}
@media(max-width:600px){{.hero{{padding:28px 22px}}.hero h1{{font-size:25px}}.search{{width:100%}}}}
</style></head><body>
<nav><div class="navin"><div class="logo"><span class="mark">✦</span><span>Zyphere <span style="color:#6b7280;font-weight:500">Store</span></span></div>
<button class="gbtn" id="gLogin" onclick="googleLogin()">{copy['login']}</button></div></nav>

<div class="hero">
  <h1>{copy['hero_h']}</h1>
  <p>{copy['hero_p']}</p>
  <div class="chips"><span class="chip">46 {th('คณะวิชา')}</span><span class="chip">PromptPay {PROMPTPAY}</span><span class="chip">{th('ส่งไฟล์จริง')}</span></div>
</div>

<section>
  <div class="shead"><h2>{copy['all']} <span class="mini">({len(products)})</span></h2>
    <input class="search" id="q" placeholder="{copy['search']}" oninput="filter()"></div>
  <div class="grid" id="grid">{''.join(cards)}</div>
  <p id="nores" style="display:none;color:var(--mut)">{copy['noresult']}</p>

  <div class="shead" style="margin-top:38px"><h2>{copy['orders']}</h2></div>
  <div class="my" id="my"><p class="mini" id="myMsg">{copy['empty']}</p><div id="myList"></div></div>
</section>

<div class="ov" id="ov"><div class="box">
  <div id="vPay"><h2>{copy['pay_title']}</h2><p class="sub" id="pTitle"></p>
    <div class="qrwrap"><img id="pQR" alt="PromptPay QR" src=""><div class="qrnum">PromptPay {PROMPTPAY}</div></div>
    <p class="note">{copy['note']}</p>
    <div class="amt" id="pPrice"></div>
    <input id="pRef" placeholder="{copy['ref_label']}">
    <button class="btn primary" onclick="submitPay()">{copy['submit']}</button>
    <button class="btn ghost" onclick="closeM()">{copy['cancel']}</button>
  </div>
  <div id="vWait" style="display:none"><h2>{copy['pending_h']}</h2><p class="sub">{copy['pending_p']}</p>
    <div class="code" id="pOrder"></div><span class="pill">awaiting_verification</span>
    <button class="btn primary" onclick="checkStatus()">{copy['check']}</button>
    <button class="btn ghost" onclick="closeM()">{copy['close']}</button>
  </div>
  <div id="vDone" style="display:none"><h2>{copy['done_h']}</h2><p class="sub">{copy['done_p']}</p>
    <a class="dl" id="dl" href="#" download>{copy['dl']}</a>
    <button class="btn ghost" onclick="closeM()">{copy['close']}</button>
  </div>
</div></div>

<footer>PromptPay {PROMPTPAY} · {copy['secure']}</footer>
<script>
const API='https://zyphere-ai-agent.onrender.com';
const TXT={copy_json};
let cur={{}},oid='',tk='';
const $=id=>document.getElementById(id);
function filter(){{const q=$('q').value.trim().toLowerCase();let n=0;
 document.querySelectorAll('.card').forEach(c=>{{const ok=c.dataset.title.toLowerCase().includes(q);c.style.display=ok?'':'none';if(ok)n++;}});
 $('nores').style.display=n?'none':'block';}}
function view(id){{['vPay','vWait','vDone'].forEach(x=>$(x).style.display=(x===id?'block':'none'));$('ov').style.display='flex';}}
function closeM(){{$('ov').style.display='none';}}
function buy(b){{const c=b.closest('.card');cur={{title:c.dataset.title,price:c.dataset.price}};
 $('pTitle').textContent=cur.title;$('pPrice').textContent='฿'+Number(cur.price).toLocaleString('th-TH');
 $('pQR').src=API+'/api/store/qr?amount='+encodeURIComponent(cur.price)+'&t='+Date.now();view('vPay');}}
function utoken(){{return localStorage.getItem('zy_token')||'';}}
function googleLogin(){{const back=encodeURIComponent(location.href.split('#')[0]);
 location.href=API+'/api/auth/google?next='+back;}}
async function submitPay(){{
 try{{const cfg=await(await fetch(API+'/api/store/config')).json();
  const o=await(await fetch(API+'/api/store/order',{{method:'POST',headers:{{'Content-Type':'application/json'}},
   body:JSON.stringify({{product:cur.title,amount:cur.price,user_token:utoken()}})}})).json();
  if(!o.ok)throw new Error(o.error||'order failed');oid=o.id;tk=o.token;
  if(cfg.omise_enabled){{
   const p=await(await fetch(API+'/api/store/pay/omise',{{method:'POST',headers:{{'Content-Type':'application/json'}},
    body:JSON.stringify({{order_id:oid,token:tk}})}})).json();
   if(!p.ok)throw new Error(p.error||'payment failed');
   if(p.authorize_uri){{location.href=p.authorize_uri;return}}
   if(p.qr){{$('pQR').src=p.qr;alert('สแกน QR จากประตูชำระเงินเพื่อชำระครับ');return}}
  }}
  const s=await(await fetch(API+'/api/store/submit',{{method:'POST',headers:{{'Content-Type':'application/json'}},
   body:JSON.stringify({{order_id:oid,token:tk,ref:$('pRef').value}})}})).json();
  if(!s.ok)throw new Error(s.error||'submit failed');
  $('pOrder').textContent=oid;view('vWait');loadMy();}}
 catch(e){{alert('ชำระเงินไม่ได้: '+e.message)}}
}}
async function checkStatus(){{
 try{{const j=await(await fetch(API+'/api/store/download?order_id='+encodeURIComponent(oid)+'&token='+encodeURIComponent(tk))).json();
  if(j.ok){{$('dl').href=j.url;$('dl').download=j.filename||'zyphere-product-pack.zip';view('vDone');}}
  else alert('ยังไม่ได้รับการอนุมัติ: '+(j.error||j.status||'pending'));}}
 catch(e){{alert('ตรวจสถานะไม่ได้: '+e.message)}}
}}
async function loadMy(){{
 const t=utoken();if(!t)return;
 try{{const j=await(await fetch(API+'/api/store/my-orders?token='+encodeURIComponent(t))).json();
  if(!j.ok)throw new Error(j.error||'failed');
  const os=j.orders||[];
  $('myMsg').style.display=os.length?'none':'block';
  $('myList').innerHTML=os.map(o=>{{
   const st=o.status,cls=st==='approved'?'st-ok':(st==='rejected'?'st-rej':'st-wait');
   const dl=st==='approved'?'<button class="gbtn" onclick="getLink(\\''+o.id+'\\',\\''+o.token+'\\')">'+TXT.dl+'</button>':'';
   return '<div class="myrow"><div><b>'+esc(o.product)+'</b><br><span class="mini">฿'+Number(o.amount).toLocaleString('th-TH')+' · '+
     new Date(o.t*1000).toLocaleDateString('th-TH')+'</span></div><div><span class="st '+cls+'">'+esc(st)+'</span> '+dl+'</div></div>';
  }}).join('');}}
 catch(e){{$('myMsg').textContent=e.message}}
}}
async function getLink(id,tk2){{
 try{{const j=await(await fetch(API+'/api/store/download?order_id='+encodeURIComponent(id)+'&token='+encodeURIComponent(tk2))).json();
  if(j.ok){{$('dl').href=j.url;$('dl').download=j.filename||'zyphere-product-pack.zip';view('vDone');}}
  else alert('ยังไม่ได้รับการอนุมัติ');}}
 catch(e){{alert(e.message)}}
}}
function esc(s){{return String(s||'').replace(/[&<>]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;'}}[c]))}}
(async function(){{
 const h=location.hash.match(/oauth=([^&]+)/);
 if(h){{try{{const p=new URLSearchParams(decodeURIComponent(h[1]));localStorage.setItem('zy_token',p.get('token')||'');
   history.replaceState(null,'',location.pathname+location.search);}}catch(e){{}}}}
 if(utoken()){{try{{const me=await(await fetch(API+'/api/store/me?token='+encodeURIComponent(utoken()))).json();
   if(me.ok){{$('gLogin').textContent=me.name||me.email;$('gLogin').onclick=loadMy;}}}}catch(e){{}}loadMy();}}
}})();
</script></body></html>'''
        fp = os.path.join(self.out_dir, "STORE.html")
        os.makedirs(self.out_dir, exist_ok=True)
        open(fp, "w", encoding="utf-8").write(doc)
        return {"ok": True, "path": fp, "products": len(products), "url": "/media/STORE.html"}
