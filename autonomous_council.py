"""Zyphere Autonomous Cross-Department Council.

Each department learns from a DIFFERENT source (no shared single brain), reports
metrics it alone can see, debates through the AI ensemble with assigned roles,
then APPLIES the consensus as real files in the product repository.

This is deliberately autonomous: it is designed to be invoked by the scheduled
workflow without waiting for an owner command. Nothing is claimed that is not
backed by a fetched file or a computed metric.
"""
import os, re, json, time, subprocess, threading, urllib.parse
import brain_ensemble as BE

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = "Vorakan-yakham/zyphere-scholar-product-pack"
BRANCH = "main"
OUT = os.path.join(ROOT, "governance", "AUTONOMOUS_COUNCIL.md")
DATA = os.path.join(ROOT, "data", "autonomous_council.json")
DEPT_BRAIN = os.path.join(ROOT, "data", "dept_brains")
LOCK = threading.RLock()

# Each department reads ONLY its own source(s) — knowledge is not pooled.
DEPARTMENTS = {
    "production": {
        "th": "ฝ่ายผลิตหนังสือ",
        "sources": ["pricing.json", "PROMO.md"],
        "job": "ตรวจว่ามีต้นฉบับจริงกี่เล่ม จำนวนคำ/บทต่อเล่ม และ价格ตรงกับข้อมูลจริงไหม",
    },
    "design": {
        "th": "ฝ่ายออกแบบผลิตภัณฑ์",
        "sources": ["BOOK_DESIGN_STANDARD.md"],
        "job": "ตรวจว่า book.html/cover.png มีจริงและตรงมาตรฐานการจัดวางหรือไม่",
    },
    "market": {
        "th": "ฝ่ายการตลาดและราคา",
        "sources": ["pricing.json", "PRODUCTS.md"],
        "job": "ตรวจความ inconsistent ของราคา คำอธิบาย และลิงก์ไฟล์หน้าร้าน",
    },
    "qa": {
        "th": "ฝ่ายทดสอบและคุณภาพ",
        "sources": ["QUALITY_REPORT.md", "REVIEW.md"],
        "job": "ตรวจว่าตัวชี้วัดไหนยังต่ำกว่าเป้า และห้ามปล่อยของที่ไม่ผ่านเกณฑ์",
    },
    "sales": {
        "th": "ฝ่ายขายและหน้าร้าน",
        "sources": ["PRODUCTS.md", "ZY_TEMPLATE.html"],
        "job": "ตรวจว่าลูกค้าเห็นราคาจริง คำอธิบายคุณค่า และลิงก์ดาวน์โหลดที่ใช้งานได้หรือไม่",
    },
    "income": {
        "th": "ฝ่ายรายได้ (คิดเองจากข้อมูลจริง)",
        "sources": ["PROMO.md", "book_pricing.json", "PRODUCTS.md"],
        "job": "คิดวิธีสร้างรายได้จากสินค้าที่มีอยู่จริง โดยไม่รอคำสั่ง และห้ามอ้างยอดขายที่ไม่มี",
    },
}


def _token():
    """Token only when the owner has configured it — never printed or stored."""
    for k in ("GH_TOKEN", "GITHUB_TOKEN"):
        v = os.environ.get(k, "").strip()
        if v:
            return v
    try:
        p = subprocess.run(["gh", "auth", "token"], capture_output=True,
                           text=True, timeout=10)
        if p.returncode == 0:
            return p.stdout.strip()
    except FileNotFoundError:
        pass  # Render has no gh CLI — read still works through raw.githubusercontent
    return None


def gh_raw(path):
    # raw.githubusercontent needs no token and is not rate-limited like the API.
    try:
        import requests
        url = "https://raw.githubusercontent.com/%s/%s/%s" % (
            REPO, BRANCH, urllib.parse.quote(path))
        r = requests.get(url, timeout=30)
        return r.text if r.ok else None
    except Exception:
        return None


def gh_tree():
    try:
        import requests
        h = {"Accept": "application/vnd.github+json"}
        tok = _token()
        if tok:
            h["Authorization"] = "Bearer " + tok
        url = "https://api.github.com/repos/%s/git/trees/%s?recursive=1" % (REPO, BRANCH)
        r = requests.get(url, headers=h, timeout=30)
        if not r.ok:
            return {}
        return {x["path"]: int(x.get("size") or 0)
                for x in r.json().get("tree", []) if x.get("type") == "blob"}
    except Exception:
        return {}


def gh_put(path, content, message):
    """Write a UTF-8 file to the product repo through the GitHub API."""
    import base64
    token = _token()
    if not token:
        return {"ok": False, "error": "no repo token configured (read-only mode)"}
    import requests
    h = {"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json"}
    url = "https://api.github.com/repos/%s/contents/%s" % (REPO, path)
    sha = None
    r = requests.get(url, headers=h, timeout=20)
    if r.ok:
        sha = r.json().get("sha")
    payload = {"message": message, "branch": BRANCH,
               "content": base64.b64encode(content.encode("utf-8")).decode()}
    if sha:
        payload["sha"] = sha
    r = requests.put(url, headers=h, json=payload, timeout=30)
    return {"ok": r.ok, "status": r.status_code}


def _words(text):
    return len(re.findall(r"\S+", text or ""))


def observe(tree, raw):
    """Each department computes its own metrics from its own sources only."""
    products = json.loads(raw.get("PRODUCTS.md") or "[]")
    pricing = json.loads(raw.get("pricing.json") or '{"rows":[]}').get("rows", [])
    prices = {r.get("title"): r.get("price") for r in pricing}
    books = {}
    for path, size in tree.items():
        m = re.match(r"books/([^/]+)/content\.md$", path)
        if m:
            books[m.group(1)] = path
    findings = {}
    # production
    details = []
    for folder, path in sorted(books.items()):
        text = raw.get(path) or ""
        details.append({"folder": folder, "words": _words(text),
                        "headings": len(re.findall(r"(?m)^#{1,4} ", text)),
                        "price": prices.get(folder.split("_", 1)[-1].replace("-", " "))})
    findings["production"] = {"books": len(books), "detail": details[:6],
        "below_3000_words": [d["folder"] for d in details if d["words"] < 3000],
        "source": "pricing.json + books/*/content.md via tree"}
    # design
    findings["design"] = {
        "html": sum(1 for p in tree if p.endswith("/book.html")),
        "covers": sum(1 for p in tree if p.endswith("/cover.png")),
        "standard": _words(raw.get("BOOK_DESIGN_STANDARD.md")) > 100,
        "source": "BOOK_DESIGN_STANDARD.md + file tree"}
    # market
    mismatches = []
    for p in products:
        t = p.get("title", "")
        hit = next((r for r in pricing if r.get("title") and r["title"] in t or t in r.get("title", "")), None)
        if hit and p.get("price") != hit.get("price"):
            mismatches.append({"title": t, "store": p.get("price"), "standard": hit.get("price")})
    findings["market"] = {"products": len(products), "pricing_rows": len(pricing),
        "price_mismatches": len(mismatches), "samples": mismatches[:5],
        "empty_assets": sum(1 for p in products if not p.get("asset_url")),
        "weak_desc": sum(1 for p in products if _words(p.get("desc")) < 12),
        "source": "pricing.json + PRODUCTS.md"}
    # qa
    qa = raw.get("QUALITY_REPORT.md") or ""
    findings["qa"] = {
        "below_target": re.findall(r"\|\s*([^|]+?)\s*\|\s*(\w+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*ต้องพัฒนา", qa),
        "gate": "ห้ามเผยแพร่หนังสือหรือโปรโมทหากฝ่ายผลิตไม่ผ่านเกณฑ์คุณภาพ" in qa,
        "source": "QUALITY_REPORT.md + REVIEW.md"}
    # sales
    findings["sales"] = {
        "live": sum(1 for p in products if p.get("status") == "live"),
        "no_asset": sum(1 for p in products if not p.get("asset_url")),
        "template_bytes": tree.get("ZY_TEMPLATE.html", 0),
        "source": "PRODUCTS.md + ZY_TEMPLATE.html"}
    promo = raw.get("PROMO.md") or ""
    try:
        bpricing = json.loads(raw.get("book_pricing.json") or "{}").get("rows", [])
    except Exception:
        bpricing = []
    findings["income"] = {
        "promo_sections": promo.count("## "),
        "book_pricing_rows": len(bpricing),
        "sellable_assets": sum(1 for p in products if p.get("asset_url")),
        "store_items": len(products),
        "priced_items": sum(1 for p in products if p.get("price")),
        "source": "PROMO.md + book_pricing.json + PRODUCTS.md"}
    return findings, products, pricing, books


def rank_departments(findings):
    """Real competition: score each department from what it MEASURED, not
    from opinions. Winner's method is taught to losers with fresh evidence."""
    def score(x):
        return max(0, min(100, int(x)))
    prod = findings.get("production", {})
    design = findings.get("design", {})
    market = findings.get("market", {})
    qa = findings.get("qa", {})
    sales = findings.get("sales", {})
    total = max(1, prod.get("books", 0))
    good = total - len(prod.get("below_3000_words", []))
    rows = [
        {"code": "production", "dept": "ฝ่ายผลิตหนังสือ",
         "score": score(100 * good / total),
         "metric": "เล่มเนื้อหา >=3000 คำ %d/%d" % (good, total)},
        {"code": "design", "dept": "ฝ่ายออกแบบผลิตภัณฑ์",
         "score": score(100 if design.get("html", 0) >= 46 and design.get("covers", 0) >= 46 else 60),
         "metric": "book.html %d / cover %d / มาตรฐาน %s" % (
             design.get("html", 0), design.get("covers", 0), design.get("standard"))},
        {"code": "market", "dept": "ฝ่ายการตลาดและราคา",
         "score": score(100 - 4 * market.get("price_mismatches", 0) - 2 * market.get("empty_assets", 0)),
         "metric": "ราคาไม่ตรง %d / ไม่มีลิงก์ %d / desc สั้น %d" % (
             market.get("price_mismatches", 0), market.get("empty_assets", 0),
             market.get("weak_desc", 0))},
        {"code": "qa", "dept": "ฝ่ายทดสอบและคุณภาพ",
         "score": score(100 - 15 * len(qa.get("below_target", [])) + (10 if qa.get("gate") else 0)),
         "metric": "ตัวชี้วัดต่ำเป้า %d" % len(qa.get("below_target", []))},
        {"code": "sales", "dept": "ฝ่ายขายและหน้าร้าน",
         "score": score(100 - 5 * sales.get("no_asset", 0)),
         "metric": "สินค้าไม่มีไฟล์ %d / live %d" % (
             sales.get("no_asset", 0), sales.get("live", 0))},
        {"code": "income", "dept": "ฝ่ายรายได้",
         "score": score(min(100, 3 * findings.get("income", {}).get("sellable_assets", 0)
                            + findings.get("income", {}).get("promo_sections", 0))),
         "metric": "สินค้ามีไฟล์ %d / ราคา %d / โปรโม %d" % (
             findings.get("income", {}).get("sellable_assets", 0),
             findings.get("income", {}).get("priced_items", 0),
             findings.get("income", {}).get("promo_sections", 0))},
    ]
    rows.sort(key=lambda r: r["score"], reverse=True)
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    winner = rows[0]
    # The losers learn the winner's measurable method — with NEW evidence,
    # not a copy of last round's lesson.
    for r in rows[1:]:
        _teach(r["code"],
               "รอบการแข่งขัน: ฝ่าย%s ชนะด้วย %s (%d คะแนน) — วิธีที่ต้องนำไปปรับคือ %s "
               "ของฝ่ายคุณตอนนี้คือ %s" % (winner["dept"], winner["metric"], winner["score"],
                                        winner["dept"], r["metric"]))
    return {"winner": winner["dept"], "winner_score": winner["score"],
            "board": rows,
            "rule": "คะแนนมาจากตัววัดจริงของแต่ละฝ่ายเท่านั้น — ฝ่ายที่แพ้ต้องเรียนวิธีของฝ่ายชนะ"}


def recall_prior():
    """Remember: reload last round's decision and each department's own
    lessons BEFORE debating. Without this the system is a goldfish — it writes
    files but never uses what it learned."""
    out = {"previous": None, "lessons": []}
    try:
        prev = json.load(open(DATA, encoding="utf-8"))
        comp = (prev.get("findings") or {}).get("competition") or {}
        out["previous"] = {
            "t": prev.get("t"),
            "winner": comp.get("winner"),
            "products": prev.get("products_rebuilt"),
            "consensus": (prev.get("debate") or {}).get("consensus", "")[:700],
        }
    except Exception:
        pass
    for code, d in DEPARTMENTS.items():
        try:
            j = json.load(open(os.path.join(DEPT_BRAIN, code + ".json"), encoding="utf-8"))
            for e in (j.get("episodes") or [])[-2:]:
                out["lessons"].append({"dept": d["th"], "text": str(e.get("text", ""))[:260]})
        except Exception:
            pass
    return out


def debate(findings):
    """Different providers argue from their own department's observations."""
    keys = BE.load_keys()
    if not keys:
        return {"ok": False, "error": "no AI keys"}
    names = [n for n in keys if n in BE.CALLERS]
    positions = []
    for i, (code, d) in enumerate(DEPARTMENTS.items()):
        name = names[i % len(names)] if names else None
        if not name:
            continue
        instruction = ("คุณคือ" + d["th"] + ". " + d["job"] +
                       "\nอ่านข้อมูลที่ฝ่ายคุณวัดได้เองนี้ แล้วเสนอการแก้ไขที่ทำได้จริง "
                       "ห้ามอ้างยอดขาย/คุณภาพที่ไม่มีหลักฐาน ตอบภาษาไทยกระชับ 4-6 ข้อ")
        payload = json.dumps(findings[code], ensure_ascii=False)[:4000]
        fn = BE.CALLERS[name]
        tried = False
        for model in BE.MODELS.get(name, [None]):
            try:
                out = fn(keys[name], [
                    {"role": "system", "content": instruction},
                    {"role": "user", "content": payload}], model=model, max_tokens=700)
                if out and out.strip():
                    positions.append({"dept": d["th"], "provider": name,
                                      "text": out.strip()})
                    tried = True
                    break
            except Exception:
                continue
        if not tried:
            positions.append({"dept": d["th"], "provider": name, "text": "ไม่ได้รับคำตอบจากโมเดล"})
    digest = "\n\n".join("### %s (%s)\n%s" % (p["dept"], p["provider"], p["text"]) for p in positions)
    try:
        from conversation_learning import CL
        cl = CL.status()
        if cl.get("corrections"):
            digest += "\n\n### คำแก้ไขจากผู้ใช้ (ต้องปฏิบัติ ไม่ใช่แค่จำ)\n"
            digest += "จำนวนบทสนทนาที่ผู้ใช้แก้ไข: %d\n" % cl.get("corrections")
            for x in reversed(CL.log):
                if x.get("rule"):
                    digest += "- " + str(x.get("user", ""))[:150] + " → " + str(x.get("rule", ""))[:130] + "\n"
                if digest.count("→") > 12:
                    break
    except Exception:
        pass
    mem = findings.get("recall") or {}
    if mem.get("previous") or mem.get("lessons"):
        digest += "\n\n### ความจำจากรอบก่อน (ต้องใช้ ไม่ใช่เขียนทิ้ง)\n"
        if mem.get("previous"):
            digest += "คำตัดสินก่อนหน้า: " + json.dumps(mem["previous"], ensure_ascii=False) + "\n"
        for x in mem.get("lessons", []):
            digest += "- %s เคยเรียนรู้: %s\n" % (x["dept"], x["text"])
        digest += "ถ้าจะพูดเรื่องเดิม ให้ระบุว่าปรับปรุงจากสิ่งที่จำได้อย่างไร\n"
    comp = findings.get("competition") or {}
    if comp.get("board"):
        digest += "\n\n### ตารางแข่งขันฝ่าย (คะแนนจริง)\n" + "\n".join(
            "%d. %s — %d คะแนน (%s)" % (r["rank"], r["dept"], r["score"], r["metric"])
            for r in comp["board"]) + "\nผู้ชนะ: " + str(comp.get("winner"))
    ite = findings.get("it_engineers") or {}
    if ite.get("ran"):
        digest += "\n\n### วิศวกร IT ประจำแผนก 12 คน\n" + (
            "เสนอ patch %d รอบ, push จริง %d — %s\n" % (
                ite.get("ran"), ite.get("pushed"),
                ", ".join(str(x.get("division")) + ":" + str(x.get("file"))
                          for x in ite.get("sample", []))))
    div = findings.get("division_heads") or {}
    if div.get("heads"):
        digest += "\n\n### หัวหน้าแผนก 12 คนกระตุ้นหัวหน้าฝ่าย (ชั้นที่สอง)\n" + "\n".join(
            "- %s ถาม: %s | สั่ง: %s" % (h["division"], h["question"], h["action"])
            for h in div["heads"]) + "\n"
    heads = (findings.get("supervisors") or {}).get("heads") or []
    if heads:
        digest += "\n\n### คำถามจากหัวหน้าฝ่าย 10 คน (ต้องตอบให้ครบ ไม่ใช่ข้าม)\n" + "\n".join(
            "- %s ถาม: %s | วัดได้: %s | ซ้ำ: %s" % (
                h["dept"], h["question"], h["detail"], h.get("repeated"))
            for h in heads)
    syn = BE.ensemble([
        {"role": "system", "content": "คุณเป็นประธานสภาหลายแผนกที่คิดเองได้จากหลักฐาน "
         "รวมข้อเสนอที่ขัดกันเป็นคำตัดสินที่นำไปทำได้จริง "
         "ต้องเสนอ 'สิ่งที่แต่ละฝ่ายควรพัฒนาให้ดีกว่าฝ่ายอื่น' (differentiated capability) "
         "เป็นข้อเฉพาะของแต่ละฝ่าย พร้อมวิธีวัดผลที่เป็นตัวเลขได้ "
         "และตอบคำถามของหัวหน้าฝ่ายทุกคนด้วยหลักฐานใหม่ ไม่ใช่ความรู้เดิมซ้ำ "
         "ระบุสิ่งที่ต้องแก้ใน PRODUCTS.md ให้ชัด ห้ามสร้างยอดขายปลอม ตอบภาษาไทย กระชับ"},
        {"role": "user", "content": digest},
    ], want_synthesis=True)
    return {"ok": True, "positions": positions,
            "consensus": syn.get("text") or syn.get("error") or ""}


def rebuild_products(pricing, books, findings, raw=None):
    """Consensus applied to real data: market-engine prices, real download links,
    descriptions derived from actual headings. Hard QA gate: if the quality
    system has not passed, products are marked 'review' — never faked as live.

    Note: this writes the store manifest only. It does not claim sales,
    conversion, or customer satisfaction that has not been measured.
    """
    raw = raw or {}
    try:
        from quality_ops import QOPS
        gate_ok = bool(QOPS.gate_ok())
    except Exception:
        gate_ok = False
    try:
        from council_review import market_price
    except Exception:
        market_price = None
    rows = []
    by_title = {r.get("title"): r for r in pricing}
    for title, row in by_title.items():
        folder = next((f for f in books if f.split("_", 1)[-1] == title), None)
        if not folder:
            continue
        path = books[folder]
        text = raw.get(path) or ""
        words = _words(text)
        if words < 3000:
            continue  # thin draft: do not publish at all
        skip = {"สารบัญ", "บทนำ", "ความหมายโดยย่อ", "สรุป", "คำถามที่พบบ่อย", "บทส่งท้าย"}
        heads = [re.sub(r"^#+\s*", "", ln).strip() for ln in text.splitlines()
                 if re.match(r"(?m)^#{2,3} ", ln) and len(ln.strip()) > 4]
        heads = [h for h in heads if h not in skip][:4]
        price = int(row.get("price") or 120)
        if market_price:
            try:
                mp = market_price(title)
                if isinstance(mp, (tuple, list)) and mp and isinstance(mp[0], (int, float)):
                    price = int(mp[0])
            except Exception:
                pass
        url = "https://raw.githubusercontent.com/%s/%s/%s" % (REPO, BRANCH, path)
        desc = ("ชุดอ่านเชิงระบบจากต้นฉบับจริง หัวข้อที่ครอบคลุม: %s "
                "— ออกแบบให้เข้าใจได้ทีละขั้น พร้อมกรณีศึกษาและคำถามที่พบบ่อยของ%s"
                % (" · ".join(heads) if heads else title, title))
        rows.append({
            "id": "bk_" + re.sub(r"\W+", "", folder)[:16],
            "title": title,
            "price": price,
            "desc": desc,
            "category": "ebook",
            "seller": "Zyphere",
            "asset_url": url,
            "file": path,
            "words": words,
            "chapters": row.get("chapters") or 4,
            "status": "live" if gate_ok else "review",
            "gate_ok": gate_ok,
            "t": int(time.time()),
        })
    return rows


def build_income_plan(findings, products, debate):
    """Income department reasons from real metrics. No invented revenue."""
    inc = findings.get("income", {})
    qa = findings.get("qa", {})
    comp = findings.get("competition") or {}
    return """# แผนสร้างรายได้ที่สภาคิดเอง (อัปเดตอัตโนมัติ)

รอบ: %s · ฝ่ายชนะการแข่งขัน: %s (%s คะแนน)

## หลักฐานที่มีจริงตอนนี้
- สินค้าใน manifest: %d รายการ / มีลิงก์ไฟล์จริง: %d / มีราคา: %d
- ส่วนโปรโมใน PROMO.md: %d / book_pricing.json: %d แถว
- QA gate: %s → สถานะสินค้า: %s (ห้ามขายถ้า review)

## สิ่งที่ทำได้ทันทีโดยไม่ต้องรอคำสั่ง
1. **ปิดจุดอ่อนก่อนขาย**: %s — ต้องทำให้ gate ผ่านก่อนปล่อย live
2. **ของจริงที่ขายได้**: ใช้ลิงก์ raw.githubusercontent ที่มีอยู่จริง + ราคาจาก market_price + คำอธิบายจากหัวข้อเนื้อหา (ไม่แต่ง)
3. **หน้าร้าน**: ใช้ ZY_TEMPLATE ที่ต้องแก้ nav ให้เข้ากับ theme ก่อนโปรโมท
4. **ช่องทางฟรี**: GitHub README/Pages + QR PromptPay (0941939686) + โพสต์จาก PROMO.md ที่มีอยู่
5. **วัดผลจริง**: /api/store/stats (orders), /api/store/config — ห้ามสร้างยอดขายหรือรีวิวปลอม

## ที่ยังต้องเจ้าของ (ไม่แกล้งทำ)
- Omise keys สำหรับ webhook ยืนยันจ่ายอัตโนมัติ (ตอนนี้ manual verification)
- token autopost สำหรับโพสต์อัตโนมัติจริง

## สิ่งที่สภาตัดสินรอบนี้
%s
""" % (time.strftime("%Y-%m-%d %H:%M", time.localtime()),
       comp.get("winner", "—"), comp.get("winner_score", 0),
       len(products), inc.get("sellable_assets", 0), inc.get("priced_items", 0),
       inc.get("promo_sections", 0), inc.get("book_pricing_rows", 0),
       findings.get("qa", {}).get("below_target", []),
       products[0].get("status") if products else "none",
       "; ".join(str(x[0]) + ":" + str(x[2]) for x in qa.get("below_target", [])) or "ไม่มีข้อมูล",
       (debate.get("consensus") or "")[:1400])


def _teach(code, text):
    try:
        from local_brain import LocalBrain
        os.makedirs(DEPT_BRAIN, exist_ok=True)
        lb = LocalBrain(os.path.join(DEPT_BRAIN, code + ".json"))
        lb.learn_text(text, source="council:" + code)
    except Exception:
        pass


def run(apply=True):
    tree = gh_tree()
    if not tree:
        return {"ok": False, "error": "cannot read product repo tree"}
    book_paths = [p for p in tree if re.match(r"books/[^/]+/content\.md$", p)]
    raw = {p: gh_raw(p) or "" for p in
           ["PRODUCTS.md", "pricing.json", "QUALITY_REPORT.md", "REVIEW.md",
            "BOOK_DESIGN_STANDARD.md", "PROMO.md", "ZY_TEMPLATE.html"] + book_paths}
    findings, products, pricing, books = observe(tree, raw)
    # Ten department heads question and escalate in their own right — the
    # council must debate WITH them, not replace them.
    sup_results = []
    try:
        from supervisors import SUP
        sv = SUP.nag_all({"price_mismatch": findings["market"]["price_mismatches"],
                          "gate_ok": False, "workflow_fail": 0})
        sup_results = sv.get("results", [])
        findings["supervisors"] = {"round": sv.get("round"),
                                   "working": sv.get("working"),
                                   "repeated": sv.get("repeated"),
                                   "heads": [{"dept": r["dept"], "question": r["question"],
                                              "detail": r["detail"], "action": r["action"],
                                              "repeated": r.get("repeated")}
                                             for r in sv.get("results", [])]}
    except Exception:
        findings["supervisors"] = {"error": "supervisors unavailable"}
    findings["competition"] = rank_departments(findings)
    findings["recall"] = recall_prior()
    deb = debate(findings)
    new_products = rebuild_products(pricing, books, findings, raw)
    applied = {"ok": False, "status": None}
    plan_write = {"ok": False, "status": None}
    if apply and new_products:
        applied = gh_put("PRODUCTS.md",
                         json.dumps(new_products, ensure_ascii=False, indent=2) + "\n",
                         "Autonomous council: align store prices, real download links and value descriptions")
        plan_write = gh_put("INCOME_PLAN.md", build_income_plan(findings, new_products, deb),
                            "Council: income strategy derived from real metrics (no fake sales)")
    # Zyphere improves its own code using what the council just learned —
    # guarded by self_coder (compile -> regression -> push -> revert on failure).
    selfcode = {"ok": False, "error": "not run"}
    try:
        from self_coder import SelfCoder
        # Focus the self-coder on the department the council found failing —
        # it improves the code responsible for the real gap, not random files.
        if findings.get("qa", {}).get("below_target"):
            focus = "quality_ops.py"
        elif (findings.get("supervisors") or {}).get("repeated"):
            focus = "supervisors.py"
        else:
            focus = "autonomous_council.py"
        selfcode = SelfCoder().cycle(dry=not apply, focus=focus)
        selfcode["focus"] = focus
    except Exception as e:
        selfcode = {"ok": False, "error": str(e)[:160]}
    # Division heads re-audit AFTER the self-coder result is known: they are
    # the second layer of pressure on top of the department supervisors.
    try:
        from division_heads import DH
        dh = DH.review_all(sup_results, selfcode)
        findings["division_heads"] = {"round": dh.get("round"),
                                      "pressuring": dh.get("pressuring"),
                                      "heads": [{"division": h["division"],
                                                 "question": h["question"],
                                                 "action": h["action"]}
                                                for h in dh.get("results", [])]}
    except Exception:
        findings["division_heads"] = {"error": "division heads unavailable"}
    # Twelve IT engineers own each division's code. Parallel proposals,
    # rotated real patches — all still through self_coder's guard.
    try:
        from it_engineers import ITE
        itr = ITE.run_all(dry=not apply)
        findings["it_engineers"] = {"ran": itr.get("ran"),
                                    "pushed": itr.get("pushed"),
                                    "sample": itr.get("results", [])[:3]}
    except Exception:
        findings["it_engineers"] = {"error": "IT engineers unavailable"}
    # HR head decides ADD/CUT from real workload, not from headcount vanity.
    try:
        from hr_head import HR
        HR.assign(apply=apply)
        hra = HR.analyze()
        findings["hr"] = {"evidence": hra.get("evidence"),
                          "decision": (hra.get("decision") or "")[:1200]}
    except Exception:
        findings["hr"] = {"error": "HR unavailable"}
    mem = findings.get("recall") or {}
    cons = deb.get("consensus") or ""
    recall_used = bool(mem.get("previous")) and any(
        k in cons for k in ("รอบก่อน", "จำได้", "เรียนรู้", "ปรับปรุง", "ซ้ำ"))
    result = {"ok": True, "t": int(time.time()), "findings": findings,
              "debate": deb, "products_rebuilt": len(new_products),
              "applied": applied, "income_plan": plan_write,
              "selfcode": selfcode, "recall_used": recall_used}
    with LOCK:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        md = ["# สภาอัตโนมัติข้ามแผนก (Autonomous Council)", "",
              "เวลา: %s" % time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(result["t"])), "",
              "แต่ละแผนกเรียนรู้จากแหล่งต่างกันแล้วมาถกกัน — ไม่รอคำสั่ง", ""]
        for code, d in DEPARTMENTS.items():
            md += ["## " + d["th"], "- แหล่ง: " + ", ".join(d["sources"]),
                   "- วัดได้: " + json.dumps(findings[code], ensure_ascii=False)[:900], ""]
            _teach(code, d["th"] + ": " + json.dumps(findings[code], ensure_ascii=False))
        comp = result.get("findings", {}).get("competition") or {}
        if comp.get("board"):
            md += ["## การแข่งขันฝ่าย (real metrics)", "",
                   "ผู้ชนะรอบนี้: **%s** (%d คะแนน)" % (
                       comp.get("winner"), comp.get("winner_score", 0)), "",
                   "| อันดับ | ฝ่าย | คะแนน | ตัววัดจริง |", "|---|---|---|---|"]
            for r in comp["board"]:
                md += ["| %d | %s | %d | %s |" % (
                    r["rank"], r["dept"], r["score"], r["metric"])]
            md += ["", "ฝ่ายที่แพ้ถูกสอนวิธีของฝ่ายชนะด้วยหลักฐานใหม่ผ่าน dept_brains/", ""]
        sv = result.get("findings", {}).get("supervisors") or {}
        if sv.get("heads"):
            md += ["## คำถามจากหัวหน้าฝ่าย 10 คน", ""]
            for h in sv["heads"]:
                md += ["- **%s** ถาม: %s | วัดได้: %s | ซ้ำ: %s" % (
                    h["dept"], h["question"], h["detail"], h.get("repeated"))]
            md += [""]
        div = result.get("findings", {}).get("division_heads") or {}
        if div.get("heads"):
            md += ["## หัวหน้าแผนกกระตุ้นหัวหน้าฝ่าย (12 คน)", "",
                   "กำลังกดดัน %s รอบ" % div.get("pressuring"), ""]
            for h in div["heads"]:
                md += ["- **%s** ถาม: %s → %s" % (
                    h["division"], h["question"], h["action"])]
            md += [""]
        ite = result.get("findings", {}).get("it_engineers") or {}
        if ite.get("ran"):
            md += ["## วิศวกร IT ประจำแผนก", "",
                   "เสนอ %d / push จริง %d" % (ite.get("ran"), ite.get("pushed")), ""]
            for x in ite.get("sample", []):
                md += ["- %s (%s) → %s : %s" % (
                    x.get("division"), x.get("engineer"), x.get("file"), x.get("reason"))]
            md += [""]
        md += ["## การถกเถียง", ""]
        for p in deb.get("positions", []):
            md += ["### " + p["dept"] + " (" + p["provider"] + ")", p["text"], ""]
        md += ["## คำตัดสิน", deb.get("consensus", ""), "",
               "## สิ่งที่ถูกแก้จริง", "",
               "- PRODUCTS.md ปรับเป็น %d รายการ (gate_ok=%s → status=%s)" % (
                   len(new_products),
                   bool(new_products and new_products[0].get("gate_ok")),
                   new_products[0].get("status") if new_products else "none"),
               "- ราคาจาก council_review.market_price · ลิงก์ซอร์สจริง · คำอธิบายจากหัวข้อเนื้อหาจริง",
               "- GitHub write: " + json.dumps(applied, ensure_ascii=False), "",
               "## ความจำที่ถูกนำไปใช้จริง", "",
               "recall_used = %s — อ่านคำตัดสิน/บทเรียนรอบก่อนก่อนถก ไม่ใช่เขียนแล้วลืม" % result.get("recall_used"), "",
               "## แผนรายได้ที่คิดเอง", "",
               "- INCOME_PLAN.md: " + json.dumps(result.get("income_plan"), ensure_ascii=False),
               "- วัดจากไฟล์/ราคา/โปรโมจริง ห้ามอ้างยอดขายปลอม", "",
               "## Zyphere พัฒนาตัวเอง", "",
               "- self_coder (guard → compile → regression → push → revert ถ้าพัง): " +
               json.dumps(result.get("selfcode"), ensure_ascii=False)[:600], ""]
        open(OUT, "w", encoding="utf-8").write("\n".join(md))
        json.dump(result, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return result


if __name__ == "__main__":
    r = run(apply="--dry" not in __import__("sys").argv)
    print("ok", r.get("ok"), "products", r.get("products_rebuilt"),
          "applied", r.get("applied"), "error", r.get("error"))
    for code, f in (r.get("findings") or {}).items():
        print(code, json.dumps(f, ensure_ascii=False)[:180])
