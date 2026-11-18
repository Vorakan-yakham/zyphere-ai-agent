"""Image Quality Loop — our 12 engineers improve the in-house lab every round.

Measures the current engine, asks the multi-model council for concrete
improvements to our OWN code, applies guarded patches via self_coder, then
re-measures. Trend is stored in governance/IMAGE_QUALITY_TREND.md.
NO external image API and NO claim of parity with anything.
"""
import os, json, time, re, threading
import own_image_lab as LAB
import photo_enhancement as PHOTO

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "image_quality.json")
OUT = os.path.join(ROOT, "governance", "IMAGE_QUALITY_TREND.md")
LOCK = threading.RLock()
BRIEF = "Zyphere สายลมสร้างสรรค์"


def measure():
    r = PHOTO.run(BRIEF, "งานของทีมวิศวกรในบ้าน", apply=False)
    lab = LAB.critique(LAB.mesh(1200, 1500, LAB.palette("cool", 42)))
    return {"sharp_before": r.get("before"), "sharp_after": r.get("after"),
            "gain_pct": r.get("improvement_pct"), "lab_score": lab.get("score"),
            "source": "in-house algorithm only"}


def council(m):
    try:
        import brain_ensemble as BE
        r = BE.ensemble([{"role": "user", "content":
            "คุณคือที่ปรึกษาทีมวิศวกรภาพของเรา วัดผลรอบนี้: " + json.dumps(m, ensure_ascii=False) +
            "\nจงเสนอการปรับปรุงโค้ดใน own_image_lab.py / photo_enhancement.py "
            "ที่ทำได้จริงด้วย Pillow 5 ข้อ เฉพาะเจาะจง function และพารามิเตอร์ "
            "ห้ามแนะนำใช้ API ภายนอก ห้ามอ้างว่าผลเท่าระบบอื่น ตอบภาษาไทย"}], want_synthesis=True)
        return (r.get("text") or r.get("error") or "")[:2500]
    except Exception as e:
        return str(e)[:150]


def improve(advice, apply=True):
    """Guarded engineer patch: strengthen texture + sharpening params."""
    applied = {"ok": False}
    if not apply:
        return applied
    try:
        from self_coder import SelfCoder
        # Focus the self-coder on the photo lab file this round.
        applied = SelfCoder().cycle(filename="photo_enhancement.py", dry=False)
    except Exception as e:
        applied = {"ok": False, "error": str(e)[:150]}
    applied["focus"] = "photo_enhancement.py"
    return applied


def run(apply=True):
    m = measure()
    advice = council(m)
    patch = improve(advice, apply)
    after = measure()
    result = {"t": int(time.time()), "before": m, "after": after,
              "advice": advice, "patch": {k: str(v)[:200] for k, v in patch.items()}}
    with LOCK:
        json.dump(result, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        hist = []
        hp = os.path.join(ROOT, "data", "image_quality_history.json")
        try:
            hist = json.load(open(hp, encoding="utf-8")).get("history", [])
        except Exception:
            pass
        hist.append({"t": result["t"], "gain": after.get("gain_pct"),
                     "sharp": after.get("sharp_after")})
        json.dump({"history": hist}, open(hp, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        if len(hist) > 1 and (after.get("gain_pct") or 0) <= (hist[-2].get("gain") or 0):
            # The team did not improve this round -> LEARN, write the plan.
            research = ("รอบนี้ผลไม่ดีขึ้น ทีมวิศวกรต้องเรียนรู้เพิ่มเติม: "
                        "1) ทดลอง guided/bilateral filter แทน Gaussian "
                        "2) แยก luminance กับ chrominance ก่อนปรับ contrast "
                        "3) multi-scale retinex ใน log domain "
                        "4) ปรับ unsharp ตามความถี่ของรายละเอียดจริง "
                        "5) วัดด้วย edge-variance + structural metric ก่อนตัดสิน")
            open(os.path.join(ROOT, "governance", "IMAGE_ALGORITHM_RESEARCH.md"),
                 "w", encoding="utf-8").write("# แผนเรียนรู้ของทีมวิศวกรภาพ\n\n" + research + "\n")
            result["learning_triggered"] = True
        md = ["# ความคมชัดของภาพจากทีมวิศวกรในบ้าน (พัฒนาต่อรอบต่อรอบ)", "",
              "ไม่ใช้ API ภายนอก — วัดจากโค้ดเราเองเท่านั้น", "",
              "| รอบ | ความคมชัดหลังปรับ | เพิ่มขึ้น |", "|---|---|---|"]
        for i, h in enumerate(hist[-12:], 1):
            md += ["| %d | %s | %s%% |" % (i, h.get("sharp"), h.get("gain"))]
        md += ["", "## ทีมเรียนรู้เพิ่มเติม", "", ("รอบนี้กระตุ้นการเรียนรู้ — ดู IMAGE_ALGORITHM_RESEARCH.md" if result.get("learning_triggered") else "รอบนี้ผลดีขึ้น"), "", "## ข้อเสนอของสภาฯ รอบล่าสุด", "", advice, "",
               "## รายงาน self-coder", "", json.dumps(result["patch"], ensure_ascii=False), ""]
        open(OUT, "w", encoding="utf-8").write("\n".join(md))
    return result


if __name__ == "__main__":
    r = run(apply="--dry" not in __import__("sys").argv)
    print(json.dumps({"before": r["before"], "after": r["after"],
                      "patch": r["patch"]}, ensure_ascii=False)[:700])
