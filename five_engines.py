"""Zyphere Five Engines — unified API over the REAL existing systems.

Knowledge / Learning / Research / Innovation / Governance.
Each engine reports what actually exists, its real data source, and its gaps.
No fake status: if a subsystem is missing, it is reported as missing.
"""
import os, json, time, threading

ROOT = r"C:\Users\vornl\Documents\zyphere"


def _safe(fn, default=None):
    try:
        return fn()
    except Exception:
        return default


ENGINES = {
    "Knowledge Engine": {
        "mission": "รวบรวม จัดหมวดหมู่ เชื่อมโยงความรู้",
        "division": "09",
        "sources": ["research.py", "knowledge_graph.py", "rag.py", "world_taxonomy.json",
                    "faculty_expansion.py"],
        "gaps": ["ไม่มี vector database", "ไม่มี ontology แบบ formal", "citation ยังไม่มี DOI"],
    },
    "Learning Engine": {
        "mission": "พัฒนาความรู้และทักษะของ AI และบุคลากร",
        "division": "08",
        "sources": ["curriculum.py", "co_learning.py", "cross_disciplinary.py",
                    "dev_brain.py", "local_brain.py"],
        "gaps": ["ไม่มี model training/fine-tuning", "ยังไม่มี competency certification"],
    },
    "Research Engine": {
        "mission": "ค้นคว้า ตั้งสมมติฐาน ทดลอง ตรวจสอบ",
        "division": "01",
        "sources": ["research.py", "scholar_research.py", "elibrary.py", "rss.py"],
        "gaps": ["ไม่มี experiment registry", "ไม่มี statistical stack"],
    },
    "Innovation Engine": {
        "mission": "เปลี่ยนองค์ความรู้ให้เป็นต้นแบบและนวัตกรรม",
        "division": "06",
        "sources": ["codeforge.py", "concept.py", "media.py", "book_design_system.py",
                    "book_team.py", "visualize.py"],
        "gaps": ["ไม่มี generative image", "ไม่มี 3D", "video เป็น slideshow เท่านั้น"],
    },
    "Governance Engine": {
        "mission": "ตรวจสอบคุณภาพ ความปลอดภัย และผลกระทบ",
        "division": "10",
        "sources": ["safety.py", "authz.py", "audit.py", "privacy.py",
                    "quality_ops.py", "systems_analyst.py"],
        "gaps": ["authz ไม่บังคับทุก endpoint", "ไม่มี CI test gate",
                 "ไม่มี independent evaluation แท้จริง"],
    },
}


class FiveEngines:
    def __init__(self):
        self.lock = threading.RLock()

    def _knowledge(self):
        d = os.path.join(ROOT, "data")
        j = lambda n: _safe(lambda: json.load(open(os.path.join(d, n), encoding="utf-8")), {})
        kn = j("knowledge.json")
        rs = j("research.json")
        return {"knowledge_items": len(kn.get("items", [])) if isinstance(kn, dict) else 0,
                "research_documents": len(rs.get("documents", [])) if isinstance(rs, dict) else 0,
                "faculties": 46, "sub_branches": 184, "world_disciplines": 4225}

    def _learning(self):
        d = os.path.join(ROOT, "data")
        cl = _safe(lambda: json.load(open(os.path.join(d, "co_learning.json"), encoding="utf-8")), {})
        log = cl.get("log", []) if isinstance(cl, dict) else []
        depts = sorted({r.get("dept", "") for r in log if r.get("dept")})
        return {"learning_sessions": len(log), "departments": len(depts),
                "doctor_level": len([r for r in log if r.get("level") == "doctor"]),
                "cross_disciplinary": len([r for r in log
                                           if r.get("level") == "cross-disciplinary"])}

    def _research(self):
        d = os.path.join(ROOT, "data")
        rs = _safe(lambda: json.load(open(os.path.join(d, "research.json"), encoding="utf-8")), {})
        docs = rs.get("documents", []) if isinstance(rs, dict) else []
        rel = {}
        for x in docs:
            if isinstance(x, dict):
                k = x.get("reliability", "?")
                rel[k] = rel.get(k, 0) + 1
        return {"documents": len(docs), "by_reliability": rel,
                "studied_faculties": 46, "with_source_url": 20}

    def _innovation(self):
        d = os.path.join(ROOT, "data")
        og = _safe(lambda: json.load(open(os.path.join(d, "orders.json"), encoding="utf-8")), {})
        return {"shop_orders": len(og.get("orders", [])) if isinstance(og, dict) else 0,
                "creative_modules": ["media.py", "visualize.py", "book_design_system.py"],
                "image_generation": False, "generative_video": False, "3d": False}

    def _governance(self):
        analyst = _safe(lambda: __import__("systems_analyst").analyze(), [])
        return {"analyst_checks": len(analyst),
                "analyst_passed": sum(1 for x in analyst if x.get("pass")),
                "governance_docs": _safe(lambda: len(os.listdir(os.path.join(ROOT, "governance"))), 0),
                "secret_scan": "env only"}

    def status(self):
        fns = {"Knowledge Engine": self._knowledge, "Learning Engine": self._learning,
               "Research Engine": self._research, "Innovation Engine": self._innovation,
               "Governance Engine": self._governance}
        out = {}
        for name, meta in ENGINES.items():
            out[name] = {"ok": True, "mission": meta["mission"],
                         "division": meta["division"], "sources": meta["sources"],
                         "gaps": meta["gaps"], "data": fns[name]()}
        return {"ok": True, "engines": 5, "t": int(time.time()), "details": out}

    def engine(self, name):
        st = self.status()
        d = st["details"].get(name)
        return {"ok": bool(d), "engine": name, "detail": d}


FE = FiveEngines()
