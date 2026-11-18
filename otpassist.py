"""Zyphere OTP Assistant - the LEGAL, honest way to help with sign-ups.

We NEVER receive, read, store, or bypass OTP. The owner's phone/email gets the
code and the OWNER types it. This module only:
- records which platform is being signed up
- prepares the info to fill (owner's name/email/phone — owner supplies)
- tells the owner WHICH STEP needs OTP (so they know when to act)
- reminds/notifies the owner (in-app) and logs progress
- never auto-creates accounts, never asks for the code, never touches bank

Owner's rule: 'สิ่งผิดกฎหมาย งดเด็ดขาด' — respected here.
Ethics: no gambling/illegal platforms (refused). No fake claims.
"""
import os, json, time, threading

BLOCK = ("พนัน", "casino", "gambling", "บาคาร่า", "สล็อต", "ผิดกฎหมาย")

STEPS = ["เปิดเว็บ/แอป", "กรอกอีเมล", "กรอกชื่อ", "กรอกเบอร์", "กดส่ง OTP",
         "คุณพิมพ์ OTP จาก SMS ของคุณเอง", "ยืนยันตัวตน", "เสร็จ"]


class OTPAssistant:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.tasks = []
        self._load()

    def _load(self):
        try:
            self.tasks = json.load(open(self.path, encoding="utf-8")).get("tasks", [])
        except Exception:
            pass

    def save(self):
        with self.lock:
            try:
                os.makedirs(os.path.dirname(self.path), exist_ok=True)
                json.dump({"tasks": self.tasks[-500:]},
                          open(self.path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            except Exception:
                pass

    def prepare(self, platform="", owner_name="", owner_email="", owner_phone=""):
        """Prepare a sign-up task. No code is requested or stored."""
        p = str(platform or "").strip()
        if not p or any(b in p.lower() for b in BLOCK):
            return {"ok": False, "error": "งดแพลตฟอร์มพนัน/ผิดกฎหมาย หรือชื่อว่าง"}
        rec = {"ok": True, "id": "otp_" + str(int(time.time() * 1000)),
               "platform": p[:120],
               "prepared": {"name": str(owner_name or "")[:80],
                            "email": str(owner_email or "")[:120],
                            "phone": str(owner_phone or "")[:40]},
               "steps": STEPS, "otp_step": "คุณพิมพ์ OTP จาก SMS ของคุณเอง",
               "status": "ready_for_owner", "t": int(time.time()),
               "reminder": "ผมเตรียมข้อมูลให้แล้ว — เหลือแค่คุณกด OTP ในขั้นตอนที่ 6 ครับ",
               "never": ["ไม่รับรหัส OTP", "ไม่อ่าน SMS", "ไม่สร้างบัญชีแทน", "ไม่เข้าบัญชีธนาคาร"]}
        with self.lock:
            self.tasks.append(rec)
        self.save()
        return rec

    def mark(self, tid="", step="", note=""):
        """Owner reports progress; Zyphere just records it."""
        with self.lock:
            for t in self.tasks:
                if t["id"] == tid or (not tid and t["status"] == "ready_for_owner"):
                    t["status"] = step or "in_progress"
                    t["note"] = str(note or "")[:200]
                    t["updated"] = int(time.time())
                    break
        self.save()
        return {"ok": True, "status": step}

    def pending(self):
        with self.lock:
            return [t for t in reversed(self.tasks) if t.get("status") in ("ready_for_owner", "in_progress")]

    def stats(self):
        with self.lock:
            return {"tasks": len(self.tasks), "awaiting_owner": len(self.pending()),
                    "never_stores_otp": True}

    def snapshot(self):
        with self.lock:
            return {"tasks": self.tasks[-500:]}

    def restore(self, data):
        with self.lock:
            if isinstance(data, dict) and "tasks" in data:
                self.tasks = data.get("tasks", [])
                self.save()
                return True
        return False
