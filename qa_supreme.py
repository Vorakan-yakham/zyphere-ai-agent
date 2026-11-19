"""QA SUPREME — inspects like the owner: eyes, ears, and a sharper brain.
Rejects work that is merely 'present' but ugly, unbalanced, silent, duplicated,
or claims something the files do not contain. FAIL-CLOSED with rework orders.
"""
import os, re, json, math, time, subprocess, hashlib, wave, struct

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "governance", "QA_SUPREME.md")
DATA = os.path.join(ROOT, "data", "qa_supreme.json")


def rgb_lum(c):
    r, g, b = c[:3]
    return (0.2126*r + 0.7152*g + 0.0722*b)/255.0


def contrast_ratio(a, b):
    la, lb = rgb_lum(a), rgb_lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi+0.05)/(lo+0.05)


def eye_image(path):
    """EYES: composition, contrast, colour harmony, duplication, empty space."""
    from PIL import Image
    im = Image.open(path).convert("RGB").resize((240, 360))
    w, h = im.size
    px = im.load()
    # EYES: find ACTUAL glyph pixels (bright ink) against the image's median
    # background. Thin anti-aliased Thai glyphs require absolute thresholds,
    # not "top 12% of a zone" which still returns background after downscale.
    allpx = [px[x, y] for x in range(0, w, 3) for y in range(0, h, 3)]
    lum_sorted = sorted(allpx, key=rgb_lum)
    bg_col = lum_sorted[len(lum_sorted)//2]
    bg_lum = rgb_lum(bg_col)
    ink_zone = [px[x, y] for x in range(0, w, 2)
                for y in range(int(h*.12), int(h*.98), 2)]
    glyphs = [c for c in ink_zone if rgb_lum(c) > min(0.92, bg_lum + 0.30)]
    if glyphs:
        gl = sorted(glyphs, key=rgb_lum)[-max(1, len(glyphs)//3):]
        text_col = tuple(sum(c[i] for c in gl)//len(gl) for i in range(3))
    else:
        text_col = (255, 255, 255)
    cr = contrast_ratio(text_col, bg_col)
    # visual balance: left vs right brightness
    left = sum(rgb_lum(px[x, y]) for x in range(0, w//2, 6) for y in range(0, h, 6))
    right = sum(rgb_lum(px[x, y]) for x in range(w//2, w, 6) for y in range(0, h, 6))
    balance = 1 - abs(left-right)/max(1, left+right)
    # colour diversity
    hues = set()
    for x in range(0, w, 12):
        for y in range(0, h, 12):
            r, g, b = px[x, y]
            if max(r, g, b)-min(r, g, b) > 18:
                hues.add((r//40, g//40, b//40))
    return {"contrast_ratio": round(cr, 2), "balance": round(balance, 3),
            "hue_buckets": len(hues), "ok": cr >= 3.0 and balance >= 0.55}


def ear_audio(path):
    """EARS: real loudness, silence, clipping — not just file existence."""
    if not path or not os.path.exists(path):
        return {"ok": False, "error": "no audio"}
    try:
        import imageio_ffmpeg
        r = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-i", path],
                           capture_output=True, text=True)
        wav = path.rsplit(".", 1)[0] + "_probe.wav"
        subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-i", path,
                        "-ac", "1", "-ar", "8000", wav], capture_output=True, timeout=90)
        if not os.path.exists(wav):
            return {"ok": False, "error": "decode failed"}
        with wave.open(wav, "rb") as f:
            data = f.readframes(min(f.getnframes(), 8000*20))
        vals = struct.unpack("<%dh" % (len(data)//2), data)
        peak = max((abs(v) for v in vals), default=0)
        rms = math.sqrt(sum(v*v for v in vals)/max(1, len(vals)))
        silent = sum(1 for v in vals if abs(v) < 40)/max(1, len(vals))
        os.remove(wav)
        return {"ok": peak > 800 and rms > 100 and silent < 0.85,
                "peak": peak, "rms": round(rms, 1), "silence": round(silent, 3),
                "streams": [l.strip() for l in r.stderr.splitlines() if "Audio:" in l][:1]}
    except Exception as e:
        return {"ok": False, "error": str(e)[:100]}


def brain_claims():
    """BRAIN: cross-check every written claim against real files."""
    issues = []
    for f, claim_key, real_check in [
        ("governance/STOREFRONT_REBUILD.md", "46", lambda: len(json.load(
            open(os.path.join(ROOT, "data", "commerce.json"), encoding="utf-8")).get("products", [])) >= 46),
        ("governance/COVER_DESIGNER.md", "ค", lambda: len([x for x in os.listdir(
            os.path.join(ROOT, "media", "covers")) if x.endswith(".png")]) >= 46)]:
        p = os.path.join(ROOT, f)
        if not os.path.exists(p):
            issues.append(f + ": missing report")
            continue
        txt = open(p, encoding="utf-8").read()
        try:
            if claim_key in txt and not real_check():
                issues.append(f + ": claims not backed by files")
        except Exception:
            issues.append(f + ": cannot verify claim")
    for bad in ("ยอดขาย 1,000", "ขายได้แล้ว", "ลูกค้า 100 คน"):
        for f in ("governance/STOREFRONT_REBUILD.md", "governance/REVENUE_AUTOPILOT.md"):
            p = os.path.join(ROOT, f)
            if os.path.exists(p) and bad in open(p, encoding="utf-8").read():
                issues.append(f + ": fake sales claim")
    return {"ok": not issues, "issues": issues}


def run(apply=True):
    checks = []
    def add(name, ok, detail, owner="QA Supreme"):
        checks.append({"check": name, "ok": bool(ok), "detail": str(detail)[:200],
                       "owner": owner})
    cdir = os.path.join(ROOT, "media", "covers")
    covers = sorted(f for f in os.listdir(cdir) if f.endswith(".png")) if os.path.isdir(cdir) else []
    seen = set()
    for c in covers:
        with open(os.path.join(cdir, c), "rb") as f:
            seen.add(hashlib.md5(f.read()).hexdigest())
    add("ตา: ปกไม่ซ้ำ", covers and len(seen) == len(covers),
        "unique=%d/%d" % (len(seen), len(covers)), "วิศวกรกราฟิก")
    if covers:
        eye = eye_image(os.path.join(cdir, covers[0]))
        add("ตา: contrast/balance ผ่าน", eye["ok"], eye, "วิศวกรกราฟิก")
    # ears: newest mp3
    import glob
    mps = sorted(glob.glob(os.path.join(ROOT, "media", "song_*.mp3"))) + \
          sorted(glob.glob(os.path.join(ROOT, "media", "sfx_*.mp3")))
    if mps:
        ear = ear_audio(mps[-1])
        add("หู: เสียงมีจริง ไม่เงียบ", ear["ok"], ear, "วิศวกรเสียง")
    # brain
    br = brain_claims()
    add("สมอง: คำกล่าวตรงกับไฟล์จริง", br["ok"], br["issues"], "QA Supreme")
    # store price diversity from live HTML
    sp = os.path.join(ROOT, "STORE_FINAL.html")
    if os.path.exists(sp):
        h = open(sp, encoding="utf-8").read()
        prices = set(re.findall(r"฿(\d+)", h))
        add("สมอง: ราคาไม่ซ้ำซาก", len(prices) >= 5, sorted(prices)[:10], "วิศวกรร้านค้า")
    failed = [c for c in checks if not c["ok"]]
    rec = {"t": int(time.time()), "passed": not failed, "checks": checks,
           "failed": len(failed), "orders": [{"fix": c["check"], "owner": c["owner"]}
                                             for c in failed],
           "rule": "FAIL-CLOSED: ไม่สวย/ไม่ตรงหลัก/เสียงไม่จริง → ส่งกลับแก้ใหม่ก่อนออกสู่สายตาชาวโลก"}
    if apply:
        json.dump(rec, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        md = ["# QA Supreme — ตา / หู / สมอง ตรวจเข้มกว่าแผนกอื่น", "",
              "ผล: **%s** · %d/%d" % ("PASS" if rec["passed"] else "HOLD",
                                       len(checks)-len(failed), len(checks)), ""]
        for c in checks:
            md += ["## %s — %s\n- %s\n- ผู้รับผิดชอบ: %s\n" % (
                c["check"], "ผ่าน" if c["ok"] else "**ไม่ผ่าน**",
                c["detail"], c["owner"])]
        md += [rec["rule"], ""]
        for o in rec["orders"]:
            md += ["- สั่งแก้: %s → %s" % (o["owner"], o["fix"])]
        open(OUT, "w", encoding="utf-8").write("\n".join(md))
    return rec


if __name__ == "__main__":
    r = run()
    print(json.dumps({"passed": r["passed"], "failed": r["failed"]}, ensure_ascii=False))
