"""Zyphere Identity - a persistent AI persona that keeps learning.
Identity + self-learning loop: absorbs facts, skills and gaps from every interaction.
"""
import json, os, time, secrets, threading, re
from collections import Counter

class Identity:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.data = {}
        self._load()

    def _load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        except Exception:
            self.data = {
                "id": "ZY-" + secrets.token_hex(4).upper(),
                "name": "Zyphere", "thai_name": "ไซเฟอร์",
                "role": "AI ส่วนตัวที่เรียนรู้เอง จำได้ และช่วยสร้างสรรค์",
                "created": int(time.time()),
                "owner": "vorayakham@gmail.com",
                "capabilities": ["สนทนา", "ความจำถาวร", "เรียนรู้เอง", "ค้นเว็บ",
                                 "อ่านไฟล์", "สร้างวิดีโอ", "เสียงพูด", "13 ภาษา",
                                 "เขียนโค้ด", "วิเคราะห์"],
                "skills": {},          # skill -> level (auto grows)
                "topics": {},          # topic -> count learned
                "lessons": [],         # learned lessons
                "stats": {"interactions": 0, "learned": 0, "gaps": 0},
            }
            self.save()

    def save(self):
        with self.lock:
            try:
                with open(self.path, "w", encoding="utf-8") as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

    # ---------- learning loop ----------
    KEY_SKILLS = {
        "โค้ด": ("โค้ด|code|python|javascript|function|debug", "เขียนโค้ด"),
        "แปล": ("แปล|translate|ภาษา", "ภาษา"),
        "วิเคราะห์": ("วิเคราะห์|analyze|เปรียบเทียบ|why|เพราะ", "วิเคราะห์"),
        "สร้าง": ("สร้าง|เขียน|make|create|วาด|เพลง|นิทาน", "สร้างสรรค์"),
        "ค้นหา": ("ค้น|search|หา|what|who|where", "ค้นคว้า"),
        "เสียง": ("เสียง|พูด|ฟัง|audio|voice", "เสียง"),
        "วิดีโอ": ("วิดีโอ|คลิป|video", "วิดีโอ"),
    }

    def learn(self, text, source="interaction"):
        """Continuously learn from any text: grow skills, topics and lessons."""
        t = str(text or "").strip()
        if not t:
            return {}
        with self.lock:
            self.data.setdefault("stats", {})["interactions"] = self.data["stats"].get("interactions", 0) + 1
            grew = {}
            for name, (pat, skill) in self.KEY_SKILLS.items():
                if re.search(pat, t, re.I):
                    self.data.setdefault("skills", {})[skill] = round(
                        self.data["skills"].get(skill, 0.1) + 0.1, 2)
                    grew[skill] = self.data["skills"][skill]
            for w in re.findall(r"[\u0E00-\u0E7FA-Za-z0-9]{3,}", t.lower()):
                if len(w) > 2:
                    self.data.setdefault("topics", {})[w] = self.data["topics"].get(w, 0) + 1
                    if self.data["topics"][w] in (3, 10, 25):
                        lesson = "เรียนรู้คำว่า '" + w + "' จากการใช้งานจริง"
                        if lesson not in self.data.setdefault("lessons", []):
                            self.data["lessons"].append(lesson)
                            self.data["stats"]["learned"] = self.data["stats"].get("learned", 0) + 1
            self.data["last_active"] = int(time.time())
            self.save()
            return grew

    def touch(self, kind="interaction"):
        with self.lock:
            m = {"interaction": "interactions", "learned": "learned", "gap": "gaps"}
            k = m.get(kind)
            if k:
                self.data.setdefault("stats", {})[k] = self.data["stats"].get(k, 0) + 1
            self.data["last_active"] = int(time.time())
            self.save()
        return self.data

    def public(self):
        with self.lock:
            d = dict(self.data)
            d["top_skills"] = sorted(self.data.get("skills", {}).items(), key=lambda x: -x[1])[:6]
            d["top_topics"] = Counter(self.data.get("topics", {})).most_common(8)
            return d
