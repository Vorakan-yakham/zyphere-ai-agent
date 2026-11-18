"""Zyphere World Taxonomy — parse REAL global academic branches from Wikipedia's
Outline of academic disciplines and attach them to our 46 faculties.

Source: https://en.wikipedia.org/wiki/List_of_academic_disciplines
(fetched; saved locally by the assistant). Result is a 3-level tree:
faculty (46) -> our sub-branch (184) -> real worldwide sub-disciplines.

HONEST: source is Wikipedia (CC BY-SA), fetched on this date. It is a map of
what exists globally, not a claim that Zyphere masters all of it.
"""
import os, re, json, time, requests, subprocess, base64

SRC = r"C:\Users\vornl\.local\share\opencode\tool-output\tool_1ece63d1c001z0YDwa5jTtuSlM"
REPO = "Vorakan-yakham/zyphere-scholar-product-pack"
BASE = "https://api.github.com/repos/" + REPO + "/contents/"

# English Wikipedia section -> our faculty keys
MAP = {
    "Physics": ["ฟิสิกส์ควอนตัม", "ฟิสิกส์คลาสสิก"],
    "Astronomy": ["ดาราศาสตร์-จักรวาล", "อวกาศ-การสำรวจ"],
    "Space sciences": ["อวกาศ-การสำรวจ", "ดาราศาสตร์-จักรวาล"],
    "Chemistry": ["วิศวกรรมเคมี-วัสดุ"],
    "Earth science": ["ภูมิอากาศ-สิ่งแวดล้อม", "น้ำ-ทรัพยากร"],
    "Mathematics": ["คณิตศาสตร์บริสุทธิ์", "คณิตศาสตร์ประยุกต์"],
    "Statistics": ["คณิตศาสตร์ประยุกต์"],
    "Logic": ["ตรรกะและทฤษฎีข้อมูล"],
    "Computer science": ["ปัญญาประดิษฐ์", "อัลกอริทึม-โครงสร้างข้อมูล",
                         "วิศวกรรมซอฟต์แวร์", "ฐานข้อมูล-ข้อมูลขนาดใหญ่",
                         "ความมั่นคงไซเบอร์", "คอมพิวเตอร์วิทัศน์-เสียง",
                         "หุ่นยนต์-ระบบอัตโนมัติ"],
    "Biology": ["พันธุกรรม-ชีวโมเลกุล", "เซลล์และเนื้อเยื่อ", "ภูมิคุ้มกัน-โรค"],
    "Neuroscience": ["สมอง-ประสาทวิทยา"],
    "Medicine and health": ["การแพทย์คลินิก", "สรีระและเภสัช"],
    "Psychology": ["จิตวิทยา"],
    "Economics": ["เศรษฐกิจมหภาค-การเงิน", "การเงิน-การลงทุน"],
    "Business": ["การตลาด-ธุรกิจ", "การจัดการ-ภาวะผู้นำ", "การบัญชี-ตรวจสอบ"],
    "Law": ["กฎหมาย-สิทธิมนุษยชน"],
    "Philosophy": ["จริยธรรม-ปรัชญา"],
    "History": ["ประวัติศาสตร์-อารยธรรม"],
    "Anthropology": ["สังคมวิทยา-มานุษยวิทยา"],
    "Sociology": ["สังคมวิทยา-มานุษยวิทยา"],
    "Political science": ["รัฐศาสตร์-ความสัมพันธ์ระหว่างประเทศ"],
    "Linguistics": ["ภาษาศาสตร์-การแปล"],
    "Languages and literature": ["ภาษาศาสตร์-การแปล", "วรรณกรรม-การเขียน"],
    "Literature": ["วรรณกรรม-การเขียน"],
    "Education": ["การสอน-การศึกษา"],
    "Educational technology": ["การสอน-การศึกษา"],
    "Music": ["ดนตรี-เสียง"],
    "Theatre": ["ภาพยนตร์-สื่อ-กราฟฟิก"],
    "Film": ["ภาพยนตร์-สื่อ-กราฟฟิก"],
    "Visual arts": ["ภาพยนตร์-สื่อ-กราฟฟิก", "สถาปัตยกรรม-การออกแบบ"],
    "Architecture and design": ["สถาปัตยกรรม-การออกแบบ"],
    "Agriculture": ["เกษตร-อาหาร"],
    "Environmental studies and forestry": ["ภูมิอากาศ-สิ่งแวดล้อม", "น้ำ-ทรัพยากร"],
    "Chemical engineering": ["วิศวกรรมเคมี-วัสดุ"],
    "Civil engineering": ["วิศวกรรมโยธา-โครงสร้าง"],
    "Electrical engineering": ["วิศวกรรมไฟฟ้า-อิเล็กทรอนิกส์"],
    "Mechanical engineering": ["วิศวกรรมเครื่องกล"],
    "Materials science": ["วิศวกรรมเคมี-วัสดุ"],
    "Systems science": ["พลังงาน-นิวเคลียร์", "การจัดการ-ภาวะผู้นำ"],
    "Transportation": ["วิศวกรรมเครื่องกล"],
    "Public policy": ["รัฐศาสตร์-ความสัมพันธ์ระหว่างประเทศ"],
    "Public administration": ["รัฐศาสตร์-ความสัมพันธ์ระหว่างประเทศ"],
    "Geography": ["ภูมิอากาศ-สิ่งแวดล้อม"],
    "Religious studies": ["จริยธรรม-ปรัชญา"],
    "Journalism, media studies and communication": ["ภาพยนตร์-สื่อ-กราฟฟิก", "การตลาด-ธุรกิจ"],
    "Family and consumer science": ["จิตวิทยา", "เกษตร-อาหาร"],
    "Human physical performance and recreation": ["การแพทย์คลินิก", "ดนตรี-เสียง"],
    "Military sciences": ["การเอาชีวิตรอด-ความปลอดภัย"],
    "Library and museum studies": ["ประวัติศาสตร์-อารยธรรม"],
    "Social work": ["สังคมวิทยา-มานุษยวิทยา"],
}

SKIP_PREFIX = ("Main article", "Main articles", "See also", "Further reading",
               "External links", "Notes", "References", "Retrieved from")


def parse_sections(text):
    lines = [l.strip() for l in text.split("\n")]
    out = {}
    i = 0
    while i < len(lines):
        m = re.match(r"^(.+?)\[edit\]$", lines[i])
        if m:
            name = m.group(1).strip()
            items = []
            i += 1
            while i < len(lines):
                s = lines[i]
                if re.search(r"\[edit\]$", s):
                    break
                if s and not s.startswith(SKIP_PREFIX):
                    if (len(s) < 70 and not s.endswith(":") and
                            not re.match(r"^\d", s) and
                            "http" not in s and "Wikipedia" not in s):
                        items.append(s)
                i += 1
            out[name] = items
        else:
            i += 1
    return out


def main():
    if not os.path.exists(SRC):
        print("source missing")
        return
    text = open(SRC, encoding="utf-8", errors="ignore").read()
    sections = parse_sections(text)
    print("sections", len(sections))

    per_faculty = {}
    used = []
    for sec, items in sections.items():
        if sec not in MAP:
            continue
        clean = []
        for x in items:
            x = re.sub(r"\s*\(.*?\)\s*$", "", x).strip()
            if x and x not in clean:
                clean.append(x)
        if not clean:
            continue
        used.append(sec)
        for fac in MAP[sec]:
            per_faculty.setdefault(fac, [])
            for x in clean:
                if x not in per_faculty[fac]:
                    per_faculty[fac].append(x)

    from faculty_expansion import TREE
    rows = []
    for fac, subs in TREE.items():
        world = per_faculty.get(fac, [])
        rows.append({"faculty": fac, "our_sub_branches": len(subs),
                     "world_sub_disciplines": world,
                     "world_count": len(world), "source_section": [s for s, fs in MAP.items() if fac in fs and s in used]})

    md = ["# แขนงวิชาของโลก — ขยายจากแหล่งวิชาการจริง", "",
          "แหล่งที่มา: Wikipedia - Outline of academic disciplines ",
          "(https://en.wikipedia.org/wiki/List_of_academic_disciplines)", "",
          "คณะของเรา: %d · หมวดวิชาจาก Wikipedia ที่ใช้: %d " % (len(rows), len(used)),
          "รวมสาขาย่อยจากทั่วโลก: %d รายการ" % sum(r["world_count"] for r in rows), "",
          "โครงสร้าง 3 ระดับ: คณะ → สาขาย่อยของเรา → สาขาวิชาที่มีจริงในระดับโลก ", ""]
    for r in rows:
        md += ["## " + r["faculty"], "",
               "- สาขาย่อยของเรา: %d" % r["our_sub_branches"],
               "- หมวดวิชาโลกที่เกี่ยวข้อง: " + ", ".join(r["source_section"]),
               "- สาขาวิชาจริงทั่วโลก (%d):" % r["world_count"]]
        for x in r["world_sub_disciplines"][:40]:
            md.append("  - " + x)
        md.append("")
    md.append("## ข้อความโปร่งใส")
    md.append("ข้อมูลมาจาก Wikipedia ภายใต้ CC BY-SA เป็นแผนที่ของสิ่งที่มีอยู่จริง " +
              "ไม่ได้หมายความว่า Zyphere เชี่ยวชาญทุกแขนง")

    tok = os.environ.get("GH_TOKEN", "") or os.environ.get("GITHUB_TOKEN", "")
    if not tok:
        try:
            tok = subprocess.run(["gh", "auth", "token"], capture_output=True,
                                 text=True, timeout=15).stdout.strip()
        except Exception:
            pass
    headers = {"Authorization": "Bearer " + tok, "Accept": "application/vnd.github+json"} if tok else {}
    files = [("WORLD_TAXONOMY.md", "\n".join(md)),
             ("world_taxonomy.json", json.dumps({"rows": rows, "t": int(time.time())},
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
        payload = {"message": "World taxonomy from Wikipedia " + str(int(time.time())),
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
    print("faculties", len(rows), "world disciplines", sum(r["world_count"] for r in rows),
          "pushed", ok, "errors", err)
    print("used sections", sorted(used))


if __name__ == "__main__":
    main()
