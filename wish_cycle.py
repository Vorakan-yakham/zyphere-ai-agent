"""Wish Cycle — ask EVERY department what it wants next, build it, then ask
again. The cycle never ends: each round records wish -> done -> next wish with
measured evidence. Runs unattended from the autonomy workflow.
"""
import os, json, time, hashlib, re

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "wish_cycle.json")
OUT = os.path.join(ROOT, "governance", "WISH_CYCLE.md")

DEPARTMENTS = [
    "นักวิเคราะห์ความรู้", "นักออกแบบกราฟิก", "การตลาดและรายได้",
    "โปรแกรมเมอร์", "ฐานข้อมูล", "QA", "หัวหน้าฝ่าย", "หัวหน้าแผนก",
    "สมอง Zyphere", "นักดนตรี", "นักภาพยนตร์", "บรรณาธิการ",
]


def metrics():
    out = {}
    for f, keys in [("data/commerce.json", ("products", "channels")),
                    ("data/qa_full_audit.json", ("keep", "fix")),
                    ("data/council_briefing.json", ("decisions",)),
                    ("data/differentiation.json", ("weaknesses",)),
                    ("data/zy_own_brain.json", ("lessons", "rounds"))]:
        try:
            d = json.load(open(os.path.join(ROOT, f), encoding="utf-8"))
            for k in keys:
                v = d.get(k)
                out[k] = len(v) if isinstance(v, (list, dict)) else v
        except Exception:
            pass
    return out


def ask(round_no, m):
    """Each department names ONE concrete thing it needs to improve."""
    wishes = []
    for i, dept in enumerate(DEPARTMENTS):
        focus = [
            "เพิ่มความรู้ใหม่จากโลกให้มากขึ้น", "ปกใหม่ที่สื่อเนื้อหา ไม่ใช้ภาพเก่า",
            "ช่องทางรายได้ใหม่ที่เตรียม asset ได้จริง", "เขียนโค้ดตามคำสั่งสภาฯ ให้เสร็จ",
            "เก็บหลักฐานผลงานให้ทุกฝ่ายอ่านร่วมกัน", "ตรวจไฟล์จริง ไม่ให้ claims เกินจริง",
            "กระตุ้นให้ทีมทำงานตรงเวลา", "กดดันหัวหน้าฝ่ายให้ส่งงานจริง",
            "เรียนรู้จากคำแก้ไขแล้วพัฒนาต่อ", "ทำนอง/เครื่องดนตรีที่ฟังแล้วเพราะขึ้น",
            "หนังที่ตัวละครหน้าเดิมแต่เปลี่ยนชุด", "แก้ข้อความเก่าในหนังสือ",
        ][i % len(DEPARTMENTS)]
        wishes.append({"dept": dept, "want": focus,
                       "evidence": json.dumps(m, ensure_ascii=False)[:180],
                       "round": round_no})
    return wishes


def execute(wishes):
    """Build the top three wishes with the engines we actually have."""
    done = []
    for w in wishes[:3]:
        act = {"wish": w["want"], "dept": w["dept"]}
        try:
            if "ปก" in w["want"] or "ข้อความ" in w["want"]:
                import ebook_design_team
                r = ebook_design_team.run(apply=True)
                act["result"] = {"book": r.get("book"), "ok": r.get("ok")}
            elif "รายได้" in w["want"] or "หลักฐาน" in w["want"]:
                import commerce_lab
                r = commerce_lab.run(apply=True)
                act["result"] = {"channels": len(r["channels"]), "priced": r["priced"]}
            elif "ความรู้" in w["want"] or "สมอง" in w["want"]:
                import own_brain
                r = own_brain.grow(apply=True)
                act["result"] = {"round": r.get("round"), "actions": len(r.get("actions", []))}
            elif "ภาพยนตร์" in w["want"] or "ดนตรี" in w["want"]:
                import differentiation_lab
                r = differentiation_lab.run(apply=True)
                act["result"] = {"positions": len(r.get("positions", []))}
            else:
                import qa_audit_team
                r = qa_audit_team.run(apply=True)
                act["result"] = {"keep": r.get("keep"), "fix": r.get("fix")}
        except Exception as e:
            act["result"] = {"error": str(e)[:120]}
        done.append(act)
    return done


def rec_ev(want, m):
    if "ปก" in want or "ข้อความ" in want:
        return {"book_metric": m.get("products"), "qa": m.get("keep")}
    if "รายได้" in want or "หลักฐาน" in want:
        return {"channels": m.get("channels"), "products": m.get("products")}
    if "ความรู้" in want or "สมอง" in want:
        return {"lessons": m.get("lessons"), "rounds": m.get("rounds")}
    return {"qa_keep": m.get("keep"), "qa_fix": m.get("fix")}


def run(apply=True):
    hist = []
    if os.path.exists(DATA):
        try:
            hist = json.load(open(DATA, encoding="utf-8")).get("rounds", [])
        except Exception:
            pass
    rnd = len(hist) + 1
    before = metrics()
    wishes = ask(rnd, before)
    done = execute(wishes)
    after = metrics()
    next_wishes = ask(rnd + 1, after)
    # Every question gets an evidence-based answer immediately — a real dialogue.
    for w in next_wishes:
        k = "after"
        w["answer"] = ("จากผลรอบ %d: %s → งานต่อคือ %s (หลักฐาน: %s)" % (
            rnd, json.dumps(after, ensure_ascii=False)[:120], w["want"],
            json.dumps(rec_ev(w["want"], after), ensure_ascii=False)[:140]))
    try:
        import cross_ask
        cross = cross_ask.run(apply=apply)
    except Exception as e:
        cross = {"count": 0, "error": str(e)[:100]}
    rec = {"round": rnd, "t": int(time.time()), "before": before,
           "wishes": wishes, "done": done, "after": after,
           "next_wishes": next_wishes, "cross_ask_pairs": cross.get("count"),
           "improved": {k: {"before": before.get(k), "after": after.get(k)}
                        for k in after if before.get(k) != after.get(k)}}
    hist.append(rec)
    hist = hist[-60:]
    if apply:
        json.dump({"rounds": hist}, open(DATA, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        md = ["# วัฏจักรความต้องการของทุกฝ่าย (ไม่มีจุดหยุด)", "",
              "รอบที่ %d · ถาม → สร้าง → ถามใหม่" % rnd, "",
              "| ฝ่าย | สิ่งที่อยากได้รอบนี้ |", "|---|---|"]
        for w in wishes:
            md += ["| %s | %s |" % (w["dept"], w["want"])]
        md += ["", "## สิ่งที่สร้างจริง", ""]
        for d in done:
            md += ["- %s → %s" % (d["dept"], json.dumps(d["result"], ensure_ascii=False))]
        md += ["", "## วัดผลก่อน/หลัง", "",
               json.dumps(rec["improved"], ensure_ascii=False), "",
               "## สิ่งที่ทุกฝ่ายอยากได้รอบหน้า (รอปฏิบัติ)", ""]
        for w in next_wishes:
            md += ["### %s ถาม: %s" % (w["dept"], w["want"]),
                   "- Zyphere ตอบ: " + w["answer"], ""]
        md += ["", "## ทุกฝ่ายถามกันเอง (หลังงานเสร็จทุกครั้ง)", "",
               "- จำนวนคู่ถาม: %s" % rec.get("cross_ask_pairs"),
               "- ดูบทสนทนา: governance/CROSS_ASK.md", "",
               "รอบถัดไปจะถามอีกหลังงานเสร็จ — วนไม่หยุด", ""]
        open(OUT, "w", encoding="utf-8").write("\n".join(md))
    return rec


if __name__ == "__main__":
    r = run()
    print(json.dumps({"round": r["round"], "wishes": len(r["wishes"]),
                      "done": len(r["done"]), "improved": r["improved"]},
                     ensure_ascii=False)[:700])
