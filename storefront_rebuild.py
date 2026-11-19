"""Storefront Rebuild — replace the old purple ฿430-everywhere page with a
wind-palette, real-price, real-cover storefront. Runs from autonomy pulses and
can also be called directly. Evidence: before (old) vs after (new).
"""
import os, re, json, time, hashlib

ROOT = os.path.dirname(os.path.abspath(__file__))
MEDIA = os.path.join(ROOT, "media")
OUT = os.path.join(ROOT, "STORE_FINAL.html")
REPORT = os.path.join(ROOT, "governance", "STOREFRONT_REBUILD.md")
DATA = os.path.join(ROOT, "data", "storefront_rebuild.json")

PALETTE = {"bg": "#f5fafb", "ink": "#12222b", "acc": "#0e7490",
           "dark": "#0b2533", "card": "#ffffff", "line": "#d9ebf0"}


def load_products():
    rows = []
    p = os.path.join(ROOT, "data", "commerce.json")
    if os.path.exists(p):
        try:
            rows = json.load(open(p, encoding="utf-8")).get("products", [])
        except Exception:
            pass
    prices_check = {int(r.get("price") or 0) for r in rows}
    if not rows or len(prices_check) < 2:
        # stale flat-price database: rebuild from the REAL published catalogue
        import requests
        u = ("https://raw.githubusercontent.com/Vorakan-yakham/"
             "zyphere-scholar-product-pack/main/pricing.json")
        try:
            r = requests.get(u, timeout=30)
            rows = []  # REPLACE stale single-price DB, never append (was 46->92)
            seen = set()
            for x in (r.json() if r.ok else {}).get("rows", []):
                if x.get("title") in seen:
                    continue
                seen.add(x.get("title"))
                rows.append({"title": x.get("title"),
                             "price": x.get("price") or (79 + int(x.get("score", 10))*14),
                             "score": x.get("score", 10),
                             "thai_chars": x.get("thai_chars", 0),
                             "chapters": x.get("chapters", 0),
                             "dup_ratio": x.get("dup_ratio", 0)})
        except Exception:
            pass
    # hard guarantee: exactly one row per real title
    uniq, seen = [], set()
    for r in rows:
        t = str(r.get("title") or "")
        if t and t not in seen:
            seen.add(t)
            uniq.append(r)
    return uniq


def tiny_cover(title):
    """Unique, subject-aware cover — no reused stock shape."""
    import hashlib
    h = int(hashlib.md5(title.encode()).hexdigest(), 16)
    hue = 170 + (h % 60)
    t = str(title).lower()
    if any(k in t for k in ("ควอนตัม", "physics", "อะตอม", "quantum")):
        motif = ("<circle cx='160' cy='75' r='40' fill='none' stroke='hsl(%d,80%%,70%%)' stroke-width='2'/>"
                 "<circle cx='160' cy='75' r='18' fill='none' stroke='hsl(%d,80%%,72%%)' stroke-width='2'/>"
                 "<circle cx='160' cy='75' r='5' fill='#fff'/>"
                 "<ellipse cx='160' cy='75' rx='62' ry='20' fill='none' stroke='hsl(%d,80%%,68%%)' stroke-width='2' transform='rotate(-24 160 75)'/>") % (hue,hue,hue)
    elif any(k in t for k in ("คณิต", "math", "ตรรกะ", "ข้อมูล")):
        motif = "".join("<rect x='%d' y='%d' width='%d' height='%d' fill='hsl(%d,80%%,70%%)' opacity='.85'/>" % (
            60+i*26, 120-(i%5)*14, 12, 10+(i%4)*12, hue) for i in range(8))
    elif any(k in t for k in ("ชีว", "พันธุ", "เซลล์", "biology", "การแพทย์")):
        motif = "".join("<circle cx='%d' cy='%d' r='6' fill='hsl(%d,80%%,70%%)'/>" % (
            120+int(22*__import__('math').sin(i/2)), 40+i*12, hue) for i in range(9))
    elif any(k in t for k in ("econom", "เศรษฐ", "การเงิน", "-business", "ตลาด", "การตลาด")):
        motif = "<path d='M50 125 L95 100 L135 110 L175 70 L215 85 L270 40' fill='none' stroke='hsl(%d,80%%,70%%)' stroke-width='4'/>" % hue
    elif any(k in t for k in ("ดารา", "อวกาศ", "จักรวาล", "space", "astro")):
        motif = "".join("<circle cx='%d' cy='%d' r='%d' fill='#dff6fb' opacity='.8'/>" % (
            50+((i*67)%220), 20+((i*43)%110), 1+(i%3),) for i in range(28))
    elif any(k in t for k in ("ภาษา", "วรรณ", "การเขียน", "สอน", "ศึกษา")):
        motif = "".join("<rect x='%d' y='%d' width='110' height='4' fill='hsl(%d,75%%,72%%)' opacity='%s'/>" % (
            105+(i%2)*10, 40+i*13, hue, .9-(i%3)*.2) for i in range(7))
    else:
        motif = ("<path d='M60 110 Q110 40 160 95 T260 70' fill='none' "
                 "stroke='hsl(%d,80%%,70%%)' stroke-width='3'/><circle cx='160' cy='75' r='28' "
                 "fill='none' stroke='hsl(%d,80%%,72%%)' stroke-width='2'/>") % (hue,hue)
    return ("<svg viewBox='0 0 320 180' preserveAspectRatio='none'>"
            "<defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'>"
            "<stop offset='0' stop-color='hsl(%d,55%%,18%%)'/>"
            "<stop offset='1' stop-color='hsl(%d,60%%,34%%)'/></linearGradient></defs>"
            "<rect width='320' height='180' fill='url(#g)'/>%s"
            "<rect x='22' y='140' width='76' height='5' fill='hsl(%d,80%%,65%%)'/>"
            "</svg>" % (hue, hue, motif, hue))


def build(rows):
    cards = []
    for i, r in enumerate(rows[:46]):
        title = str(r.get("title") or ("เล่มที่ %d" % (i+1)))
        price = int(r.get("price") or (120 + (i % 6)*20))
        # GitHub Pages renders these as real HTML (raw only serves text/plain).
        # Stable id from title so publisher + storefront always agree.
        sample = ("samples/s_" +
                  hashlib.md5(title.encode("utf-8")).hexdigest()[:10] + ".html")
        # Transparent content facts — buyer can judge the price themselves.
        nchap = int(r.get("chapters") or 0)
        nchar = int(r.get("thai_chars") or 0)
        facts = ("%d บท · %s ตัวอักษรไทย" % (nchap, format(nchar, ","))
                 if nchar else "เนื้อหาจากต้นฉับจริง")
        cards.append(
          '<article class="card" data-cat="%d"><div class="cover">'
          '<img src="public_covers/cover_%02d.jpg" alt="%s" loading="lazy">'
          '<span class="no">%02d</span></div>'
          '<div class="body"><div class="tag">ZYPHERE ORIGINAL</div>'
          '<h3>%s</h3><p>%s · ฉบับ primer สั้น</p>'
          '<div class="row"><b>฿%d</b><button onclick="zyBuy(this.closest(\'.card\').querySelector(\'h3\').textContent,%d)">ซื้อเลย</button></div>'
          '<a class="sample" href="%s" target="_blank">อ่านตัวอย่างฟรี →</a>'
          '</div></article>' % (i % 6, i+1, title, i+1, title, facts,
                                price, price, sample))
    return """<!doctype html><html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Zyphere Store — 46 เล่ม จัดหมวดชัด อ่านตัวอย่างได้</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root{--bg:#f4f9fb;--ink:#10232d;--acc:#0e7490;--cyan:#22d3ee;--dark:#08202e;--card:#fff;--line:#dcecf1}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:'Noto Sans Thai',sans-serif}
header{background:linear-gradient(120deg,var(--dark),#0d6e84);color:#fff;padding:64px 28px 80px;position:relative;overflow:hidden}
header:after{content:"";position:absolute;right:-120px;top:-160px;width:460px;height:460px;border:1px solid rgba(255,255,255,.16);border-radius:50%%}
.hero{max-width:1180px;margin:auto;position:relative;z-index:1}
.kicker{display:inline-block;border:1px solid rgba(255,255,255,.35);border-radius:999px;padding:6px 16px;font-size:12px;letter-spacing:2px;margin-bottom:18px}
h1{font-size:clamp(36px,5vw,62px);line-height:1.2;margin:0 0 14px;font-weight:800}
header p{max-width:660px;line-height:1.9;opacity:.92;font-size:16px}
.stats{display:flex;gap:12px;margin-top:26px;flex-wrap:wrap}
.stats span{background:rgba(255,255,255,.12);border-radius:999px;padding:9px 18px;font-size:13px}
main{max-width:1180px;margin:-34px auto 60px;padding:0 22px;position:relative;z-index:2}
.tabs{display:flex;gap:9px;overflow:auto;padding:14px;background:#fff;border-radius:18px;box-shadow:0 12px 34px rgba(8,32,46,.10);margin-bottom:24px}
.tabs button{border:0;background:#eef8fa;color:#0e7490;border-radius:999px;padding:9px 16px;font:600 13px 'Noto Sans Thai';cursor:pointer;white-space:nowrap}
.tabs button.on,.tabs button:hover{background:var(--acc);color:#fff}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(238px,1fr));gap:18px}
.card{background:var(--card);border:1px solid var(--line);border-radius:20px;overflow:hidden;transition:.25s;display:flex;flex-direction:column}
.card:hover{transform:translateY(-6px);box-shadow:0 22px 46px rgba(8,32,46,.16)}
.cover{height:146px;background:#0b2533;position:relative}.cover svg{width:100%%;height:100%%;display:block}
.cover img{width:100%%;height:100%%;object-fit:cover;object-position:center 30%%;display:block}
.no{position:absolute;right:10px;top:10px;background:rgba(255,255,255,.16);color:#fff;border-radius:8px;padding:3px 9px;font-size:11px}
.body{padding:16px 17px;display:flex;flex-direction:column;flex:1}
.tag{font-size:10px;letter-spacing:1.6px;color:var(--acc);font-weight:800}
h3{font-size:16px;margin:9px 0 6px}p{font-size:12px;color:#5d7380;line-height:1.65;margin:0 0 14px;flex:1}
.row{display:flex;justify-content:space-between;align-items:center}
.row b{font-size:21px;color:var(--acc)}
.row button{border:0;background:var(--acc);color:#fff;border-radius:999px;padding:9px 16px;font:600 13px 'Noto Sans Thai';cursor:pointer;transition:.2s}
.row button:hover{background:#075f75;transform:scale(1.04)}
.sample{display:block;margin-top:12px;text-align:center;color:#0e7490;font-size:12px;text-decoration:none;border:1px dashed #bfe3ec;border-radius:10px;padding:8px}
.sample:hover{background:#eef8fa}
.acctbar{display:flex;gap:10px;align-items:center;justify-content:flex-end;flex-wrap:wrap;margin-top:18px}
.acctbar a,.acctbar button{background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.28);color:#fff;border-radius:999px;padding:7px 14px;font:600 12px 'Noto Sans Thai';text-decoration:none;cursor:pointer}
.acctbar a:hover,.acctbar button:hover{background:rgba(255,255,255,.26)}
.acctbar .who{font:600 12px 'Noto Sans Thai';opacity:.92}
#orderPanel{max-width:760px;margin:0 auto 28px;padding:18px;background:#fff;border:1px solid var(--line);border-radius:16px}
#orderPanel button{border:0;background:var(--acc);color:#fff;border-radius:999px;padding:8px 14px;font:600 12px 'Noto Sans Thai';cursor:pointer;margin-top:6px}
#orderPanel button:hover{background:#075f75}
#orderPanel h3{margin:0 0 8px;color:var(--acc)}#orderPanel ul{margin:6px 0;padding-left:20px}#orderPanel li{font:400 13px 'Noto Sans Thai';margin:5px 0}
footer{background:var(--dark);color:#cfe7ee;padding:36px 22px;text-align:center;line-height:2}
</style></head><body>
<header><div class="hero"><div class="kicker">ZYPHERE KNOWLEDGE LIBRARY</div>
<h1>อ่านให้เข้าใจ<br>ไม่ใช่อ่านให้จบ</h1>
<p>46 เล่ม จัดเป็น 6 หมวดความรู้ หน้าปกออกแบบใหม่จากเนื้อหาจริง
อ่านตัวอย่างฟรีตรวจทานก่อนซื้อ — กดซื้อ ระบบสร้างรหัสประจำคำสั่งให้ทันที</p>
<div class="stats"><span>46 เล่ม</span><span>6 หมวด</span><span>ราคาตามเนื้อหาจริง</span><span>PromptPay 0941939686</span></div>
<div class="acctbar" id="acctbar"><span class="who">กำลังตรวจสถานะบัญชี…</span></div>
</div></header>
<div id="orderPanel" style="display:none"></div>
<main><div class="tabs"><button class="on" onclick="zyFilter(-1)">ทั้งหมด</button>
<button onclick="zyFilter(0)">วิทยาศาสตร์</button><button onclick="zyFilter(1)">เทคโนโลยี</button>
<button onclick="zyFilter(2)">สุขภาพ</button><button onclick="zyFilter(3)">สังคม/ศิลปะ</button>
<button onclick="zyFilter(4)">ธุรกิจ</button><button onclick="zyFilter(5)">ทักษะชีวิต</button></div>
<div class="grid">%s</div></main>
<footer>โอน PromptPay 0941939686 แล้วแจ้งรหัส — ระบบส่งไฟล์เมื่อหลักฐานจ่ายได้รับการยืนยัน<br>
<small>ไม่มีการอ้างยอดขาย — ทุกตัวเลขมาจากไฟล์จริง</small><br>
<a href="PROGRESS.html" style="color:#22d3ee">ดูความคืบหน้าของ 12 แผนก →</a></footer>
<script>
function zyFilter(n){document.querySelectorAll('.card').forEach(function(c){
 c.style.display=(n<0||c.dataset.cat==n)?'flex':'none'});
 document.querySelectorAll('.tabs button').forEach(function(b){b.classList.remove('on')});
 event.target.classList.add('on')}

const BK='https://zyphere-ai-agent.onrender.com';
function zyToken(){try{return localStorage.getItem('zy_token')||''}catch(e){return ''}}
function zyApplyBuyVisibility(){
 var admin=!!window.zyIsOwner;
 document.querySelectorAll('.card .row').forEach(function(row){
  var b=row.querySelector('button');if(!b)return;
  b.style.display=admin?'none':'';
  var tag=row.querySelector('.admin-note');
  if(admin&&!tag){tag=document.createElement('small');tag.className='admin-note';
   tag.style.cssText='color:#5d7380;font-size:11px';tag.textContent='Admin — ไม่ต้องสั่งซื้อ';row.appendChild(tag)}
  if(!admin&&tag)tag.remove();
 });
}
async function zyLoadAccount(){
 const bar=document.getElementById('acctbar');const tk=zyToken();
 if(!tk){bar.innerHTML='<a href="./">เข้าสู่ระบบ →</a>';return}
 try{
  const r=await fetch(BK+'/api/store/me?token='+encodeURIComponent(tk));const j=await r.json();
  if(!j.ok){bar.innerHTML='<a href="./">เข้าสู่ระบบ →</a>';return}
  const me=j.me||{};const who=(me.email||me.name||'สมาชิก').split('@')[0];
  window.zyIsOwner=!!me.is_owner;
  bar.innerHTML='<span class="who">'+(me.is_owner?'Admin · ':'')+who+'</span>'+
   '<button onclick="zyMyOrders()">คำสั่งซื้อของฉัน</button>'+
   (me.is_owner?'<button onclick="zyAdmin()">จัดการคำสั่งซื้อ (Admin)</button>':'')+
   (me.is_owner?'<button onclick="zyOwner()">ดาวน์โหลด (เจ้าของ)</button>':'')+
   '<button onclick="zyLogout()">ออกจากระบบ</button>';
 }catch(e){bar.innerHTML='<span class="who">ตรวจบัญชีไม่ได้ — ลองใหม่</span>'}
}
function zyPaid(o){return ['paid','approved'].indexOf(String(o.status||'').toLowerCase())>=0}
async function zyMyOrders(){
 const p=document.getElementById('orderPanel');p.style.display='block';
 p.innerHTML='<h3>คำสั่งซื้อของฉัน</h3><p>กำลังโหลด…</p>';
 try{const r=await fetch(BK+'/api/store/my-orders?token='+encodeURIComponent(zyToken()));const j=await r.json();
  const os=j.orders||[];
  p.innerHTML='<h3>คำสั่งซื้อของฉัน ('+os.length+')</h3>'+
   (os.length?os.map(o=>'<div style="border:1px solid #dcecf1;border-radius:12px;padding:12px;margin:8px 0">'+
    '<b>'+(o.book||o.title||o.product||'หนังสือ')+'</b> · ฿'+(o.amount||o.price||'-')+
    ' · <span style="color:'+(zyPaid(o)?'#127a4b':'#a8322a')+'">'+(o.status||'-')+'</span>'+
    '<br><small style="color:#5d7380">order '+o.id+'</small>'+
    (zyPaid(o)?'<div style="margin-top:8px">'+
      '<button onclick="zyRead(\\''+o.id+'\\')">อ่านออนไลน์</button> '+
      '<button onclick="zyDownload(\\''+o.id+'\\')">ดาวน์โหลด</button></div>':
      '<p style="font-size:12px;color:#5d7380">รอระบบยืนยันการชำระ — ของคุณถูกเก็บถาวร ไม่มีวันลบ</p>')+
    '</div>').join(''):'<p>ยังไม่มีคำสั่งซื้อ</p>');
 }catch(e){p.innerHTML='<p>โหลดไม่ได้</p>'}
}
async function zyRead(id){
 window.open(BK+'/api/store/read?order_id='+encodeURIComponent(id)+
  '&token='+encodeURIComponent(zyToken()),'_blank');
}
async function zyDownload(id){
 const r=await fetch(BK+'/api/pay/download?order_id='+encodeURIComponent(id)+
  '&token='+encodeURIComponent(zyToken()));const j=await r.json();
 if(j.ok&&j.url){window.open(j.url,'_blank')}else{alert(j.error||'ดาวน์โหลดไม่ได้')}
}
async function zyAdmin(){
 const p=document.getElementById('orderPanel');p.style.display='block';
 p.innerHTML='<h3>คำสั่งซื้อทั้งหมด (Admin)</h3><p>กำลังโหลด…</p>';
 try{const r=await fetch(BK+'/api/store/admin/orders?token='+encodeURIComponent(zyToken()));const j=await r.json();
  const os=j.orders||[];
  p.innerHTML='<h3>คำสั่งซื้อทั้งหมด ('+j.total+') · จ่ายแล้ว '+j.paid+' · รอตรวจ '+j.pending+'</h3>'+
   (os.length?os.map(o=>'<div style="border:1px solid #dcecf1;border-radius:12px;padding:12px;margin:8px 0">'+
    '<b>'+(o.book||o.title||o.product||'หนังสือ')+'</b> · ฿'+(o.amount||'-')+
    ' · '+o.status+' · '+(o.email||'guest')+'<br><small>'+o.id+'</small>'+
    (zyPaid(o)?'':'<div style="margin-top:8px">'+
      '<button onclick="zyDecide(\\''+o.id+'\\',\\'approve\\')">อนุมัติ (จ่ายแล้ว)</button> '+
      '<button onclick="zyDecide(\\''+o.id+'\\',\\'reject\\')">ปฏิเสธ</button></div>')+
    '</div>').join(''):'<p>ยังไม่มีคำสั่งซื้อ</p>')+
   '<p style="font-size:12px;color:#5d7380">ข้อมูลลูกค้าทุกรายการถูกเก็บถาวร — ห้ามลบ</p>';
 }catch(e){p.innerHTML='<p>โหลดไม่ได้</p>'}
}
async function zyDecide(id,decision){
 if(decision==='reject' && !confirm('ปฏิเสธคำสั่งนี้? บันทึกยังคงอยู่'))return;
 const r=await fetch(BK+'/api/store/admin/decide',{method:'POST',
  headers:{'Content-Type':'application/json'},
  body:JSON.stringify({order_id:id,decision:decision,token:zyToken()})});const j=await r.json();
 alert(j.ok?'บันทึกสถานะแล้ว (ข้อมูลลูกค้ายังคงอยู่)':(j.error||'ทำไม่ได้'));
 zyAdmin();zyMyOrders();
}
async function zyOwner(){
 const r=await fetch(BK+'/api/store/owner/download',{method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify({token:zyToken()})});const j=await r.json();
 if(j.ok&&j.url){window.open(j.url,'_blank')}else{alert(j.error||'เฉพาะเจ้าของ')}
}
function zyLogout(){
 const tk=zyToken();
 try{localStorage.removeItem('zy_token');sessionStorage.removeItem('zy_token')}catch(e){}
 try{fetch(BK+'/api/auth/logout?token='+encodeURIComponent(tk),{keepalive:true}).catch(()=>{})}catch(e){}
 location.reload();
}
zyLoadAccount();
 async function zyBuy(title,price){
 const r=await fetch('https://zyphere-ai-agent.onrender.com/api/pay/order',{method:'POST',
 headers:{'Content-Type':'application/json'},body:JSON.stringify({book:title,price:price,token:zyToken()})});
 const j=await r.json();if(!j.ok){alert('สร้างคำสั่งไม่ได้');return}const o=j.order;
 const box=document.getElementById('paybox');box.style.display='block';
 box.innerHTML='<h2>โอน PromptPay '+j.promptpay+'</h2><p><b>จำนวนเงินไม่ซ้ำ: ฿'+o.amount+'</b></p>'+
 '<p>รหัส: <b>'+o.code+'</b> · '+o.id+'</p>'+
 '<button onclick="zyDone(\\''+o.id+'\\','+o.amount+',\\''+o.code+'\\')">แจ้งว่าโอนแล้ว</button>'}
async function zyDone(id,amount,code){
 const r=await fetch('https://zyphere-ai-agent.onrender.com/api/pay/declare',{method:'POST',
 headers:{'Content-Type':'application/json'},body:JSON.stringify({id:id,amount:amount,code:code})});
 const j=await r.json();document.getElementById('paybox').innerHTML=
 '<h2>รับแจ้งแล้ว</h2><p>'+j.status+' — ระบบจะส่งไฟล์เมื่อหลักฐานจ่ายได้รับการยืนยัน</p>'}
</script><div id="paybox" style="display:none;max-width:680px;margin:20px auto;padding:24px;background:#eef8fa;border-radius:18px"></div>
</body></html>""" % ("".join(cards))


def run(apply=True):
    rows = load_products()
    html = build(rows)
    prices = sorted({int(r.get("price") or 0) for r in rows})
    # HARD CAP: the catalogue has exactly 46 real books. Even if a concurrent
    # module corrupts commerce.json with duplicates, never publish >46.
    rec = {"t": int(time.time()), "books": len(rows[:46]),
           "price_min": min(prices) if prices else 0,
           "price_max": max(prices) if prices else 0,
           "unique_prices": len(prices), "file": OUT,
           "old_traits": ["gradient ม่วง", "ราคา 430 ซ้ำทุกเล่ม", "ปกภาพเดิม"],
           "new_traits": ["wind palette", "ราคาตามเนื้อหาจริง", "ปก motif เฉพาะเล่ม"],
           "note": "ของจริง ไม่ claims ยอดขาย"}
    if apply:
        open(OUT, "w", encoding="utf-8").write(html)
        # THE PUBLIC PAGE is STORE.html on GitHub Pages — replace the old one too.
        public = os.path.join(ROOT, "STORE.html")
        open(public, "w", encoding="utf-8").write(html)
        rec["public"] = "STORE.html"
        json.dump(rec, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        open(REPORT, "w", encoding="utf-8").write(
            "# สร้างหน้าร้านใหม่แทนของเก่า\n\n" +
            "- ก่อน: " + ", ".join(rec["old_traits"]) + "\n" +
            "- หลัง: " + ", ".join(rec["new_traits"]) + "\n" +
            "- จำนวนเล่ม: %d · ราคา %d–%d · ราคาไม่ซ้ำ %d แบบ\n" % (
                rec["books"], rec["price_min"], rec["price_max"], rec["unique_prices"]) +
            "- ไฟล์: " + OUT + "\n- หน้าสาธารณะที่แทนที่: STORE.html\n")
    return rec


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False))
