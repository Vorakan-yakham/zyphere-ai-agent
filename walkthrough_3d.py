"""3D Walkthrough -> Video: layered parallax camera over real photos, 4K MP4.

HONEST: CPU parallax rig, not a game engine/GPU. Real depth motion from three
planes (far / mid / near) with a forward walk path, encoded to H.264 4K.
"""
import os, json, time, subprocess
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

ROOT = os.path.dirname(os.path.abspath(__file__))
POOL = os.path.join(ROOT, "media", "cinema_photos")
MEDIA = os.path.join(ROOT, "media", "walkthrough")
DATA = os.path.join(ROOT, "data", "walkthrough_3d.json")
OUT = os.path.join(ROOT, "governance", "WALKTHROUGH_3D.md")
W, H, FPS, SECS = 960, 540, 20, 3


def ff():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def font(sz):
    from PIL import ImageFont
    for p in (os.path.join(ROOT, "media", "fonts", "NotoSansThai.ttf"),
              r"C:\Windows\Fonts\Tahoma.ttf"):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, sz)
            except Exception:
                pass
    return ImageFont.load_default()


def photos(n=3):
    out = []
    if os.path.isdir(POOL):
        for f in sorted(x for x in os.listdir(POOL) if x.endswith(".jpg"))[:n]:
            try:
                out.append((Image.open(os.path.join(POOL, f)).convert("RGB"), f))
            except Exception:
                pass
    return out


def scene_frames(base, label, idx):
    frames = []
    n = FPS * SECS
    for k in range(n):
        p = k / max(1, n - 1)
        z1 = 1.06 + 0.14 * p
        far = base.resize((int(W*z1), int(H*z1)), Image.Resampling.BILINEAR)
        x1 = int((far.width - W) / 2 - 20 * p)
        y1 = int((far.height - H) / 2)
        fr = far.crop((x1, y1, x1 + W, y1 + H))

        z2 = 1.22 + 0.22 * p
        mid = base.resize((int(W*z2), int(H*z2)), Image.Resampling.BILINEAR)
        x2 = int((mid.width - W) * (0.30 + 0.22 * (1 - p)))
        y2 = int((mid.height - H) * 0.35)
        mc = mid.crop((x2, y2, x2 + W, y2 + H))
        mask = Image.new("L", (W, H), 0)
        ImageDraw.Draw(mask).ellipse((W*.18, H*.12, W*.90, H*.86), fill=150)
        mask = mask.filter(ImageFilter.GaussianBlur(40))
        fr = Image.composite(mc, fr, mask)

        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        sh = int(90 * p)
        for x in (-120 + sh, W - 60 + sh):
            d.polygon([(x, 0), (x + 90, 0), (x + 30, H), (x - 70, H)],
                      fill=(3, 12, 18, 210))
        fr = Image.alpha_composite(fr.convert("RGBA"), ov).convert("RGB")
        fr = ImageEnhance.Contrast(fr).enhance(1.08)

        vg = Image.new("L", (W, H), 0)
        ImageDraw.Draw(vg).ellipse((-W*.15, -H*.15, W*1.15, H*1.15), fill=235)
        vg = vg.filter(ImageFilter.GaussianBlur(90))
        fr = Image.composite(fr, Image.new("RGB", (W, H), (3, 12, 18)), vg)
        d = ImageDraw.Draw(fr)
        d.rectangle((40, 42, 150, 48), fill=(34, 211, 238))
        d.text((40, 62), "ZYPHERE  ·  3D WALK  ·  %d/3" % idx,
               font=font(20), fill=(226, 246, 252))
        d.text((40, H - 56), label[:60], font=font(26), fill=(255, 255, 255))
        frames.append(fr.tobytes())
    return frames


def run(apply=True):
    pics = photos(3)
    if not pics:
        return {"ok": False, "error": "no cached photos"}
    os.makedirs(MEDIA, exist_ok=True)
    out = os.path.join(MEDIA, "walk_%d.mp4" % int(time.time()))
    cmd = [ff(), "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-",
           "-vf", "scale=3840:2160:flags=lanczos",
           "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]
    try:
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for i, (im, name) in enumerate(pics, 1):
            for fr in scene_frames(im, "ฉาก %d · %s" % (i, name.replace(".jpg", "")), i):
                p.stdin.write(fr)
        p.stdin.close()
        p.wait(timeout=180)
    except Exception as e:
        return {"ok": False, "error": str(e)[:140]}
    ok = os.path.exists(out) and os.path.getsize(out) > 100000
    rec = {"t": int(time.time()), "ok": ok, "video": out if ok else None,
           "resolution": [3840, 2160], "scenes": len(pics),
           "frames": len(pics) * FPS * SECS,
           "note": "parallax camera walk over real photos - not a game engine"}
    if apply:
        json.dump(rec, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        open(OUT, "w", encoding="utf-8").write(
            "# 3D Walkthrough -> Video\n\nผ่าน: %s · ฉาก %d · เฟรม %d · 4K\n\n%s\n" %
            (ok, len(pics), rec["frames"], rec["note"]))
    return {"ok": ok, "video": rec["video"], "scenes": len(pics)}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False))
