"""Zyphere Book Design System — based on real book-design principles.

Sources studied: Wikipedia "Book design" and "Graphic design" (CC BY-SA).
Applied structure:
  Front matter : half-title, title page, copyright, contents, introduction
  Body matter  : parts -> chapters -> sections, running head, folio, figures
  Back matter  : conclusion, appendix, glossary, colophon (typeface notes)
  Page         : A5, inner/outer margins, baseline grid, print space
  Typography   : serif body (readability), sans headings (hierarchy),
                 1.6-1.7 leading, 60-70 character measure
  Imagery      : real figure from Wikimedia with caption + attribution,
                 plus generated abstract motif when no image is available
Process ownership:
  author -> language editor -> graphic designer -> typesetter -> QA -> release
"""
import os, time, base64, subprocess, requests, hashlib

REPO = "Vorakan-yakham/zyphere-scholar-product-pack"
BASE = "https://api.github.com/repos/" + REPO + "/contents/"

STANDARD = """# มาตรฐานการออกแบบหนังสือ Zyphere

อ้างอิงหลักการจาก Book design / Graphic design (Wikipedia, CC BY-SA)

## กระบวนการ (ใครทำอะไร)
1. นักเขียนต้นฉบับ (Author) — โครงเรื่อง 1 แนวคิดต่อบท
2. บรรณาธิการภาษา (Language editor) — แก้คำ จังหวะ วรรคตอน
3. นักออกแบบกราฟิก (Graphic designer) — ปก motif ฟอนต์ สี พื้นที่ว่าง
4. ช่างจัดหน้า (Typesetter) — grid A5 margin baseline running head folio
5. QA — uniqueness ภาษา โครงสร้าง ภาพและเครดิต
6. เผยแพร่ได้เฉพาะเมื่อผ่าน QA

## โครงสร้างเล่ม
- ส่วนหน้า: กึ่ง-title, title page, ลิขสิทธิ์, สารบัญ, บทนำ
- เนื้อหา: ภาค → บท → หัวข้อย่อย มี running head และหมายเลขหน้า
- ส่วนท้าย: บทส่งท้าย, ภาคผนวก, อภิธานศัพท์, colophon (ระบุฟอนต์)

## หน้ากระดาษ
A5 · margin ใน 24 มม. · นอก 18 มม. · บน 20 มม. · ล่าง 18 มม.
print space ตามสัดส่วนคลาสสิก · baseline grid ทุก 22 px

## ตัวอักษร
เนื้อหา: Noto Serif Thai (อ่านนานไม่เมื่อย) · หัวข้อ: Noto Sans Thai (ชัดเจน)
ขนาดเนื้อหา 15px · leading 1.7 · ความยาวบรรทัด 60-70 ตัวอักษร
ห้ามใช้ font เดียวกับหัวข้อและเนื้อหา

## ภาพ
- ใช้ภาพจริงจาก Wikimedia Commons พร้อมคำอธิบายและลิงก์เครดิต
- ถ้าไม่มีภาพ ให้สร้าง abstract motif จากคณิตศาสตร์/เรขาคณิต
- ทุกภาพต้องมี caption และแหล่งที่มา (ตรวจสอบได้)

## ปก
typography-driven · negative space · motif สะท้อนเนื้อหา · ชื่อผู้เขียน · ISBN · barcode
ห้ามใช้ gradient ฉูดฉาดแบบโปสเตอร์
"""


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
    p = {"message": "Book design standard " + str(int(time.time())),
         "content": base64.b64encode(content.encode("utf-8")).decode(), "branch": "main"}
    if sha:
        p["sha"] = sha
    r = requests.put(BASE + path, headers=h, json=p, timeout=30)
    return r.ok, r.status_code


EN_TITLE = {
    "ฟิสิกส์ควอนตัม": "Quantum mechanics", "ฟิสิกส์คลาสสิก": "Classical physics",
    "ดาราศาสตร์-จักรวาล": "Astronomy", "คณิตศาสตร์บริสุทธิ์": "Mathematics",
    "ปัญญาประดิษฐ์": "Artificial intelligence", "จิตวิทยา": "Psychology",
    "การแพทย์คลินิก": "Medicine", "เศรษฐกิจมหภาค-การเงิน": "Economics",
    "การตลาด-ธุรกิจ": "Marketing", "กฎหมาย-สิทธิมนุษยชน": "Law",
    "จริยธรรม-ปรัชญา": "Philosophy", "ประวัติศาสตร์-อารยธรรม": "History",
    "ภาษาศาสตร์-การแปล": "Linguistics", "วรรณกรรม-การเขียน": "Literature",
    "การสอน-การศึกษา": "Education", "ดนตรี-เสียง": "Music",
    "เกษตร-อาหาร": "Agriculture", "ภูมิอากาศ-สิ่งแวดล้อม": "Climate change",
    "พลังงาน-นิวเคลียร์": "Nuclear power", "อวกาศ-การสำรวจ": "Space exploration",
}


def figure(faculty):
    """Real image + attribution from Wikimedia, or None."""
    title = EN_TITLE.get(faculty)
    if not title:
        return None
    try:
        r = requests.get("https://en.wikipedia.org/api/rest_v1/page/summary/" +
                         requests.utils.quote(title), timeout=15,
                         headers={"User-Agent": "ZyphereBook/1.0 (educational)"})
        if not r.ok:
            return None
        j = r.json()
        src = (j.get("thumbnail") or {}).get("source") or (j.get("originalimage") or {}).get("source")
        if not src:
            return None
        return {"url": src, "caption": str(j.get("description") or faculty)[:160],
                "source": j.get("content_urls", {}).get("desktop", {}).get("page", ""),
                "title": j.get("title", title)}
    except Exception:
        return None


def publish_standard():
    return put("BOOK_DESIGN_STANDARD.md", STANDARD)


if __name__ == "__main__":
    print("standard", publish_standard())
