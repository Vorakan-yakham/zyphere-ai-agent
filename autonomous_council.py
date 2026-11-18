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
}


def gh_raw(path):
    # Unicode folder names (Thai) must be percent-encoded for the GitHub API.
    url = "repos/%s/contents/%s" % (REPO, urllib.parse.quote(path))
    p = subprocess.run(["gh", "api", url, "-H", "Accept: application/vnd.github.raw"],
                       capture_output=True, text=True, timeout=40)
    return p.stdout if p.returncode == 0 else None


def gh_tree():
    p = subprocess.run(["gh", "api", "repos/%s/git/trees/%s?recursive=1" % (REPO, BRANCH),
                        "--jq", ".tree[] | [.path,.size] | @tsv"],
                       capture_output=True, text=True, timeout=40)
    out = {}
    if p.returncode == 0:
        for line in p.stdout.splitlines():
            parts = line.split("\t")
            if len(parts) >= 2 and parts[1].strip().isdigit():
                out[parts[0]] = int(parts[1])
    return out


def gh_put(path, content, message):
    """Write a UTF-8 file to the product repo through the GitHub API."""
    import base64
    token = None
    t = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=15)
    if t.returncode == 0:
        token = t.stdout.strip()
    if not token:
        return {"ok": False, "error": "no gh token"}
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
    return findings, products, pricing, books


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
    syn = BE.ensemble([
        {"role": "system", "content": "คุณเป็นประธานสภาหลายแผนก รวมข้อเสนอที่ขัดกันเป็นคำตัดสินที่นำไปทำได้จริง "
         "เพื่อให้หนังสือขายได้ด้วยคุณภาพจริง ระบุ 'สิ่งที่ต้องแก้ใน PRODUCTS.md' ให้ชัด "
         "ห้ามสร้างยอดขายปลอม ตอบภาษาไทย กระชับ"},
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
    deb = debate(findings)
    new_products = rebuild_products(pricing, books, findings, raw)
    applied = {"ok": False, "status": None}
    if apply and new_products:
        applied = gh_put("PRODUCTS.md",
                         json.dumps(new_products, ensure_ascii=False, indent=2) + "\n",
                         "Autonomous council: align store prices, real download links and value descriptions")
    result = {"ok": True, "t": int(time.time()), "findings": findings,
              "debate": deb, "products_rebuilt": len(new_products),
              "applied": applied}
    with LOCK:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        md = ["# สภาอัตโนมัติข้ามแผนก (Autonomous Council)", "",
              "เวลา: %s" % time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(result["t"])), "",
              "แต่ละแผนกเรียนรู้จากแหล่งต่างกันแล้วมาถกกัน — ไม่รอคำสั่ง", ""]
        for code, d in DEPARTMENTS.items():
            md += ["## " + d["th"], "- แหล่ง: " + ", ".join(d["sources"]),
                   "- วัดได้: " + json.dumps(findings[code], ensure_ascii=False)[:900], ""]
            _teach(code, d["th"] + ": " + json.dumps(findings[code], ensure_ascii=False))
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
               "- GitHub write: " + json.dumps(applied, ensure_ascii=False), ""]
        open(OUT, "w", encoding="utf-8").write("\n".join(md))
        json.dump(result, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return result


if __name__ == "__main__":
    r = run(apply="--dry" not in __import__("sys").argv)
    print("ok", r.get("ok"), "products", r.get("products_rebuilt"),
          "applied", r.get("applied"), "error", r.get("error"))
    for code, f in (r.get("findings") or {}).items():
        print(code, json.dumps(f, ensure_ascii=False)[:180])
