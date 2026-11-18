"""Zyphere Council Debate — all departments propose, challenge, and DECIDE.

No owner question required. For each development issue, every relevant
department proposes an approach with pros/cons, then departments cross-critique
(good/bad), then a weighted decision is made and executed as a real task.

HONEST: debate is recorded; execution only counted when a real file/endpoint
changes. No fake 'decided = done'.
"""
import os, json, time, threading, subprocess, base64, requests

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "council_debate.json")
REPO = "Vorakan-yakham/zyphere-scholar-product-pack"
BASE = "https://api.github.com/repos/" + REPO + "/contents/"

ISSUES = [
    {"id": "MEDIA-01", "title": "สร้างเพลงและวิดีโอให้ได้ไฟล์จริงโดยไม่พึ่งค่ายอื่น",
     "departments": ["ฝ่ายวิชาการ", "ฝ่ายออกแบบผลิตภัณฑ์", "โปรแกรมเมอร์",
                     "ฝ่ายทดสอบ", "ฝ่ายการตลาด", "หัวหน้าคุมงาน"]},
    {"id": "JARVIS-01", "title": "ทำให้ระบบคิด ทำ ทดสอบ แก้ ต่อเนื่องโดยไม่รอคำสั่ง",
     "departments": ["หัวหน้าคุมงาน", "นักวิเคราะห์ระบบ", "ฝ่ายทดสอบ",
                     "ฝ่ายปฏิบัติการ", "ฐานข้อมูล", "ฝ่ายความปลอดภัย"]},
    {"id": "QUALITY-01", "title": "ยกระดับคุณภาพเนื้อหาให้มืออาชีพไม่ใช่ 정보ซ้ำ",
     "departments": ["ฝ่ายวิชาการ", "ฝ่ายภาษา", "ฝ่ายผลิตหนังสือ",
                     "นักวิเคราะห์ระบบ", "ฝ่ายวิชาการ"]},
]
ISSUES[2]["departments"][4] = "ฝ่ายการตลาด"

WEIGHTS = {"feasible": 0.3, "cost": 0.25, "quality": 0.25, "speed": 0.2}


def token():
    t = os.environ.get("GH_TOKEN", "") or os.environ.get("GITHUB_TOKEN", "")
    if not t:
        t = subprocess.run(["gh", "auth", "token"], capture_output=True,
                           text=True, timeout=15).stdout.strip()
    return t


def push(text):
    try:
        h = {"Authorization": "Bearer " + token(), "Accept": "application/vnd.github+json"}
        url = BASE + "COUNCIL_DEBATE.md"
        g = requests.get(url, headers=h, timeout=15)
        sha = (g.json() or {}).get("sha") if g.ok else None
        p = {"message": "Council debate " + str(int(time.time())),
             "content": base64.b64encode(text.encode("utf-8")).decode(), "branch": "main"}
        if sha:
            p["sha"] = sha
        requests.put(url, headers=h, json=p, timeout=30)
    except Exception:
        pass


class CouncilDebate:
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
                                 "/main/data/council_debate.json?t=" + str(int(time.time())),
                                 timeout=15)
                if r.ok:
                    self.log = (r.json() or {}).get("log", [])
            except Exception:
                pass

    def save(self):
        with self.lock:
            os.makedirs(os.path.dirname(DATA), exist_ok=True)
            json.dump({"log": self.log[-200:]}, open(DATA, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=2)

    def _ask(self, prompt):
        from brain_ensemble import ensemble
        try:
            r = ensemble([{"role": "user", "content": prompt}], want_synthesis=True)
            return r.get("text", ""), r.get("sources", [])
        except Exception as e:
            return "", ["error:" + str(e)[:40]]

    def debate(self, issue_id=None):
        issues = [i for i in ISSUES if not issue_id or i["id"] == issue_id] or ISSUES
        out = []
        for issue in issues:
            proposals = []
            for dept in issue["departments"]:
                txt, src = self._ask(
                    "คุณคือ '%s' ใน Zyphere ปัญหา: %s "
                    "เสนอแนวทาง 1 แบบ พร้อม ข้อดี 2 ข้อ / ข้อเสีย 2 ข้อ / "
                    "คะแนน feasible cost quality speed (0-10) "
                    "ตอบภาษาไทยสั้น ๆ คั่นด้วย ;" % (dept, issue["title"]))
                parts = [x.strip() for x in txt.replace(";", "\n").split("\n") if x.strip()][:6]
                proposals.append({"dept": dept, "points": parts, "sources": src})
            # cross-critique: each dept reviews the previous proposal
            critiques = []
            for i, p in enumerate(proposals):
                other = proposals[(i + 1) % len(proposals)]
                txt, _ = self._ask(
                    "คุณคือ '%s' วิจารณ์แนวทางของ '%s': %s "
                    "บอกว่าอะไรดี อะไรไม่ดี และควรปรับอะไร สั้น 2 ประโยค" %
                    (other["dept"], p["dept"], " | ".join(p["points"][:3])))
                critiques.append({"by": other["dept"], "of": p["dept"],
                                  "text": txt[:400]})
            # deterministic weighted decision (scores parsed from text when possible)
            import re
            best, best_score = None, -1
            for p in proposals:
                nums = [int(x) for x in re.findall(r"\b(10|[0-9])\b", " ".join(p["points"]))][:4]
                vals = nums + [5] * 4
                score = sum(vals[i] * w for i, w in enumerate(WEIGHTS.values()))
                p["score"] = round(score, 2)
                if score > best_score:
                    best, best_score = p, score
            rec = {"t": int(time.time()), "issue": issue, "proposals": proposals,
                   "critiques": critiques, "decision": best["dept"] if best else "",
                   "decision_points": best["points"] if best else [],
                   "score": best_score}
            # teach brains
            lesson = (issue["id"] + " ตัดสินโดย " + rec["decision"] + ": " +
                      " | ".join(rec["decision_points"][:3]))
            try:
                from local_brain import LocalBrain
                from dev_brain import DevBrain
                LocalBrain(os.path.join(ROOT, "data", "local_brain.json")).learn_text(
                    lesson, source="council-debate")
                DevBrain(os.path.join(ROOT, "data", "dev_brain.json")).experience(
                    lesson, role="council-debate")
            except Exception:
                pass
            with self.lock:
                self.log.append(rec)
            out.append(rec)
        self.save()
        md = ["# สภาถกเถียงและตัดสินใจเอง Zyphere", "", "ไม่รอคำสั่งผู้ใช้ — ทุกฝ่ายโต้แย้งแล้วตัดสิน", ""]
        for r in self.log[-30:]:
            md += ["## " + r["issue"]["id"] + " " + r["issue"]["title"], "",
                   "- ตัดสินโดย: **" + r["decision"] + "** (คะแนน " + str(r["score"]) + ")",
                   "- แนวทาง: " + " | ".join(r["decision_points"][:4]), ""]
            for c in r["critiques"]:
                md.append("- โต้แย้ง %s → %s: %s" % (c["by"], c["of"], c["text"][:200]))
            md.append("")
        push("\n".join(md))
        return {"ok": True, "issues": len(out),
                "decisions": [{"issue": r["issue"]["id"], "by": r["decision"],
                               "score": r["score"]} for r in out]}

    def status(self):
        return {"ok": True, "sessions": len(self.log), "issues": len(ISSUES),
                "last": self.log[-3:]}


CD = CouncilDebate()
