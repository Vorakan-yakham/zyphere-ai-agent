"""Zyphere Quality Operations: PDCA-based excellence framework.

This module enforces quality gates (uniqueness, Thai-first, structure, design,
payment, persistence, learning) via a continuous Plan-Do-Check-Act cycle.

Operations:
1. Measure: Evaluate metrics against defined quality thresholds.
2. Learn: Generate remediation tasks for non-compliant areas.
3. Report: Persist findings to QUALITY_REPORT.md and quality_ops.json.
4. Enforce: Block deployment/publishing if gates fail.

Note: All operations are strictly read-only regarding external repo structure
except for the mandatory generation of quality artifacts."""
import os
import json
import time
import threading
import subprocess
import base64
import requests

REPO = "Vorakan-yakham/zyphere-scholar-product-pack"
BASE = f"https://api.github.com/repos/{REPO}/contents/"
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "quality_ops.json")

# department -> (quality metric key, target, learning curriculum)
DEPTS = {
    "ฝ่ายวิชาการ": ("knowledge_depth", 85, [
        "การแยกแนวคิดหลักออกจากรายละเอียด", "การจัดลำดับความรู้แบบขั้นบันได",
        "การเชื่อมสาขาวิชาข้ามคณะ", "การอ้างอิงแหล่งที่ตรวจสอบได้"]),
    "ฝ่ายภาษา": ("language_quality", 90, [
        "กฎแก้คำที่ไม่ทำลายคำถูกต้อง", "เครื่องหมายวรรคตอนภาษาไทย",
        "การเรียงลำดับคำและประโยค", "การเขียนให้ผู้อ่านอ่านจบ"]),
    "ฝ่ายออกแบบผลิตภัณฑ์": ("design_quality", 85, [
        "Typography hierarchy", "Negative space และ grid",
        "การออกแบบปกแบบหนังสือ ไม่ใช่โปสเตอร์", "A5 margin และ callout box"]),
    "ฝ่ายผลิตหนังสือ": ("content_quality", 90, [
        "8-12 บทต่อเล่ม", "หนึ่งแนวคิดต่อบท",
        "แบบฝึกหัดไม่ซ้ำ", "Uniqueness index >= 85%"]),
    "ฝ่ายการตลาด": ("value_pricing", 85, [
        "Value-based pricing", "การอธิบายเหตุผลราคา",
        "การเขียนโพสต์ที่ไม่กล่าวอ้างเกินจริง", "การวัดผลการคลิกจริง"]),
    "ฝ่ายทดสอบ": ("test_coverage", 95, [
        "Regression test", "ตรวจ endpoint จริง",
        "ตรวจไฟล์ที่ดาวน์โหลดได้", "ตรวจหา copy-paste"]),
    "นักวิเคราะห์ระบบ": ("system_health", 95, [
        "Import order", "Route ไม่ซ้ำ", "Fail-closed admin",
        "ไม่มี secret ในโค้ด"]),
    "ฐานข้อมูล": ("persistence", 95, [
        "Remote KV restore", "GitHub durable store",
        "ทดสอบ restart", "สำรองอัตโนมัติ"]),
    "โปรแกรมเมอร์": ("build_quality", 95, [
        "py_compile", "targeted edit", "deploy สำเร็จ", "ไม่ทำลายของเดิม"]),
    "ฝ่ายปฏิบัติการ": ("uptime", 95, [
        "health 200", "restart เมื่อจำเป็น", "env ครบ", "ตรวจ deploy"]),
}


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
    p = {"message": "Quality cycle " + str(int(time.time())),
         "content": base64.b64encode(content.encode("utf-8")).decode(), "branch": "main"}
    if sha:
        p["sha"] = sha
    r = requests.put(BASE + path, headers=h, json=p, timeout=30)
    return r.ok, r.status_code


class QualityOps:
    def __init__(self):
        self.lock = threading.RLock()
        self.history = []
        self._load()

    def _load(self):
        try:
            self.history = json.load(open(DATA, encoding="utf-8")).get("history", [])
        except Exception:
            pass

    def save(self):
        with self.lock:
            try:
                os.makedirs(os.path.dirname(DATA), exist_ok=True)
                json.dump({"history": self.history[-100:]}, open(DATA, "w", encoding="utf-8"),
                          ensure_ascii=False, indent=2)
            except Exception:
                pass

    def measure(self, state=None):
        """Score each department from REAL signals supplied by the pipeline."""
        s = state or {}
        scores = {
            "knowledge_depth": s.get("knowledge_depth", 0),
            "language_quality": s.get("language_quality", 0),
            "design_quality": s.get("design_quality", 0),
            "content_quality": s.get("content_quality", 0),
            "value_pricing": s.get("value_pricing", 0),
            "test_coverage": 95 if s.get("tests_ok") else 0,
            "system_health": s.get("analyst_pass", 0) * 9,
            "persistence": 95 if s.get("db_ok") else 0,
            "build_quality": 95 if s.get("deploy_ok") else 0,
            "uptime": 95 if s.get("live_ok") else 0,
        }
        rows = []
        for dept, (key, target, curriculum) in DEPTS.items():
            score = min(100, int(scores.get(key, 0)))
            rows.append({"dept": dept, "metric": key, "score": score,
                         "target": target, "passed": score >= target,
                         "learning_topics": curriculum,
                         "action": ("รักษามาตรฐานและพัฒนาต่อ" if score >= target
                                    else "เรียนรู้หัวข้อต่อไปนี้แล้ววัดใหม่")})
        return rows

    def cycle(self, state=None, learn_fn=None):
        rows = self.measure(state)
        rec = {"t": int(time.time()), "rows": rows,
               "passed": sum(1 for r in rows if r["passed"]),
               "total": len(rows)}
        with self.lock:
            self.history.append(rec)
        self.save()
        # PDCA Act: issue learning tasks to failing departments
        tasks = []
        for r in rows:
            if not r["passed"]:
                for topic in r["learning_topics"][:2]:
                    if learn_fn:
                        try:
                            learn_fn(topic, "quality:" + r["dept"])
                        except Exception:
                            pass
                    tasks.append({"dept": r["dept"], "topic": topic})
        rec["learning_tasks"] = tasks
        self.publish(rec)
        return {"ok": True, **rec}

    def publish(self, rec):
        prev = self.history[-2]["rows"] if len(self.history) >= 2 else []
        old = {r["dept"]: r["score"] for r in prev}
        md = ["# รายงานคุณภาพต่อเนื่อง Zyphere (PDCA)", "",
              "รอบที่ %d · เวลา %s" % (len(self.history),
                                   time.strftime("%Y-%m-%d %H:%M", time.localtime(rec["t"]))), "",
              "ผ่านเกณฑ์ **%d/%d** แผนก" % (rec["passed"], rec["total"]), "",
              "| แผนก | ตัวชี้วัด | คะแนน | เป้า | ผล | เปลี่ยน |", "|---|---|---|---|---|---|"]
        for r in rec["rows"]:
            delta = r["score"] - old.get(r["dept"], r["score"])
            md.append("| %s | %s | %d | %d | %s | %+d |" %
                      (r["dept"], r["metric"], r["score"], r["target"],
                       "ผ่าน" if r["passed"] else "ต้องพัฒนา", delta))
        md += ["", "## งานที่ต้องเรียนรู้รอบนี้", ""]
        for t in rec.get("learning_tasks", []):
            md.append("- **%s**: %s" % (t["dept"], t["topic"]))
        md += ["", "## หลักการบริหาร", "",
               "Plan ตั้งเป้าคุณภาพ → Do ผลิต → Check วัดจริง → Act สั่งเรียนรู้และปรับ ",
               "ห้ามเผยแพร่หนังสือหรือโปรโมทหากฝ่ายผลิตไม่ผ่านเกณฑ์คุณภาพ", ""]
        put("QUALITY_REPORT.md", "\n".join(md))
        put("quality_ops.json", json.dumps({"history": self.history[-50:]},
                                           ensure_ascii=False, indent=2))

    def status(self):
        last = self.history[-1] if self.history else None
        return {"ok": True, "rounds": len(self.history),
                "last": last, "departments": len(DEPTS)}

    def gate_ok(self):
        """Store/marketing may publish only when ALL quality gates pass."""
        if not self.history:
            return False
        return all(r["passed"] for r in self.history[-1]["rows"])


QOPS = QualityOps()
