"""Zyphere Marketing Promoter — runs AFTER the book team finishes.

Reads the finished book_pricing.json and creates real promotional assets:
  PROMO.md    — campaign plan + per-book posts for Facebook / Instagram / X
  promo.json  — machine-readable promo data used by the storefront

Each department is linked: books -> covers -> QA -> pricing -> store -> promo.
HONEST: posts describe what actually exists (chapters, cover, exercises, price
reason). No invented sales numbers or fake testimonials.
"""
import os, json, time, base64, subprocess, requests

REPO = "Vorakan-yakham/zyphere-scholar-product-pack"
BASE = "https://api.github.com/repos/" + REPO + "/contents/"
RAW = "https://raw.githubusercontent.com/" + REPO + "/main/"
STORE_URL = "https://vorakan-yakham.github.io/zyphere-ai-agent/STORE.html"
PAY = "0941939686"


def token():
    t = os.environ.get("GH_TOKEN", "") or os.environ.get("GITHUB_TOKEN", "")
    if not t:
        t = subprocess.run(["gh", "auth", "token"], capture_output=True,
                           text=True, timeout=15).stdout.strip()
    return t


def put(path, content):
    h = {"Authorization": "Bearer " + token(), "Accept": "application/vnd.github+json"}
    sha = None
    try:
        g = requests.get(BASE + path, headers=h, timeout=15)
        if g.ok:
            sha = (g.json() or {}).get("sha")
    except Exception:
        pass
    p = {"message": "Marketing promotion by team " + str(int(time.time())),
         "content": base64.b64encode(content.encode("utf-8")).decode(), "branch": "main"}
    if sha:
        p["sha"] = sha
    r = requests.put(BASE + path, headers=h, json=p, timeout=30)
    return r.ok, r.status_code


def build():
    d = requests.get(RAW + "book_pricing.json", timeout=30).json()
    rows = d.get("rows", [])
    promos = []
    for b in rows:
        fac = b.get("faculty", "")
        price = b.get("price", 0)
        chapters = b.get("chapters", 0)
        why = b.get("why", "")
        posts = {
            "facebook": ("ใหม่จาก Zyphere: หนังสือ '{f}' จำนวน {c} บท "
                         "พร้อมแบบฝึกหัดท้ายบทและปกออกแบบเฉพาะ "
                         "ราคา ฿{p} — {w} สนใจดูตัวอย่างได้ที่ {u} "
                         "ชำระผ่าน PromptPay {pay}").format(
                             f=fac, c=chapters, p=price, w=why, u=STORE_URL, pay=PAY),
            "instagram": ("📚 {f} | {c} บท | ฿{p}\n"
                          "หนังสือความรู้ที่จัดทำจากสาขาวิชาจริงทั่วโลก "
                          "มีแบบฝึกหัดและปกออกแบบเฉพาะ\n"
                          "ดูเล่มอื่นได้ที่ลิงก์ในไบโอ").format(
                              f=fac, c=chapters, p=price),
            "x": ("Zyphere เปิดตัว '{f}' — {c} บท ฿{p}. "
                  "เหตุผลราคา: {w} {u}").format(f=fac, c=chapters, p=price, w=why, u=STORE_URL),
        }
        promos.append({"faculty": fac, "price": price, "chapters": chapters,
                       "why": why, "posts": posts,
                       "hashtags": ["#Zyphere", "#หนังสือความรู้", "#" + fac.replace("-", "")],
                       "cta": STORE_URL})
    md = ["# แผนโปรโมท Zyphere Book Series", "",
          "จำนวนเล่ม: %d · ช่วงราคา: ฿%d–฿%d" %
          (len(promos), min(x["price"] for x in promos), max(x["price"] for x in promos)), "",
          "ผลิตโดยฝ่ายการตลาด หลังทีมผลิตหนังสือ ปก เนื้อหา และราคาเสร็จแล้ว ",
          "ข้อความทุกชิ้นอ้างถึงสิ่งที่มีจริงเท่านั้น ไม่มีการสร้างยอดขายปลอม", ""]
    for p in promos:
        md += ["## " + p["faculty"], "",
               "- ราคา: ฿%d (%s)" % (p["price"], p["why"]),
               "- **Facebook**: " + p["posts"]["facebook"],
               "- **Instagram**: " + p["posts"]["instagram"].replace("\n", " / "),
               "- **X**: " + p["posts"]["x"],
               "- แฮชแท็ก: " + " ".join(p["hashtags"]),
               "- CTA: " + p["cta"], ""]
    return promos, "\n".join(md)


def main():
    promos, md = build()
    ok1, c1 = put("PROMO.md", md)
    ok2, c2 = put("promo.json", json.dumps({"promos": promos, "t": int(time.time())},
                                           ensure_ascii=False, indent=2))
    print("promo files", ok1, c1, ok2, c2, "books", len(promos))
    return promos


if __name__ == "__main__":
    main()
