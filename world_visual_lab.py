"""World Visual Lab — send the graphic engineer OUT into the world.

Harvest REAL images + licence metadata from open sources (Wikimedia Commons,
Openverse), learn style grammar from genuine tags/titles/categories, store a
visual reference library locally, then hand the learned rules to poster/cover
designers. NO paid API, NO invented examples, NO fake image claims.
"""
import os, re, json, time, hashlib

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "world_visual_library.json")
OUT = os.path.join(ROOT, "governance", "WORLD_VISUAL_STUDY.md")
QUERIES = ["portrait photography studio light", "graphic design poster typography",
           "traditional thai costume portrait", "cinematic lighting portrait",
           "product photography minimal"]

STYLE_RULES = [
    (r"portrait|face|คน|ใบหน้า", "subject", "ภาพบุคคล: ต้องมีจุดโฟกัสที่ดวงตา + แสงตกกระทบนุ่ม"),
    (r"light|studio|แสง|lighting", "light", "แสง: ใช้ key light ด้านข้าง + fill อ่อน ๆ ไม่แบน"),
    (r"poster|typography|text|ตัวอักษร", "type", "ตัวอักษร: headline ใหญ่ชัด + hierarchy 3 ระดับ"),
    (r"costume|thai|traditional|ชุดไทย", "culture", "วัฒนธรรม: ใช้สัญลักษณ์จริง ไม่แต่งศัพท์"),
    (r"minimal|product|สินค้า", "space", "พื้นที่ว่าง: ให้ subject หายใจ อย่าแน่นเกินไป"),
]


def harvest(query):
    import requests
    items = []
    try:
        r = requests.get("https://api.openverse.org/v1/images/",
            params={"q": query, "page_size": 8, "license": "cc0,pdm,by,by-sa"},
            headers={"User-Agent": "Zyphere-WorldVisual/1.0"}, timeout=30)
        if r.ok:
            for x in r.json().get("results", []):
                items.append({"source": "Openverse", "title": str(x.get("title", ""))[:120],
                              "url": x.get("url") or x.get("thumbnail"),
                              "license": x.get("license"),
                              "creator": str(x.get("creator", ""))[:70],
                              "tags": [str(t)[:40] for t in (x.get("tags") or [])[:8]]})
    except Exception:
        pass
    if not items:
        try:
            r = requests.get("https://commons.wikimedia.org/w/api.php",
                params={"action":"query","generator":"search",
                        "gsrsearch":"filetype:bitmap "+query[:40],"gsrnamespace":6,
                        "gsrlimit":6,"prop":"imageinfo","iiprop":"url|extmetadata",
                        "format":"json"},
                headers={"User-Agent":"Zyphere-WorldVisual/1.0"}, timeout=30)
            for pg in (r.json().get("query") or {}).get("pages", {}).values():
                ii=(pg.get("imageinfo") or [{}])[0]
                items.append({"source":"Wikimedia","title":pg.get("title","")[:120],
                    "url":ii.get("thumburl") or ii.get("url"),
                    "license":ii.get("extmetadata",{}).get("LicenseShortName",{}).get("value",""),
                    "creator":ii.get("extmetadata",{}).get("Artist",{}).get("value","")[:70],
                    "tags":[]})
        except Exception:
            pass
    return items


def learn(items):
    blob = " ".join((i.get("title","")+" "+" ".join(i.get("tags",[]))).lower() for i in items)
    rules = []
    for pat, key, rule in STYLE_RULES:
        if re.search(pat, blob):
            rules.append({"aspect": key, "rule": rule,
                          "evidence": "พบคำที่ตรงใน title/tags ของภาพจริง"})
    return rules


def run(apply=True):
    hist = []
    if os.path.exists(DATA):
        try:
            hist = json.load(open(DATA, encoding="utf-8")).get("studies", [])
        except Exception:
            pass
    gathered, rules = [], []
    for q in QUERIES:
        it = harvest(q)
        rr = learn(it)
        gathered += it[:6]
        rules += rr
    seen, uniq = set(), []
    for x in gathered:
        k = hashlib.md5(str(x.get("url")).encode()).hexdigest()
        if k not in seen and x.get("url"):
            seen.add(k); uniq.append(x)
    # dedupe rules
    out_rules, keys = [], set()
    for r in rules:
        if r["aspect"] not in keys:
            keys.add(r["aspect"]); out_rules.append(r)
    rec = {"t": int(time.time()), "sources": sorted({x["source"] for x in uniq}),
           "images": len(uniq), "rules": out_rules, "samples": uniq[:6],
           "note": "เรียนรู้จากภาพ/คำอธิบายจริงบนโลก — ไม่ได้สร้างภาพปลอม"}
    hist.append(rec); hist = hist[-30:]
    if apply:
        json.dump({"studies": hist}, open(DATA, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        md = ["# ทีมกราฟิกออกไปดูโลก (World Visual Study)", "",
              "แหล่ง: " + ", ".join(rec["sources"]) + " · ภาพจริง " + str(rec["images"]) + " ภาพ", "",
              "## กฎที่เรียนรู้จากภาพจริง", ""]
        for r in out_rules:
            md += ["- **%s**: %s (%s)" % (r["aspect"], r["rule"], r["evidence"])]
        md += ["", "## ตัวอย่างอ้างอิง (มี URL/ลิขสิทธิ์จริง)", ""]
        for x in rec["samples"]:
            md += ["- [%s](%s) — %s · %s" % (
                x["title"][:60], x["url"], x.get("license"), x.get("creator"))]
        md += ["", "กฎเหล่านี้ถูกส่งให้ poster/cover designer ใช้ต่อ", ""]
        open(OUT, "w", encoding="utf-8").write("\n".join(md))
    return rec


if __name__ == "__main__":
    r = run()
    print(json.dumps({"sources": r["sources"], "images": r["images"],
                      "rules": [x["aspect"] for x in r["rules"]]}, ensure_ascii=False))
