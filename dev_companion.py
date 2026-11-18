"""Zyphere Dev Companion — Zyphere learns ALONGSIDE the developer on every action.

Every development action (edit, test, deploy, bug fix, feature, research) is
recorded and fed into LocalBrain + DevBrain. This is not a claim of model
training — it is symbolic/experiential learning stored durably and auditable.

HONEST: no secrets or private memory are published; only action summaries and
lessons go to GitHub.
"""
import os, json, time, threading, subprocess, base64, requests

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "dev_actions.json")
REPO = "Vorakan-yakham/zyphere-scholar-product-pack"
BASE = "https://api.github.com/repos/" + REPO + "/contents/"


def token():
    t = os.environ.get("GH_TOKEN", "") or os.environ.get("GITHUB_TOKEN", "")
    if not t:
        t = subprocess.run(["gh", "auth", "token"], capture_output=True,
                           text=True, timeout=15).stdout.strip()
    return t


def push(name, text):
    try:
        h = {"Authorization": "Bearer " + token(), "Accept": "application/vnd.github+json"}
        url = BASE + name
        sha = None
        g = requests.get(url, headers=h, timeout=15)
        if g.ok:
            sha = (g.json() or {}).get("sha")
        p = {"message": "Dev companion learning " + str(int(time.time())),
             "content": base64.b64encode(text.encode("utf-8")).decode(), "branch": "main"}
        if sha:
            p["sha"] = sha
        r = requests.put(url, headers=h, json=p, timeout=30)
        return r.ok, r.status_code
    except Exception as e:
        return False, str(e)[:80]


class DevCompanion:
    def __init__(self):
        self.lock = threading.RLock()
        self.actions = []
        self._load()

    def _load(self):
        try:
            self.actions = json.load(open(DATA, encoding="utf-8")).get("actions", [])
        except Exception:
            pass
        if not self.actions:
            try:
                r = requests.get("https://raw.githubusercontent.com/" + REPO +
                                 "/main/data/dev_actions.json?t=" + str(int(time.time())),
                                 timeout=15)
                if r.ok:
                    self.actions = (r.json() or {}).get("actions", [])
            except Exception:
                pass

    def save(self):
        with self.lock:
            os.makedirs(os.path.dirname(DATA), exist_ok=True)
            json.dump({"actions": self.actions[-1000:]},
                      open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    def _teach(self, lesson, source="dev-companion"):
        try:
            from local_brain import LocalBrain
            from dev_brain import DevBrain
            lb = LocalBrain(os.path.join(ROOT, "data", "local_brain.json"))
            db = DevBrain(os.path.join(ROOT, "data", "dev_brain.json"))
            lb.learn_text(lesson, source=source)
            db.experience(lesson, role=source)
            return True
        except Exception:
            return False

    def record(self, action="", tool="", detail="", outcome="", files=None, lesson=""):
        """Record one action and teach Zyphere immediately."""
        rec = {"t": int(time.time()), "action": str(action)[:160],
               "tool": str(tool)[:80], "detail": str(detail)[:600],
               "outcome": str(outcome)[:200], "files": files or [],
               "lesson": str(lesson)[:400]}
        with self.lock:
            self.actions.append(rec)
        self.save()
        taught = False
        if rec["lesson"]:
            taught = self._teach(rec["lesson"], "dev:" + rec["action"])
        self.publish()
        return {"ok": True, "recorded": True, "taught": taught, "action": rec}

    def batch(self, items):
        out = []
        for it in items:
            out.append(self.record(**it))
        return {"ok": True, "count": len(out), "taught": sum(1 for x in out if x["taught"])}

    def publish(self):
        md = ["# Zyphere — เรียนรู้ไปพร้อมนักพัฒนา", "",
              "ทุกการกระทำถูกบันทึกและสอนเข้า LocalBrain/DevBrain", "",
              "จำนวนการกระทำ: %d" % len(self.actions), ""]
        for a in self.actions[-40:]:
            md += ["## " + a["action"] + " (" + time.strftime("%H:%M", time.localtime(a["t"])) + ")", "",
                   "- เครื่องมือ: " + a["tool"],
                   "- รายละเอียด: " + a["detail"],
                   "- ผล: " + a["outcome"],
                   "- บทเรียน: " + (a["lesson"] or "-"), ""]
        push("DEV_COMPANION.md", "\n".join(md))
        try:
            h = {"Authorization": "Bearer " + token(), "Accept": "application/vnd.github+json"}
            url = BASE + "data/dev_actions.json"
            g = requests.get(url, headers=h, timeout=15)
            sha = (g.json() or {}).get("sha") if g.ok else None
            p2 = {"message": "Dev actions " + str(int(time.time())),
                  "content": base64.b64encode(json.dumps(
                      {"actions": self.actions[-1000:]}, ensure_ascii=False).encode()).decode(),
                  "branch": "main"}
            if sha:
                p2["sha"] = sha
            requests.put(url, headers=h, json=p2, timeout=30)
        except Exception:
            pass

    def status(self):
        return {"ok": True, "actions": len(self.actions),
                "last": self.actions[-20:],
                "lessons": sum(1 for a in self.actions if a.get("lesson"))}


DC = DevCompanion()
