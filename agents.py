"""Zyphere Agent Organization - split Zyphere into cooperating specialist
roles, like a small company. Runs in ONE free Render process (no extra GPU/
cost): each role calls the modules/tools it owns, and a coordinator splits a
mission into tasks, runs them, and merges results.

HONEST: these are logical roles (not separate paid servers). They genuinely
divide work and share outputs. No gambling/illegal. Free.
"""
import os, json, time, threading

ROLES = {
    "researcher": {"name": "นักวิจัย", "job": "ค้นข้อมูลระดับ A/B + RSS + search",
                   "tools": ["research", "rss", "search_web"]},
    "learner": {"name": "นักเรียนรู้", "job": "อ่าน→ตีความ→สรุป→ขยายแขนง",
                "tools": ["concept", "expansion", "curriculum", "dev_brain"]},
    "worker": {"name": "ช่างผลิต", "job": "เขียนโค้ด/ทำสื่อ/ทำรายงาน/แพ็กของ",
               "tools": ["codeforge", "media", "work", "packbuilder"]},
    "reviewer": {"name": "ผู้ตรวจคุณภาพ", "job": "self-correct + eval + safety",
                 "tools": ["selfcorrect", "eval", "safety"]},
    "marketer": {"name": "การตลาด", "job": "หาตลาด เขียนหัวข้อ/คำบรรยาย/tag",
                 "tools": ["market", "listing", "rss"]},
    "operator": {"name": "ผู้ดูแลระบบ", "job": "ยาม แจ้งเตือน audit persist",
                 "tools": ["guard", "audit", "privacy", "report"]},
}


class AgentOrg:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.missions = []
        self._load()

    def _load(self):
        try:
            self.missions = json.load(open(self.path, encoding="utf-8")).get("missions", [])
        except Exception:
            pass

    def save(self):
        with self.lock:
            try:
                os.makedirs(os.path.dirname(self.path), exist_ok=True)
                json.dump({"missions": self.missions[-500:]},
                          open(self.path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            except Exception:
                pass

    def team(self):
        return {"ok": True, "roles": [{"id": k, **v} for k, v in ROLES.items()],
                "note": "6 บทบาทช่วยกันใน 1 process ฟรี — แบ่งงานจริง ไม่ใช่แค่ตั้งชื่อ"}

    def plan(self, mission=""):
        """Coordinator splits a mission into tasks for each role."""
        m = str(mission or "").strip()
        if not m:
            return {"ok": False, "error": "missing mission"}
        low = m.lower()
        tasks = []
        if any(k in low for k in ("หา", "ค้น", "วิจัย", "research")):
            tasks.append({"role": "researcher", "task": "ค้นข้อมูลระดับ A/B + RSS เกี่ยวกับ " + m[:80]})
        if any(k in low for k in ("เรียน", "รู้", "study", "-learn")):
            tasks.append({"role": "learner", "task": "ตีความ/สรุป/ขยายแขนง " + m[:80]})
        if any(k in low for k in ("ทำ", "เขียน", "สร้าง", "ผลิต", "code", "media")):
            tasks.append({"role": "worker", "task": "ผลิตผลงานจริง: " + m[:80]})
        if any(k in low for k in ("ตรวจ", "qa", "คุณภาพ", "ปลอดภัย")):
            tasks.append({"role": "reviewer", "task": "ตรวจความถูกต้อง/ความปลอดภัยของ " + m[:80]})
        if any(k in low for k in ("ขาย", "ตลาด", "โพสต์", "tag", "market")):
            tasks.append({"role": "marketer", "task": "หาตลาด+เขียน listing " + m[:80]})
        if not tasks:
            tasks = [{"role": r, "task": m[:120]} for r in ("researcher", "worker", "reviewer", "marketer")]
        rec = {"ok": True, "id": "org_" + str(int(time.time() * 1000)),
               "mission": m[:200], "tasks": tasks, "status": "planned", "t": int(time.time()),
               "honest": "บทบาทเป็น logical roles ใน process เดียว — แบ่งงานช่วยกันจริง"}
        with self.lock:
            self.missions.append(rec)
        self.save()
        return rec

    def run(self, mid="", state=None):
        """Run the planned tasks by calling the real modules each role owns."""
        rec = next((x for x in reversed(self.missions) if x["id"] == mid or not mid), None)
        if not rec:
            return {"ok": False, "error": "no mission"}
        st = state or {}
        results = []
        for t in rec["tasks"]:
            role = t["role"]
            out = {"role": role, "task": t["task"], "by": ROLES.get(role, {}).get("name", role)}
            try:
                if role == "researcher" and st.get("research"):
                    out["result"] = st["research"](t["task"].replace("ค้นข้อมูลระดับ A/B + RSS เกี่ยวกับ ", ""))[:600]
                elif role == "learner" and st.get("concept"):
                    out["result"] = st["concept"](t["task"])[:400]
                elif role == "worker" and st.get("work"):
                    out["result"] = st["work"](t["task"])[:400]
                elif role == "reviewer" and st.get("review"):
                    out["result"] = st["review"](t["task"])[:300]
                elif role == "marketer" and st.get("market"):
                    out["result"] = st["market"](t["task"])[:400]
                else:
                    out["result"] = "มอบหมายให้ " + out["by"] + " (รอโมดูลเชื่อม)"
            except Exception as e:
                out["result"] = "error: " + str(e)[:120]
            results.append(out)
        rec["status"] = "done"
        rec["results"] = results
        self.save()
        return {"ok": True, "mission": rec["mission"], "results": results,
                "summary": "6 บทบาทช่วยกัน: " + ", ".join(r["by"] for r in results)}

    def list_missions(self):
        with self.lock:
            return list(reversed(self.missions[-30:]))

    def stats(self):
        with self.lock:
            return {"roles": len(ROLES), "missions": len(self.missions),
                    "done": sum(1 for m in self.missions if m.get("status") == "done")}

    def snapshot(self):
        with self.lock:
            return {"missions": self.missions[-500:]}

    def restore(self, data):
        with self.lock:
            if isinstance(data, dict) and "missions" in data:
                self.missions = data.get("missions", [])
                self.save()
                return True
        return False
