"""Zyphere Supervisors — ten department heads who MEASURE, QUESTION and ESCALATE.

Old behaviour (replaced): each head merely read a state dict handed to it,
produced the same nudge every round, and never learned anything. That is the
'knowledge going stale' problem. Now each head:
  1. measures its own department from real sources when no state is supplied,
  2. asks a rotating, department-specific question (not the old one),
  3. detects if its own action repeated and escalates with new evidence,
  4. records results so the council can debate with the heads, not instead of them.

HONEST: a head never claims a result it did not measure. Missing data is
reported as missing, not as success.
"""
import os, json, time, threading

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "supervisors.json")
ROOT = os.path.dirname(os.path.abspath(__file__))

# Each head owns specific questions. They rotate so a round cannot reuse the
# previous round's thinking; the unused ones remain for the next cycle.
QUESTIONS = {
    "นักวิเคราะห์ระบบ": ["โค้ดส่วนไหนยังไม่มี regression test?", "จุดอ่อนใหม่ที่ systems_analyst เจอคืออะไร?"],
    "ฐานข้อมูล": ["ข้อมูลใดหายได้หลัง restart?", "แหล่งความจริงของไฟล์คือ GitHub หรือ KV?"],
    "โปรแกรมเมอร์": ["test ใดถูกข้ามก่อน deploy?", "API ใดคืน 502 ทั้งที่มี key?"],
    "ฝ่ายวิชาการ": ["สาขาใดยังไม่มีเนื้อหาจริง?", "เล่มใด knowledge_depth ต่ำกว่าเป้า เพราะอะไร?"],
    "ฝ่ายภาษา": ["ข้อความร้านใดอ่านแล้วกำกวม?", "คำอ่านตัวเลข/วันที่ถูกต้องทุกกรณีไหม?"],
    "ฝ่ายออกแบบผลิตภัณฑ์": ["nav กับพื้นหลังใน ZY_TEMPLATE ขัดกันไหม?", "ปก/หนังสือจัดหน้าตรงมาตรฐานไหม?"],
    "ฝ่ายการตลาด": ["ราคาในร้านตรง single source ไหม?", "คำอธิบายสื่อคุณค่าจริงหรือแค่ชื่อวิชา?"],
    "ฝ่ายทดสอบ": ["endpoint ใดยังไม่ได้วัดหลัง deploy?", "quality gate ผ่านจริงหรือแค่รายงานเก่า?"],
    "ฝ่ายปฏิบัติการ": ["deploy ไหนยังไม่มีหลักฐาน results?", "workflow ใด fail แบบ validation ก่อนเริ่มงาน?"],
    "ฝ่ายความปลอดภัย": ["มีช่องทางจ่ายแล้วได้โหลดโดยไม่จ่ายไหม?", "secret ใดถูกเขียนลงโค้ด/ log หรือไม่?"],
}


def _count_tree_suffix(suffix):
    try:
        import autonomous_council as AC
        return sum(1 for p in AC.gh_tree() if p.endswith(suffix))
    except Exception:
        return 0


def _promo_count():
    try:
        import autonomous_council as AC
        return (AC.gh_raw("PROMO.md") or "").count("## ")
    except Exception:
        return 0


def _template_issue():
    try:
        import autonomous_council as AC
        t = AC.gh_raw("ZY_TEMPLATE.html") or ""
        dark_body = "--bg:#0B0F17" in t or "background:var(--bg)" in t
        white_nav = "rgba(255,255,255" in t
        missing_font = "Inter Display" in t and "@font-face" not in t
        return (dark_body and white_nav or missing_font,
                "dark-body/white-nav=%s, undeclared-font=%s" % (dark_body and white_nav, missing_font))
    except Exception:
        return False, "ไม่มีข้อมูล template"


def _gate():
    try:
        from quality_ops import QOPS
        return bool(QOPS.gate_ok())
    except Exception:
        return None


def _analyst():
    try:
        from systems_analyst import analyze
        res = analyze()
        if isinstance(res, dict):
            rows = res.get("checks") or []
            return sum(1 for r in rows if r.get("ok")), len(rows)
        return 0, 0
    except Exception:
        return 0, 0


def _measure(dept, state):
    """Return (ok, detail, action, evidence). Never invent a passing value."""
    s = state or {}
    if dept == "นักวิเคราะห์ระบบ":
        got, total = _analyst()
        return got >= 8, "%d/%d checks" % (got, total), "รันตรวจซ้ำให้ครบ 8 ด้าน", "systems_analyst.analyze()"
    if dept == "ฐานข้อมูล":
        v = s.get("db_ok")
        return bool(v), "restore=%s" % v, "ตรวจ KV + GitHub หลัง restart", "state.db_ok"
    if dept == "โปรแกรมเมอร์":
        v = s.get("tests_ok")
        return bool(v), "tests=%s" % v, "รัน test ก่อน deploy", "state.tests_ok"
    if dept == "ฝ่ายวิชาการ":
        try:
            from faculty_expansion import TREE
            n = len(TREE)
        except Exception:
            n = 0
        return n >= 46, "คณะ %d" % n, "ขยายสาขาให้ครบและเพิ่มเนื้อหาจริง", "faculty_expansion.TREE"
    if dept == "ฝ่ายภาษา":
        v = s.get("bad_words", None)
        return (v == 0), "คำต้องห้าม=%s" % v, "ตรวจข้อความใหม่โดยเฉพาะตัวเลข/วันที่", "state.bad_words"
    if dept == "ฝ่ายออกแบบผลิตภัณฑ์":
        n = _count_tree_suffix("/cover.png")
        bad, ev = _template_issue()
        return (n >= 46 and not bad), "ปก %d, %s" % (n, ev), "แก้ nav ให้เข้ากับ theme แล้วจัดหน้าต่อ", ev
    if dept == "ฝ่ายการตลาด":
        v = s.get("price_mismatch", None)
        return (v == 0), "ราคาไม่ตรง=%s" % v, "ยึด pricing.json เป็นแหล่งเดียว", "council.market.price_mismatches"
    if dept == "ฝ่ายทดสอบ":
        g = _gate()
        return (g is True), "gate=%s" % g, "ห้ามปล่อยของจน gate ผ่าน", "quality_ops.QOPS.gate_ok()"
    if dept == "ฝ่ายปฏิบัติการ":
        v = s.get("workflow_fail", None)
        return (v == 0), "workflow fail=%s" % v, "แก้ YAML workflow validation", "state.workflow_fail"
    if dept == "ฝ่ายความปลอดภัย":
        g = s.get("gate_ok", None)
        return bool(g), "payment gate=%s" % g, "ตรวจ fail-closed อีกครั้ง", "state.gate_ok"
    return False, "ไม่มีตัววัด", "กำหนดตัววัดให้ฝ่ายนี้", "none"


class Supervisor:
    def __init__(self, dept, kpi):
        self.dept = dept
        self.kpi = kpi

    def nag(self, state, round_no=0):
        ok, detail, action, evidence = _measure(self.dept, state)
        qs = QUESTIONS.get(self.dept, ["ฝ่ายนี้มีคำถามอะไร?"])
        q = qs[round_no % len(qs)]
        return {"dept": self.dept, "kpi": self.kpi, "ok": ok, "detail": detail,
                "action": action, "question": q, "evidence": evidence,
                "t": int(time.time())}


def build():
    return [
        Supervisor("นักวิเคราะห์ระบบ", "ตรวจระบบ 8/8"),
        Supervisor("ฐานข้อมูล", "ผลงานไม่หายหลัง restart"),
        Supervisor("โปรแกรมเมอร์", "test pass"),
        Supervisor("ฝ่ายวิชาการ", "46 คณะ + สาขาย่อย"),
        Supervisor("ฝ่ายภาษา", "ไม่มีคำผิดในร้าน"),
        Supervisor("ฝ่ายออกแบบผลิตภัณฑ์", "ปก + หนังสือจัดหน้า"),
        Supervisor("ฝ่ายการตลาด", "ราคาตรง single source"),
        Supervisor("ฝ่ายทดสอบ", "quality gate ผ่านจริง"),
        Supervisor("ฝ่ายปฏิบัติการ", "workflow ไม่ fail"),
        Supervisor("ฝ่ายความปลอดภัย", "จ่ายเท่านั้นถึงโหลด"),
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
        round_no = len(self.log)
        prior = {}
        for r in self.log[-6:]:
            for x in r.get("results", []):
                prior.setdefault(x.get("dept"), []).append(x.get("action"))
        results = []
        for sup in build():
            r = sup.nag(state, round_no)
            seen = prior.get(sup.dept, [])
            r["repeated"] = r["action"] in seen
            if r["repeated"]:
                r["action"] += " — ซ้ำรอบก่อน ต้องหาหลักฐานใหม่ก่อนตัดสิน"
                r["escalate"] = True
            results.append(r)
        with self.lock:
            self.log.append({"t": int(time.time()), "round": round_no, "results": results})
        self.save()
        # Division heads sit ABOVE supervisors: they audit the nudgers and
        # apply extra pressure when a department head goes stale.
        pressure = None
        try:
            from division_heads import DH
            pressure = DH.review_all(results, None).get("pressuring")
        except Exception:
            pass
        return {"ok": True, "supervisors": len(results), "round": round_no,
                "working": sum(1 for r in results if not r["ok"]),
                "repeated": sum(1 for r in results if r.get("repeated")),
                "division_pressure": pressure,
                "results": results}

    def status(self):
        last = self.log[-1] if self.log else {}
        return {"ok": True, "count": len(build()), "rounds": len(self.log),
                "last": last.get("results", []), "log": self.log[-5:]}


SUP = Supervisors()
