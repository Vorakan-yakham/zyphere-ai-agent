"""Zyphere Own Brain — harvests everything we learned from real work, then
uses it to FIND WEAKNESSES and ACT (improve, re-measure, update itself).

Not a static archive: every growth round turns old lessons into new work and
new evidence. No external model is needed to remember or decide.
"""
import os, json, re, time

ROOT = os.path.dirname(os.path.abspath(__file__))
STORE = os.path.join(ROOT, "data", "zy_own_brain.json")
GROWTH = os.path.join(ROOT, "governance", "ZY_BRAIN_GROWTH.md")


def _load(path):
    try:
        return json.load(open(os.path.join(ROOT, path), encoding="utf-8"))
    except Exception:
        return None


def harvest():
    out = []
    cl = _load("data/conversation_learning.json") or {}
    for x in cl.get("log", []):
        if x.get("rule"):
            out.append({"src": "user-correction", "text":
                        str(x.get("user", ""))[:140] + " → " + str(x.get("rule", ""))[:160]})
    qa = _load("data/qa_full_audit.json") or {}
    for c in qa.get("checks", []):
        out.append({"src": "qa:" + str(c.get("verdict")),
                    "text": str(c.get("area"))[:70] + ": " + str(c.get("evidence"))[:120]})
    mt = _load("data/method_transfer.json") or {}
    for k, v in (mt.get("principles") or {}).items():
        out.append({"src": "method", "text": str(k) + ": " + str(v.get("rule", ""))[:150]})
    for f, src in [("data/image_quality_history.json", "image"),
                   ("data/media_twin.json", "media"),
                   ("data/nudge_idle.json", "nudge")]:
        d = _load(f)
        if d:
            out.append({"src": src, "text": str(d)[:200]})
    return out


def build(apply=True):
    lessons = harvest()
    kb = {"t": int(time.time()), "lessons": lessons, "count": len(lessons),
          "rule": "ความรู้เดิมใช้หาจุดอ่อน แล้วพัฒนาต่อ — ไม่ใช่เก็บไว้เฉย ๆ"}
    if apply:
        os.makedirs(os.path.dirname(STORE), exist_ok=True)
        json.dump(kb, open(STORE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return kb


def weaknesses(kb):
    text = " ".join(x.get("text", "") for x in kb.get("lessons", []))
    out = []
    if "FIX" in text or "ไม่ผ่าน" in text:
        out.append({"gap": "QA ยังมีจุดไม่ผ่าน", "action": "แก้ FIX ให้เป็น KEEP ด้วยหลักฐานใหม่",
                    "module": "qa_audit_team"})
    if "ภาพ" in text or "คมชัด" in text:
        out.append({"gap": "ภาพยังพัฒนาได้อีก", "action": "รัน image_quality_loop วัด gain ใหม่",
                    "module": "image_quality_loop"})
    if "วิดีโอ" in text:
        out.append({"gap": "วิดีโอยังพัฒนาได้อีก", "action": "รัน media_twin_track คู่ขนาน",
                    "module": "media_twin_track"})
    return out or [{"gap": "ยังไม่พบจุดอ่อนชัดเจน", "action": "สังเกตผลรอบถัดไป", "module": None}]


def grow(apply=True):
    kb = build(apply=apply)
    gaps = weaknesses(kb)
    actions = []
    for g in gaps:
        res = {"gap": g["gap"], "action": g["action"], "result": "planned"}
        mod = g.get("module")
        if mod:
            try:
                m = __import__(mod)
                r = m.run(apply=apply)
                res["result"] = "ran"
                res["evidence"] = {k: r.get(k) for k in ("keep", "fix", "status", "t")
                                   if isinstance(r, dict) and k in r}
            except Exception as e:
                res["result"] = "error:" + str(e)[:90]
        actions.append(res)
        kb.setdefault("lessons", []).append({"src": "self-growth", "text": str(res)[:220]})
    kb["rounds"] = kb.get("rounds", 0) + 1
    kb["last_actions"] = actions
    if apply:
        json.dump(kb, open(STORE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        md = ["# การเติบโตของสมอง Zyphere", "",
              "รอบ %d — ใช้ความรู้เดิมหาจุดอ่อน แล้วลงมือ + วัดผล + จำใหม่" % kb["rounds"], ""]
        for a in actions:
            md += ["## " + a["gap"], "- ทำ: " + a["action"],
                   "- ผล: " + str(a.get("result")) + " " + str(a.get("evidence", ""))[:180], ""]
        open(GROWTH, "w", encoding="utf-8").write("\n".join(md))
    return {"ok": True, "round": kb["rounds"], "actions": actions}


def ask(q, top=3):
    kb = _load("data/zy_own_brain.json") or build(False)
    words = [w for w in re.findall(r"[\u0E00-\u0E7F]{3,}|[A-Za-z]{4,}", str(q)) if len(w) > 2]
    hits = []
    for x in kb.get("lessons", []):
        s = sum(1 for w in words if w.lower() in x.get("text", "").lower())
        if s:
            hits.append((s, x))
    hits.sort(key=lambda z: -z[0])
    return {"ok": True, "engine": "zy-own-brain", "lessons": len(kb.get("lessons", [])),
            "answers": [x for _, x in hits[:top]]}


if __name__ == "__main__":
    print(json.dumps(grow(), ensure_ascii=False)[:600])
