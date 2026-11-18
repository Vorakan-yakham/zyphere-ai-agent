"""Zyphere Engineering Council — develop together with every engineering branch.

Each branch identifies: (1) current weakness with evidence, (2) what to improve,
(3) what to continue and strengthen, (4) concrete next task. Cross-review,
then a ranked improvement plan is written and fed to the brains. No owner
question needed; decisions are auditable in ENGINEERING_PLAN.md.
"""
import os, json, time, threading, requests, subprocess, base64

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "engineering_council.json")
REPO = "Vorakan-yakham/zyphere-scholar-product-pack"
BASE = "https://api.github.com/repos/" + REPO + "/contents/"

BRANCHES = [
    ("วิศวกรรมซอฟต์แวร์", "app.py, store.py, five_engines.py", "targeted edit, authz, test gate"),
    ("วิศวกรรมไฟฟ้า-อิเล็กทรอนิกส์", "ฮาร์ดแวร์/สัญญาณ", "ยังไม่มีโมดูลจริง — ต้องระบุว่าเป็น simulaton"),
    ("วิศวกรรมเครื่องกล", "aerospace.py, applied.py", "blueprint/spec ยังไม่เชื่อม与本システム"),
    ("วิศวกรรมโยธา-โครงสร้าง", "applied.py blueprint", "ยังเป็น spec — ต้องเพิ่ม validation"),
    ("วิศวกรรมเคมี-วัสดุ", "ยังไม่มีโมดูล", "ต้องสร้าง material spec engine หรือระบุ gap"),
    ("ฐานข้อมูลและสถิติ", "app.py KV, github_backup.py", "restore, concurrency, no SQL"),
    ("AI และข้อมูล", "brain_ensemble.py, dev_brain.py", "multi-model, learning, memory"),
    ("ความมั่นคงไซเบอร์", "safety.py, authz.py, audit.py", "authz ไม่บังคับทุก endpoint"),
    ("หุ่นยนต์-ระบบอัตโนมัติ", "autopost.py, chief.py", "workflow ยังไม่มี orchestrator จริง"),
    ("คอมพิวเตอร์วิทัศน์-เสียง", "image_studio.py, music_studio.py", "不再是แค่ข้อมูล — มีไฟล์จริงแล้ว"),
    ("วิศวกรรมการผลิตสื่อ", "media.py, music_studio.py", "FFmpeg, TTS, SRT, video composer"),
    ("QA และ DevOps", "test_zyphere.py, systems_analyst.py, CI", "CI gate, before/after, regression"),
]
BRANCHES[1] = (BRANCHES[1][0], BRANCHES[1][1], "ยังไม่มีโมดูลจริง — ต้องระบุว่าเป็น simulation")
BRANCHES[2] = (BRANCHES[2][0], BRANCHES[2][1], "blueprint/spec ยังไม่เชื่อมกับระบบนี้")
BRANCHES[9] = (BRANCHES[9][0], BRANCHES[9][1], "ไม่ใช่แค่ข้อมูล — มีไฟล์จริงแล้ว")
BRANCHES[5] = ("ฐานข้อมูลและสถิติ", BRANCHES[5][1], "restore, concurrency, no SQL")


def token():
    t = os.environ.get("GH_TOKEN", "") or os.environ.get("GITHUB_TOKEN", "")
    if not t:
        t = subprocess.run(["gh", "auth", "token"], capture_output=True,
                           text=True, timeout=15).stdout.strip()
    return t


def push(text):
    try:
        h = {"Authorization": "Bearer " + token(), "Accept": "application/vnd.github+json"}
        url = BASE + "ENGINEERING_PLAN.md"
        g = requests.get(url, headers=h, timeout=15)
        sha = (g.json() or {}).get("sha") if g.ok else None
        p = {"message": "Engineering council " + str(int(time.time())),
             "content": base64.b64encode(text.encode("utf-8")).decode(), "branch": "main"}
        if sha:
            p["sha"] = sha
        requests.put(url, headers=h, json=p, timeout=30)
    except Exception:
        pass


class EngineeringCouncil:
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
                                 "/main/data/engineering_council.json?t=" +
                                 str(int(time.time())), timeout=15)
                if r.ok:
                    self.log = (r.json() or {}).get("log", [])
            except Exception:
                pass

    def save(self):
        with self.lock:
            os.makedirs(os.path.dirname(DATA), exist_ok=True)
            json.dump({"log": self.log[-200:]}, open(DATA, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=2)

    def session(self):
        from brain_ensemble import ensemble
        results = []
        for name, current, focus in BRANCHES:
            prompt = ("คุณคือวิศวกรสาขา '%s' ของ Zyphere สิ่งที่มีตอนนี้: %s "
                      "จุดที่ต้องปรับปรุง: %s "
                      "ตอบภาษาไทย: WEAKNESS=จุดอ่อนที่มีหลักฐาน ; IMPROVE=สิ่งที่ควรปรับ 2 ข้อ ; "
                      "CONTINUE=สิ่งที่ควรทำต่อให้ดีขึ้น 2 ข้อ ; NEXT=งานจริงที่ทำตอนนี้ได้ 1 อย่าง "
                      "สั้น ๆ" % (name, current, focus))
            try:
                r = ensemble([{"role": "user", "content": prompt}], want_synthesis=True)
                text = r.get("text", ""); src = r.get("sources", [])
            except Exception as e:
                text, src = "", ["error:" + str(e)[:40]]
            rec = {"t": int(time.time()), "branch": name, "current": current,
                   "focus": focus, "text": text[:900], "sources": src}
            results.append(rec)
            lesson = name + ": " + text[:300]
            try:
                from local_brain import LocalBrain
                from dev_brain import DevBrain
                LocalBrain(os.path.join(ROOT, "data", "local_brain.json")).learn_text(
                    lesson, source="eng:" + name)
                DevBrain(os.path.join(ROOT, "data", "dev_brain.json")).experience(
                    lesson, role="eng:" + name)
            except Exception:
                pass
        with self.lock:
            self.log.append({"t": int(time.time()), "results": results})
        self.save()
        md = ["# แผนพัฒนาวิศวกรรม Zyphere — ทำร่วมทุกแขนง", "",
              "ทุกแขนงเสนอจุดอ่อน สิ่งที่ปรับ และสิ่งที่ทำต่อ — ตัดสินเอง ไม่รอคำสั่ง", ""]
        for r in results:
            md += ["## " + r["branch"], "",
                   "- ของเดิม: " + r["current"],
                   "- จุดโฟกัส: " + r["focus"],
                   "- ข้อเสนอ: " + r["text"].replace("\n", " ")[:500], ""]
        push("\n".join(md))
        return {"ok": True, "branches": len(results), "results": results}

    def status(self):
        return {"ok": True, "branches": len(BRANCHES),
                "sessions": len(self.log), "last": self.log[-1]["results"][:3] if self.log else []}


EC = EngineeringCouncil()
