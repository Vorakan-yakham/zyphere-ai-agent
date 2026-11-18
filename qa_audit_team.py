"""Independent QA Audit Team — inspects EVERY built subsystem with real checks.

Verdicts are only KEEP (evidence passed), FIX (evidence failed) or UNKNOWN
(could not verify). Nothing is deleted just because it looks imperfect, and
nothing is claimed good without a measurable check.
"""
import os, json, re, time, subprocess, requests

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "governance", "QA_FULL_AUDIT.md")
DATA = os.path.join(ROOT, "data", "qa_full_audit.json")
B = "https://zyphere-ai-agent.onrender.com"
P = "https://vorakan-yakham.github.io/zyphere-ai-agent/"

AUDITORS = ["นักตรวจสอบระบบ", "นักตรวจสอบภาษา", "นักตรวจสอบสื่อ",
            "นักตรวจสอบหนังสือ", "นักตรวจสอบความปลอดภัย", "นักตรวจสอบประสบการณ์ผู้ใช้"]


def endpoint(path):
    try:
        r = requests.get(B + path, timeout=40)
        return r.status_code, r.text[:150]
    except Exception as e:
        return 0, str(e)[:100]


def source_has(file, *needles):
    p = os.path.join(ROOT, file)
    if not os.path.exists(p):
        return False, "missing"
    s = open(p, encoding="utf-8", errors="ignore").read()
    return all(n in s for n in needles), "found" if all(n in s for n in needles) else "missing marker"


def run(apply=True):
    checks = []
    def add(area, verdict, evidence, owner):
        checks.append({"area": area, "verdict": verdict,
                       "evidence": str(evidence)[:260], "owner": owner})

    # 1. Backend health + core APIs
    for p in ["/api/health", "/api/brain/status", "/api/council/autonomous/status",
              "/api/supervisors/status", "/api/conversation/status",
              "/api/media/capabilities", "/api/auto-grow/status"]:
        st, txt = endpoint(p)
        add("backend " + p, "KEEP" if st == 200 else "FIX", "HTTP %s %s" % (st, txt[:80]), AUDITORS[0])

    # 2. TTS number reading (real fixtures)
    try:
        r = subprocess.run(["node", "test_tts_numbers.js"], cwd=ROOT,
                           capture_output=True, text=True, timeout=90)
        add("TTS ตัวเลขไทย", "KEEP" if r.returncode == 0 else "FIX",
            (r.stdout or r.stderr)[:160], AUDITORS[1])
    except Exception as e:
        add("TTS ตัวเลขไทย", "UNKNOWN", str(e)[:120], AUDITORS[1])

    # 3. Frontend media-in-chat + no modal
    ok, ev = source_has("index.html", "zyphire_cinema.mp4", "User ordered media",
                        "const vm=t.match(")
    # vm marker should now be ABSENT -> check separately
    s = open(os.path.join(ROOT, "index.html"), encoding="utf-8", errors="ignore").read()
    no_modal = "const vm=t.match(" not in s
    add("UI สร้างภาพ/วิดีโอในแชท", "KEEP" if "zyphire_cinema.mp4" in s and no_modal else "FIX",
        "download button=%s, old modal=%s" % ("zyphire_cinema.mp4" in s, not no_modal), AUDITORS[5])

    # 4. Media: MP4 with audio + own image lab
    try:
        m = requests.get("https://raw.githubusercontent.com/Vorakan-yakham/zyphere-ai-agent/main/data/cinema_latest.json?x=" + str(time.time()), timeout=40).json()
        vu = (m.get("urls") or {}).get("video")
        st = requests.get("https://raw.githubusercontent.com/Vorakan-yakham/zyphere-ai-agent/main/" + vu.lstrip("/"), timeout=90) if vu else None
        import imageio_ffmpeg, tempfile
        p = os.path.join(tempfile.gettempdir(), "qa_audit.mp4")
        if st and st.ok:
            open(p, "wb").write(st.content)
            rr = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-i", p],
                                capture_output=True, text=True)
            has_audio = "Audio:" in rr.stderr
            add("วิดีโอ + เสียง", "KEEP" if has_audio else "FIX",
                "bytes=%s audio=%s" % (len(st.content), has_audio), AUDITORS[2])
        else:
            add("วิดีโอ + เสียง", "UNKNOWN", "no artefact url", AUDITORS[2])
    except Exception as e:
        add("วิดีโอ + เสียง", "UNKNOWN", str(e)[:120], AUDITORS[2])

    for f in ("own_image_lab.py", "photo_enhancement.py", "media_twin_track.py"):
        ok, ev = source_has(f, "def run(") if f != "own_image_lab.py" else source_has(f, "def generate(")
        add("grafpic lab " + f, "KEEP" if ok else "FIX", ev, AUDITORS[2])

    # 5. Ebook: real content + editor gate + standard
    try:
        r = subprocess.run(["python", "ebook_editor_gate.py"], cwd=ROOT,
                           capture_output=True, text=True, timeout=120)
        add("หนังสือ + บรรณาธิการ", "KEEP" if '"ok": true' in (r.stdout or "") else "FIX",
            (r.stdout or r.stderr)[:180], AUDITORS[3])
    except Exception as e:
        add("หนังสือ + บรรณาธิการ", "UNKNOWN", str(e)[:100], AUDITORS[3])
    for f, needles in [("human_editor.py", ("Noto Serif Thai", "def render(")),
                       ("content_visual.py", ("def analyse(", "MOTIFS"))]:
        ok, ev = source_has(f, *needles)
        add("มาตรฐานหนังสือ " + f, "KEEP" if ok else "FIX", ev, AUDITORS[3])

    # 6. Secrets / honesty
    ok, ev = source_has("set_pw.py", "os.environ")
    add("ความปลอดภัย secret", "KEEP" if ok else "FIX", ev, AUDITORS[4])
    add("โปร่งใส (ไม่ claims ยอดขาย)", "KEEP" if "ยอดขายปลอม" in open(os.path.join(ROOT, "method_transfer.py"), encoding="utf-8", errors="ignore").read() else "FIX",
        "method_transfer honesty rule", AUDITORS[4])

    result = {"t": int(time.time()), "checks": checks,
              "keep": sum(1 for c in checks if c["verdict"] == "KEEP"),
              "fix": sum(1 for c in checks if c["verdict"] == "FIX"),
              "unknown": sum(1 for c in checks if c["verdict"] == "UNKNOWN")}
    if apply:
        json.dump(result, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        md = ["# ตรวจสอบงานทุกด้านโดยทีม QA อิสระ", "",
              "KEEP=%d · FIX=%d · UNKNOWN=%d" % (result["keep"], result["fix"], result["unknown"]), "",
              "| ด้าน | ผล | หลักฐาน | ผู้ตรวจ |", "|---|---|---|---|"]
        for c in checks:
            md += ["| %s | %s | %s | %s |" % (
                c["area"], c["verdict"], c["evidence"].replace("|", "/"), c["owner"])]
        md += ["", "หลักการ: ของที่ผ่านแล้วไม่ลบ — แก้เฉพาะที่หลักฐานบอกว่าพัง", ""]
        open(OUT, "w", encoding="utf-8").write("\n".join(md))
    return result


if __name__ == "__main__":
    r = run()
    print(json.dumps({"keep": r["keep"], "fix": r["fix"], "unknown": r["unknown"]},
                     ensure_ascii=False))
    for c in r["checks"]:
        if c["verdict"] != "KEEP":
            print(c["verdict"], c["area"], c["evidence"][:90])
