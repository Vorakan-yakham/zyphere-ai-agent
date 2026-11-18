"""Zyphere Department Dialogue — every department talks, challenges and builds
together toward JARVIS-level operation, without waiting for the owner.

Each round: a department asks another department a real working question;
Zyphere's ensemble answers from both perspectives; the lesson is fed into the
brains; a concrete joint task is logged. Fully auditable.
"""
import os, json, time, threading, subprocess, base64, requests

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "department_dialogue.json")
REPO = "Vorakan-yakham/zyphere-scholar-product-pack"
BASE = "https://api.github.com/repos/" + REPO + "/contents/"

PAIRS = [
    ("ฝ่ายวิชาการ", "ฝ่ายผลิตหนังสือ", "เนื้อหาที่ถูกต้องต้องมาจากแหล่งไหนและเขียนอย่างไรให้ไม่ซ้ำ"),
    ("ฝ่ายผลิตหนังสือ", "ฝ่าย language", "ข้อความภาษาไทยต้องตรวจอะไรก่อนตีพิมพ์"),
    ("ฝ่ายออกแบบผลิตภัณฑ์", "นักวิเคราะห์ระบบ", "ปกและหน้าเว็บต้องมีโครงสร้างอย่างไรถึงจะสวยและตรวจได้"),
    ("ฝ่ายการตลาด", "ฝ่ายวิชาการ", "จะขายความรู้โดยไม่กล่าวเกินจริงต้องอธิบายคุณค่าอย่างไร"),
    ("ฝ่ายทดสอบ", "โปรแกรมเมอร์", "จะทดสอบอย่างไรถึงจะจับของก็อปปี้และบั๊กได้"),
    ("ฐานข้อมูล", "ฝ่ายปฏิบัติการ", "ข้อมูลจะอยู่รอดอย่างไรเมื่อ Render restart"),
    ("ฝ่ายความปลอดภัย", "โปรแกรมเมอร์", "จะบังคับ authz และ fail-closed ให้ครบอย่างไร"),
    ("นักวิเคราะห์ระบบ", "หัวหน้าคุมงาน", "จะวัดคุณภาพแทนการนับจำนวนได้อย่างไร"),
    ("ฝ่าย language", "ฝ่ายการตลาด", "จะเขียนโพสต์โปรโมทให้ถูกต้องและน่าสนใจอย่างไร"),
    ("ฝ่ายปฏิบัติการ", "ฝ่ายความปลอดภัย", "จะ deploy โดยไม่เปิดเผย secret อย่างไร"),
    ("หัวหน้าคุมงาน", "ทุกแผนก", "จะจี้ให้ทุกแผนกพัฒนาตนเองอย่างต่อเนื่องอย่างไร"),
]
PAIRS[1] = (PAIRS[1][0], "ฝ่ายภาษา", PAIRS[1][2])
PAIRS[8] = (PAIRS[8][0], "ฝ่ายภาษา", PAIRS[8][2])


def token():
    t = os.environ.get("GH_TOKEN", "") or os.environ.get("GITHUB_TOKEN", "")
    if not t:
        t = subprocess.run(["gh", "auth", "token"], capture_output=True,
                           text=True, timeout=15).stdout.strip()
    return t


def push(text):
    try:
        h = {"Authorization": "Bearer " + token(), "Accept": "application/vnd.github+json"}
        url = BASE + "DEPARTMENT_DIALOGUE.md"
        g = requests.get(url, headers=h, timeout=15)
        sha = (g.json() or {}).get("sha") if g.ok else None
        p = {"message": "Department dialogue " + str(int(time.time())),
             "content": base64.b64encode(text.encode("utf-8")).decode(), "branch": "main"}
        if sha:
            p["sha"] = sha
        requests.put(url, headers=h, json=p, timeout=30)
    except Exception:
        pass


class DepartmentDialogue:
    def __init__(self):
        self.lock = threading.RLock()
        self.log = []
        self._load()

    def _load(self):
        try:
            self.log = json.load(open(DATA, encoding="utf-8")).get("log", [])
        except Exception:
            pass
        if not self.log:
            try:
                r = requests.get("https://raw.githubusercontent.com/" + REPO +
                                 "/main/data/department_dialogue.json?t=" +
                                 str(int(time.time())), timeout=15)
                if r.ok:
                    self.log = (r.json() or {}).get("log", [])
            except Exception:
                pass

    def save(self):
        with self.lock:
            os.makedirs(os.path.dirname(DATA), exist_ok=True)
            json.dump({"log": self.log[-300:]}, open(DATA, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=2)

    def round(self, asker=None):
        pairs = [p for p in PAIRS if not asker or asker in (p[0], p[1])] or PAIRS
        results = []
        from brain_ensemble import ensemble
        for a, b, q in pairs:
            prompt = ("คุณคือ '%s' กำลังถาม '%s' ในองค์กร AI Zyphere: %s "
                      "ตอบเป็นภาษาไทย 3 ข้อสั้น ๆ บอกข้อตกลงร่วมที่ทั้งสองฝ่ายต้องทำ "
                      "และผลงานที่ต้องส่งมอบจริง คั่นด้วย ;" % (a, b, q))
            try:
                r = ensemble([{"role": "user", "content": prompt}], want_synthesis=True)
                text = r.get("text", "")
                src = r.get("sources", [])
            except Exception as e:
                text, src = "", ["error:" + str(e)[:40]]
            points = [x.strip() for x in text.replace(";", "\n").split("\n")
                      if x.strip() and len(x.strip()) > 8][:3]
            if not points:
                points = [a + " และ " + b + " ต้องร่วมกัน_truth ผลงานจริง"]
            lesson = a + " ↔ " + b + ": " + " | ".join(points)
            try:
                from local_brain import LocalBrain
                from dev_brain import DevBrain
                lb = LocalBrain(os.path.join(ROOT, "data", "local_brain.json"))
                db = DevBrain(os.path.join(ROOT, "data", "dev_brain.json"))
                lb.learn_text(lesson, source="dialogue")
                db.experience(lesson, role="dialogue")
            except Exception:
                pass
            rec = {"t": int(time.time()), "asker": a, "answerer": b,
                   "question": q, "points": points, "sources": src}
            results.append(rec)
            with self.lock:
                self.log.append(rec)
        self.save()
        md = ["# บทสนทนาระหว่างแผนก Zyphere", "", "ไม่รอคำสั่ง — ทุกแผนกคุยกันเองเพื่อบรรลุ JARVIS", ""]
        for r in self.log[-60:]:
            md += ["## " + r["asker"] + " → " + r["answerer"], "",
                   "- คำถาม: " + r["question"],
                   "- ข้อตกลง: " + " | ".join(r["points"]),
                   "- แหล่ง: " + ", ".join(r["sources"]), ""]
        push("\n".join(md).replace("_truth", "สร้าง"))
        return {"ok": True, "exchanges": len(results), "results": results}

    def status(self):
        return {"ok": True, "exchanges": len(self.log),
                "pairs": len(PAIRS), "last": self.log[-11:]}


DD = DepartmentDialogue()
