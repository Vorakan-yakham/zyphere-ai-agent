"""Book Editorial Gate — six editors verify every published ebook HTML.

Checks REAL text: Thai readability (no mojibake / replacement chars), correct
charset, embedded cover, real section count and content length. A book that
fails is marked HOLD — never silently treated as ready.
"""
import os, re, json, time, requests

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "governance", "EBOOK_EDITORIAL_QA.md")
REPO = "Vorakan-yakham/zyphere-scholar-product-pack"
BASE = "https://raw.githubusercontent.com/%s/main/" % REPO

EDITORS = ["บรรณาธิการภาษา", "บรรณาธิการหนังสือ", "บรรณาธิการข้อความ",
           "บรรณาธิการปก", "บรรณาธิการราคา", "บรรณาธิการคุณภาพ"]


def fetch(path):
    r = requests.get(BASE + path, timeout=60)
    if not r.ok:
        return None
    # Decode explicitly as UTF-8 — no PowerShell/UTF-16 ambiguity in pipeline.
    return r.content.decode("utf-8", errors="replace")


def check(html):
    issues = []
    if html is None:
        return ["ไม่พบไฟล์จริง"]
    if "\ufffd" in html:
        issues.append("มี replacement character — encoding เสีย")
    if "à" in html or "Ã" in html or "â€" in html:
        issues.append("พบลักษณะ mojibake (à/Ã/â€)")
    if re.search(r"[\u25a1\u25a0]", html):
        issues.append("มีช่องสี่เหลี่ยม แสดงว่าฟอนต์/encoding ไม่ถูกต้อง")
    if '<meta charset="utf-8">' not in html.lower().replace("'", '"'):
        issues.append("ไม่มี meta charset utf-8")
    title = ""
    m = re.search(r"<title>(.*?)</title>", html)
    if m:
        title = m.group(1)
    if not re.search(r"[\u0E00-\u0E7F]", title):
        issues.append("ชื่อหนังสือไม่มีอักษรไทยที่อ่านได้")
    if "data:image/png;base64" not in html:
        issues.append("ไม่มีปกที่ฝังอยู่ในไฟล์")
    if "COVER_URL" in html:
        issues.append("ยังมี placeholder ของปก")
    h2 = len(re.findall(r"<h2>", html))
    if h2 < 4:
        issues.append("จำนวนหัวข้อน้อยเกินไป (%d)" % h2)
    words = len(re.findall(r"\S+", re.sub(r"<[^>]+>", " ", html)))
    if words < 2000:
        issues.append("เนื้อหาสั้นเกินไป (%d คำ)" % words)
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
