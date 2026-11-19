"""Department Scouts — EVERY department goes out and studies the world in its
own field, then brings the findings back to improve itself. No waiting to be
fed. Twelve scouts, twelve domains, real open sources, real work orders.
"""
import os, re, json, time

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "department_scouts.json")
OUT = os.path.join(ROOT, "governance", "DEPARTMENT_SCOUTS.md")

DOMAINS = [
    ("วิชาการ", "world history philosophy science", "อัปเดตความรู้พื้นฐานที่ขาด"),
    ("กราฟิก", "poster typography graphic design", "ศึกษา layout/font ที่โลกใช้จริง"),
    ("การตลาด", "content marketing growth free channels", "หาช่องทางดึงคนแบบไม่จ่ายเงิน"),
    ("โปรแกรมเมอร์", "creative coding generative art python", "หาเทคนิคโค้ดใหม่มาปรับระบบ"),
    ("ฐานข้อมูล", "local first offline database pattern", "หาวิธีเก็บข้อมูลให้ทุกฝ่ายใช้ร่วม"),
    ("QA", "software quality gate acceptance criteria", "ยกระดับมาตรฐานตรวจรับงาน"),
    ("หัวหน้าฝ่าย", "team autonomy management pattern", "หาวิธีกระตุ้นทีมโดยไม่ต้องสั่ง"),
    ("หัวหน้าแผนก", "organizational accountability system", "หาวิธีวัดผลงานแผนกจริง"),
    ("สมอง AI", "persistent memory offline ai agent", "หาวิธีจำและพัฒนาต่อโดยไม่พึ่ง API"),
    ("ดนตรี", "music theory songwriting arrangement", "ศึกษาโครงสร้างเพลงที่ฟังดี"),
    ("ภาพยนตร์", "film editing continuity character design", "ศึกษาความต่อเนื่องของตัวละคร"),
    ("บรรณาธิการ", "editorial writing plain language thai", "ศึกษาการเขียนให้อ่านง่ายและมีชีวิต"),
]


def probe(query):
    import requests
    hits = []
    for url, params, key in [
        ("https://en.wikipedia.org/w/api.php",
         {"action":"query","list":"search","srsearch":query,"format":"json","srlimit":3},
         lambda j: [x.get("title","") for x in j.get("query",{}).get("search",[])]),
        ("https://api.openalex.org/works", {"search":query,"per-page":3},
         lambda j: [str(x.get("title",""))[:110] for x in j.get("results",[])]),
        ("https://api.github.com/search/repositories",
         {"q":query,"sort":"stars","per_page":3},
         lambda j: [x.get("full_name","") for x in j.get("items",[])]),
    ]:
        try:
            r = requests.get(url, params=params,
                             headers={"User-Agent":"Zypher-DeptScout/1.0"}, timeout=20)
            if r.ok:
                hits += [str(x) for x in key(r.json()) if x]
        except Exception:
            pass
    return hits[:8]


def run(apply=True):
    reports = []
    for dept, query, goal in DOMAINS:
        found = probe(query)
        reports.append({"dept": dept, "studied": query, "found": found,
                        "order": goal + (" — อ้างอิง: " + found[0][:80] if found else "")})
    ok = sum(1 for r in reports if r["found"])
    rec = {"t": int(time.time()), "scouts": len(reports), "successful": ok,
           "reports": reports,
           "rule": "ทุกแผนกต้องออกไปดูงานโลกแล้วนำมาพัฒนาตนเองทุก.rอบ — ห้ามรอป้อน"}
    if apply:
        json.dump(rec, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        md = ["# ทีมสำรวจ 12 แผนก — ออกไปดูโลกกันแล้ว", "",
              "สำเร็จ %d/%d แผนก" % (ok, len(reports)), "",
              "| แผนก | สิ่งที่ศึกษา | งานที่นำกลับมาพัฒนา |", "|---|---|---|"]
        for r in reports:
            md += ["| %s | %s | %s |" % (
                r["dept"], r["studied"], r["order"][:160])]
        md += ["", rec["rule"], ""]
        open(OUT, "w", encoding="utf-8").write("\n".join(md))
    return rec


if __name__ == "__main__":
    r = run()
    print(json.dumps({"scouts": r["scouts"], "successful": r["successful"]},
                     ensure_ascii=False))
