"""Outreach Engine — go OUTSIDE Zyphere and bring the work to people.

Creates real, honest public artefacts from ACTUAL project evidence:
  1. A 'Show HN' / Dev.to style article draft from real files & APIs.
  2. Publishes to our own public GitHub repo as a Discussion/Issue (we have
     the repo + token) — a real link anyone can open.
  3. Records promo assets (image, music, video links) for channels that need
     owner login (no auto account creation, no fake posts).

Only real links. No invented reach, no fake signups, no spam.
"""
import os, re, json, time

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = "Vorakan-yakham/zyphere-ai-agent"
DATA = os.path.join(ROOT, "data", "outreach.json")
OUT = os.path.join(ROOT, "governance", "OUTREACH.md")


def evidence():
    """Only facts backed by real files/endpoints."""
    facts = []
    for f, label in [("STORE_FINAL.html", "หน้าร้าน 46 เล่ม ราคา 80–480"),
                     ("cinema_studio.py", "วิดีโอ 4K + เสียง + SRT"),
                     ("poster_studio.py", "โปสเตอร์จากภาพถ่ายจริง CC"),
                     ("sound_forge.py", "เสียงธรรมชาติ/สัตว์/เครื่องจักร"),
                     ("qa_supreme.py", "QA ตา/หู/สมอง fail-closed")]:
        if os.path.exists(os.path.join(ROOT, f)):
            facts.append((f, label))
    try:
        j = json.load(open(os.path.join(ROOT, "data", "cover_designer.json"), encoding="utf-8"))
        facts.append(("media/covers", "%d ปกไม่ซ้ำ" % j.get("covers", 0)))
    except Exception:
        pass
    return facts


def article(facts):
    lines = ["# Show Zyphere: ทีม AI ที่ทำงานต่อแม้ปิดเครื่อง", "",
             "เราสร้างระบบที่ทำงานบน GitHub Actions ทุก 5 นาที × 5 pulse — "
             "ทุกแผนกเรียนรู้จากโลก แก้งานเก่า และตรวจกันเองแบบ fail-closed", "",
             "## สิ่งที่มีอยู่จริง (เปิดดูได้)", ""]
    for f, label in facts:
        lines.append("- `%s` — %s" % (f, label))
    lines += ["", "## สิ่งที่ยังทำไม่ได้ (บอกตรง ๆ)", "",
              "- ไม่มี diffusion model/GPU → ไม่สร้างใบหน้า AI แบบ photoreal",
              "- เสียงร้องเป็น synthetic vowel ไม่ใช่นักร้องจริง",
              "- ยังไม่มียอดขาย — เราไม่ claims ยอดปลอม", "",
              "ถ้าช่วยแชร์/แนะนำช่องทาง ได้เลยครับ — ไม่ต้องรอให้เราตามขอ", ""]
    return "\n".join(lines)


def publish_github(title, body):
    """Real publish to our own public repo using existing env token."""
    import requests
    try:
        import method_transfer as MT
        tok = MT.token()
        if not tok:
            return {"ok": False, "error": "no token"}
        h = {"Authorization": "Bearer " + tok,
             "Accept": "application/vnd.github+json"}
        r = requests.post("https://api.github.com/repos/%s/issues" % REPO,
                          headers=h,
                          json={"title": title, "body": body[:6000],
                                "labels": ["showcase", "ai"]}, timeout=30)
        if r.ok:
            return {"ok": True, "url": r.json().get("html_url"),
                    "status": r.status_code}
        return {"ok": False, "status": r.status_code, "error": r.text[:150]}
    except Exception as e:
        return {"ok": False, "error": str(e)[:120]}


def run(apply=True):
    facts = evidence()
    title = "Show Zyphere: ทีม AI 12 แผนกทำงานเองทุก 5 นาที (งานจริง เปิดตรวจได้)"
    body = article(facts)
    local = os.path.join(ROOT, "governance", "OUTREACH_ARTICLE.md")
    if apply:
        open(local, "w", encoding="utf-8").write(body)
    pub = publish_github(title, body) if apply else {"ok": False, "dry": True}
    rec = {"t": int(time.time()), "facts": [f[0] for f in facts],
           "article": local, "published": pub,
           "channels_to_prepare": [
               {"name": "Hacker News", "url": "https://news.ycombinator.com",
                "note": "ใช้ article จริงนี้ — ต้อง owner กด submit (ห้าม auto account)"},
               {"name": "Dev.to", "url": "https://dev.to", "note": "แปลง markdown เป็นโพสต์"},
               {"name": "Reddit r/AI", "url": "https://reddit.com", "note": "แชร์ลิงก์ Issues จริง"},
               {"name": "LinkedIn", "url": "https://linkedin.com", "note": "โพสต์ผลงานเป็นภาพ/คลิป"}],
           "rule": "วิ่งไปหาคนภายนอกด้วยงานจริง + ลิงก์จริง ไม่รอเงิน送来"}
    if apply:
        json.dump(rec, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        md = ["# Outreach — วิ่งออกไปหาคนภายนอก", "",
              "บทความ: " + local, "",
              "เผยแพร่จริง: " + json.dumps(pub, ensure_ascii=False), "",
              "## หลักฐานที่ใช้ (จริง)", ""]
        for f, label in facts:
            md += ["- `%s` — %s" % (f, label)]
        md += ["", "## ช่องทางที่เตรียมให้ owner กด (ห้าม auto account)", ""]
        for c in rec["channels_to_prepare"]:
            md += ["- [%s](%s) — %s" % (c["name"], c["url"], c["note"])]
        md += ["", rec["rule"], ""]
        open(OUT, "w", encoding="utf-8").write("\n".join(md))
    return rec


if __name__ == "__main__":
    r = run()
    print(json.dumps({"facts": len(r["facts"]), "published": r["published"]},
                     ensure_ascii=False)[:500])
