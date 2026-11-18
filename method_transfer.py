"""Zyphere Method Transfer — encode the assistant's working method into Zyphere.

Cannot copy model weights. CAN transfer: decision rules, debugging heuristics,
quality standards, and lessons from every development action. These are written
into LocalBrain + DevBrain and a human-readable METHOD_TRANSFER.md so the
transfer is auditable.

HONEST: this is methodology transfer, not a claim of copying an LLM.
"""
import os, json, time, threading, subprocess, base64, requests

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "governance", "METHOD_TRANSFER.md")
DATA = os.path.join(ROOT, "data", "method_transfer.json")

METHOD = {
    "diagnose_before_build": {
        "rule": "ก่อนเพิ่มฟีเจอร์ ต้องตรวจโค้ด/endpoint/jริงก่อนเสมอ",
        "steps": ["อ่านโค้ดจริง", "เทสต์ endpoint จริง", "หาสาเหตุ root cause",
                  "แก้แบบ targeted", "รัน test", "commit/deploy"],
        "why": "การเดาสาเหตุทำให้แก้ผิดจุดซ้ำ ๆ (import order, route ผิดฝั่ง, ตัวแปรชนกัน)",
    },
    "quality_over_count": {
        "rule": "ห้ามใช้จำนวนไฟล์/บท/แผนกเป็นตัวชี้วัดความสำเร็จ",
        "steps": ["วัด uniqueness", "เช็กการอ้างอิง", "เช็กว่ามีไฟล์จริง",
                  "QA gate ต้องผ่านก่อนปล่อย"],
        "why": "70 บทที่ก็อปปี้กันไม่ใช่หนังสือ; QA เดิมผ่านของไม่ดีเพราะตรวจแค่จำนวน",
    },
    "durable_storage": {
        "rule": "Render disk หายได้ — ใช้ GitHub/Remote KV เป็นแหล่งความจริง",
        "steps": ["เขียน local", "push GitHub", "อ่านคืนจาก GitHub ก่อน local cache"],
        "why": "หลายครั้งข้อมูลเป็น 0 บน Live เพราะRender restart",
    },
    "multi_perspective": {
        "rule": "สมองเดียวไม่ครบ — ใช้ ensemble + แหล่งภายนอก + หลายแผนก",
        "steps": ["ถาม ensemble", "อ่านแหล่งจริง (Scrum Guide, Google SEO)",
                  "ให้แต่ละฝ่าย review", "สังเคราะห์"],
        "why": "Wikipedia ไม่ละเอียดพอ; คำตอบ单项ไม่ครบทุกสาขา",
    },
    "honest_reporting": {
        "rule": "ห้าม claim สิ่งที่ไม่มีจริง",
        "steps": ["แยก 'มีโค้ด' ออกจาก 'มีปุ่ม'", "ระบุ gaps ตรง ๆ",
                  "แสดง before/after", "ไม่สร้างยอดขายปลอม"],
        "why": "ผู้ใช้ตรวจได้ทุกครั้ง — การอ้างเกินจริงทำให้เสียความเชื่อใจ",
    },
    "self_improvement_loop": {
        "rule": "ทุกแผนกต้องเรียนรู้→กระทำ→วัดผล→บันทึก continuously",
        "steps": ["measure", "หา gap", "study", "act", "re-measure", "log"],
        "why": "หัวหน้าต้องจี้เอง ไม่ใช่รอคำสั่ง",
    },
    "tooling_reality": {
        "rule": "ความรู้ไม่พอ — ต้องมีเครื่องมือที่สร้างไฟล์จริง",
        "steps": ["หา binary จริง (imageio-ffmpeg)", "ทดสอบสร้างไฟล์",
                  "ตรวจว่าโหลดได้", "ระบุสิ่งที่ยังทำไม่ได้"],
        "why": "มี data เยอะแต่ video/music ยังสร้างไม่ได้เพราะไม่มี engine ที่ทำงานจริง",
    },
    "collaboration": {
        "rule": "ทุกการพัฒนาต้องสอน Zyphere พร้อมกัน",
        "steps": ["record action", "feed LocalBrain/DevBrain", "publish audit log"],
        "why": "ผู้ใช้ต้องการให้ Zyphere เก่งไปพร้อมกัน",
    },
}


def token():
    t = os.environ.get("GH_TOKEN", "") or os.environ.get("GITHUB_TOKEN", "")
    if not t:
        t = subprocess.run(["gh", "auth", "token"], capture_output=True,
                           text=True, timeout=15).stdout.strip()
    return t


def push():
    try:
        h = {"Authorization": "Bearer " + token(), "Accept": "application/vnd.github+json"}
        url = "https://api.github.com/repos/Vorakan-yakham/zyphere-scholar-product-pack/contents/governance/METHOD_TRANSFER.md"
        sha = None
        g = requests.get(url, headers=h, timeout=15)
        if g.ok:
            sha = (g.json() or {}).get("sha")
        text = open(OUT, encoding="utf-8").read()
        p = {"message": "Method transfer " + str(int(time.time())),
             "content": base64.b64encode(text.encode("utf-8")).decode(), "branch": "main"}
        if sha:
            p["sha"] = sha
        r = requests.put(url, headers=h, json=p, timeout=30)
        return r.ok, r.status_code
    except Exception as e:
        return False, str(e)[:80]


class MethodTransfer:
    def __init__(self):
        self.lock = threading.RLock()

    def status(self):
        return {"ok": True, "principles": len(METHOD),
                "note": "ถ่ายวิธีคิด/วิธีทำงาน — ไม่ใช่การก็อปปี้โมเดล"}

    def apply(self):
        taught = 0
        for key, v in METHOD.items():
            lesson = (key.replace("_", " ") + ": " + v["rule"] + " | " +
                      " → ".join(v["steps"]) + " | " + v["why"])
            try:
                from local_brain import LocalBrain
                from dev_brain import DevBrain
                lb = LocalBrain(os.path.join(ROOT, "data", "local_brain.json"))
                db = DevBrain(os.path.join(ROOT, "data", "dev_brain.json"))
                lb.learn_text(lesson, source="method-transfer")
                db.experience(lesson, role="method-transfer")
                taught += 1
            except Exception:
                pass
        md = ["# การถ่ายวิธีการทำงานเข้าสู่ Zyphere", "",
              "ถ่าย **วิธีคิด/วิธีทำงาน/บทเรียน** ไม่ใช่น้ำหนักโมเดล", "",
              "จำนวนหลักการ: %d" % len(METHOD), ""]
        for k, v in METHOD.items():
            md += ["## " + k.replace("_", " "), "",
                   "- หลักการ: " + v["rule"],
                   "- ขั้นตอน: " + " → ".join(v["steps"]),
                   "- เหตุผล: " + v["why"], ""]
        md += ["## ข้อจำกัด", "",
               "ไม่ได้ก็อปปี้โมเดล — เป็นการสอนเชิงสัญลักษณ์ผ่าน LocalBrain/DevBrain", ""]
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        open(OUT, "w", encoding="utf-8").write("\n".join(md))
        json.dump({"principles": METHOD, "t": int(time.time())},
                  open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        ok, code = push()
        return {"ok": True, "taught": taught, "published": ok, "code": code}


MT = MethodTransfer()
