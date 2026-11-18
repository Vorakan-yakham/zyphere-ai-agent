"""Zyphere Role Registry — auto-creates a department whenever a role is mentioned.

The owner says "systems analyst" -> the system registers that department,
defines how it works, what it receives, what it delivers, and who it works
with. Same for database, programmer, design, language, marketing, etc.

Persisted locally (data/roles.json), in Upstash-style snapshot, and pushed to
GitHub as DEPARTMENTS.md + departments.json so it is durable and visible.
HONEST: these are working definitions, not claims of certified staff.
"""
import os, json, time, threading, re, requests, subprocess, base64

REPO = "Vorakan-yakham/zyphere-scholar-product-pack"
BASE = "https://api.github.com/repos/" + REPO + "/contents/"

SEED = {
    "นักวิเคราะห์ระบบ": {
        "mission": "ตรวจสถาปัตยกรรม หาจุดอ่อนของระบบ และเสนอการแก้ไขที่ตรวจสอบได้",
        "inputs": ["source code", "error logs", "live endpoint results"],
        "outputs": ["SYSTEM_ANALYSIS.md", "รายการบั๊กและความเสี่ยง", "ข้อเสนอแก้ไข"],
        "workflow": ["อ่านโค้ดจริง", "รันตรวจสอบอัตโนมัติ", "จัดอันดับความรุนแรง", "เขียนรายงานลง repo"],
        "collaborators": ["โปรแกรมเมอร์", "ฐานข้อมูล", "ฝ่ายทดสอบ"],
        "kpi": ["จำนวน check ที่ผ่าน", "ไม่มี secret ฝังในโค้ด", "ไม่มี route ซ้ำ"],
    },
    "ฐานข้อมูล": {
        "mission": "ออกแบบโครงสร้างจัดเก็บ ให้ข้อมูลอยู่รอดหลัง restart และดึงกลับได้",
        "inputs": ["state ของระบบ", "KV snapshot", "ไฟล์ผลงาน"],
        "outputs": ["schema", "นโยบายสำรอง", "รายงานความต่อเนื่องของข้อมูล"],
        "workflow": ["กำหนด primary storage", "ตั้ง remote KV", "ตั้ง GitHub เป็นที่เก็บถาวร",
                     "ทดสอบ restore หลัง restart"],
        "collaborators": ["นักวิเคราะห์ระบบ", "โปรแกรมเมอร์", "ฝ่ายปฏิบัติการ"],
        "kpi": ["restore สำเร็จหลัง restart", "ไม่เสียออเดอร์", "มี backup ภายนอก"],
    },
    "โปรแกรมเมอร์": {
        "mission": "เขียนและแก้โค้ดให้ตรงตามที่สภาฯ ตกลง พร้อมทดสอบก่อนปล่อย",
        "inputs": ["สเปกจากสภาฯ", "รายงานบั๊ก", "โค้ดเดิม"],
        "outputs": ["โค้ดที่ compile ผ่าน", "regression test ที่ผ่าน", "commit และ deploy"],
        "workflow": ["อ่านสเปก", "แก้โค้ดแบบ targeted", "รัน py_compile", "รัน test", "commit/push/deploy"],
        "collaborators": ["นักวิเคราะห์ระบบ", "ฝ่ายทดสอบ", "ฝ่ายปฏิบัติการ"],
        "kpi": ["test ผ่าน 100%", "deploy สำเร็จ", "ไม่ทำลายของเดิม"],
    },
    "ฝ่ายออกแบบผลิตภัณฑ์": {
        "mission": "กำหนดโครงสร้างหน้าเว็บและเอกสารให้อ่านง่าย สวย และใช้งานได้จริง",
        "inputs": ["เนื้อหา", "ข้อกำหนดแบรนด์", "โครงสร้างเดิม"],
        "outputs": ["design system", "STORE.html", "โครงสร้างไฟล์ผลงาน"],
        "workflow": ["วิเคราะห์ผู้ใช้", "กำหนด hierarchy", "เลือกสีและตัวอักษร", "ทำ responsive", "ตรวจบนมือถือ"],
        "collaborators": ["ฝ่ายภาษา", "ฝ่ายการตลาด", "โปรแกรมเมอร์"],
        "kpi": ["หน้าเว็บเปิดได้", "มี QR และปุ่มซื้อ", "ข้อความอ่านง่าย"],
    },
    "ฝ่ายภาษา": {
        "mission": "ตรวจแก้ทุกบรรทัดของข้อความให้ถูกต้อง เป็นธรรมชาติ และน่าสนใจ",
        "inputs": ["ข้อความหน้าร้าน", "เนื้อหาหนังสือ", "บทสนทนา"],
        "outputs": ["ข้อความที่แก้แล้ว", "รายการคำที่แก้", "แนวทางการอ่าน"],
        "workflow": ["รัน LanguageMastery.correct", "ลบอักขระต่างถิ่น", "ปรับจังหวะประโยค",
                     "เพิ่มคำถาม/กรณีศึกษาให้เนื้อหาน่าสนใจ"],
        "collaborators": ["ฝ่ายออกแบบ", "ฝ่ายวิชาการ", "ฝ่ายเนื้อหา"],
        "kpi": ["ไม่มีอักขระจีนปน", "ไม่มีคำซ้ำ", "เนื้อหามีคำถามท้ายบท"],
    },
    "ฝ่ายการตลาด": {
        "mission": "ศึกษาความต้องการตลาดและกำหนดราคาให้สอดคล้องกับความยากและคุณค่า",
        "inputs": ["หัวข้อสินค้า", "สัญญาณความต้องการ", "คู่แข่ง"],
        "outputs": ["pricing.json", "tier ราคา", "เหตุผลประกอบการตั้งราคา"],
        "workflow": ["ให้คะแนนความยาก", "ให้คะแนนความน่าสนใจ", "คำนวณราคา", "บันทึกเหตุผล"],
        "collaborators": ["ฝ่ายวิชาการ", "ฝ่ายออกแบบ", "ฝ่ายขาย"],
        "kpi": ["ราคาไม่เท่ากันทุกชิ้น", "มีช่วงราคาหลายระดับ", "ตรวจสอบได้"],
    },
    "ฝ่ายวิชาการ": {
        "mission": "ขยายสาขาความรู้และตรวจความถูกต้องของเนื้อหาวิชาการ",
        "inputs": ["คณะวิชาเดิม", "หัวข้อที่ผู้ใช้กล่าวถึง"],
        "outputs": ["FACULTY_TREE.md", "สาขาย่อย", "แนวคิดหลักของแต่ละสาขา"],
        "workflow": ["รับหัวข้อ", "แตกเป็นสาขาย่อย", "ระบุแนวคิดหลัก", "เขียนเป็นต้นไม้ความรู้"],
        "collaborators": ["ฝ่ายภาษา", "ฝ่ายเนื้อหา", "ฝ่ายการตลาด"],
        "kpi": ["ทุกคณะมีสาขาย่อย", "แต่ละสาขามีแนวคิดหลัก", "ขยายอัตโนมัติ"],
    },
    "ฝ่ายทดสอบ": {
        "mission": "ตรวจว่าสิ่งที่ปล่อยออกมาทำงานจริง ไม่ใช่แค่ตัวเลข",
        "inputs": ["โค้ด", "endpoint", "ไฟล์ที่สร้าง"],
        "outputs": ["test ที่ผ่าน", "รายงานความล้มเหลว", "หลักฐานการทดสอบจริง"],
        "workflow": ["รัน regression", "เรียก endpoint จริง", "ตรวจไฟล์ที่ดาวน์โหลดได้", "รายงานผล"],
        "collaborators": ["โปรแกรมเมอร์", "นักวิเคราะห์ระบบ"],
        "kpi": ["ALL REGRESSION TESTS PASSED", "endpoint ตอบ 200", "ไฟล์เปิดได้"],
    },
    "ฝ่ายปฏิบัติการ": {
        "mission": "ดูแลระบบให้ทำงานต่อเนื่องบน Render และกู้คืนเมื่อ restart",
        "inputs": ["service id", "deploy status", "environment variables"],
        "outputs": ["deploy สำเร็จ", "restart สำเร็จ", "state ที่ restored"],
        "workflow": ["ตรวจ deploy", "restart เมื่อต้องการ", "ตั้ง env var", "ตรวจ health"],
        "collaborators": ["ฐานข้อมูล", "โปรแกรมเมอร์", "ฝ่ายทดสอบ"],
        "kpi": ["health 200", "ผลงานไม่หายหลัง restart", "env ครบ"],
    },
    "ฝ่ายความปลอดภัย": {
        "mission": "ป้องกันการอนุมัติโดยไม่ได้รับอนุญาตและการรั่วไหลของความลับ",
        "inputs": ["token", "payment webhook", "source code"],
        "outputs": ["นโยบาย fail-closed", "รายการความเสี่ยง", "gateway ที่ยืนยันเงินจริง"],
        "workflow": ["ตรวจ fail-open", "บังคับ webhook", "สแกน secret", "ตรวจ permission"],
        "collaborators": ["นักวิเคราะห์ระบบ", "ฐานข้อมูล", "โปรแกรมเมอร์"],
        "kpi": ["ไม่ approve ได้โดยไม่มี token", "ไม่มี secret ในโค้ด"],
    },
}


class RoleRegistry:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.roles = dict(SEED)
        self._load()

    def _load(self):
        try:
            d = json.load(open(self.path, encoding="utf-8"))
            for k, v in (d.get("roles") or {}).items():
                self.roles.setdefault(k, v)
        except Exception:
            pass

    def save(self):
        with self.lock:
            try:
                os.makedirs(os.path.dirname(self.path), exist_ok=True)
                json.dump({"roles": self.roles, "t": int(time.time())},
                          open(self.path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            except Exception:
                pass

    def ensure(self, role):
        """Auto-create a department when a role is mentioned by the owner."""
        role = re.sub(r"\s+", " ", str(role or "").strip())[:60]
        if not role:
            return {"ok": False, "error": "empty role"}
        if role in self.roles:
            return {"ok": True, "created": False, "role": role, "dept": self.roles[role]}
        dept = {
            "mission": "ทำหน้าที่ " + role + " ให้กับระบบตามที่เจ้าของระบบมอบหมาย",
            "inputs": ["งานที่เจ้าของระบบมอบหมาย", "ข้อมูลจากสายงานอื่น"],
            "outputs": ["ผลงานที่ตรวจสอบได้", "รายงานส่งมอบ"],
            "workflow": ["รับงาน", "วิเคราะห์", "ดำเนินการ", "ตรวจสอบ", "ส่งมอบผลจริง"],
            "collaborators": ["นักวิเคราะห์ระบบ", "ฝ่ายทดสอบ"],
            "kpi": ["มีผลงานจริง", "ตรวจสอบได้", "ไม่กล่าวอ้างเกินจริง"],
            "auto_created": True,
        }
        self.roles[role] = dept
        self.save()
        return {"ok": True, "created": True, "role": role, "dept": dept}

    def list(self):
        return {"ok": True, "count": len(self.roles), "roles": self.roles}

    def push(self):
        doc = ["# สายงานและบทบาท Zyphere (ทำงานอัตโนมัติเมื่อกล่าวถึง)", "",
               "จำนวนสายงาน: %d" % len(self.roles), "",
               "เจ้าของระบบกล่าวถึงตำแหน่งใด ระบบจะสร้างสายงานนั้นทันที ",
               "พร้อมภารกิจ ข้อมูลเข้า ผลส่งมอบ วิธีทำงาน และผู้ทำงานร่วม ", ""]
        for name, d in self.roles.items():
            doc += ["## " + name, "",
                    "- **ภารกิจ**: " + d.get("mission", ""),
                    "- **ข้อมูลเข้า**: " + ", ".join(d.get("inputs", [])),
                    "- **ผลส่งมอบ**: " + ", ".join(d.get("outputs", [])),
                    "- **วิธีทำงาน**: " + " → ".join(d.get("workflow", [])),
                    "- **ทำงานร่วมกับ**: " + ", ".join(d.get("collaborators", [])),
                    "- **ตัวชี้วัด**: " + ", ".join(d.get("kpi", [])), ""]
        tok = os.environ.get("GH_TOKEN", "") or os.environ.get("GITHUB_TOKEN", "")
        if not tok:
            try:
                tok = subprocess.run(["gh", "auth", "token"], capture_output=True,
                                     text=True, timeout=15).stdout.strip()
            except Exception:
                pass
        headers = {"Authorization": "Bearer " + tok,
                   "Accept": "application/vnd.github+json"} if tok else {}
        files = [("DEPARTMENTS.md", "\n".join(doc)),
                 ("departments.json", json.dumps({"roles": self.roles, "t": int(time.time())},
                                                 ensure_ascii=False, indent=2))]
        ok = err = 0
        for path, content in files:
            sha = None
            try:
                g = requests.get(BASE + path, headers=headers, timeout=15)
                if g.ok:
                    sha = (g.json() or {}).get("sha")
            except Exception:
                pass
            payload = {"message": "Role registry auto-update " + str(int(time.time())),
                       "content": base64.b64encode(content.encode("utf-8")).decode(), "branch": "main"}
            if sha:
                payload["sha"] = sha
            try:
                r = requests.put(BASE + path, headers=headers, json=payload, timeout=30)
                if r.ok:
                    ok += 1
                else:
                    err += 1
                    print("ERR", path, r.status_code, str(r.text)[:90])
            except Exception as e:
                err += 1
                print("ERR", path, str(e)[:80])
        return {"ok": True, "pushed": ok, "errors": err, "count": len(self.roles)}


if __name__ == "__main__":
    import sys
    rg = RoleRegistry(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "data", "roles.json"))
    for r in sys.argv[1:]:
        print(rg.ensure(r))
    print(rg.push())
