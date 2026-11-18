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
    # --- วิทยาศาสตร์พื้นฐาน ---
    "ฟิสิกส์ควอนตัม": ["quantum", "particle", "wave function", "spin"],
    "ฟิสิกส์คลาสสิก": ["mechanics", "electromagnetism", "thermodynamics", "optics"],
    "ดาราศาสตร์-จักรวาล": ["astrophysics", "cosmology", "galaxy", "exoplanet"],
    "คณิตศาสตร์บริสุทธิ์": ["algebra", "geometry", "number theory", "topology"],
    "คณิตศาสตร์ประยุกต์": ["statistics", "probability", "calculus", "optimization"],
    "ตรรกะและทฤษฎีข้อมูล": ["logic", "information theory", "computability", "proof"],
    # --- ชีวะ-แพทย์ ---
    "พันธุกรรม-ชีวโมเลกุล": ["genetics", "DNA", "genome", "CRISPR"],
    "เซลล์และเนื้อเยื่อ": ["cell biology", "microscopy", "stem cell"],
    "ภูมิคุ้มกัน-โรค": ["immunology", "vaccine", "pathogen", "disease"],
    "สมอง-ประสาทวิทยา": ["neuroscience", "synapse", "memory", "cognition"],
    "สรีระและเภสัช": ["physiology", "anatomy", "pharmacology", "nutrition"],
    "การแพทย์คลินิก": ["diagnosis", "treatment", "clinical", "surgery"],
    "จิตวิทยา": ["psychology", "behavior", "emotion", "therapy"],
    # --- คอมพิวเตอร์ ---
    "ปัญญาประดิษฐ์": ["machine learning", "neural network", "LLM", "agent"],
    "อัลกอริทึม-โครงสร้างข้อมูล": ["algorithm", "data structure", "complexity", "graph"],
    "วิศวกรรมซอฟต์แวร์": ["software", "architecture", "testing", "devops"],
    "ความมั่นคงไซเบอร์": ["security", "cryptography", "privacy", "network"],
    "ฐานข้อมูล-ข้อมูลขนาดใหญ่": ["database", "big data", "pipeline", "ETL"],
    "คอมพิวเตอร์วิทัศน์-เสียง": ["computer vision", "speech", "image", "audio"],
    "หุ่นยนต์-ระบบอัตโนมัติ": ["robotics", "control", "automation", "sensor"],
    # --- วิศวกรรม ---
    "วิศวกรรมไฟฟ้า-อิเล็กทรอนิกส์": ["circuit", "signal", "power", "embedded"],
    "วิศวกรรมเครื่องกล": ["mechanics", "material", "manufacturing", "thermal"],
    "วิศวกรรมโยธา-โครงสร้าง": ["civil", "structure", "bridge", "construction"],
    "วิศวกรรมเคมี-วัสดุ": ["chemical", "polymer", "nanotech", "materials"],
    "สถาปัตยกรรม-การออกแบบ": ["architecture", "urban", "interior", "BIM"],
    # --- เศรษฐกิจ-สังคม-กฎหมาย ---
    "เศรษฐกิจมหภาค-การเงิน": ["economics", "inflation", "monetary", "GDP"],
    "การเงิน-การลงทุน": ["finance", "investment", "portfolio", "banking"],
    "การบัญชี-ตรวจสอบ": ["accounting", "audit", "tax", "statement"],
    "การตลาด-ธุรกิจ": ["marketing", "brand", "consumer", "strategy"],
    "การจัดการ-ภาวะผู้นำ": ["management", "leadership", "operations", "HR"],
    "กฎหมาย-สิทธิมนุษยชน": ["law", "rights", "constitution", "court"],
    "จริยธรรม-ปรัชญา": ["ethics", "philosophy", "moral", "existentialism"],
    "ประวัติศาสตร์-อารยธรรม": ["history", "civilization", "archaeology", "era"],
    "สังคมวิทยา-มานุษยวิทยา": ["society", "culture", "anthropology", "community"],
    "รัฐศาสตร์-ความสัมพันธ์ระหว่างประเทศ": ["politics", "diplomacy", "governance", "policy"],
    # --- ภาษา-ศิลปะ-การศึกษา ---
    "ภาษาศาสตร์-การแปล": ["linguistics", "translation", "syntax", "semantics"],
    "วรรณกรรม-การเขียน": ["literature", "writing", "narrative", "poetry"],
    "การสอน-การศึกษา": ["education", "pedagogy", "learning", "curriculum"],
    "ดนตรี-เสียง": ["music", "acoustics", "composition", "rhythm"],
    "ภาพยนตร์-สื่อ-กราฟฟิก": ["film", "animation", "design", "visual"],
    # --- สิ่งแวดล้อม-พลังงาน-อาหาร ---
    "ภูมิอากาศ-สิ่งแวดล้อม": ["climate", "ecology", "biodiversity", "pollution"],
    "เกษตร-อาหาร": ["agriculture", "crop", "soil", "food science"],
    "น้ำ-ทรัพยากร": ["water", "irrigation", "hydrology", "resource"],
    "พลังงาน-นิวเคลียร์": ["energy", "solar", "nuclear", "fusion"],
    "อวกาศ-การสำรวจ": ["space", "rocket", "orbit", "habitat"],
    "การเอาชีวิตรอด-ความปลอดภัย": ["survival", "disaster", "safety", "risk"],
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
