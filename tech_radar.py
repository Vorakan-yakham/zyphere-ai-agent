"""Tech Radar — harvest REAL current technology knowledge from free sources and
turn it into concrete upgrade tasks for graphics/video/audio. No keys, no
account creation. Every finding cites a real URL.
"""
import os, re, json, time
import requests

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "tech_radar.json")
OUT = os.path.join(ROOT, "governance", "TECH_RADAR.md")

TOPICS = [
    ("image", "image upscaling algorithm"),
    ("video", "video interpolation frame generation"),
    ("audio", "neural audio synthesis"),
    ("design", "typography variable font"),
    ("render", "real-time rendering technique"),
]


def harvest(topic):
    import free_image_sources as F  # reuse validated HTTP helpers if needed
    out = []
    # Wikipedia REST summary — free, no key
    try:
        r = requests.get("https://en.wikipedia.org/api/rest_v1/page/summary/" +
                         requests.utils.quote(topic.replace(" ", "_")),
                         headers={"User-Agent": "Zyphere-TechRadar/1.0"}, timeout=15)
        if r.ok:
            j = r.json()
            out.append({"title": j.get("title", topic),
                        "url": j.get("content_urls", {}).get("desktop", {}).get("page", ""),
                        "note": (j.get("extract") or "")[:260], "source": "wikipedia"})
    except Exception:
        pass
    # OpenAlex — free scholarly search
    try:
        r = requests.get("https://api.openalex.org/works",
                         params={"search": topic, "per-page": 3},
                         headers={"User-Agent": "Zyphere-TechRadar/1.0"}, timeout=15)
        if r.ok:
            for w in (r.json().get("results") or [])[:3]:
                out.append({"title": str(w.get("title") or topic)[:120],
                            "url": w.get("doi") or w.get("id") or "",
                            "note": str(w.get("publication_year", "")),
                            "source": "openalex"})
    except Exception:
        pass
    return out


def upgrade_tasks(findings):
    """Map real findings to OUR concrete upgrade actions (no fake claims)."""
    text = " ".join(str(f.get("title", "")) + " " + str(f.get("note", ""))
                    for f in findings).lower()
    tasks = []
    if any(w in text for w in ("upscal", "super-resolution", "resolution")):
        tasks.append("graphics: Lanczos + multi-scale residual upscale (already in pipeline) — refine radius/percent from real findings")
    if any(w in text for w in ("interpol", "frame", "optical flow")):
        tasks.append("video: zoompan/xfade motion — evaluate frame interpolation on cached 720p render before 4K upscale")
    if any(w in text for w in ("neural", "audio", "synthes")):
        tasks.append("audio: keep 3-formant synth + browser fallback; study new synthesis papers next pulse")
    if not tasks:
        tasks.append("no direct match yet — keep harvesting; record findings for next pulse")
    return tasks


def run(apply=True):
    all_f, by_topic = [], {}
    for key, q in TOPICS:
        got = harvest(q)
        by_topic[key] = got
        all_f += [dict(x, topic=key) for x in got]
    tasks = upgrade_tasks(all_f)
    rec = {"t": int(time.time()), "findings": len(all_f), "by_topic": by_topic,
           "upgrade_tasks": tasks,
           "note": " findings from Wikipedia/OpenAlex — real URLs; tasks are next steps, not claims"}
    if apply:
        json.dump(rec, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        open(OUT, "w", encoding="utf-8").write(
            "# Tech Radar — เทคโนโลยีใหม่จากแหล่งจริง\n\nพบ **%d** ข้อมูล\n\n## สิ่งที่ต้องอัพเดท\n" %
            len(all_f) +
            "\n".join("- " + t for t in tasks) +
            "\n\n## หลักฐาน\n\n| ด้าน | ชื่อ | แหล่ง | ลิงก์ |\n|---|---|---|---|\n" +
            "\n".join("| %s | %s | %s | %s |" % (f.get("topic"), f.get("title", "")[:60],
                      f.get("source"), f.get("url", "")[:70]) for f in all_f[:20]) + "\n")
    return {"ok": True, "findings": len(all_f), "tasks": len(tasks)}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False))
