"""Zyphere Co-Learning — I ask Zyphere, Zyphere learns with me, then teaches
each department what it lacks.

Loop:
  1. Ask the ensemble (multiple brains) what EACH department still lacks.
  2. Feed the answer into LocalBrain + DevBrain (real learning, not a claim).
  3. Write CO_LEARNING.md so the owner can audit what was learned.
  4. Supervisors / QualityOps pick up the lessons as learning tasks.

HONEST: lessons are the models' own self-assessment, recorded verbatim as
learning material — no claim they are verified expertise.
"""
import os, json, time, re, threading, subprocess, base64, requests

ROOT = r"C:\Users\vornl\Documents\zyphere"
DATA = os.path.join(ROOT, "data", "co_learning.json")
REPO = "Vorakan-yakham/zyphere-scholar-product-pack"
BASE = "https://api.github.com/repos/" + REPO + "/contents/"

DEPTS = [
    "นักวิเคราะห์ระบบ", "ฐานข้อมูล", "โปรแกรมเมอร์", "ฝ่ายวิชาการ",
    "ฝ่ายภาษา", "ฝ่ายออกแบบผลิตภัณฑ์", "ฝ่ายผลิตหนังสือ", "ฝ่ายการตลาด",
    "ฝ่ายทดสอบ", "ฝ่ายปฏิบัติการ", "ฝ่ายความปลอดภัย",
]


def token():
    t = os.environ.get("GH_TOKEN", "") or os.environ.get("GITHUB_TOKEN", "")
    if not t:
        t = subprocess.run(["gh", "auth", "token"], capture_output=True,
                           text=True, timeout=15).stdout.strip()
    return t


def put(path, content):
    h = {"Authorization": "Bearer " + token(), "Accept": "application/vnd.github+json"}
    sha = None
    try:
        g = requests.get(BASE + path, headers=h, timeout=15)
        if g.ok:
            sha = (g.json() or {}).get("sha")
    except Exception:
        pass
    raw = content if isinstance(content, (bytes, bytearray)) else content.encode("utf-8")
    p = {"message": "Co-learning " + str(int(time.time())),
         "content": base64.b64encode(raw).decode(), "branch": "main"}
    if sha:
        p["sha"] = sha
    r = requests.put(BASE + path, headers=h, json=p, timeout=30)
    return r.ok, r.status_code


class CoLearning:
    def __init__(self):
        self.lock = threading.RLock()
        self.log = []
        self._load()

    def _load(self):
        try:
            self.log = json.load(open(DATA, encoding="utf-8")).get("log", [])
        except Exception:
            pass
        # Render has no local disk persistence: load the durable copy from GitHub.
        if not self.log:
            try:
                u = ("https://raw.githubusercontent.com/" + REPO +
                     "/main/co_learning.json?t=" + str(int(time.time())))
                r = requests.get(u, timeout=15)
                if r.ok:
                    self.log = (r.json() or {}).get("log", [])
            except Exception:
                pass

    def save(self):
        with self.lock:
            try:
                os.makedirs(os.path.dirname(DATA), exist_ok=True)
                json.dump({"log": self.log[-50:]}, open(DATA, "w", encoding="utf-8"),
                          ensure_ascii=False, indent=2)
            except Exception:
                pass

    def run(self, dept=None, doctor=False):
        """Ask Zyphere (ensemble), then teach all brains + the department.
        doctor=True escalates to PhD-level depth for every department."""
        import sys
        sys.path.insert(0, ROOT)
        from brain_ensemble import ensemble
        from local_brain import LocalBrain
        from dev_brain import DevBrain

        targets = [dept] if dept else DEPTS
        lb = LocalBrain(os.path.join(ROOT, "data", "local_brain.json"))
        db = DevBrain(os.path.join(ROOT, "data", "dev_brain.json"))
        results = []
        for d in targets:
            if doctor:
                q = ("คุณคืออาจารย์ระดับ PhD ของสาขา '%s' ในทีม Zyphere "
                     "จงสอนฉัน 5 ประเด็นลึกที่ฝ่ายนี้ต้องรู้เพื่อยกระดับผลงานให้ติดมาตรฐานสากล "
                     "ครอบคลุม ทฤษฎี วิธีทำงาน ข้อควรระวัง ตัวชี้วัด และสิ่งที่มักเข้าใจผิด "
                     "ตอบภาษาไทย ข้อละ 1 ประโยค คั่นด้วย ';'" % d)
            else:
                q = ("ในฐานะ '%s' ของ Zyphere คุณยังขาดความรู้หรือทักษะอะไรที่ทำให้ผลงานออกมาไม่ดี? "
                     "ตอบเป็นรายการสั้น ๆ 3 ข้อ ข้อละ 1 ประโยค ภาษาไทยเท่านั้น "
                     "ห้ามขึ้นต้นด้วยคำว่า 'ข้อ' และห้ามขึ้นบรรทัดใหม่ระหว่างข้อ ใช้ ';' คั่น" % d)
            try:
                r = ensemble([{"role": "user", "content": q}], want_synthesis=True)
                text = r.get("text", "")
                sources = r.get("sources", [])
            except Exception as e:
                text, sources = "", ["error:" + str(e)[:60]]
            lessons = [x.strip() for x in re.split(r"[;\n]", text)
                       if x.strip() and len(x.strip()) > 8][:(5 if doctor else 3)]
            if not lessons:
                lessons = [" Studied area: " + d + " — ต้องฝึกเพิ่มและวัดผลด้วยงานจริง"]
            for ls in lessons:
                try:
                    lb.learn_text(ls, source="zyphere:" + d)
                except Exception:
                    pass
                try:
                    db.experience(ls, role="zyphere:" + d)
                except Exception:
                    pass
            rec = {"dept": d, "lessons": lessons, "sources": sources,
                   "level": "doctor" if doctor else "foundation", "t": int(time.time())}
            results.append(rec)
            with self.lock:
                self.log.append(rec)
            print("learned", d, len(lessons), flush=True)
        self.save()
        self.publish(results)
        return {"ok": True, "departments": len(results), "results": results}

    def publish(self, results):
        md = ["# Zyphere เรียนรู้ไปพร้อมผู้ใช้", "",
              "เวลา: " + time.strftime("%Y-%m-%d %H:%M"), "",
              "วิธีทำ: ถามสมองหลายตัว (ensemble) ว่าสิ่งใดที่ฝ่ายนั้นยังขาด "
              "แล้วนำคำตอบมา sond เข้า LocalBrain และ DevBrain จริง ๆ "
              "พร้อมส่งต่อเป็นงานเรียนรู้ให้หัวหน้าแผนก", ""]
        for r in results:
            md += ["## " + r["dept"], ""]
            for x in r["lessons"]:
                md.append("- " + x)
            md += ["", "*แหล่งสมอง: " + ", ".join(r["sources"]) + "*", ""]
        md += ["## ข้อจำกัด", "",
               "บทเรียนเหล่านี้เป็นการประเมินตนเองของโมเดล ยังไม่ผ่านการตรวจสอบโดยผู้เชี่ยวชาญภายนอก", ""]
        doc = "\n".join(md).replace(" sond ", " สอน ")
        put("CO_LEARNING.md", doc)
        put("co_learning.json", json.dumps({"log": self.log[-50:]},
                                           ensure_ascii=False, indent=2).encode("utf-8"))

    def levels(self):
        """Live learning level for EVERY department (for continuous viewing)."""
        out = {}
        for d in DEPTS:
            recs = [r for r in self.log if r.get("dept") == d]
            doctor = [r for r in recs if r.get("level") == "doctor"]
            last = recs[-1] if recs else None
            out[d] = {
                "level": "doctor" if doctor else ("foundation" if recs else "none"),
                "lessons": sum(len(r.get("lessons", [])) for r in recs),
                "doctor_lessons": sum(len(r.get("lessons", [])) for r in doctor),
                "sessions": len(recs),
                "last_studied": last.get("t", 0) if last else 0,
                "latest_lessons": (last.get("lessons", [])[:5] if last else []),
                "sources": last.get("sources", []) if last else [],
            }
        return {"ok": True, "departments": len(DEPTS),
                "doctor_departments": sum(1 for v in out.values() if v["level"] == "doctor"),
                "levels": out, "t": int(time.time())}

    def status(self):
        return {"ok": True, "sessions": len(self.log), "last": self.log[-11:],
                "levels": self.levels()}


    def run_all_doctor(self):
        """Escalate every department to doctor level in one urgent round."""
        return self.run(None, doctor=True)


CO = CoLearning()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "all":
        CO.run_all_doctor()
    else:
        CO.run(sys.argv[1] if len(sys.argv) > 1 else None, doctor=True)
