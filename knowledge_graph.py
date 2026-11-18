"""Zyphere Knowledge Graph — connect every branch and map it to REAL work.

For each of the 184 sub-branches:
  - find sibling/bridge links to other faculties via shared concepts
  - assign 2-3 concrete work applications (how a learner actually uses it)

Output: KNOWLEDGE_GRAPH.md + knowledge_graph.json in the product repo.
HONEST: a learning roadmap and application map, not a claim of accredited
cross-disciplinary research.
"""
import os, json, re, time, requests, subprocess, base64
from faculty_expansion import TREE
from scholar_routing import build as build_assignments

REPO = "Vorakan-yakham/zyphere-scholar-product-pack"
BASE = "https://api.github.com/repos/" + REPO + "/contents/"

# role -> concrete real-world work applications
APPLICATIONS = {
    "นักฟิสิกส์": ["วิเคราะห์ข้อมูลเชิงปริมาณ", "สร้างแบบจำลองทำนายผล", "ตรวจสอบความถูกต้องของการวัด"],
    "นักคณิตศาสตร์": ["ออกแบบสูตรคำนวณ", "พิสูจน์ความถูกต้องของขั้นตอน", "วิเคราะห์ความเสี่ยงเชิงตัวเลข"],
    "นักชีววิทยา": ["วิเคราะห์ข้อมูลชีวภาพ", "ออกแบบการทดลอง", "ประเมินความปลอดภัยของผลิตภัณฑ์"],
    "แพทย์และผู้เชี่ยวชาญด้านความปลอดภัย": ["ประเมินความเสี่ยงด้านสุขภาพ", "วางแผนปฐมพยาบาล", "ตรวจความปลอดภัยของงาน"],
    "นักจิตวิทยา": ["ออกแบบประสบการณ์ผู้ใช้", "วิเคราะห์พฤติกรรมผู้บริโภค", "ปรับการสื่อสารให้เข้ากับกลุ่มเป้าหมาย"],
    "วิศวกรซอฟต์แวร์และข้อมูล": ["เขียนระบบทำงานอัตโนมัติ", "สร้าง API และฐานข้อมูล", "วิเคราะห์ข้อมูลขนาดใหญ่"],
    "วิศวกรHardwareและอุตสาหกรรม": ["ออกแบบและตรวจสอบระบบกายภาพ", "ปรับปรุงกระบวนการผลิต", "คำนวณความมั่นคงของโครงสร้าง"],
    "นักเศรษฐศาสตร์และธุรกิจ": ["วิเคราะห์ตลาดและกำหนดราคา", "วางแผนการเงิน", "ประเมินผลกำลังของธุรกิจ"],
    "นักกฎหมายและจริยธรรม": ["ตรวจความสอดคล้องกับกฎหมาย", "กำหนดจริยธรรมการใช้งาน", "จัดการสิทธิและหน้าที่"],
    "นักสังคมศาสตร์และประวัติศาสตร์": ["วิเคราะห์บริบทสังคม", "ออกแบบนโยบาย", "ศึกษาผลกระทบต่อชุมชน"],
    "ฝ่ายภาษา": ["เขียนและตรวจข้อความให้ถูกต้อง", "แปลและปรับให้เข้าใจง่าย", "สร้างเนื้อหาที่น่าสนใจ"],
    "นักการศึกษา": ["ออกแบบหลักสูตร", "สร้างสื่อการเรียนรู้", "ประเมินผลการเรียนรู้"],
    "ฝ่ายออกแบบผลิตภัณฑ์และสื่อ": ["ออกแบบหน้าเว็บและแอป", "สร้างสื่อภาพและเสียง", "ปรับปรุงการใช้งานจริง"],
    "นักวิทยาศาสตร์สิ่งแวดล้อมและเกษตร": ["วิเคราะห์ข้อมูลสิ่งแวดล้อม", "วางแผนการใช้ทรัพยากร", "ประเมินผลกระทบต่อระบบนิเวศ"],
    "นักวิเคราะห์ระบบ": ["ตรวจสอบสถาปัตยกรรม", "หาและแก้บั๊ก", "วางแผนความต่อเนื่องของระบบ"],
    "นักวิชาการทั่วไป": ["สรุปและสังเคราะห์ความรู้", "สร้างเอกสารความรู้", "ต่อยอดเป็นผลงานใหม่"],
}

# curated cross-faculty bridges (faculty -> related faculties and why)
BRIDGES = [
    ("ปัญญาประดิษฐ์", "คณิตศาสตร์ประยุกต์", "AI ใช้คณิตศาสตร์เชิงเส้นและสถิติเป็นพื้นฐาน"),
    ("ปัญญาประดิษฐ์", "ภาษาศาสตร์-การแปล", "แบบจำลองภาษาต้องการความเข้าใจโครงสร้างภาษา"),
    ("ปัญญาประดิษฐ์", "จริยธรรม-ปรัชญา", "การตัดสินใจของ AI ต้องมีกรอบจริยธรรม"),
    ("ฐานข้อมูล-ข้อมูลขนาดใหญ่", "การเงิน-การลงทุน", "ระบบการเงินต้องการจัดการข้อมูลจำนวนมาก"),
    ("ความมั่นคงไซเบอร์", "กฎหมาย-สิทธิมนุษยชน", "ความปลอดภัยข้อมูลเกี่ยวข้องกับกฎหมายและสิทธิ"),
    ("เศรษฐกิจมหภาค-การเงิน", "การตลาด-ธุรกิจ", "นโยบายเศรษฐกิจส่งผลต่อกลยุทธ์ธุรกิจ"),
    ("จิตวิทยา", "การออกแบบประสบการณ์ผู้ใช้", "พฤติกรรมผู้ใช้ช่วยออกแบบหน้าเว็บให้ตรงใจ"),
    ("ดนตรี-เสียง", "คอมพิวเตอร์วิทัศน์-เสียง", "การผลิตเสียงต้องการการประมวลผลสัญญาณ"),
    ("ภูมิอากาศ-สิ่งแวดล้อม", "เกษตร-อาหาร", "สภาพภูมิอากาศส่งผลต่อการผลิตอาหาร"),
    ("พลังงาน-นิวเคลียร์", "วิศวกรรมไฟฟ้า-อิเล็กทรอนิกส์", "ระบบพลังงานต้องการวิศวกรรมไฟฟ้า"),
    ("ฟิสิกส์ควอนตัม", "วิศวกรรมซอฟต์แวร์", "ควอนตัมคอมพิวติ้งเชื่อมฟิสิกส์กับโปรแกรม"),
    ("การสอน-การศึกษา", "วรรณกรรม-การเขียน", "สื่อการสอนต้องการการเขียนที่เข้าใจง่าย"),
]


def norm(s):
    return re.sub(r"[^0-9a-zก-๙]+", "", str(s).lower())


def build():
    assignments = build_assignments()
    apps = {r["faculty"] + "|" + r["sub_branch"]: r["assigned_role"] for r in assignments}
    rows = []
    concepts_index = {}
    for faculty, subs in TREE.items():
        for sub, concepts in subs.items():
            for c in concepts:
                concepts_index.setdefault(norm(c), []).append(faculty + " :: " + sub)
    for faculty, subs in TREE.items():
        for sub, concepts in subs.items():
            role = apps.get(faculty + "|" + sub, "นักวิชาการทั่วไป")
            links = set()
            for c in concepts:
                for other in concepts_index.get(norm(c), []):
                    if other != faculty + " :: " + sub:
                        links.add(other)
            bridges = [b for b in BRIDGES if b[0] == faculty or b[1] == faculty]
            # Fallback 1: same-faculty siblings (every branch has neighbours).
            if not links:
                links = {f + " :: " + s for f, ss in TREE.items() for s in ss
                         if f == faculty and s != sub}
            # Fallback 2: same specialist connects branches across faculties.
            if not bridges:
                bridges = [((faculty, "สาขาที่ใช้นักวิชาการคนเดียวกัน",
                             "ใช้ผู้เชี่ยวชาญ " + role + " ร่วมกัน จึงถ่ายโอนวิธีคิดระหว่างกันได้"))]
            rows.append({
                "faculty": faculty,
                "sub_branch": sub,
                "concepts": concepts,
                "assigned_role": role,
                "applications": APPLICATIONS.get(role, APPLICATIONS["นักวิชาการทั่วไป"]),
                "related_branches": sorted(links)[:6],
                "cross_faculty_bridges": [
                    {"with": b[1] if b[0] == faculty else b[0], "why": b[2]} for b in bridges
                ],
            })
    return rows


def main():
    rows = build()
    md = ["# กราฟความรู้ Zyphere — วิชาสัมพันธ์กันและใช้กับงานได้", "",
          "สาขาที่เชื่อมแล้ว: %d" % len(rows), "",
          "ทุกสาขามี (1) แนวคิดหลัก (2) นักวิชาการที่เหมาะ ",
          "(3) งานที่นำไปใช้ได้จริง (4) สาขาที่เกี่ยวข้อง ",
          "(5) สะพานข้ามคณะวิชา ", ""]
    cur = None
    for r in rows:
        if r["faculty"] != cur:
            cur = r["faculty"]
            md += ["## " + cur, ""]
        md += ["### " + r["sub_branch"], ""]
        md.append("- แนวคิด: " + ", ".join(r["concepts"]))
        md.append("- ผู้เหมาะสม: " + r["assigned_role"])
        md.append("- งานที่ใช้ได้จริง: " + " ; ".join(r["applications"]))
        if r["related_branches"]:
            md.append("- สาขาที่เกี่ยวข้อง: " + " | ".join(r["related_branches"][:4]))
        for b in r["cross_faculty_bridges"]:
            md.append("- สะพานข้ามคณะ → " + b["with"] + ": " + b["why"])
        md.append("")
    tok = os.environ.get("GH_TOKEN", "") or os.environ.get("GITHUB_TOKEN", "")
    if not tok:
        try:
            tok = subprocess.run(["gh", "auth", "token"], capture_output=True,
                                 text=True, timeout=15).stdout.strip()
        except Exception:
            pass
    headers = {"Authorization": "Bearer " + tok,
               "Accept": "application/vnd.github+json"} if tok else {}
    files = [("KNOWLEDGE_GRAPH.md", "\n".join(md)),
             ("knowledge_graph.json", json.dumps({"rows": rows, "t": int(time.time())},
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
        payload = {"message": "Knowledge graph: interlink branches + work applications " + str(int(time.time())),
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
    with_links = sum(1 for r in rows if r["related_branches"] or r["cross_faculty_bridges"])
    print("branches", len(rows), "connected", with_links, "pushed", ok, "errors", err)


if __name__ == "__main__":
    main()
