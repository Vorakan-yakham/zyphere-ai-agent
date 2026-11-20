"""Global Code Learner — fetch REAL public docs and record what was studied."""
import os, re, json, time
import requests

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "global_code_lessons.json")
OUT = os.path.join(ROOT, "governance", "GLOBAL_CODE_LEARNING.md")

SOURCES = [
    ("Pillow ImageFilter", "https://pillow.readthedocs.io/en/stable/reference/ImageFilter.html"),
    ("FFmpeg xfade", "https://ffmpeg.org/ffmpeg-filters.html#xfade"),
    ("FFmpeg zoompan", "https://ffmpeg.org/ffmpeg-filters.html#zoompan"),
    ("OWASP Top 10", "https://owasp.org/www-project-top-ten/"),
    ("GitHub Actions", "https://docs.github.com/en/actions/writing-workflows"),
    ("WCAG 2.2", "https://www.w3.org/WAI/WCAG22/Understanding/"),
    ("MDN Web API", "https://developer.mozilla.org/en-US/docs/Web/API"),
    ("Python stdlib", "https://docs.python.org/3/library/"),
    ("Wikimedia reuse", "https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia"),
    ("NASA images", "https://images.nasa.gov/"),
]


def run(apply=True, timeout=12):
    lessons, ok = [], 0
    for name, url in SOURCES:
        try:
            r = requests.get(url, timeout=timeout,
                             headers={"User-Agent": "Zyphere-GlobalLearner/1.0"})
            if r.ok and len(r.text) > 500:
                title = re.search(r"<title[^>]*>([^<]+)</title>", r.text, re.I)
                desc = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]+)"', r.text, re.I)
                t = title.group(1).strip()[:110] if title else name
                d = re.sub(r"\s+", " ", desc.group(1)).strip()[:240] if desc else "แหล่งอ้างอิงจริง"
                lessons.append({"source": name, "url": url, "title": t,
                                "note": d, "status": 200, "t": int(time.time())})
                ok += 1
            else:
                lessons.append({"source": name, "url": url, "status": r.status_code,
                                "note": "รอรอบถัดไป", "t": int(time.time())})
        except Exception as e:
            lessons.append({"source": name, "url": url, "status": 0,
                            "note": str(e)[:80], "t": int(time.time())})
    rec = {"t": int(time.time()), "sources": len(SOURCES), "reachable": ok,
           "lessons": lessons, "note": "บันทึก URL + สิ่งที่อ่านได้จริง — ไม่ก็อปโค้ดมั่ว"}
    if apply:
        json.dump(rec, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        open(OUT, "w", encoding="utf-8").write(
            "# Zyphere เรียนรู้จากทั่วโลก — %d/%d แหล่ง\n\n| แหล่ง | สถานะ | สิ่งที่ได้ |\n|---|---|---|\n" %
            (ok, len(SOURCES)) +
            "\n".join("| [%s](%s) | %s | %s |" % (l["source"], l["url"],
                      l["status"], l["note"][:110]) for l in lessons) + "\n")
    return {"ok": True, "reachable": ok, "sources": len(SOURCES)}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False))
