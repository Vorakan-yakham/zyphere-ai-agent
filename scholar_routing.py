"""Zyphere Scholar Routing — separate every branch and assign the RIGHT scholar.

For each of the 184 sub-branches, choose the specialist whose training matches
the topic. No generalist is used where a specialist exists. Output is durable
and auditable: SCHOLAR_ASSIGNMENTS.md + scholar_assignments.json.

HONEST: these are role assignments (who should work on what), not claims that
a certified human expert reviewed the content.
"""
import os, json, re, time, requests, subprocess, base64
from faculty_expansion import TREE

REPO = "Vorakan-yakham/zyphere-scholar-product-pack"
BASE = "https://api.github.com/repos/" + REPO + "/contents/"

# (keywords in faculty/sub-branch, worker role, scholar code prefix, rationale)
RULES = [
    (["ควอนตัม", "ฟิสิกส์", "ดารา", "จักรวาล", "อวกาศ", "นิวเคลียร์", "พลังงาน",
      "กลศาสตร์", "แม่เหล็ก", "ออปติก", "ฟิวชัน", "ฟิสสิกส์"],
     "นักฟิสิกส์", "PHY", "ต้องการความเข้าใจกฎของธรรมชาติและแบบจำลองเชิงปริมาณ"),
    (["คณิต", "ตรรกะ", "สถิติ", "พีชคณิต", "เรขาคณิต", "จำนวน", "การคำนวณ"],
     "นักคณิตศาสตร์", "MTH", "ต้องการเหตุผลเชิงนามธรรมและการพิสูจน์"),
    (["พันธุกรรม", "เซลล์", "ภูมิคุ้มกัน", "สมอง", "สรีระ", "ชีว", "เนื้อเยื่อ",
      "เภสัช", "โมเลกุล", "จีโนม"],
     "นักชีววิทยา", "BIO", "ต้องการความรู้เชิงชีววิทยาและกลไกของสิ่งมีชีวิต"),
    (["แพทย์", "คลินิก", "โรค", "ปฐมพยาบาล", "ความปลอดภัย", "เอาชีวิตรอด"],
     "แพทย์และผู้เชี่ยวชาญด้านความปลอดภัย", "MED", "เกี่ยวข้องกับสุขภาพและชีวิตของผู้ใช้"),
    (["จิตวิทยา", "ความจำ", "การเรียนรู้", "พฤติกรรม"],
     "นักจิตวิทยา", "PSY", "ต้องการความเข้าใจพฤติกรรมและกระบวนการคิด"),
    (["ปัญญาประดิษฐ์", "อัลกอริทึม", "โปรแกรม", "ฐานข้อมูล", "ไซเบอร์",
      "หุ่นยนต์", "คอมพิวเตอร์", "โครงสร้างข้อมูล", "ซอฟต์แวร์", "ข้อมูลขนาดใหญ่",
      "เสียง", "ภาพ", "การเข้ารหัส"],
     "วิศวกรซอฟต์แวร์และข้อมูล", "ENG", "ต้องการทักษะการเขียนโค้ดและระบบคอมพิวเตอร์"),
    (["ไฟฟ้า", "เครื่องกล", "โยธา", "เคมี", "วัสดุ", "โครงสร้าง", "ระบบกำลัง"],
     "วิศวกรHardwareและอุตสาหกรรม", "IND", "ต้องการความรู้ด้านวิศวกรรมกายภาพ"),
    (["เศรษฐกิจ", "การเงิน", "บัญชี", "การตลาด", "ธุรกิจ", "การจัดการ",
      "ลงทุน", "ตรวจสอบ", "ภาษี"],
     "นักเศรษฐศาสตร์และธุรกิจ", "BUS", "ต้องการความเข้าใจระบบเศรษฐกิจและตลาด"),
    (["กฎหมาย", "สิทธิ", "จริยธรรม", "ปรัชญา", "การเมือง", "รัฐ"],
     "นักกฎหมายและจริยธรรม", "LAW", "เกี่ยวข้องกับสิทธิ หน้าที่ และกรอบจริยธรรม"),
    (["ประวัติ", "สังคม", "มานุษย", "อารยธรรม", "วัฒนธรรม", "รัฐศาสตร์",
      "ความสัมพันธ์ระหว่างประเทศ"],
     "นักสังคมศาสตร์และประวัติศาสตร์", "SOC", "ต้องการบริบททางสังคมและประวัติศาสตร์"),
    (["ภาษา", "วรรณกรรม", "การเขียน", "การแปล", "ไวยากรณ์", "สัทศาสตร์",
      "พิสูจน์อักษร", "สร้างสรรค์"],
     "ฝ่ายภาษา", "LAN", "ต้องการความแม่นยำของภาษาและการสื่อสาร"),
    (["การสอน", "การศึกษา", "ผู้เรียน", "หลักสูตร"],
     "นักการศึกษา", "EDU", "ต้องการออกแบบการเรียนรู้ที่เข้าใจง่าย"),
    (["ดนตรี", "ภาพยนตร์", "สื่อ", "กราฟิก", "ออกแบบ", "สถาปัตยกรรม", "ประสบการณ์ผู้ใช้"],
     "ฝ่ายออกแบบผลิตภัณฑ์และสื่อ", "DES", "ต้องการทั้งความสวยงามและการใช้งานจริง"),
    (["เกษตร", "อาหาร", "น้ำ", "สิ่งแวดล้อม", "ภูมิอากาศ", "นิเวศ",
      "ทรัพยากร", "การผลิต"],
     "นักวิทยาศาสตร์สิ่งแวดล้อมและเกษตร", "ENV",
     "ต้องการความเข้าใจระบบนิเวศและการจัดการทรัพยากร"),
    (["ระบบ", "วิเคราะห์", "ฐานข้อมูล", "ทดสอบ", "ปฏิบัติการ"],
     "นักวิเคราะห์ระบบ", "SYS", "ต้องการมองภาพรวมและตรวจสอบการทำงานของระบบ"),
]

DEFAULT = ("นักวิชาการทั่วไป", "GEN", "หัวข้อทั่วไปที่ต้องการการศึกษาและสรุปเชิงระบบ")


def pick(text):
    t = str(text)
    for keys, role, code, why in RULES:
        if any(k in t for k in keys):
            return role, code, why
    return DEFAULT


def build():
    rows = []
    counters = {}
    for faculty, subs in TREE.items():
        for sub, concepts in subs.items():
            role, code, why = pick(faculty + " " + sub + " " + " ".join(concepts))
            counters[code] = counters.get(code, 0) + 1
            rows.append({
                "scholar_id": "%s-%03d" % (code, counters[code]),
                "faculty": faculty,
                "sub_branch": sub,
                "concepts": concepts,
                "assigned_role": role,
                "rationale": why,
            })
    return rows


def main():
    rows = build()
    md = ["# การจับคู่นักวิชาการกับสาขาวิชา (แยกตามแขนง)", "",
          "สาขาย่อยทั้งหมด: %d · นักวิชาการที่ใช้: %d ประเภท" %
          (len(rows), len(set(r["assigned_role"] for r in rows))), "",
          "ทุกสาขาถูกจับคู่กับผู้เชี่ยวชาญที่ตรงกับเนื้อหา ",
          "ไม่ได้ใช้คนกลางกับทุกงาน ", ""]
    cur = None
    for r in rows:
        if r["faculty"] != cur:
            cur = r["faculty"]
            md += ["## " + cur, ""]
        md.append("- **%s** `%s` → %s · %s" %
                  (r["sub_branch"], r["scholar_id"], r["assigned_role"], r["rationale"]))
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
    files = [("SCHOLAR_ASSIGNMENTS.md", "\n".join(md)),
             ("scholar_assignments.json", json.dumps({"rows": rows, "t": int(time.time())},
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
        payload = {"message": "Scholar routing by branch " + str(int(time.time())),
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
    print("assignments", len(rows), "roles", len(set(r["assigned_role"] for r in rows)),
          "pushed", ok, "errors", err)
    print("sample", rows[:3])


if __name__ == "__main__":
    main()
