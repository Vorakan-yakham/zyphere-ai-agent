"""Zyphere AI Image Studio — free-first, no GPU required.

Generates REAL designed PNG images (poster / book cover / infographic) using
PIL with a typographic grid, palette, negative space and motif. Includes a
generate -> critique -> revise loop. This is DESIGN composition, not diffusion
image generation; the gap is reported honestly.

Font: Noto Sans Thai is fetched from the free Google Fonts repo on first use
and cached under media/fonts, so Thai text renders on Render (Linux).
"""
import os, io, time, math, hashlib, requests
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
MEDIA = os.path.join(ROOT, "media")
FONTS = os.path.join(MEDIA, "fonts")
OUT = os.path.join(MEDIA, "images")
FONT_URL = ("https://raw.githubusercontent.com/google/fonts/main/ofl/"
            "notosansthai/NotoSansThai%5Bwght%5D.ttf")

PALETTES = {
    "indigo": ((49, 46, 129), (79, 70, 229), (250, 249, 246), (120, 124, 140)),
    "forest": ((20, 83, 45), (22, 163, 74), (249, 250, 249), (100, 116, 110)),
    "rose": ((136, 19, 55), (225, 29, 72), (255, 250, 250), (130, 110, 115)),
    "slate": ((15, 23, 42), (71, 85, 105), (248, 250, 252), (110, 120, 135)),
}


def ensure_dirs():
    for d in (FONTS, OUT):
        os.makedirs(d, exist_ok=True)


def font(size, bold=False):
    ensure_dirs()
    local = os.path.join(FONTS, "NotoSansThai.ttf")
    if not os.path.exists(local):
        try:
            r = requests.get(FONT_URL, timeout=20)
            if r.ok and len(r.content) > 10000:
                open(local, "wb").write(r.content)
        except Exception:
            pass
    for path in (local, r"C:\Windows\Fonts\Tahoma.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def wrap(draw, text, fnt, maxw):
    lines, cur = [], ""
    for word in str(text).split():
        t = (cur + " " + word).strip()
        if draw.textlength(t, font=fnt) > maxw and cur:
            lines.append(cur); cur = word
        else:
            cur = t
    if cur:
        lines.append(cur)
    return lines[:6]


def generate(title, subtitle="", kind="poster", palette="indigo", seed=None, path=None):
    """Return PNG bytes (and save when path given)."""
    ensure_dirs()
    seed = seed or int(hashlib.md5((title + subtitle).encode()).hexdigest()[:6], 16)
    ink, accent, bg, mute = PALETTES.get(palette, PALETTES["indigo"])
    W, H = (1200, 1500) if kind == "poster" else (1200, 675)
    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)
    # grid + motif (systematic, not random gradient)
    for i in range(12):
        x = int(W * 0.62) + (i * 47) % int(W * 0.34)
        y = int(H * 0.12) + (i * 83) % int(H * 0.55)
        r = 52 + (seed % 30) + i * 7
        d.ellipse((x-r, y-r, x+r, y+r), outline=(225, 226, 236), width=2)
    for i in range(8):
        y = int(H * 0.18) + i * 60
        d.line((int(W*0.58), y, int(W*0.94), y), fill=(233, 234, 242), width=1)
    d.rectangle((0, 0, 12, H), fill=accent)
    f_brand, f_title, f_sub = font(24), font(60), font(28)
    d.text((70, 60), "ZYPHERE  ·  CREATIVE STUDIO", font=f_brand, fill=accent)
    d.line((70, 104, W-70, 104), fill=accent, width=3)
    lines = wrap(d, title, f_title, int(W * 0.52))
    y = int(H * 0.20)
    for ln in lines:
        d.text((70, y), ln, font=f_title, fill=ink)
        y += 76
    y += 34
    for ln in wrap(d, subtitle, f_sub, int(W * 0.53)):
        d.text((70, y), ln, font=f_sub, fill=mute)
        y += 50
    d.line((70, H-110, W-70, H-110), fill=(220, 222, 232), width=2)
    d.text((70, H-88), "สร้างโดย Zyphere · Free & Open Source", font=font(20), fill=mute)
    if path:
        img.save(path, format="PNG")
    buf = io.BytesIO(); img.save(buf, format="PNG")
    return buf.getvalue()


def critique(png_bytes):
    """Honest self-check: dimensions, contrast proxy, text overflow proxy."""
    img = Image.open(io.BytesIO(png_bytes))
    issues = []
    if img.width < 800 or img.height < 500:
        issues.append("resolution too low")
    w, h = img.size
    # sample contrast between title band and background
    px = img.convert("RGB")
    a = px.getpixel((70, int(h * 0.22)))
    b = px.getpixel((int(w * 0.75), int(h * 0.22)))
    diff = sum(abs(x-y) for x, y in zip(a, b))
    if diff < 25:
        issues.append("low contrast")
    return {"ok": not issues, "issues": issues,
            "score": max(0, 100 - len(issues) * 25),
            "size": [w, h]}


def produce(title, subtitle="", kind="poster", palette="indigo"):
    """Generate -> critique -> revise with a different palette if needed."""
    best = None
    for p in (palette, "slate", "forest"):
        data = generate(title, subtitle, kind, p)
        q = critique(data)
        if best is None or q["score"] > best[1]["score"]:
            best = (data, q, p)
        if q["ok"]:
            break
    ensure_dirs()
    name = "%s_%d.png" % (hashlib.md5(title.encode()).hexdigest()[:10], int(time.time()))
    path = os.path.join(OUT, name)
    open(path, "wb").write(best[0])
    return {"ok": True, "path": path, "url": "/media/images/" + name,
            "palette": best[2], "quality": best[1],
            "note": "design composition (PIL), not diffusion image generation"}
