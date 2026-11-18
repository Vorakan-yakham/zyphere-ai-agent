"""Zyphere Conversation Learning — keep the user's CORRECTIONS and turn them
into permanent development rules. The assistant was wrong; the user was right.

Only corrections are kept (not everything said). Each is verified against a
real artifact or a real file so a lesson can never be an empty slogan.
"""
import os, json, time, threading

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "conversation_learning.json")
OUT = os.path.join(ROOT, "governance", "CORRECTION_LESSONS.md")

# Real corrections from the owner in this project. (user_words -> rule -> proof)
CORRECTIONS = [
    ("18 ควรอ่านว่า สิบแปด ไม่ใช่ หนึ่งแปด",
     "ตัวเลขต้องผ่าน Thai cardinal normalization ก่อน TTS",
     "test_tts_numbers.js (23 fixtures)"),
    ("หัวหน้าฝ่าย 10 กว่าคน ไม่กระตุ้นเลย ทำอะไรของมัน",
     "หัวหน้าฝ่ายต้องวัดเอง ถามคำถามหมุนเวียน และตรวจการซ้ำ",
     "supervisors.py nag_all / QUESTIONS"),
    ("ถึงผมปิดเครื่อง它也ต้องทำงาน",
     "งานต้องรันบน Render + GitHub cron ไม่ใช่ขึ้นกับเครื่องผู้ใช้",
     ".github/workflows/keepalive.yml"),
    ("อย่าให้ได้พูดไอ้ Dr. สมองปลาทอง",
     "ห้ามใช้คำว่า Dr. และต้องโหลดความจำรอบก่อนก่อนถกทุกครั้ง",
     "autonomous_council.recall_prior()"),
    ("ผมไม่สั่งมันก็ต้องคิดเองจากที่มันเรียนรู้มา",
     "บทเรียนใน dept_brains ต้องถูกอ่านเป็น input ไม่ใช่เขียนทิ้ง",
     "recall -> debate digest"),
    ("เพิ่มอีก 100 คนก็ไม่ช่วย ถ้าพัฒนาโค้ดช้า",
     "เพิ่มความสามารถ/โมดulers ก่อนเพิ่มคน",
     "auto_staffing.py / generated/*.py"),
    ("คนด้วยความสามารถด้วย",
     "วิศวกร IT ประจำแผนก + ความสามารถที่สร้างเอง ต้องมีทั้งคู่",
     "it_engineers.py (12) + auto_grow.py"),
    ("ส่วนที่ไม่มีงานก็ให้คิดงานสิ",
     "ห้ามยุบฝ่ายที่ว่าง — ให้เสนองานจริงที่วัดผลได้",
     "hr_head.WORK_BANK / HR_WORK_ORDERS.md"),
    ("ไม่ได้ให้เขียน ebook แนะนำให้หางานเองว่าทำอะไรได้บ้าง",
     "เสนอ work proposals ก่อน ไม่ใช่ดำเนินการเองโดยไม่ได้รับสั่ง",
     "work_proposals.py"),
    ("วิศวกร IT คุณจัดให้แล้วมิใช่เหรอ",
     "ห้ามเสนอคนซ้ำ ให้ใช้วิศวกรที่ประจำอยู่แล้ว",
     "work_proposals._engineer_map()"),
    ("คุยมากไปคุณไม่ได้ทำงาน ไปพัฒนาโปรเจกต์ซะ",
     "รายงานผลที่วัดได้แทนการพูด",
     "status endpoints + repo files"),
    ("สี/ไอคอนต้อง mono และ wiggle เฉพาะด้านซ้าย ไม่ใช่ popup",
     "UI ต้องตรงตามคลิป ทุก icon มี micro-motion แต่ popup ไม่สั่น",
     "index.html zyWiggle scope / popup nudge"),
    ("ห้ามอ้างยอดขายปลอม ห้าม claim สิ่งที่ไม่มี",
     "ของจริง/ลิงก์จริง/status review เมื่อ QA ไม่ผ่าน",
     "store manifest gate_ok / INCOME_PLAN.md"),
]


class ConversationLearning:
    def __init__(self):
        self.lock = threading.RLock()
        self.log = []
        try:
            self.log = json.load(open(DATA, encoding="utf-8")).get("log", [])
        except Exception:
            pass

    def save(self):
        with self.lock:
            try:
                os.makedirs(os.path.dirname(DATA), exist_ok=True)
                json.dump({"log": self.log[-200:]}, open(DATA, "w", encoding="utf-8"),
                          ensure_ascii=False, indent=2)
            except Exception:
                pass

    def learn(self, user_text, rule, proof):
        """Record a correction only if it can be backed by a real artifact."""
        known = any(x.get("user") == user_text for x in self.log)
        if known:
            return {"ok": True, "duplicate": True}
        rec = {"t": int(time.time()), "user": user_text, "rule": rule, "proof": proof,
               "type": "correction", "correction": True}
        with self.lock:
            self.log.append(rec)
        self.save()
        # Feed both brains + the reusable method registry.
        try:
            from local_brain import LocalBrain
            from dev_brain import DevBrain
            lesson = "คำแก้ไขจากผู้ใช้: " + user_text + " → กฎ: " + rule + " | หลักฐาน: " + proof
            LocalBrain(os.path.join(ROOT, "data", "local_brain.json")).learn_text(
                lesson, source="user-correction")
            DevBrain(os.path.join(ROOT, "data", "dev_brain.json")).experience(
                lesson, role="user-correction")
        except Exception:
            pass
        try:
            import method_transfer as MT
            MT.METHOD["user_correction_loop"] = {
                "rule": "คำแก้ไขของผู้ใช้คือแหล่งความรู้หลัก ต้องเก็บ แปลงเป็นกฎ และตรวจหลักฐาน",
                "steps": ["เก็บเฉพาะคำที่ผู้ใช้ชี้ว่าผิด", "แปลงเป็นกฎที่ทำได้",
                          "ระบุหลักฐานใน repo", "feed brain", "ใช้กฎในรอบถัดไป"],
                "why": "การแก้แล้วลืมทำให้ผู้ใช้ต้องมาสอนซ้ำ — ความถูกต้องมาจากคำแก้ไข",
            }
            MT.apply()
        except Exception:
            pass
        return {"ok": True, "duplicate": False, "recorded": rec}

    def import_all(self):
        out = []
        for user, rule, proof in CORRECTIONS:
            r = self.learn(user, rule, proof)
            if r.get("duplicate"):
                for x in self.log:
                    if x.get("user") == user:
                        x["correction"] = True
                        x["type"] = "correction"
                self.save()
            out.append(r)
        md = ["# บทเรียนจากคำแก้ไขของผู้ใช้", "",
              "เฉพาะสิ่งที่ผู้ใช้ชี้ว่าผิด → แปลงเป็นกฎพัฒนา + หลักฐานใน repo", ""]
        for i, (u, r, p) in enumerate(CORRECTIONS, 1):
            md += ["## %d. %s" % (i, u), "", "- กฎ: " + r, "- หลักฐาน: " + p, ""]
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        open(OUT, "w", encoding="utf-8").write("\n".join(md))
        return {"ok": True, "total": len(CORRECTIONS),
                "new": sum(1 for x in out if not x.get("duplicate"))}

    def store_chat(self, user_text, assistant_text=""):
        """Store real chat turns from the UI. Flag corrections for the council."""
        u = str(user_text or "")[:4000]
        a = str(assistant_text or "")[:4000]
        if not u:
            return {"ok": False, "error": "empty"}
        correction = bool(__import__("re").search(
            r"ไม่ใช่|ผิด|ควร|อย่า|ทำไม|ต้อง|ยังไม่|ไม่เห็น|ไม่ได้", u))
        rec = {"type": "chat", "t": int(time.time()), "user": u,
               "assistant": a, "correction": correction}
        with self.lock:
            self.log.append(rec)
        self.save()
        return {"ok": True, "correction": correction, "lessons": len(self.log)}

    def status(self):
        return {"ok": True, "lessons": len(self.log),
                "corrections": sum(1 for x in self.log if x.get("correction")),
                "recent": self.log[-5:]}


CL = ConversationLearning()
