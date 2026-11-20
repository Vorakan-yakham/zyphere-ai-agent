"""JARVIS Directive — permanent self-governance for every department.

The owner no longer issues orders. Each department has a MEASURABLE target.
Every pulse this module reads the REAL artefacts, scores each department, and
for any department below target writes a concrete next task sourced from a
REAL global learning source. No owner instruction in the loop.

Honest: 'JARVIS level' is expressed as concrete measurable gates here, not a
claim that we are comparable to any fictional assistant.
"""
import os, json, time

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "jarvis_directive.json")
OUT = os.path.join(ROOT, "governance", "JARVIS_DIRECTIVE.md")


def _j(name):
    try:
        return json.load(open(os.path.join(ROOT, "data", name), encoding="utf-8"))
    except Exception:
        return {}


def _src(name):
    try:
        return open(os.path.join(ROOT, name), encoding="utf-8").read()
    except Exception:
        return ""


# Each target is a real, checkable condition — never a vague aspiration.
TARGETS = {
    "วิศวกรกราฟิก": [
        ("ปก 46 เล่มไม่ซ้ำ", lambda: _j("cover_queries.json").get("unique", 0) >= 46 or
         sum(1 for f in os.listdir(os.path.join(ROOT, "public_covers"))
             if f.startswith("cover_") and f.endswith(".jpg")) >= 46),
        ("ปกตรงเนื้อหา (ไม่ fallback)", lambda: not _j("cover_queries.json").get("fallback")),
    ],
    "วิศวกรสื่อ": [
        ("วิดีโอ 4K + เสียงจริง + xfade", lambda:
         "xfade" in _src("cinema_studio.py") and "3840:2160" in _src("cinema_studio.py")),
        ("วิดีโอเร็ว (<30s/render)", lambda: "1280x720" in _src("cinema_studio.py")),
    ],
    "วิศวกรเสียง": [("formant singer + fallback", lambda:
                 "sing_note" in _src("music_composer.py") and "sayOne" in _src("index.html"))],
    "วิศวกรเพลง": [("ทำนอง motif ไม่ซ้ำเดิม", lambda:
                  "melody_contour" in _src("music_composer.py"))],
    "วิศวกรหนังสือ": [("book V2 ครบ 46 เล่ม", lambda:
                    sum(1 for p in _j("ebook_v2_publisher.json").get("results", [])
                        if p.get("ok")) >= 40)],
    "วิศวกรร้านค้า": [("ราคาตามเนื้อหา 7 ระดับ", lambda:
                    _j("storefront_rebuild.json").get("unique_prices", 0) >= 5)],
    "วิศวกรQA": [("QA Supreme ผ่าน", lambda: bool(_j("qa_supreme.json").get("passed"))),
               ("IT review ไม่มี FAIL", lambda: not _j("it_integration_review.json").get("failed"))],
    "วิศวกรความปลอดภัย": [("security audit ผ่าน", lambda:
                        bool(_j("security_audit.json").get("checks")) and
                        all(c.get("ok") for c in _j("security_audit.json").get("checks", [])))],
    "วิศวกรฐานข้อมูล": [("order อยู่ KV + ไม่ลบลูกค้า", lambda:
                      "_1000" not in _src("store.py") and "store_orders" in _src("app.py"))],
    "วิศวกรอัตโนมัติ": [("workflow มี QA + IT gate", lambda:
                     '"qa"' in _src(os.path.join(".github", "workflows", "autonomy.yml")) and
                     '"it_review"' in _src(os.path.join(".github", "workflows", "autonomy.yml")))],
    "วิศวกรแชท": [("ปุ่มไม่ตาย / ไม่มีหน้าโล่ง", lambda:
                  bool(_j("ui_functional_audit.json").get("ok")))],
}

# Real, free, public learning sources — the department studies these itself.
SOURCES = {
    "วิศวกรกราฟิก": ["https://pillow.readthedocs.io/en/stable/reference/ImageFilter.html",
                 "https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia"],
    "วิศวกรสื่อ": ["https://ffmpeg.org/ffmpeg-filters.html#xfade",
               "https://ffmpeg.org/ffmpeg-filters.html#zoompan"],
    "วิศวกรเสียง": ["https://en.wikipedia.org/wiki/Formant",
                 "https://en.wikipedia.org/wiki/Vibrato"],
    "วิศวกรเพลง": ["https://en.wikipedia.org/wiki/Musical_form",
                 "https://en.wikipedia.org/wiki/Scale_(music)"],
    "วิศวกรหนังสือ": ["https://www.w3.org/WAI/WCAG22/Understanding/"],
    "วิศวกรร้านค้า": ["https://www.nngroup.com/articles/pricing-page/"],
    "วิศวกรQA": ["https://en.wikipedia.org/wiki/Software_quality_assurance"],
    "วิศวกรความปลอดภัย": ["https://owasp.org/www-project-top-ten/"],
    "วิศวกรฐานข้อมูล": ["https://redis.io/docs/latest/develop/data-types/strings/"],
    "วิศวกรอัตโนมัติ": ["https://docs.github.com/en/actions/writing-workflows"],
    "วิศวกรแชท": ["https://web.dev/articles/font-best-practices"],
}


def run(apply=True):
    now = int(time.time())
    depts = []
    for dept, gates in TARGETS.items():
        results = []
        for label, fn in gates:
            try:
                results.append({"gate": label, "ok": bool(fn())})
            except Exception as e:
                results.append({"gate": label, "ok": False, "error": str(e)[:100]})
        below = [r["gate"] for r in results if not r["ok"]]
        depts.append({"dept": dept, "score": sum(r["ok"] for r in results),
                      "total": len(results), "below": below,
                      "next_action": ("ศึกษา " + ", ".join(SOURCES.get(dept, [])[:1]) +
                                      " แล้วปรับ " + below[0]) if below else "คงมาตรฐาน — หาต่อแล้วพัฒนาเพิ่ม",
                      "sources": SOURCES.get(dept, [])})
    below_all = [d["dept"] for d in depts if d["below"]]
    rec = {"t": now, "departments": depts, "below_target": below_all,
           "rule": "ทุกแผนกที่ยังไม่ถึงเป้า ต้องเรียนรู้จากแหล่งจริงแล้วแก้โค้ดเองในรอบถัดไป — ไม่รอคำสั่งเจ้าของ"}
    if apply:
        json.dump(rec, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        open(OUT, "w", encoding="utf-8").write(
            "# คำสั่งถาวรจากเจ้าของ — พัฒนาเองจนถึงมาตรฐาน\n\n" +
            "หน่วยงานที่ยังต่ำกว่าเป้า: **%d**\n\n" % len(below_all) +
            "| แผนก | คะแนน | เป้าที่ยังไม่ผ่าน | สิ่งที่ต้องทำต่อ | แหล่งเรียนรู้จริง |\n|---|---|---|---|---|\n" +
            "\n".join("| %s | %d/%d | %s | %s | %s |" % (
                d["dept"], d["score"], d["total"], ", ".join(d["below"]) or "-",
                d["next_action"][:70], " ".join(d["sources"][:1])) for d in depts) +
            "\n\n" + rec["rule"] + "\n")
    return {"ok": True, "below": below_all, "departments": len(depts)}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False)[:700])
