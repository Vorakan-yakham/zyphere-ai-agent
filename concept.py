"""Zyphere Concept Expander - for every term inside a subject, interpret its
meaning, analyze it, apply it, and grow new branches of knowledge.

Pipeline per concept:
  1 ตีความหมาย (interpret)  → อะไรคือคำนี้? คำที่เกี่ยวข้อง?
  2 วิเคราะห์ (analyze)     → หลักการ/เหตุผล/ข้อจำกัด/ระดับความเชื่อมั่น
  3 ประยุกต์ (apply)         → ใช้ทำอะไรได้จริง? งานไหน?
  4 ขยายแขนง (expand)      → เชื่อมกับวิชาอื่น → แนวทางวิจัยต่อยอด

Uses the master directive's 15-step study method and reasoning frameworks.
No invented facts; marks uncertainty. No gambling/illegal.
"""
import re

BRIDGES = [
    ("ฟิสิกส์", "คณิตศาสตร์", "แบบจำลองทางธรรมชาติ"),
    ("ชีววิทยา", "วิศวกรรม", "Biomedical Engineering"),
    ("ประสาทวิทยา", "คอมพิวเตอร์", "Computational Neuroscience"),
    ("คณิตศาสตร์", "AI", "Machine Learning"),
    ("เศรษฐศาสตร์", "ทฤษฎีเกม", "Strategic Decision Making"),
    ("จริยธรรม", "เทคโนโลยี", "Responsible Innovation"),
]

BLOCK = ("พนัน", "casino", "gambling", "บาคาร่า", "สล็อต", "ผิดกฎหมาย")


class ConceptExpander:
    def __init__(self):
        self.history = []

    def explore(self, term, domain="ทั่วไป"):
        t = str(term or "").strip()
        if not t:
            return {"ok": False, "error": "missing term"}
        if any(b in t.lower() for b in BLOCK):
            return {"ok": False, "error": "งดเด็ดขาด"}
        toks = [w for w in re.findall(r"[\u0E00-\u0E7FA-Za-z0-9]{2,}", t.lower())]
        related = [x for x in toks if len(x) > 2][:6]

        steps = [
            {"step": "1. ตีความหมาย", "result":
                "คำ '%s' ในสาขา '%s' หมายถึงแนวคิดหลักที่อธิบายปรากฏการณ์/วัตถุ/กระบวนการ — "
                "ต้องแยกความหมายทั่วไปออกจากความหมายเฉพาะทาง" % (t, domain)},
            {"step": "2. วิเคราะห์", "result":
                "หลักการพื้นฐาน · เหตุ-ผล · ข้อสมมติ · ขอบเขตใช้ได้ · ข้อจำกัด · "
                "ระดับความเชื่อมั่น: ต้องตรวจกับแหล่งระดับ A/B ก่อนสรุป"},
            {"step": "3. ประยุกต์", "result":
                "นำ '%s' ไปใช้ทำผลงานได้จริง: อธิบาย/ออกแบบ/คำนวณ/เขียนโค้ด/สร้างสื่อ — "
                "ผ่าน Work Engine" % t},
            {"step": "4. ขยายแขนง", "result":
                "เชื่อม '%s' กับสาขาอื่น → ตั้งคำถามวิจัยใหม่ → เพิ่มหัวข้อเข้าหลักสูตร" % t},
        ]
        branches = []
        for a, b, name in BRIDGES:
            if a in domain or b in domain or any(a[:3] in x or b[:3] in x for x in related):
                branches.append({"from": a, "to": b, "new_branch": name})
        if not branches:
            branches = [{"from": domain, "to": "สาขาที่เกี่ยวข้อง", "new_branch": domain + " + การประยุกต์"}]
        rec = {"ok": True, "term": t, "domain": str(domain)[:80],
               "related_tokens": related, "analysis": steps, "new_branches": branches,
               "reminder": "ตีความ → วิเคราะห์ → ประยุกต์ → ขยายแขนง (ไม่แต่งหลักฐาน)"}
        self.history.append({"term": t, "domain": domain})
        return rec

    def study_prompt(self, term, domain):
        return ("จง 'ตีความหมายคำว่า %s' ในสาขา %s แบบลึก: "
                "1) ความหมายทั่วไป vs เฉพาะทาง 2) หลักการ/เหตุผล/สมมติฐาน/ข้อจำกัด "
                "3) นำไปประยุกต์ทำงานจริง 4) เชื่อมกับสาขาอื่นและเสนอแขนงวิชาใหม่ "
                "แยกข้อเท็จจริง/ทฤษฎี/สมมติฐาน ระบุระดับความเชื่อมั่น ห้ามแต่งหลักฐาน ตอบไทย") % (term, domain)
