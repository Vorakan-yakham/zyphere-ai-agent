"""Autonomous Scout — NOBODY feeds it. Every cycle it goes OUT to open sources
(Wikipedia, OpenAlex, arXiv, GitHub, Hacker News, Openverse), studies what the
world is actually making, extracts usable techniques, and turns them into
executable work orders for our engineers.

This is the 'don't wait for mother bird to feed you' rule, written in code.
"""
import os, re, json, time, hashlib

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "autonomous_scout.json")
OUT = os.path.join(ROOT, "governance", "AUTONOMOUS_SCOUT.md")

SOURCES = [
    ("Wikipedia", "https://en.wikipedia.org/w/api.php",
     {"action":"query","list":"search","srsearch":"graphic design typography poster","format":"json","srlimit":5}),
    ("OpenAlex", "https://api.openalex.org/works",
     {"search":"visual design principles","per-page":5}),
    ("arXiv", "http://export.arxiv.org/api/query",
     {"search_query":"all:image generation design","max_results":5}),
    ("HackerNews", "https://hacker-news.firebaseio.com/v0/topstories.json", None),
    ("Openverse", "https://api.openverse.org/v1/images/",
     {"q":"graphic design poster","page_size":5,"license":"cc0,pdm,by,by-sa"}),
    ("GitHub", "https://api.github.com/search/repositories",
     {"q":"creative coding p5 topic:generative-art","sort":"stars","per_page":5}),
]


def fetch(name, url, params):
    import requests
    try:
        r = requests.get(url, params=params,
                         headers={"User-Agent":"Zypher-Scout/1.0"}, timeout=25)
        if not r.ok:
            return {"source": name, "ok": False, "status": r.status_code}
        if name == "HackerNews":
            ids = r.json()[:5]
            titles = []
            for i in ids:
                try:
                    d = requests.get("https://hacker-news.firebaseio.com/v0/item/%d.json" % i,
                                     timeout=10).json()
                    titles.append(str(d.get("title", ""))[:120])
                except Exception:
                    pass
            return {"source": name, "ok": True, "titles": titles}
        if name == "GitHub":
            return {"source": name, "ok": True,
                    "titles": [str(x.get("full_name")) + " ★" + str(x.get("stargazers_count"))
                               for x in r.json().get("items", [])]}
        if name == "Wikipedia":
            return {"source": name, "ok": True,
                    "titles": [x.get("title","") for x in
                               r.json().get("query",{}).get("search",[])]}
        if name == "OpenAlex":
            return {"source": name, "ok": True,
                    "titles": [str(x.get("title",""))[:140]
                               for x in r.json().get("results",[])]}
        if name == "Openverse":
            return {"source": name, "ok": True,
                    "titles": [str(x.get("title",""))[:120]
                               for x in r.json().get("results",[])]}
        if name == "arXiv":
            return {"source": name, "ok": True,
                    "titles": re.findall(r"<title>([^<]+)</title>", r.text)[1:6]}
    except Exception as e:
        return {"source": name, "ok": False, "error": str(e)[:100]}
    return {"source": name, "ok": False}


def orders_from(titles):
    """Turn what the world is doing into OUR next concrete work."""
    blob = " ".join(titles).lower()
    out = []
    if any(k in blob for k in ("design", "poster", "type", "visual")):
        out.append({"owner": "วิศวกรกราฟิก", "order":
                    "นำหลักการ typography/composition ที่เจอมาปรับ poster/cover รอบหน้า"})
    if any(k in blob for k in ("image", "generative", "diffusion", "render")):
        out.append({"owner": "วิศวกรภาพ", "order":
                    "ลองเทคนิค procedural/generative ใหม่ใน own_image_lab แล้ววัด contrast"})
    if any(k in blob for k in ("video", "film", "motion")):
        out.append({"owner": "วิศวกรสื่อ", "order":
                    "ปรับ film_editor ให้การตัด/เคลื่อนกล้องสมจริงขึ้นตามที่โลกทำ"})
    if not out:
        out.append({"owner": "วิศวกรสมอง", "order":
                    "บันทึกสิ่งที่เจอเป็นความรู้ใหม่แล้วหามุมประยุกต์กับระบบเรา"})
    return out


def run(apply=True):
    findings = [fetch(n, u, p) for n, u, p in SOURCES]
    titles = [t for f in findings for t in f.get("titles", [])]
    orders = orders_from(titles)
    rec = {"t": int(time.time()), "findings": findings,
           "sources_ok": [f["source"] for f in findings if f.get("ok")],
           "sample_titles": titles[:12], "orders": orders,
           "rule": "ห้ามรอป้อนความรู้ — ออกไปดูงานโลกแล้วนำมาพัฒนาตนเองทุก.rอบ"}
    if apply:
        json.dump(rec, open(DATA, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        md = ["# Autonomous Scout — ออกไปดูโลกเอง ไม่รอใครป้อน", "",
              "แหล่งที่เชื่อมสำเร็จ: " + ", ".join(rec["sources_ok"]), "",
              "## สิ่งที่โลกำลังทำ (ตัวอย่างจริง)", ""]
        for t in rec["sample_titles"]:
            md += ["- " + t]
        md += ["", "## คำสั่งพัฒนาที่ระบบตั้งขึ้นเอง", ""]
        for o in orders:
            md += ["- %s → %s" % (o["owner"], o["order"])]
        md += ["", rec["rule"], ""]
        open(OUT, "w", encoding="utf-8").write("\n".join(md))
    return rec


if __name__ == "__main__":
    r = run()
    print(json.dumps({"ok_sources": r["sources_ok"],
                      "titles": len(r["sample_titles"]),
                      "orders": len(r["orders"])}, ensure_ascii=False))
