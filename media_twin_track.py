"""Twin-track media development: graphics and video improve TOGETHER.

One brief -> two teams in parallel:
  GRAPHICS: in-house image lab + photo enhancement -> PNG with measured gain
  VIDEO:    cinema studio -> MP4 + frames + overlays + SRT + narration + music
Both use the same palette/motif system so style stays consistent. Results are
published to governance/MEDIA_TWIN_TRACK.md with REAL measurements only.
"""
import os, json, time, threading
import own_image_lab as LAB
import photo_enhancement as PHOTO

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "governance", "MEDIA_TWIN_TRACK.md")
DATA = os.path.join(ROOT, "data", "media_twin.json")


def graphics_team(brief):
    r = PHOTO.run(brief, brief, apply=True)
    lab = LAB.generate(brief, apply=True)
    return {"file": r.get("file"), "before": r.get("before"), "after": r.get("after"),
            "gain_pct": r.get("improvement_pct"), "lab_file": lab.get("file"),
            "lab_quality": lab.get("quality"), "engines": 12}


def video_team(brief):
    try:
        import cinema_studio
        r = cinema_studio.run(brief, 18, "th")
        return {"ok": r.get("ok"), "video": r.get("video"), "urls": r.get("urls"),
                "srt": r.get("srt"), "coverage": r.get("coverage"),
                "music": r.get("music"), "engines": 12}
    except Exception as e:
        return {"ok": False, "error": str(e)[:180]}


def _clean(v):
    """Remove non-JSON objects (BytesIO from synth) before logging/returning."""
    if isinstance(v, dict):
        return {str(k): _clean(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_clean(x) for x in v]
    if isinstance(v, (str, int, float, bool)) or v is None:
        return v
    return str(v)[:200]


def run(brief="Zyphere สายลมสร้างสรรค์", apply=True):
    g, v = {}, {}
    def ga(): g.update(graphics_team(brief) if apply else {"skipped": True})
    def va(): v.update(video_team(brief) if apply else {"skipped": True})
    t1 = threading.Thread(target=ga); t2 = threading.Thread(target=va)
    t1.start(); t2.start(); t1.join(); t2.join()
    result = _clean({"t": int(time.time()), "brief": brief, "graphics": g, "video": v,
              "parallel": True,
              "status": "both" if g.get("file") and v.get("ok") else "partial"}
    os.makedirs(os.path.dirname(DATA), exist_ok=True)
    json.dump(result, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    md = ["# พัฒนากราฟฟิกและวิดีโอคู่ขนาน", "",
          "brief: " + brief + " · " + time.strftime("%Y-%m-%d %H:%M"), "",
          "| ทีม | ผลจริง | ตัวเลข |", "|---|---|---|",
          "| กราฟิก | %s | คมชัด %s → %s (+%s%%) |" % (
              g.get("file") or "-", g.get("before"), g.get("after"), g.get("gain_pct")),
          "| วิดีโอ | %s | %s |" % (v.get("video") or "-",
              "มีเสียง+ซับ" if v.get("ok") else str(v.get("error", ""))[:60]), "",
          "ไฟล์ตัดต่อ (frame/overlay/SRT):", json.dumps(v.get("urls") or {}, ensure_ascii=False)[:800], ""]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write("\n".join(md))
    return result


if __name__ == "__main__":
    r = run()
    print(json.dumps({"status": r["status"], "graphics": r["graphics"],
                      "video": {k: r["video"].get(k) for k in ("ok", "video", "music")}},
                     ensure_ascii=False)[:800])
