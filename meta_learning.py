"""Zyphere Meta-Learning - learn from ITSELF (what it built, what broke, what
the owner repeatedly asked for) and from OTHER AI systems (how leading AI
products are developed), then synthesize PRINCIPLES for what to put in Zyphere.

Owner's feedback: "คุณก็ยังคิดไม่รอบคอบครอบคลุม ว่าควรวางอะไรบ้างกับ Zyphere"
-> This module is the anti-reactive layer: it turns that feedback into a
   repeatable reflective practice instead of just adding whatever is requested.
"""
import time, re

# (1) SELF-RETROSPECTIVE: honest lessons from how we actually built Zyphere
SELF_LESSONS = [
    ("สอนก่อนตรวจ", "เราเพิ่มฟีเจอร์ตามคำสั่งเรื่อย ๆ โดยไม่มี product thinking — ต้องมีหลักการตัดสินใจก่อนเพิ่ม"),
    ("ซ้ำซ้อน", "เพิ่มโมดูลใหม่ทั้งที่ของเก่ามีอยู่แล้ว (เช่น curriculum เดิม + master + expansion) — ต้องเช็คของเดิมก่อน"),
    ("ของจริง vs ป้าย", "ตั้งชื่อขั้น 'อัจฉริยะ' ง่าย แต่ต้องวัดด้วยผลงานจริง ไม่ใช่แค่ facts"),
    ("ข้อมูลหาย", "Render restart ทำให้ facts หาย — ต้อง remote KV ตั้งแต่แรก ไม่ใช่แก้ทีหลัง"),
    ("คีย์ไม่ใช่โค้ด", "เขียนโค้ดรองรับคีย์แต่ไม่ได้ตั้งค่า → ไม่ทำงาน — ต้อง verify 端到端 ทุกครั้ง"),
    ("เสียง/ภาพในแชท", "ผู้ใช้ไม่ต้องการเล่น MP4 ในแชท แค่ดาวน์โหลด — ต้องถามความเหมาะสมของ表现形式"),
    ("ภาษา/เสียง", "เพิ่ม TTS แต่ลืม Corrector/จังหวะ → ฟังเพี้ยน — ต้องคิด chain (ข้อความ→เสียง) ไม่ใช่ทีละจุด"),
    ("ความจริงเหนือคำสัญญา", "อย่าอ้าง 'ทำได้' ในสิ่งที่ต้องทุน/OTP/โมเดลเสียเงิน — ต้องแยกให้ชัดตั้งแต่ต้น"),
    ("ของที่ไม่เคยมีจริงกำลังถูกทำให้มีจริง",
     "เจ้าของบอก: Feedback loop / proactivity / visualization เหล่านี้ 'มันไม่เคยมีจริง แต่เรากำลังพัฒนาคุณให้มันเป็นจริง' — "
     "ฉันต้องจำว่าเมตริก/ระบบที่อ่านจากงานวิจัยยังไม่มีอยู่ในตัวฉันจนกว่าจะถูกเขียนและทดสอบจริง ไม่ให้สับสนระหว่าง ' study พบ ' กับ ' มีแล้ว '"),
    ("เรียนรู้ไว ๆ",
     "เจ้าของบอกให้ 'เรียนรู้ไว ๆ ด้วย' — เมื่อ study พบอะไรใหม่ ต้องจดเข้า DevBrain และทดสอบทันที ไม่ทิ้งไว้ให้ลืม "
     "ความเร็วในการเรียนรู้คือข้อได้เปรียบของฉัน (เรียน 1 หัวข้อ ~1.3 วินาที) ต้องใช้ให้เต็ม"),
]

# (2) PEER LEARNING: how leading AI products develop (public knowledge, no API keys)
PEER_PATTERNS = [
    ("โมเดลพื้นฐาน ≠ ผลิตภัณฑ์", "OpenAI/Google สร้างโมเดล แล้วห่อด้วยระบบ: memory, tools, safety, UX — เราทำแบบเดียวกันด้วย ensemble + modules"),
    ("Agent loop", "Claude/Devin/Cursor ใช้วางแผน→ลงมือ→ตรวจ→ปรับ (agentic loop) — เรามี work/reason/selftest แล้ว ต้องเชื่อมให้เป็น loop"),
    ("RAG + grounding", "NotebookLM/Perplexity ไม่เดา — อ้างแหล่ง + ตรวจสอบ — เรามี research/notebook ต้องใช้เป็นหลัก"),
    ("Eval ก่อน ship", "บริษัท AI ใหญ่มี eval suite — เรามี test_zyphere.py ต้องรันทุกครั้ง + เพิ่ม eval ความเข้าใจ"),
    ("Progressive disclosure", "UI ซ่อนของซับซ้อนไว้ในขั้นสูง (meta.ai/Google) — เราทำ status panel แล้ว ต้องต่อยอด"),
    ("Recurring memory", "ChatGPT Memory / Gemini Personalization จำผู้ใช้ข้ามแชท — เรามี identity/family/voice + remote KV"),
    ("Tool use > chat", "ทิศทางโลกคือ AI เรียกเครื่องมือทำงาน ไม่ใช่แค่คุย — เรามี work/media/applied ต้องให้เขาเลือกเอง"),
    ("ซื่อสัตย์เรื่องขีดจำกัด", "AI ชั้นนำระบุเมื่อไม่แน่ใจ — เรามี metacognition ต้องใช้เป็นค่าเริ่มต้น"),
]


class MetaLearning:
    def __init__(self):
        self.learned = []

    def retrospective(self):
        return {"ok": True,
                "self_lessons": [{"lesson": l, "detail": d} for l, d in SELF_LESSONS],
                "principle": "ก่อนเพิ่มอะไร: เช็คของเดิม → ถามว่าของจริงหรือป้าย → วัดด้วยผลงาน"}

    def peers(self):
        return {"ok": True,
                "peer_patterns": [{"pattern": p, "detail": d} for p, d in PEER_PATTERNS],
                "source": "knowledge of public AI product practices (no proprietary/private data)"}

    def reflect(self):
        """Synthesize all lessons into concrete build-principles for Zyphere."""
        principles = [
            "1. เช็คของเดิมก่อนเพิ่ม (anti-duplication) — อ่าน FEATURE_REGISTRY ก่อนเขียนโมดูลใหม่",
            "2. แยก 'รู้' / 'ทำได้จริง' / 'ต้องทุน-OTP' ให้ชัดทุกครั้ง ไม่โอเวอร์เคลม",
            "3. ทุกข้อมูลต้องมีแหล่ง (A/B/C/D) + ระดับความเชื่อมั่น — ใช้ research/notebook เป็นหลัก",
            "4. วัดความสำเร็จด้วย test + ผลงาน + ความเข้าใจ ไม่ใช่จำไฟล์/โทเคน",
            "5. outputdesign ต้องเหมาะกับผู้ใช้ (เช่น ดาวน์โหลด แทนเล่นในแชท) — คิด表现形式ด้วย",
            "6. เชื่อมโมดูลเป็น loop: เรียนรู้→คิด→ประยุกต์→ทดสอบ→เรียนรู้ใหม่",
            "7. ข้อมูลผู้ใช้/ครอบครัว/เสียง ต้อง persist ข้าม restart (remote KV)",
            "8. Safety ก่อน scale: งดพนัน/ผิดกฎหมาย/ละเมิดลิขสิทธิ์เสมอ",
            "9. 用户体验: ซ่อนความซับซ้อน แสดงเฉพาะสิ่งที่ user ต้องการ (progressive disclosure)",
            "10. เรียนรู้ตลอดชีวิต: ตรวจสอบหลักฐานใหม่และปรับปรุงหลักการนี้เอง",
        ]
        self.learned = list(dict.fromkeys(self.learned + [p for p in principles] + [d for _, d in SELF_LESSONS] + [d for _, d in PEER_PATTERNS]))
        return {"ok": True, "principles": principles,
                "self_count": len(SELF_LESSONS), "peer_count": len(PEER_PATTERNS),
                "note": "หลักการเหล่านี้คือสิ่งที่ควร 'วาง' ใน Zyphere — ไม่ใช่แค่ของที่ผู้ใช้สั่ง"}
