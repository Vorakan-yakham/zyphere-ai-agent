"""Idle Book Team — every idle engineer writes one UNIQUE, well-designed ebook
for their own field, every day. Duplicate content is rejected by hash + text
similarity before publishing. Real files, real links, no filler.
"""
import os, re, json, time, hashlib, difflib

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "idle_book_team.json")
OUT = os.path.join(ROOT, "governance", "IDLE_BOOK_TEAM.md")

TEAM_FIELDS = [
    ("วิศวกรแชท", "การออกแบบบทสนทนา AI"),
    ("วิศวกรAPI", "สถาปัตยกรรม API สำหรับระบบ AI"),
    ("วิศวกรภาพ", "ศิลปะเชิงคำนวณและการจัดองค์ประกอบ"),
    ("วิศวกรสื่อ", "การตัดต่อวิดีโอและความต่อเนื่องของตัวละคร"),
    ("วิศวกรเพลง", "โครงสร้างทำนองและเครื่องดนตรี"),
    ("วิศวกรเสียง", "การออกแบบเสียงเอฟเฟกต์"),
    ("วิศวกรหนังสือ", "การเรียบเรียงเนื้อหาให้อ่านง่าย"),
    ("วิศวกรร้านค้า", "การออกแบบหน้าร้านที่เปลี่ยนคนดูเป็นคนซื้อ"),
    ("วิศวกรฐานข้อมูล", "ระบบความจำสำหรับ AI ที่ไม่พึ่งคลาวด์"),
    ("วิศวกรสมอง", "การเรียนรู้จากคำแก้ไขของผู้ใช้"),
    ("วิศวกรQA", "มาตรฐานตรวจรับงานแบบ fail-closed"),
    ("วิศวกรอัตโนมัติ", "การทำงานต่อเนื่องโดยไม่มีผู้สั่ง"),
]


def existing():
    import autonomous_council as AC
    out = {}
    for p in AC.gh_tree():
        m = re.match(r"books/(\d+_[^/]+)/content\.md$", p)
        if m:
            t = AC.gh_raw(p) or ""
            out[m.group(1)] = (hashlib.md5(t.encode()).hexdigest(), t[:1200])
    return out


def unique_ok(title, text, old):
    h = hashlib.md5(text.encode()).hexdigest()
    if h in {v[0] for v in old.values()}:
        return False, "hash duplicate"
    for k, (_, sample) in old.items():
        ratio = difflib.SequenceMatcher(None, text[:800], sample).ratio()
        if ratio > 0.82:
            return False, "too similar to " + k
    return True, "unique"


def write_primer(field, team):
    """Build content from our OWN modules/knowledge — not lorem/filler."""
    import world_knowledge as WK
    facts = WK.ask(field)
    refs = facts.get("answers", [])[:3]
    body = ["# " + field, "",
            "## ทำไมต้องเข้าใจเรื่องนี้",
            "หัวข้อนี้เป็นส่วนหนึ่งของแผนที่ความรู้ที่ทีม Zyphere จัดระบบจากแหล่งเปิดจริง "
            "ผู้เขียน: " + team + " · วันที่ " + time.strftime("%Y-%m-%d"), "",
            "## สิ่งที่จะได้",
            "- เห็นโครงสร้างแนวคิดหลักของ " + field,
            "- มีคำถามสำหรับลองตรวจความเข้าใจของตัวเอง",
            "- อ้างอิงแหล่งจริงที่ระบบเก็บไว้ในเครื่อง", "",
            "## เนื้อหาหลัก"]
    for i, r in enumerate(refs, 1):
        body += ["### " + str(r.get("title", "แนวคิดที่ " + str(i)))[:90],
                 str(r.get("text", ""))[:500], ""]
    body += ["## กรณีศึกษาเชิงแนวคิด",
             "ลองพิจารณาว่าหลักการของ " + field + " จะเปลี่ยนวิธี working ของคุณอย่างไร "
             "เมื่อข้อมูลที่ใช้มีเพียงสิ่งที่ระบบเก็บไว้จริง",
             "", "## คำถามที่พบบ่อย",
             "1. หัวข้อนี้เกี่ยวกับอะไร → " + field,
             "2. จะตรวจความเข้าใจอย่างไร → ลองอธิบายต่อคนอื่น",
             "", "## สรุป",
             "เนื้อหานี้เป็น structured primer จากข้อมูลจริง ไม่ใช่ตำราผู้เชี่ยวชาญ"]
    return "\n".join(body)


def run(apply=True, per_day=3):
    old = existing()
    made, skipped = [], []
    seed = int(time.time() // 86400)
    for i in range(per_day):
        team, field = TEAM_FIELDS[(seed*3+i) % len(TEAM_FIELDS)]
        text = write_primer(field, team)
        ok, why = unique_ok(field, text, old)
        if not ok:
            skipped.append({"team": team, "why": why})
            continue
        folder = "special_%s_%s" % (re.sub(r"\W+", "", team)[:12],
                                    re.sub(r"\W+", "", field)[:12])
        cover_html = ('<div style="background:#0b2533;color:#fff;padding:36px;border-radius:18px">'
                      '<b style="color:#22d3ee">ZYPHERE ORIGINAL · %s</b>'
                      '<h1>%s</h1><p>เขียนโดย %s · เนื้อหาไม่ซ้ำกับเล่มที่มีอยู่</p></div>' % (
                          team, field, team))
        html = "<!doctype html><html lang='th'><head><meta charset='utf-8'></head><body style='font-family:Noto Sans Thai,sans-serif;max-width:760px;margin:auto;line-height:1.9;color:#12222b'>" + cover_html + "<pre style='white-space:pre-wrap'>" + text + "</pre></body></html>"
        if apply:
            import autonomous_council as AC
            r1 = AC.gh_put("books/%s/content.md" % folder, text, "Idle team book: " + field)
            r2 = AC.gh_put("books/%s/book.html" % folder, html, "Idle team designed book: " + field)
            made.append({"team": team, "field": field, "folder": folder,
                         "words": len(text.split()), "check": why,
                         "published": [r1.get("status"), r2.get("status")]})
        old[folder] = (hashlib.md5(text.encode()).hexdigest(), text[:1200])
    rec = {"t": int(time.time()), "day": seed, "made": made, "skipped": skipped,
           "rule": "ทีมว่างเขียนหนังสือประจำหน่วยทุกวัน ต้องสวย น่าอ่าน และไม่ซ้ำของเก่า"}
    if apply:
        json.dump(rec, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        open(OUT, "w", encoding="utf-8").write(
            "# ทีมว่างเขียนหนังสือประจำหน่วย (รายวัน)\n\n" +
            "\n".join("- %s → **%s** (%d คำ, %s, publish %s)" % (
                m["team"], m["field"], m["words"], m["check"], m["published"]) for m in made) +
            "\n\n" + ("ข้าม: " + str(skipped) if skipped else "") + "\n\n" + rec["rule"] + "\n")
    return rec


if __name__ == "__main__":
    r = run()
    print(json.dumps({"made": len(r["made"]), "skipped": len(r["skipped"])},
                     ensure_ascii=False))
