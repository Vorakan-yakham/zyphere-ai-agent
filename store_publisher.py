"""Zyphere Store Publisher — auto-rebuild the storefront after the book team
finishes. Reads book_pricing.json from the product repo, renders a polished
store with real covers, chapter counts and a transparent price explanation,
then pushes STORE.html to the Pages repo automatically.

Called by book_team_v2 at the end of production. No manual steps.
"""
import os, json, time, base64, subprocess, requests, html as H

OWNER = "Vorakan-yakham"
PRODUCT_REPO = OWNER + "/zyphere-scholar-product-pack"
SITE_REPO = OWNER + "/zyphere-ai-agent"
RAW = "https://raw.githubusercontent.com/" + PRODUCT_REPO + "/main/"
COVER = "https://raw.githubusercontent.com/" + PRODUCT_REPO + "/main/books/"
API = "https://zyphere-ai-agent.onrender.com"
PROMPTPAY = "0941939686"


def token():
    t = os.environ.get("GH_TOKEN", "") or os.environ.get("GITHUB_TOKEN", "")
    if not t:
        t = subprocess.run(["gh", "auth", "token"], capture_output=True,
                           text=True, timeout=15).stdout.strip()
    return t


def push_site(path, content):
    tok = token()
    h = {"Authorization": "Bearer " + tok, "Accept": "application/vnd.github+json"}
    url = "https://api.github.com/repos/" + SITE_REPO + "/contents/" + path
    sha = None
    try:
        g = requests.get(url, headers=h, timeout=15)
        if g.ok:
            sha = (g.json() or {}).get("sha")
    except Exception:
        pass
    payload = {"message": "Store auto-publish by book team " + str(int(time.time())),
               "content": base64.b64encode(content.encode("utf-8")).decode(), "branch": "main"}
    if sha:
        payload["sha"] = sha
    r = requests.put(url, headers=h, json=payload, timeout=30)
    return r.ok, r.status_code


def build():
    r = requests.get(RAW + "book_pricing.json", timeout=30)
    data = r.json() if r.ok else {"rows": []}
    rows = data.get("rows", [])
    print("pricing rows", len(rows))
    cards = []
    for i, b in enumerate(rows):
        fac = b.get("faculty", "")
        folder = "%02d_%s" % (i + 1, fac.replace("/", "_"))
        cover = COVER + folder + "/cover.png"
        price = int(b.get("price", 0))
        chapters = b.get("chapters", 0)
        why = H.escape(str(b.get("why", "")))
        t = H.escape(fac)
        cards.append(f'''
<article class="book" data-title="{t}" data-price="{price}" data-cover="{cover}"
  data-why="{why}" data-chapters="{chapters}" data-book="{COVER}{folder}/book.html">
 <div class="cover"><img src="{cover}" alt="ปก {t}" loading="lazy"></div>
 <div class="info"><span class="badge">{chapters} บท</span>
  <h3>{t}</h3>
  <button class="why" onclick="showWhy(this)">ทำไมราคานี้?</button>
  <div class="foot"><span class="price">฿{price:,}</span>
   <button class="buy" onclick="buy(this)">เลือกซื้อ</button></div>
 </div>
</article>''')

    doc = f'''<!doctype html><html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Zyphere Book Store — หนังสือความรู้จากคณะวิชา</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+Thai:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{{--ink:#1b1f2a;--mut:#6b7280;--line:#e8eaf1;--ind:#4f46e5;--vio:#7c3aed}}
*{{box-sizing:border-box}}
body{{margin:0;background:#f6f7fb;color:var(--ink);font-family:Inter,'Noto Sans Thai',sans-serif}}
.top{{position:sticky;top:0;z-index:20;background:rgba(255,255,255,.82);backdrop-filter:blur(16px);border-bottom:1px solid var(--line)}}
.nav{{max-width:1160px;margin:auto;padding:14px 22px;display:flex;align-items:center;justify-content:space-between}}
.logo{{display:flex;align-items:center;gap:10px;font-weight:700;font-size:19px}}
.mark{{width:32px;height:32px;border-radius:10px;background:linear-gradient(135deg,#2563eb,#7c3aed);display:grid;place-items:center;color:#fff}}
.gbtn{{border:1px solid var(--line);background:#fff;border-radius:11px;padding:9px 15px;font:600 13px inherit;cursor:pointer}}
.gbtn:hover{{border-color:#a5b4fc;background:#f5f7ff}}
.hero{{max-width:1160px;margin:26px auto 0;padding:54px 46px;border-radius:28px;color:#fff;
 background:radial-gradient(circle at 85% 15%,rgba(255,255,255,.18),transparent 40%),
 linear-gradient(125deg,#3730a3,#6d28d9 55%,#a21caf);box-shadow:0 24px 60px rgba(79,70,229,.25)}}
.hero h1{{margin:0;font-size:38px;letter-spacing:-1px;line-height:1.3;max-width:720px}}
.hero p{{margin:16px 0 0;max-width:700px;line-height:1.9;color:rgba(255,255,255,.92);font-size:15px}}
.stats{{display:flex;gap:10px;flex-wrap:wrap;margin-top:26px}}
.stats span{{background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.25);border-radius:99px;padding:7px 14px;font-size:12px}}
.sec{{max-width:1160px;margin:auto;padding:34px 22px 70px}}
.head{{display:flex;justify-content:space-between;align-items:center;gap:14px;margin-bottom:22px;flex-wrap:wrap}}
.head h2{{margin:0;font-size:22px}}
.search{{border:1px solid var(--line);background:#fff;border-radius:12px;padding:11px 15px;font:14px inherit;min-width:240px;outline:none}}
.search:focus{{border-color:#a5b4fc;box-shadow:0 0 0 3px #eef2ff}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:20px}}
.book{{background:#fff;border:1px solid var(--line);border-radius:20px;overflow:hidden;transition:.2s;box-shadow:0 3px 14px rgba(17,24,39,.04)}}
.book:hover{{transform:translateY(-5px);box-shadow:0 20px 40px rgba(17,24,39,.12);border-color:#dbe2ff}}
.cover{{height:280px;background:#eef2ff;overflow:hidden}}
.cover img{{width:100%;height:100%;object-fit:cover;display:block}}
.info{{padding:16px}}
.badge{{font-size:11px;background:#eef2ff;color:var(--ind);border-radius:99px;padding:4px 10px}}
.info h3{{font-size:15px;line-height:1.5;margin:10px 0 6px;min-height:44px}}
.why{{border:0;background:none;color:var(--mut);font-size:11.5px;cursor:pointer;padding:0;text-decoration:underline}}
.foot{{display:flex;justify-content:space-between;align-items:center;margin-top:12px;padding-top:12px;border-top:1px solid var(--line)}}
.price{{font:700 19px Inter;color:var(--ind)}}
.buy{{border:0;border-radius:10px;background:linear-gradient(135deg,#4f46e5,#7c3aed);color:#fff;padding:9px 14px;font:600 12.5px inherit;cursor:pointer}}
.buy:hover{{filter:brightness(1.08)}}
.my{{background:#fff;border:1px solid var(--line);border-radius:18px;padding:20px;margin-top:40px}}
.ov{{display:none;position:fixed;inset:0;background:rgba(17,24,39,.55);backdrop-filter:blur(5px);align-items:center;justify-content:center;z-index:30;padding:16px}}
.box{{background:#fff;border-radius:22px;padding:26px;max-width:440px;width:100%;max-height:92vh;overflow:auto}}
.box h2{{margin:0 0 6px;font-size:20px}}
.sub{{color:var(--mut);font-size:13px;line-height:1.7}}
img.qr{{width:186px;height:186px;background:#fff;border:1px solid var(--line);border-radius:12px}}
.center{{text-align:center;background:#f8f9ff;border-radius:14px;padding:14px;margin:14px 0}}
.num{{font-size:11px;color:var(--mut);margin-top:8px}}
.note{{font-size:12.5px;line-height:1.8;background:#f9fafb;border-radius:12px;padding:12px}}
.fine{{font-size:11.5px;line-height:1.7;color:#9a6a13;background:#fffbeb;border:1px solid #fde68a;border-radius:12px;padding:10px;margin-top:10px}}
input{{width:100%;padding:11px 13px;border:1px solid var(--line);border-radius:11px;font:14px inherit;margin-top:8px}}
.btn{{width:100%;border:0;border-radius:11px;padding:12px;font:600 14px inherit;cursor:pointer;margin-top:10px}}
.go{{background:linear-gradient(135deg,#16a34a,#15803d);color:#fff}}
.no{{background:#f3f4f6;color:#374151}}
.dl{{display:block;text-align:center;background:linear-gradient(135deg,#4f46e5,#7c3aed);color:#fff;text-decoration:none;border-radius:11px;padding:12px;margin-top:12px;font-weight:600}}
.pill{{display:inline-block;background:#fef3c7;color:#92400e;border-radius:99px;padding:5px 11px;font-size:12px}}
footer{{text-align:center;color:var(--mut);font-size:12px;padding:30px 16px 44px;border-top:1px solid var(--line)}}
@media(max-width:600px){{.hero{{padding:34px 22px}}.hero h1{{font-size:27px}}.cover{{height:240px}}}}
</style></head><body>
<nav class="top"><div class="nav"><div class="logo"><span class="mark">✦</span> Zyphere <span style="color:#6b7280;font-weight:500">Books</span></div>
<button class="gbtn" id="gLogin" onclick="googleLogin()">เข้าสู่ระบบด้วย Google</button></div></nav>
<div class="hero"><h1>หนังสือความรู้จากคณะวิชา 46 สาขา</h1>
<p>แต่ละเล่มจัดทำจากสาขาวิชาที่มีอยู่จริงทั่วโลก มีหลายสิบบท พร้อมแบบฝึกหัดท้ายบท ปกออกแบบเฉพาะ และจัดหน้าแบบหนังสืออ่านได้จริง</p>
<div class="stats"><span>{len(rows)} เล่ม</span><span>PromptPay {PROMPTPAY}</span><span>อัพเดทโดยทีมงานอัตโนมัติ</span></div></div>
<section class="sec"><div class="head"><h2>หนังสือทั้งหมด ({len(rows)})</h2>
<input class="search" id="q" placeholder="ค้นหาหัวข้อ..." oninput="filter()"></div>
<div class="grid">{''.join(cards)}</div>
<div class="my" style="margin-top:38px"><h3 style="margin:0 0 6px">คำสั่งซื้อของฉัน</h3>
<p class="sub" id="myMsg">เข้าสู่ระบบด้วย Google เพื่อดูประวัติการซื้อ</p>
<p class="sub" id="myStats" style="display:none"></p><div id="myList"></div></div>
<div class="my" id="ownerBox" style="display:none;border-color:#c7d2fe;background:#f5f7ff">
<h3 style="margin:0 0 6px">โหมดเจ้าของระบบ</h3>
<p class="sub">ดาวน์โหลดหนังสือเพื่อตรวจสอบได้โดยไม่ต้องชำระเงิน</p>
<button class="gbtn" style="margin-top:12px" onclick="ownerDownload()">ดาวน์โหลดเพื่อตรวจสอบ</button></div>
</section>
<div class="ov" id="ov"><div class="box">
 <div id="vPay"><h2>ชำระเงินสำหรับสินค้า</h2><p class="sub" id="pTitle"></p>
  <div class="center"><img class="qr" id="pQR" src="" alt="PromptPay QR"><div class="num">PromptPay {PROMPTPAY}</div></div>
  <p class="note">สแกนคิวอาร์โค้ดเพื่อชำระตามยอดที่แสดง ระบบจะปลดล็อกไฟล์ให้เมื่อยืนยันการชำระเรียบร้อยแล้ว</p>
  <div class="price" id="pPrice"></div><input id="pRef" placeholder="หมายเลขอ้างอิงการโอน หรือตัวเลข 4 ตัวสุดท้าย">
  <button class="btn go" onclick="submitPay()">แจ้งชำระเงิน</button><button class="btn no" onclick="closeM()">ยกเลิก</button></div>
 <div id="vWait" style="display:none"><h2>กำลังตรวจสอบรายการชำระ</h2>
  <p class="sub">รับหลักฐานการชำระของคุณแล้ว กรุณาเก็บหมายเลขคำสั่งซื้อไว้</p>
  <div class="note" id="pOrder"></div><span class="pill">กำลังรอการตรวจสอบ</span>
  <button class="btn go" onclick="checkStatus()">ตรวจสถานะคำสั่งซื้อ</button><button class="btn no" onclick="closeM()">ปิด</button></div>
 <div id="vDone" style="display:none"><h2>ชำระเงินเรียบร้อย</h2><p class="sub">ทีมงานยืนยันและอนุมัติไฟล์ให้แล้ว ขอบคุณที่สนับสนุนครับ</p>
  <a class="dl" id="dl" href="#" download>ดาวน์โหลดแพ็กเกจหนังสือ</a><button class="btn no" onclick="closeM()">ปิด</button></div>
 <div id="vWhy" style="display:none"><h2>ทำไมราคานี้</h2><p class="note" id="whyText"></p>
  <button class="btn no" onclick="closeM()">ปิด</button></div>
</div></div>
<footer>PromptPay {PROMPTPAY} · ชำระปลอดภัย ตรวจสอบโดยทีมงาน และส่งไฟล์จริง</footer>
<script>
const API='{API}';let cur={{}},oid='',tk='';const $=id=>document.getElementById(id);
function filter(){{const q=$('q').value.trim().toLowerCase();let n=0;
 document.querySelectorAll('.book').forEach(c=>{{const ok=c.dataset.title.toLowerCase().includes(q);c.style.display=ok?'':'none';if(ok)n++;}});}}
function showWhy(b){{const c=b.closest('.book');$('whyText').textContent=c.dataset.why;show('vWhy');}}
function show(id){{['vPay','vWait','vDone','vWhy'].forEach(x=>$(x).style.display=(x===id?'block':'none'));$('ov').style.display='flex';}}
function closeM(){{$('ov').style.display='none';}}
function utoken(){{return localStorage.getItem('zy_token')||'';}}
function googleLogin(){{location.href=API+'/api/auth/google?next='+encodeURIComponent(location.href.split('#')[0]);}}
function buy(b){{const c=b.closest('.book');cur={{title:c.dataset.title,price:c.dataset.price}};
 $('pTitle').textContent=cur.title;$('pPrice').textContent='฿'+Number(cur.price).toLocaleString('th-TH');
 $('pQR').src=API+'/api/store/qr?amount='+encodeURIComponent(cur.price)+'&t='+Date.now();show('vPay');}}
async function submitPay(){{
 try{{const cfg=await(await fetch(API+'/api/store/config')).json();
  const o=await(await fetch(API+'/api/store/order',{{method:'POST',headers:{{'Content-Type':'application/json'}},
   body:JSON.stringify({{product:cur.title,amount:cur.price,user_token:utoken()}})}})).json();
  if(!o.ok)throw new Error(o.error);oid=o.id;tk=o.token;
  if(cfg.omise_enabled){{const p=await(await fetch(API+'/api/store/pay/omise',{{method:'POST',headers:{{'Content-Type':'application/json'}},
    body:JSON.stringify({{order_id:oid,token:tk}})}})).json();
   if(!p.ok)throw new Error(p.error);if(p.authorize_uri){{location.href=p.authorize_uri;return}}
   if(p.qr){{$('pQR').src=p.qr;alert('สแกน QR จากประตูชำระเงินครับ');return}}}}
  const s=await(await fetch(API+'/api/store/submit',{{method:'POST',headers:{{'Content-Type':'application/json'}},
   body:JSON.stringify({{order_id:oid,token:tk,ref:$('pRef').value}})}})).json();
  if(!s.ok)throw new Error(s.error);$('pOrder').textContent=oid;show('vWait');loadMy();}}
 catch(e){{alert('ชำระเงินไม่ได้: '+e.message)}}
}}
async function checkStatus(){{const j=await(await fetch(API+'/api/store/download?order_id='+encodeURIComponent(oid)+'&token='+encodeURIComponent(tk))).json();
 if(j.ok){{$('dl').href=j.url;$('dl').download=j.filename||'zyphere-product-pack.zip';show('vDone');}}
 else alert('ยังไม่ได้รับการอนุมัติ');}}
async function loadMy(){{const t=utoken();if(!t)return;
 try{{const st=await(await fetch(API+'/api/store/my/stats?token='+encodeURIComponent(t))).json();
  if(st.ok){{$('myStats').style.display='block';$('myStats').textContent='ซื้อไปแล้ว '+st.books+' เล่ม · รวม '+Number(st.spent).toLocaleString('th-TH')+' บาท';}}
  const j=await(await fetch(API+'/api/store/my-orders?token='+encodeURIComponent(t))).json();
  $('myMsg').style.display=(j.orders||[]).length?'none':'block';
  $('myList').innerHTML=(j.orders||[]).map(o=>'<div style="padding:8px 0;border-bottom:1px solid #eef0f5">'+esc(o.product)+
   ' — <b>฿'+Number(o.amount).toLocaleString('th-TH')+'</b> · '+esc(o.status)+'</div>').join('');}}
 catch(e){{}}}}
async function ownerDownload(){{const j=await(await fetch(API+'/api/store/owner/download',{{method:'POST',headers:{{'Content-Type':'application/json'}},
 body:JSON.stringify({{token:utoken()}})}})).json();
 if(j.ok){{$('dl').href=j.url;$('dl').download=j.filename;show('vDone');}}else alert(j.error||'failed');}}
function esc(s){{return String(s||'').replace(/[&<>]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;'}}[c]))}}
(async function(){{const h=location.hash.match(/oauth=([^&]+)/);
 if(h){{try{{const p=new URLSearchParams(decodeURIComponent(h[1]));localStorage.setItem('zy_token',p.get('token')||'');
  history.replaceState(null,'',location.pathname+location.search);}}catch(e){{}}}}
 if(utoken()){{try{{const me=await(await fetch(API+'/api/store/me?token='+encodeURIComponent(utoken()))).json();
  if(me.ok){{$('gLogin').textContent=me.name||me.email;if(me.me&&me.me.is_owner)$('ownerBox').style.display='block';}}}}catch(e){{}}loadMy();}}
}})();
</script></body></html>'''
    return doc


def main():
    doc = build()
    local = r"C:\Users\vornl\Documents\zyphere\STORE.html"
    open(local, "w", encoding="utf-8").write(doc)
    ok, code = push_site("STORE.html", doc)
    print("published", ok, code, "bytes", len(doc))


if __name__ == "__main__":
    main()
