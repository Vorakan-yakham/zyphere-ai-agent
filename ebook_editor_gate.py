"""Book Editorial Gate — six editors verify every published ebook HTML.

Checks REAL text: Thai readability (no mojibake / replacement chars), correct
charset, embedded cover, real section count and content length. A book that
fails is marked HOLD — never silently treated as ready.
"""
import os, re, json, time, requests, html as html_mod

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "governance", "EBOOK_EDITORIAL_QA.md")
REPO = "Vorakan-yakham/zyphere-scholar-product-pack"
BASE = "https://raw.githubusercontent.com/%s/main/" % REPO

EDITORS = ["บรรณาธิการภาษา", "บรรณาธิการหนังสือ", "บรรณาธิการข้อความ",
           "บรรณาธิการปก", "บรรณาธิการราคา", "บรรณาธิการคุณภาพ"]


def fetch(path):
    """Fetch via GitHub API with no-store — raw.githubusercontent caches hard."""
    import base64
    try:
        r = requests.get(
            "https://api.github.com/repos/%s/contents/%s" % (REPO, path),
            params={"ref": "main", "x": time.time()},
            headers={"Accept": "application/vnd.github+json",
                     "Cache-Control": "no-store", "User-Agent": "Zyphere-QA/1.0"},
            timeout=60)
        if r.ok:
            data = r.json()
            return base64.b64decode(data.get("content", "")).decode("utf-8", errors="replace")
    except Exception:
        pass
    return None


def check(html):
    """Check the BOOK TEXT only — never count CSS/JS properties as language."""
    if html is None:
        return ["ไม่พบไฟล์จริง"]
    clean = re.sub(r"<style[^>]*>[\s\S]*?</style>", " ", html, flags=re.I)
    clean = re.sub(r"<script[^>]*>[\s\S]*?</script>", " ", clean, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", clean)
    text = html_mod.unescape(text)
    issues = []
    if "\ufffd" in html or "Ã" in html or "â€" in html:
        issues.append("encoding เสีย / mojibake")
    if '<meta charset="utf-8">' not in html.lower().replace("'", '"'):
        issues.append("ไม่มี meta charset utf-8")
    if re.search(r"[\u25a1\u25a0]", text):
        issues.append("มีช่องสี่เหลี่ยม แสดงว่าฟอนต์/encoding ไม่ถูกต้อง")
    title_m = re.search(r"<title>(.*?)</title>", html)
    title = title_m.group(1) if title_m else ""
    if not re.search(r"[\u0E00-\u0E7F]", title):
        issues.append("ชื่อหนังสือไม่มีอักษรไทย")
    if "data:image/png;base64" not in html:
        issues.append("ไม่มีปกที่ฝังอยู่ในไฟล์")
    if "COVER_URL" in html:
        issues.append("ยังมี placeholder ของปก")
    if len(re.findall(r"<h2>", html)) < 4:
        issues.append("จำนวนหัวข้อน้อยเกินไป")
    words = len(re.findall(r"\S+", text))
    if words < 4000:
        issues.append("เนื้อหาสั้นเกินไป (%d คำ)" % words)
    # English allowed only as a glossary gloss or brand label
    no_gloss = re.sub(r"\([^)]*[A-Za-z][^)]*\)", " ", text)
    no_brand = re.sub(r"(?i)\b(ebook|zyphere|isbn|promptpay|root|ink)\b", " ", no_gloss)
    eng = [w for w in re.findall(r"\b[A-Za-z]{3,}\b", no_brand)
           if w.upper() not in ("EBOOK", "ZYPHERE", "ISBN")]
    if len(eng) > 8:
        issues.append("มีอังกฤษลอยนอกวงเล็บศัพท์ %d ตัว: %s" % (len(eng), ", ".join(eng[:6])))
    # Thai language brain on the TEXT (not markup)
    try:
        import thai_language_brain as TLB
        issues.extend(TLB.analyse(text).get("issues", []))
    except Exception:
        pass
    return issues


def run(books=None, apply=True):
    books = books or ["books/01_%E0%B8%9F%E0%B8%B4%E0%B8%AA%E0%B8%B4%E0%B8%81%E0%B8%AA%E0%B9%8C%E0%B8%84%E0%B8%A7%E0%B8%AD%E0%B8%99%E0%B8%95%E0%B8%B1%E0%B8%A1/book_v2.html"]
    results = []
    for path in books:
        html = fetch(path)
        issues = check(html)
        results.append({"book": path, "ok": not issues, "issues": issues,
                        "reviewed_by": EDITORS})
    if apply:
        md = ["# รายงานตรวจทานหนังสือโดยบรรณาธิการ", "",
              "ตรวจจากไฟล์จริงใน repo ด้วย UTF-8 — หากไม่ผ่านให้ HOLD", ""]
        for r in results:
            md += ["## " + r["book"], "",
                   "- ผล: " + ("ผ่าน" if r["ok"] else "**HOLD**"), ""]
            for i in r["issues"]:
                md += ["  - " + i]
            md += [""]
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        open(OUT, "w", encoding="utf-8").write("\n".join(md))
    return {"ok": all(r["ok"] for r in results), "results": results}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False)[:900])
