"""Zyphere Cross-Disciplinary Elevation — every department learns the academic
disciplines RELATED to its work, all together, so all departments work in
coordination instead of in silos.

For each department we pick related faculties from the 46-faculty tree, ask
Zyphere (ensemble) how those disciplines apply to that department's work, feed
the lessons into LocalBrain + DevBrain, and record a synchronised elevation.
"""
import os, json, time, re, sys, requests, subprocess, base64

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "cross_disciplinary.json")
REPO = "Vorakan-yakham/zyphere-scholar-product-pack"
BASE = "https://api.github.com/repos/" + REPO + "/contents/"
LOG = os.path.join(ROOT, "data", "co_learning.json")

# department -> related academic faculties (from our 46-faculty tree)
RELATED = {
    "นักวิเคราะห์ระบบ": ["ตรรกะและทฤษฎีข้อมูล", "วิศวกรรมซอฟต์แวร์", "คณิตศาสตร์ประยุกต์", "จริยธรรม-ปรัชญา"],
    "ฐานข้อมูล": ["ฐานข้อมูล-ข้อมูลขนาดใหญ่", "คณิตศาสตร์ประยุกต์", "ตรรกะและทฤษฎีข้อมูล", "สถิติ"],
    "โปรแกรมเมอร์": ["วิศวกรรมซอฟต์แวร์", "อัลกอริทึม-โครงสร้างข้อมูล", "ตรรกะและทฤษฎีข้อมูล", "ภาษาศาสตร์-การแปล"],
    "ฝ่ายวิชาการ": ["ปรัชญา", "ประวัติศาสตร์-อารยธรรม", "สังคมวิทยา-มานุษยวิทยา", "การสอน-การศึกษา"],
    "ฝ่ายภาษา": ["ภาษาศาสตร์-การแปล", "วรรณกรรม-การเขียน", "จิตวิทยา", "ปรัชญา"],
    "ฝ่ายออกแบบผลิตภัณฑ์": ["สถาปัตยกรรม-การออกแบบ", "จิตวิทยา", "ภาพยนตร์-สื่อ-กราฟฟิก", "คณิตศาสตร์บริสุทธิ์"],
    "ฝ่ายผลิตหนังสือ": ["วรรณกรรม-การเขียน", "การสอน-การศึกษา", "ภาพยนตร์-สื่อ-กราฟฟิก", "ประวัติศาสตร์-อารยธรรม"],
    "ฝ่ายการตลาด": ["เศรษฐกิจมหภาค-การเงิน", "การตลาด-ธุรกิจ", "จิตวิทยา", "สถิติ"],
    "ฝ่ายทดสอบ": ["วิศวกรรมซอฟต์แวร์", "ตรรกะและทฤษฎีข้อมูล", "คณิตศาสตร์ประยุกต์", "จริยธรรม-ปรัชญา"],
    "ฝ่ายปฏิบัติการ": ["การจัดการ-ภาวะผู้นำ", "วิศวกรรมซอฟต์แวร์", "ระบบ", "รัฐศาสตร์-ความสัมพันธ์ระหว่างประเทศ"],
    "ฝ่ายความปลอดภัย": ["ความมั่นคงไซเบอร์", "กฎหมาย-สิทธิมนุษยชน", "จริยธรรม-ปรัชญา", "ตรรกะและทฤษฎีข้อมูล"],
}


def token():
    t = os.environ.get("GH_TOKEN", "") or os.environ.get("GITHUB_TOKEN", "")
    if not t:
        t = subprocess.run(["gh", "auth", "token"], capture_output=True,
                           text=True, timeout=15).stdout.strip()
    return t


def put(path, content):
    h = {"Authorization": "Bearer " + token(), "Accept": "application/vnd.github+json"}
    sha = None
    try:
        g = requests.get(BASE + path, headers=h, timeout=15)
        if g.ok:
            sha = (g.json() or {}).get("sha")
    except Exception:
        pass
    raw = content if isinstance(content, (bytes, bytearray)) else content.encode("utf-8")
    p = {"message": "Cross-disciplinary elevation " + str(int(time.time())),
         "content": base64.b64encode(raw).decode(), "branch": "main"}
    if sha:
        p["sha"] = sha
    r = requests.put(BASE + path, headers=h, json=p, timeout=30)
    return r.ok, r.status_code


def load_brains():
    sys.path.insert(0, ROOT)
    from local_brain import LocalBrain
    from dev_brain import DevBrain
    return (LocalBrain(os.path.join(ROOT, "data", "local_brain.json")),
            DevBrain(os.path.join(ROOT, "data", "dev_brain.json")))


def run():
    from brain_ensemble import ensemble
    lb, db = load_brains()
    results = []
    stamp = int(time.time())
    for dept, faculties in RELATED.items():
        q = ("ในฐานะ '%s' ของ Zyphere จงเรียนรู้ความรู้ข้ามสาขาที่เกี่ยวข้อง: %s "
             "อธิบาย 5 ประเด็นว่าสาขาเหล่านี้สัมพันธ์กับงานของฝ่ายคุณอย่างไร "
             "และฝ่ายอื่นต้องทำงานร่วมกันยังไง เพื่อให้ทุกแผนกยกระดับพร้อมกัน "
             "ตอบภาษาไทย ข้อละ 1 ประโยค คั่นด้วย ';'" %
             (dept, ", ".join(faculties)))
        try:
            r = ensemble([{"role": "user", "content": q}], want_synthesis=True)
            text = r.get("text", "")
            sources = r.get("sources", [])
        except Exception as e:
            text, sources = "", ["error:" + str(e)[:60]]
        lessons = [x.strip() for x in re.split(r"[;\n]", text)
                   if x.strip() and len(x.strip()) > 10][:5]
        if not lessons:
            lessons = ["ฝ่าย " + dept + " ต้อง study สาขา " + faculties[0] + " เพิ่มเติม"]
        for ls in lessons:
            try: lb.learn_text(ls, source="cross:" + dept)
            except Exception: pass
            try: db.experience(ls, role="cross:" + dept)
            except Exception: pass
        rec = {"dept": dept, "related_faculties": faculties, "lessons": lessons,
               "sources": sources, "level": "cross-disciplinary", "t": stamp}
        results.append(rec)
        print("elevated", dept, len(lessons), flush=True)
    # merge into co_learning log so LEARNING.html shows it live
    try:
        log = json.load(open(LOG, encoding="utf-8")).get("log", [])
    except Exception:
        log = []
    log.extend(results)
    json.dump({"log": log[-100:]}, open(LOG, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    md = ["# การยกระดับข้ามสาขาวิชาของทุกแผนก Zyphere", "",
          "รอบ: " + time.strftime("%Y-%m-%d %H:%M"), "",
          "ทุกแผนกเรียนรู้สาขาที่สัมพันธ์กับงานของตน พร้อมกันทั้งหมด " +
          "เพื่อให้การทำงานเชื่อมโยงกัน ไม่ใช่ต่างคนต่างทำ", ""]
    for r in results:
        md += ["## " + r["dept"], "",
               "- สาขาที่เกี่ยวข้อง: " + ", ".join(r["related_faculties"]), ""]
        for x in r["lessons"]:
            md.append("- " + x)
        md.append("- แหล่งสมอง: " + ", ".join(r["sources"]))
        md.append("")
    put("CROSS_DISCIPLINARY.md", "\n".join(md))
    put("cross_disciplinary.json", json.dumps({"results": results, "t": stamp},
                                              ensure_ascii=False, indent=2))
    # also publish updated co-learning log for Render
    put("co_learning.json", json.dumps({"log": log[-100:]},
                                       ensure_ascii=False, indent=2))
    print("DONE", len(results), "departments elevated together")


if __name__ == "__main__":
    run()
