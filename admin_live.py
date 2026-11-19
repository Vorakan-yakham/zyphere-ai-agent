"""Admin Live — real-time view of what every department is actually doing.

Reads the REAL artefacts the autonomous pulses write (never invents activity).
Returns a snapshot the admin dashboard polls every few seconds.
"""
import os, json, time

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")


def _j(name, default=None):
    try:
        return json.load(open(os.path.join(DATA, name), encoding="utf-8"))
    except Exception:
        return default if default is not None else {}


def snapshot():
    now = int(time.time())
    prog = _j("department_progress.json", {})
    rows = prog.get("rows", [])

    staff = []
    for r in rows:
        age = r.get("age_hours")
        live = age is not None and age < 1.0
        staff.append({
            "name": r.get("dept"), "metric": r.get("metric"),
            "value": r.get("value"), "status": r.get("status"),
            "live": live,
            "last_seen_hours": age,
            "note": r.get("note"),
        })

    league = _j("improvement_league.json", {})
    rev = _j("revenue_autopilot.json", {})
    qa = _j("qa_supreme.json", {})
    nextd = _j("next_development.json", {})
    out = _j("outreach.json", {})
    si = _j("self_improvement.json", {})

    kpis = {
        "departments": len(staff),
        "active": sum(1 for s in staff if s["status"] == "UP"),
        "live_now": sum(1 for s in staff if s["live"]),
        "league_rounds": len(league.get("rounds", [])) if isinstance(league.get("rounds"), list) else int(league.get("rounds") or 0),
        "revenue_cycles": len(rev.get("cycles", [])) if isinstance(rev.get("cycles"), list) else int(rev.get("cycles") or 0),
        "revenue_channels": (rev["cycles"][-1].get("channels", 0)
                             if rev.get("cycles") and isinstance(rev["cycles"][-1], dict) else 0),
        "qa_passed": qa.get("passed", qa.get("failed") is False),
        "lessons": len(si.get("lessons", [])) if isinstance(si, dict) else 0,
        "outreach_published": bool(out.get("published") or out.get("ok")),
    }

    feed = []
    for s in staff:
        if s["live"]:
            feed.append({"t": now, "who": s["name"],
                         "text": "กำลังทำงาน · " + str(s["metric"]) + " = " + str(s["value"])})
    if nextd:
        feed.append({"t": nextd.get("t", now), "who": "ระบบคิดเอง",
                     "text": "เลือกเป้า " + str(nextd.get("goal_from_own_roadmap")) +
                             " → " + str(nextd.get("engine_chosen"))})
    if out:
        feed.append({"t": now, "who": "ฝ่ายรายได้",
                     "text": "เตรียมช่องทาง/เผยแพร่งานภายนอกแล้ว"})
    feed.sort(key=lambda x: -x["t"])

    return {"ok": True, "t": now, "staff": staff, "kpis": kpis,
            "feed": feed[:20],
            "next_plan": nextd.get("next_plan", []),
            "note": "ข้อมูลจากไฟล์จริงที่ pulse เขียน — ไม่ใช่สถานะปลอม"}
