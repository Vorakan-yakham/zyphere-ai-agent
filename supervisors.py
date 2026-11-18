"""Zyphere Supervisors — one nagger per department, not a single chief.

Each supervisor checks its own department's real state and issues a concrete
nudge with a target KPI. They run together so no department is left idle.
HONEST: nudges are recorded as files + status; they do not invent results.
"""
import os, json, time, threading

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "supervisors.json")


class Supervisor:
    def __init__(self, dept, kpi, check):
        self.dept = dept
        self.kpi = kpi
        self.check_fn = check

    def nag(self, state):
        ok, detail, action = self.check_fn(state)
        return {"dept": self.dept, "kpi": self.kpi, "ok": ok,
                "detail": detail, "action": action, "t": int(time.time())}


def _mk(dept, kpi, fn):
    return Supervisor(dept, kpi, fn)


def build():
    return [
        _mk("นักวิเคราะห์ระบบ", "ตรวจระบบ 8/8", lambda s: (
            s.get("analyst_pass", 0) >= 8,
            "ตรวจแล้ว %d/8" % s.get("analyst_pass", 0),
            "รัน systems_analyst.py ให้ครบ 8 checks" if s.get("analyst_pass", 0) < 8 else "ดูแลต่อเนื่อง")),
        _mk("ฐานข้อมูล", "ผลงานไม่หายหลัง restart", lambda s: (
            bool(s.get("db_ok")),
            "restore %s" % s.get("db_ok"),
            "ตรวจ KV + GitHub backup หลัง restart" if not s.get("db_ok") else "สำรองต่อเนื่อง")),
        _mk("โปรแกรมเมอร์", "test pass", lambda s: (
            bool(s.get("tests_ok")),
            "test %s" % s.get("tests_ok"),
            "รัน test_zyphere.py ก่อน deploy" if not s.get("tests_ok") else "deploy ต่อได้")),
        _mk("ฝ่ายวิชาการ", "46 คณะ + สาขาย่อย", lambda s: (
            s.get("branches", 0) >= 184,
            "สาขา %d" % s.get("branches", 0),
            "ขยาย FACULTY_TREE ให้ครบ 184 สาขา" if s.get("branches", 0) < 184 else "ขยายสาขาโลกต่อ")),
        _mk("ฝ่ายภาษา", "ไม่มีคำผิดในร้าน", lambda s: (
            s.get("bad_words", 0) == 0,
            "คำผิด %d" % s.get("bad_words", 0),
            "แก้กฎอันตราย + ตรวจข้อความใหม่" if s.get("bad_words", 0) else "ตรวจต่อเนื่อง")),
        _mk("ฝ่ายออกแบบผลิตภัณฑ์", "ปก + หนังสือจัดหน้า", lambda s: (
            s.get("books", 0) >= 46,
            "หนังสือ %d เล่ม" % s.get("books", 0),
            "ผลิตปกและจัดหน้าให้ครบ" if s.get("books", 0) < 46 else "ปรับ layout ต่อ")),
        _mk("ฝ่ายการตลาด", "โปรโมทหลังหนังสือเสร็จ", lambda s: (
            s.get("promos", 0) >= 46,
            "โปรโม %d" % s.get("promos", 0),
            "เขียน PROMO.md ทุกเล่ม" if s.get("promos", 0) < 46 else "เผยแพร่ต่อ")),
        _mk("ฝ่ายทดสอบ", "endpoint จริง 200", lambda s: (
            bool(s.get("live_ok")),
            "live %s" % s.get("live_ok"),
            "ตรวจ endpoint บน Render" if not s.get("live_ok") else "ตรวจต่อ")),
        _mk("ฝ่ายปฏิบัติการ", "deploy เสร็จ", lambda s: (
            bool(s.get("deploy_ok")),
            "deploy %s" % s.get("deploy_ok"),
            "trigger deploy + restart" if not s.get("deploy_ok") else "ดูแลต่อ")),
        _mk("ฝ่ายความปลอดภัย", "จ่ายเท่านั้นถึงโหลด", lambda s: (
            bool(s.get("gate_ok")),
            "gate %s" % s.get("gate_ok"),
            "ตรวจ webhook + fail-closed" if not s.get("gate_ok") else "ตรวจต่อ")),
    ]


class Supervisors:
    def __init__(self):
        self.lock = threading.RLock()
        self.log = []
        self._load()

    def _load(self):
        try:
            self.log = json.load(open(DATA, encoding="utf-8")).get("log", [])
        except Exception:
            pass

    def save(self):
        with self.lock:
            try:
                os.makedirs(os.path.dirname(DATA), exist_ok=True)
                json.dump({"log": self.log[-500:]}, open(DATA, "w", encoding="utf-8"),
                          ensure_ascii=False, indent=2)
            except Exception:
                pass

    def nag_all(self, state=None):
        state = state or {}
        results = [s.nag(state) for s in build()]
        with self.lock:
            self.log.append({"t": int(time.time()), "results": results})
        self.save()
        return {"ok": True, "supervisors": len(results),
                "working": sum(1 for r in results if not r["ok"]),
                "results": results}

    def status(self):
        last = self.log[-1]["results"] if self.log else []
        return {"ok": True, "count": len(build()), "rounds": len(self.log),
                "last": last, "log": self.log[-5:]}
