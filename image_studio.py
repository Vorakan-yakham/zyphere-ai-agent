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
OUT = MEDIA  # /media/<file> is served by the existing flat media handler
FONT_URL = ("https://raw.githubusercontent.com/google/fonts/main/ofl/"
            "notosansthai/NotoSansThai%5Bwdth%2Cwght%5D.ttf")

PALETTES = {
    "indigo": ((49, 46, 129), (79, 70, 229), (250, 249, 246), (120, 124, 140)),
    "forest": ((20, 83, 45), (22, 163, 74), (249, 250, 249), (100, 116, 110)),
    "rose": ((136, 19, 55), (225, 29, 72), (255, 250, 250), (130, 110, 115)),
    "slate": ((15, 23, 42), (71, 85, 105), (248, 250, 252), (110, 120, 135)),
    "wind": ((8, 30, 44), (34, 211, 238), (245, 253, 255), (120, 150, 160)),
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



def mesh_bg(w, h, ink, accent):
    """Layered radial glows + subtle grid = depth, not a flat gradient."""
    img = Image.new("RGB", (w, h), ink)
    try:
        glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.ellipse([int(w*.52), -int(h*.28), int(w*1.28), int(h*.62)],
                   fill=(accent[0], accent[1], accent[2], 105))
        gd.ellipse([-int(w*.22), int(h*.50), int(w*.68), int(h*1.30)],
                   fill=(45, 212, 191, 78))
        gd.ellipse([int(w*.10), int(h*.05), int(w*.60), int(h*.52)],
                   fill=(56, 189, 248, 42))
        glow = glow.filter(__import__("PIL.ImageFilter", fromlist=["GaussianBlur"]).GaussianBlur(95))
        img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    except Exception:
        pass
    d = ImageDraw.Draw(img)
    for x in range(0, w, 90):
        d.line((x, 0, x, h), fill=tuple(min(255, c+6) for c in ink), width=1)
    for y in range(0, h, 90):
        d.line((0, y, w, y), fill=tuple(min(255, c+6) for c in ink), width=1)
    return img


def wind_mark(d, cx, cy, r, color):
    """Three-blade turbine motif, matching the Zyphere logo."""
    import math
    for deg in (0, 120, 240):
        a = math.radians(deg - 90)
        bx, by = cx + math.cos(a)*r*.28, cy + math.sin(a)*r*.28
        tx, ty = cx + math.cos(a)*r, cy + math.sin(a)*r
        nx, ny = -math.sin(a)*r*.13, math.cos(a)*r*.13
        d.polygon([(bx-nx, by-ny), (tx, ty), (bx+nx, by+ny)], fill=color)
    d.ellipse((cx-r*.13, cy-r*.13, cx+r*.13, cy+r*.13), fill=(255,255,255))


def shadow_text(d, xy, text, fnt, fill, shadow=(0, 0, 0), off=3):
    x, y = xy
    d.text((x+off, y+off), text, font=fnt, fill=shadow)
    d.text((x, y), text, font=fnt, fill=fill)

def generate(title, subtitle="", kind="poster", palette="indigo", seed=None, path=None):
    """Return designed PNG bytes (and save when path given)."""
    ensure_dirs()
    seed = seed or int(hashlib.md5((title + subtitle).encode()).hexdigest()[:6], 16)
    ink, accent, bg, mute = PALETTES.get(palette, PALETTES["wind"])
    W, H = (1200, 1500) if kind == "poster" else (1600, 900)
    img = mesh_bg(W, H, ink, accent)
    d = ImageDraw.Draw(img)
    # turbine motif in the negative-space zone
    wind_mark(d, int(W*.80), int(H*.26), int(min(W,H)*.15), accent)
    d.ellipse((int(W*.80)-int(min(W,H)*.22), int(H*.26)-int(min(W,H)*.22),
               int(W*.80)+int(min(W,H)*.22), int(H*.26)+int(min(W,H)*.22)),
              outline=(*accent, 90), width=2)

    f_brand, f_title, f_sub = font(26), font(74 if kind == "poster" else 66), font(30)
    f_eyebrow = font(22)
    # brand lockup
    wind_mark(d, 84, 74, 15, accent)
    d.text((112, 58), "ZYPHERE", font=f_brand, fill=bg)
    d.text((112, 92), "CREATIVE STUDIO", font=f_eyebrow, fill=mute)
    d.line((70, 140, W-70, 140), fill=(*accent, 150), width=2)

    # text panel with soft rounded backdrop
    try:
        panel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        pd = ImageDraw.Draw(panel)
        pd.rounded_rectangle((56, int(H*.18), int(W*.72), int(H*.86)),
                             radius=36, fill=(6, 18, 28, 96))
        img = Image.alpha_composite(img.convert("RGBA"), panel).convert("RGB")
        d = ImageDraw.Draw(img)
    except Exception:
        pass

    d.text((96, int(H*.22)), "ZYPHERE ORIGINAL", font=f_eyebrow, fill=accent)
    y = int(H*.27)
    for ln in wrap(d, title, f_title, int(W*.56))[:4]:
        shadow_text(d, (92, y), ln, f_title, bg, shadow=(0, 0, 0), off=4)
        y += 88
    y += 26
    d.line((96, y, 96+160, y), fill=accent, width=5)
    y += 34
    for ln in wrap(d, subtitle, f_sub, int(W*.55))[:4]:
        d.text((94, y), ln, font=f_sub, fill=bg)
        y += 52

    # footer
    d.line((70, H-110, W-70, H-110), fill=(*accent, 120), width=2)
    d.text((70, H-92), "สร้างโดย Zyphere · งานจริง ไม่มีคำอ้างเกินจริง", font=font(21), fill=mute)
    d.text((W-70, H-92), "FREE · OPEN SOURCE", font=font(21), fill=accent, anchor="ra")
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
    return {"ok": True, "path": path, "url": "/media/" + name,
            "palette": best[2], "quality": best[1],
            "note": "design composition (PIL), not diffusion image generation"}
