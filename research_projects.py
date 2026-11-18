"""Zyphere Research Project System — every project has objective, questions,
method, evidence, resources, risk, validation, deliverables and a final report.

Stores projects in data/research_projects.json and mirrors to GitHub so the
owner can audit them. Seeded with ONE real cross-disciplinary project, not
fictional results.
"""
import os, json, time, threading, subprocess, base64, requests

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "research_projects.json")
REPO = "Vorakan-yakham/zyphere-scholar-product-pack"
BASE = "https://api.github.com/repos/" + REPO + "/contents/"

SEED = [{
    "id": "RP-001",
    "title": "Smart Agriculture — ระบบเกษตรอัจฉริยะด้วยความรู้ข้ามสาขา",
    "objective": "ศึกษาความเป็นไปได้ของการใช้ข้อมูลสภาพภูมิอากาศและดินเพื่อวางแผนการผลิต",
    "problem": "เกษตรกรขาดข้อมูลสภาพภูมิอากาศและดินที่เชื่อมโยงกับการตัดสินใจปลูกพืช",
    "questions": ["ข้อมูลใดที่มีอยู่จริงในระบบ?", "สาขาใดเกี่ยวข้องบ้าง?",
                  "จะสร้างแนวทางที่ตรวจสอบได้อย่างไร?"],
    "departments": ["ฝ่ายวิชาการ", "ฐานข้อมูล", "นักวิเคราะห์ระบบ", "ฝ่ายปฏิบัติการ"],
    "leader": "ฝ่ายวิชาการ",
    "method": "ใช้ world_taxonomy + scholar_research + knowledge_graph ที่มีอยู่จริง",
    "evidence": ["world_taxonomy.json", "FACULTY_TREE.md", "KNOWLEDGE_GRAPH.md"],
    "resources": "ฟรี — GitHub, Render, Wikipedia API",
    "risk": "ข้อมูลจาก Wikipedia อาจล้าสมัย — ต้องระบุแหล่งและวันที่",
    "validation": "ทุกข้อclaim ต้องมีไฟล์จริงใน repo",
    "deliverables": ["SMART_AGRICULTURE.md"],
    "status": "active",
    "t": int(time.time()),
}]


def token():
    t = os.environ.get("GH_TOKEN", "") or os.environ.get("GITHUB_TOKEN", "")
    if not t:
        t = subprocess.run(["gh", "auth", "token"], capture_output=True,
                           text=True, timeout=15).stdout.strip()
    return t


def push_md(name, text):
    h = {"Authorization": "Bearer " + token(), "Accept": "application/vnd.github+json"}
    url = BASE + name
    sha = None
    try:
        g = requests.get(url, headers=h, timeout=15)
        if g.ok:
            sha = (g.json() or {}).get("sha")
    except Exception:
        pass
    p = {"message": "Research project " + str(int(time.time())),
         "content": base64.b64encode(text.encode("utf-8")).decode(), "branch": "main"}
    if sha:
        p["sha"] = sha
    try:
        r = requests.put(url, headers=h, json=p, timeout=30)
        return r.ok, r.status_code
    except Exception as e:
        return False, str(e)[:80]


class ResearchProjects:
    def __init__(self):
        self.lock = threading.RLock()
        self.projects = SEED[:]
        self._load()

    def _load(self):
        try:
            d = json.load(open(DATA, encoding="utf-8"))
            if d.get("projects"):
                self.projects = d["projects"]
        except Exception:
            pass

    def save(self):
        with self.lock:
            os.makedirs(os.path.dirname(DATA), exist_ok=True)
            json.dump({"projects": self.projects, "t": int(time.time())},
                      open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    def list(self):
        return {"ok": True, "count": len(self.projects), "projects": self.projects}

    def create(self, payload):
        req = ["title", "objective", "problem", "questions", "departments", "leader",
               "method", "evidence", "resources", "risk", "validation", "deliverables"]
        missing = [k for k in req if not payload.get(k)]
        if missing:
            return {"ok": False, "error": "missing fields: " + ", ".join(missing)}
        p = dict(payload)
        p["id"] = "RP-%03d" % (len(self.projects) + 1)
        p["status"] = "active"
        p["t"] = int(time.time())
        with self.lock:
            self.projects.append(p)
        self.save()
        return {"ok": True, "project": p}

    def report(self):
        md = ["# Zyphere Research Projects", ""]
        for p in self.projects:
            md += ["## " + p["id"] + " " + p["title"], "",
                   "- **Objective:** " + p["objective"],
                   "- **Problem:** " + p["problem"],
                   "- **Questions:** " + " | ".join(p["questions"]),
                   "- **Departments:** " + ", ".join(p["departments"]),
                   "- **Leader:** " + p["leader"],
                   "- **Method:** " + p["method"],
                   "- **Evidence:** " + ", ".join(p["evidence"]),
                   "- **Resources:** " + p["resources"],
                   "- **Risk:** " + p["risk"],
                   "- **Validation:** " + p["validation"],
                   "- **Deliverables:** " + ", ".join(p["deliverables"]),
                   "- **Status:** " + p["status"], ""]
        return "\n".join(md)

    def publish(self):
        text = self.report()
        return push_md("RESEARCH_PROJECTS.md", text)


RP = ResearchProjects()
