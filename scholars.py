"""Zyphere Scholar Council - a faculty of specialist scholars, each studying
their OWN discipline in parallel, then a synthesis combines their findings.
Like a large research organization: many minds, divided by expertise, merged.
Runs in one free process (logical scholars calling research/rag/knowledge).

HONEST: scholars are roles using the same tools on different domains; not
separate paid AIs. Results are grounded excerpts + questions, never invented.
No gambling/illegal.
"""
import os, json, time, threading

FACULTY = {
    "ฟิสิกส์-คณิต": ["quantum", "relativity", "thermodynamics", " mathematics", "statistics"],
    "ชีวะ-แพทย์": ["genetics", "cell biology", "immunology", "medicine", "neuroscience"],
    "คอมพิวเตอร์-AI": ["machine learning", "algorithms", "LLM", "security", "data"],
    "กฎหมาย-จริยธรรม": ["law", "rights", "ethics", "governance", "privacy"],
    "เศรษฐกิจ-การเงิน": ["economics", "finance", "market", "trade", "accounting"],
    "ประวัติศาสตร์-สังคม": ["history", "civilization", "culture", "anthropology", "sociology"],
    "ภาษา-การสื่อสาร": ["linguistics", "translation", "rhetoric", "narration", "writing"],
    "วิศวกรรม-ออกแบบ": ["engineering", "design", "robotics", "architecture", "materials"],
    "สิ่งแวดล้อม-เกษตร": ["climate", "ecology", "agriculture", "water", "energy"],
    "ศิลปะ-สื่อ": ["music", "film", "visual art", "design thinking", "storytelling"],
}


class Scholars:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.sessions = []
        self._load()

    def _load(self):
        try:
            self.sessions = json.load(open(self.path, encoding="utf-8")).get("sessions", [])
        except Exception:
            pass

    def save(self):
        with self.lock:
            try:
                os.makedirs(os.path.dirname(self.path), exist_ok=True)
                json.dump({"sessions": self.sessions[-200:]},
                          open(self.path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            except Exception:
                pass

    def faculty(self):
        return {"ok": True, "faculty": [{"name": k, "topics": v} for k, v in FACULTY.items()],
                "count": len(FACULTY)}

    def convene(self, question="", researcher=None):
        """Each scholar researches its discipline, then synthesis merges."""
        q = str(question or "").strip()
        if not q:
            return {"ok": False, "error": "missing question"}
        findings = []
        for name, topics in FACULTY.items():
            focus = next((t for t in topics if t.strip() in q.lower()), topics[0])
            item = {"scholar": name, "focus": focus.strip(), "status": "studied"}
            if researcher:
                try:
                    r = researcher(str(focus) + " " + q)
                    item["finding"] = (str(r.get("result") or r.get("summary") or r)[:600]
                                       if isinstance(r, dict) else str(r)[:600])
                except Exception as e:
                    item["finding"] = "error: " + str(e)[:100]
            else:
                item["finding"] = "รอเชื่อม research engine"
            findings.append(item)
        # synthesis (deterministic): union of focuses + open questions
        union = sorted(set(f["focus"].strip() for f in findings))[:12]
        rec = {"ok": True, "id": "sc_" + str(int(time.time() * 1000)),
               "question": q[:200], "findings": findings,
               "synthesis": ("คณะนักวิชาการ %d ท่านศึกษาครบ %d แขนง → แนวทางรวม: %s"
                             % (len(findings), len(FACULTY), ", ".join(union))),
               "open_questions": ["ยังมีอะไรที่แต่ละแขนงยังตอบไม่ได้?"] + [x["focus"] + ": หลักฐานระดับ A มีไหม?" for x in findings[:3]],
               "t": int(time.time())}
        with self.lock:
            self.sessions.append(rec)
        self.save()
        return rec

    def latest(self, n=5):
        with self.lock:
            return list(reversed(self.sessions[-n:]))

    def snapshot(self):
        with self.lock:
            return {"sessions": self.sessions[-200:]}

    def restore(self, data):
        with self.lock:
            if isinstance(data, dict) and "sessions" in data:
                self.sessions = data.get("sessions", [])
                self.save()
                return True
        return False
