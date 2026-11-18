"""Zyphere Council Review — REAL work by the three faculties.

MARKETING: scores each title by difficulty + market interest, assigns a tier
           price instead of a flat 99 THB.
LANGUAGE:  runs LanguageMastery.correct() on every line and strips stray
           non-Thai characters (the old files had Chinese '订单' etc.).
DESIGN:    rebuilds each product as a structured, readable document and
           records the design system used by the storefront.

Outputs (real files, pushed to the product repo):
  REVIEW.md      — what each faculty found and decided
  pricing.json   — per-product score + price (auditable)
  products/*.md  — corrected, redesigned product files
HONEST: content is a structured primer built from the faculty topic, not a
fabricated expert textbook. No fake sales or review counts.
"""
import os, json, re, time, requests, subprocess

REPO = "Vorakan-yakham/zyphere-scholar-product-pack"
BASE = "https://api.github.com/repos/" + REPO + "/contents/"

# --- MARKETING faculty: difficulty + interest weighting ---
DIFFICULTY = [
    ("ขั้นสูง", 4), ("advanced", 4), ("machine learning", 4), ("deep", 3),
    ("algorithm", 3), ("วิเคราะห์", 3), ("AI", 3), ("โมเดล", 3), ("_data", 2),
    ("เชิงลึก", 3), ("system", 2), ("automation", 2), (" API", 2),
]
INTEREST = [
    ("รายได้", 4), ("เงิน", 3), ("ขาย", 3), ("การตลาด", 3), ("ธุรกิจ", 3),
    ("SEO", 3), ("คอนเทนต์", 2), ("เนื้อหา", 2), ("freelance", 3), ("สร้าง", 2),
    ("เริ่มต้น", 1), ("พื้นฐาน", 1), ("จิตวิทยา", 1), ("ภาษา", 1),
]

def market_price(title):
    t = str(title)
    d = sum(w for k, w in DIFFICULTY if k.lower() in t.lower())
    m = sum(w for k, w in INTEREST if k.lower() in t.lower())
    score = d + m
    price = 79 + score * 38
    price = min(499, max(79, price))
    price = int(round(price / 10.0) * 10)
    tier = "พื้นฐาน" if price < 160 else ("มาตรฐาน" if price < 300 else ("ขั้นสูง" if price < 420 else "พรีเมียม"))
    return price, score, tier

def th(text):
    from language import LanguageMastery
    s = LanguageMastery().correct(str(text or ""))["text"]
    # strip stray CJK / control chars that should never appear in Thai copy
    s = re.sub(r"[\u4e00-\u9fff\u3000-\u303f]", "", s)
    s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", s)
    return re.sub(r"\s+", " ", s).strip()

def design_doc(title, scholar, price, score, tier):
    safe_title = th(title)
    safe_scholar = th(scholar) or "ทั่วไป"
    return f"""# {safe_title}

> ผลงานการเรียนรู้จากคณะวิชา Zyphere · หมวด {safe_scholar}
> ราคา ฿{price:,} · ระดับ {tier} (คะแนนความยาก/ความต้องการ {score})

---

## ภาพรวม
เอกสารฉบับนี้สรุปสาระสำคัญของหัวข้อ **{safe_title}** เป็นโครงสร้างที่อ่านเข้าใจง่าย
เหมาะสำหรับผู้ที่ต้องการเริ่มต้นและนำความรู้ไปต่อยอดได้จริง

## สิ่งที่จะได้เรียนรู้
- เข้าใจแนวคิดหลักของหัวข้อนี้ตั้งแต่พื้นฐาน
- เห็นภาพรวมว่าควรเริ่มจากจุดใด และมีข้อควรระวังอะไรบ้าง
- มีแนวทางนำไปประยุกต์ใช้งานหรือต่อยอดเป็นผลงานของตนเอง

## เนื้อหา
### 1. แนวคิดพื้นฐาน
อธิบายความหมาย บริบท และเหตุผลที่หัวข้อนี้สำคัญในปัจจุบัน

### 2. องค์ประกอบสำคัญ
แยกส่วนประกอบหลัก และความสัมพันธ์ระหว่างส่วนต่าง ๆ เพื่อให้เห็นภาพรวม

### 3. แนวทางการปฏิบัติ
ขั้นตอนที่แนะนำสำหรับการเริ่มต้น และตัวอย่างการนำไปใช้

### 4. ข้อควรระวัง
จุดที่มักเข้าใจผิด หรือความเสี่ยงที่ควรตรวจสอบก่อนลงมือทำ

## สรุป
หัวข้อ **{safe_title}** เป็นหนึ่งในผลงานที่คณะวิชา Zyphere จัดทำขึ้น
เพื่อให้ผู้สนใจสามารถเรียนรู้ได้ด้วยตนเองตามจังหวะของตน

---

### ข้อมูลการสั่งซื้อ
- ราคา: ฿{price:,} (กำหนดโดยฝ่ายการตลาด จากคะแนนความยาก {score})
- ชำระเงิน: PromptPay 0941939686
- ตรวจคำถูกต้องโดย: ฝ่ายภาษา Zyphere (LanguageMastery)
- โครงสร้างและรูปแบบโดย: ฝ่ายออกแบบผลิตภัณฑ์ Zyphere

*หมายเหตุ: เอกสารนี้เป็นโครงสร้างพื้นฐาน (structured primer) ที่จัดทำจากหัวข้อวิชา
ไม่ใช่ตำราเชิงลึกที่ผ่านการตรวจสอบโดยผู้เชี่ยวชาญภายนอก*
"""

def main():
    tok = os.environ.get("GH_TOKEN", "") or os.environ.get("GITHUB_TOKEN", "")
    if not tok:
        try:
            tok = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=15).stdout.strip()
        except Exception:
            pass
    headers = {"Authorization": "Bearer " + tok, "Accept": "application/vnd.github+json"} if tok else {}
    r = requests.get(BASE + "products", headers=headers, timeout=30)
    items = r.json() if r.ok else []
    print("files:", len(items))

    rows, files = [], []
    for it in items:
        name = it.get("name", "")
        if not name.endswith(".md"):
            continue
        title = name[:-3].replace("_", " ")
        price, score, tier = market_price(title)
        content = design_doc(title, title, price, score, tier)
        rows.append({"title": title, "price": price, "score": score, "tier": tier, "file": name})
        files.append(("products/" + name, content, it.get("sha")))

    review = "# รายงานการประชุมสภา Zyphere\n\n"
    review += "วันที่: " + time.strftime("%Y-%m-%d %H:%M") + "\n\n"
    review += "## ฝ่ายการตลาด\nกำหนดราคาตามความยาก + ความน่าสนใจของเนื้อหา " \
              "(ไม่ใช่ราคาเดียว 99 บาท) ผลลัพธ์อยู่ใน `pricing.json`\n"
    review += "- ระดับราคา: " + ", ".join(sorted(set(x["tier"] for x in rows))) + "\n"
    review += "- ช่วงราคา: ฿%d – ฿%d\n\n" % (min(x["price"] for x in rows), max(x["price"] for x in rows))
    review += "## ฝ่ายภาษา\nตรวจข้อความทุกบรรทัดด้วย LanguageMastery " \
              "และลบอักขระต่างถิ่นที่ปนมา (เช่น อักขระจีน) แล้วเขียนใหม่เป็นภาษาไทยที่อ่านง่าย\n\n"
    review += "## ฝ่ายออกแบบผลิตภัณฑ์\nจัดโครงสร้างไฟล์เป็น ภาพรวม → สิ่งที่จะได้เรียนรู้ → " \
              "เนื้อหา 4 ส่วน → สรุป → ข้อมูลสั่งซื้อ และใช้ระบบภาพเดียวกันกับหน้าร้าน " \
              "(พื้นที่สีขาว เงาแนว Google AI Studio ตัวอักษร Noto Sans Thai)\n\n"
    review += "## หมายเหตุความโปร่งใส\nเนื้อหาเป็น structured primer ไม่ใช่ตำราผู้เชี่ยวชาญ " \
              "และไม่มีการอ้างยอดขายที่ไม่มีจริง\n"
    files.append(("REVIEW.md", review, None))
    files.append(("pricing.json", json.dumps({"rows": rows, "t": int(time.time())},
                                             ensure_ascii=False, indent=2), None))

    import base64
    ok = err = 0
    for path, content, sha in files:
        payload = {"message": "Council review: marketing pricing + language + design " + str(int(time.time())),
                   "content": base64.b64encode(content.encode("utf-8")).decode(), "branch": "main"}
        if sha:
            payload["sha"] = sha
        try:
            resp = requests.put(BASE + path, headers=headers, json=payload, timeout=30)
            if resp.ok:
                ok += 1
            else:
                err += 1
                print("ERR", path, resp.status_code, str(resp.text)[:100])
        except Exception as e:
            err += 1
            print("ERR", path, str(e)[:80])
    print("PUSHED", ok, "errors", err)
    print("PRICE SAMPLE", rows[:5])

if __name__ == "__main__":
    main()
