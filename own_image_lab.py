"""Zyphere Own Image Lab — built entirely in-house (Python + Pillow + maths).

NO external image API. Twelve engineer modules compose an image:
 01 prompt parser   02 palette harmoniser   03 mesh lighting   04 noise texture
 05 depth layers    06 subject silhouette   07 ornament         08 rule-of-thirds layout
 09 typography      10 film grain/vignette  11 self-critique    12 export manifest

HONEST LIMIT: this is algorithmic design composition, NOT a diffusion model.
Photorealistic faces/scenes like the reference samples require a trained model
and GPU; we do not have one. The lab produces real, inspectable PNG artefacts
that our engineers can keep improving without outside services.
"""
import os, math, json, time, hashlib, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

ROOT = os.path.dirname(os.path.abspath(__file__))
MEDIA = os.path.join(ROOT, "media")
W, H = 1200, 1500
FONT = os.path.join(MEDIA, "fonts", "NotoSansThai.ttf")


def font(sz):
    for p in (FONT, r"C:\Windows\Fonts\Tahoma.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, sz)
            except Exception:
                pass
    return ImageFont.load_default()


# --- engineer 01: prompt parser ------------------------------------------------
def parse_prompt(text):
    t = str(text or "")
    seeds = [w for w in t.split() if len(w) > 2][:8]
    mood = "warm" if any(x in t for x in ("อบอุ่น", "warm", "golden", "sunset")) else "cool"
    return {"subject": seeds[0] if seeds else "Zyphere", "keywords": seeds, "mood": mood,
            "engineer": "01 prompt parser"}


# --- engineer 02: palette ------------------------------------------------------
def palette(mood, seed):
    base = [(8, 24, 38), (12, 52, 68)] if mood == "cool" else [(42, 22, 16), (86, 44, 22)]
    accent = [(34, 211, 238), (45, 212, 191)] if mood == "cool" else [(255, 176, 74), (236, 110, 54)]
    rnd = random.Random(seed)
    rnd.shuffle(accent)
    return {"base": base, "accent": accent, "engineer": "02 palette"}


# --- engineer 03: mesh lighting ------------------------------------------------
def mesh(w, h, pal):
    img = Image.new("RGB", (w, h), pal["base"][0])
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h-1)
        c = tuple(int(pal["base"][0][i]*(1-t)+pal["base"][1][i]*t) for i in range(3))
        d.line((0, y, w, y), fill=c)
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    a = pal["accent"]
    gd.ellipse((int(w*.45), -int(h*.22), int(w*1.22), int(h*.62)), fill=(*a[0], 120))
    gd.ellipse((-int(w*.20), int(h*.48), int(w*.75), int(h*1.28)), fill=(*a[1], 95))
    gd.ellipse((int(w*.05), int(h*.02), int(w*.55), int(h*.48)), fill=(*a[0], 45))
    glow = glow.filter(ImageFilter.GaussianBlur(100))
    return Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")


# --- engineer 04: procedural noise texture ------------------------------------
def texture(img, seed):
    rnd = random.Random(seed)
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for _ in range(90):
        x, y = rnd.randrange(img.width), rnd.randrange(img.height)
        r = rnd.randrange(40, 260)
        d.ellipse((x-r, y-r, x+r, y+r), outline=(255, 255, 255, rnd.randrange(3, 14)), width=1)
    return Image.alpha_composite(img.convert("RGBA"), lay.filter(ImageFilter.GaussianBlur(1))).convert("RGB")


# --- engineer 05: depth layers -------------------------------------------------
def depth(img, pal):
    d = ImageDraw.Draw(img)
    w, h = img.size
    for i in range(5):
        y = int(h*(0.52 + i*0.075))
        pts = [(0, h), (0, y)]
        for x in range(0, w+1, 90):
            pts.append((x, y + int(45*math.sin(x/170.0+i)+18*math.sin(x/47.0))))
        pts.append((w, h))
        c = tuple(max(0, int(pal["base"][0][k]*(1-i*.12))) for k in range(3))
        d.polygon(pts, fill=c)
    return img


# --- engineer 06: subject silhouette (vector, not photo) ----------------------
def silhouette(img, pal):
    d = ImageDraw.Draw(img)
    w, h = img.size
    cx, cy = int(w*.5), int(h*.50)
    # halo
    for r, al in ((int(w*.23), 22), (int(w*.17), 30)):
        d.ellipse((cx-r, cy-r, cx+r, cy+r), outline=(*pal["accent"][0], al+120), width=3)
    # stylized figure
    d.ellipse((cx-30, cy-150, cx+30, cy-90), fill=(6, 14, 22))
    d.polygon([(cx-46, cy-86), (cx+46, cy-86), (cx+96, cy+180), (cx-96, cy+180)],
              fill=(7, 16, 24))
    d.line((cx, cy-150, cx, cy+180), fill=(*pal["accent"][0], 190), width=2)
    d.ellipse((cx-4, cy-16, cx+4, cy-8), fill=pal["accent"][0])
    return img


# --- engineer 07: ornaments ----------------------------------------------------
def ornaments(img, pal):
    d = ImageDraw.Draw(img)
    w, h = img.size
    for k in range(3):
        y = int(h*(0.18 + k*0.06))
        d.line((int(w*.08), y, int(w*.92), y), fill=(*pal["accent"][0], 40), width=1)
    for x in range(int(w*.1), int(w*.9), 120):
        d.ellipse((x-3, int(h*.16)-3, x+3, int(h*.16)+3), fill=(*pal["accent"][1], 160))
    return img


# --- engineer 08: rule-of-thirds composition ----------------------------------
def guide_layout(prompt, pal):
    return {"thirds": [W//3, 2*W//3], "horizon": int(H*.58),
            "title_zone": (int(W*.08), int(H*.10), int(W*.62), int(H*.42)),
            "engineer": "08 layout"}


# --- engineer 09: typography ---------------------------------------------------
def typography(img, prompt, pal):
    d = ImageDraw.Draw(img)
    w, h = img.size
    f_brand, f_title = font(26), font(68)
    d.text((int(w*.08), int(h*.055)), "ZYPHERE  ·  OWN IMAGE LAB", font=f_brand,
           fill=(*pal["accent"][0], 230))
    d.line((int(w*.08), int(h*.105), int(w*.92), int(h*.105)),
           fill=(*pal["accent"][0], 130), width=2)
    y = int(h*.13)
    for ln in wrap(d, prompt, f_title, int(w*.58))[:4]:
        d.text((int(w*.08)+3, y+4), ln, font=f_title, fill=(0, 0, 0))
        d.text((int(w*.08), y), ln, font=f_title, fill=(245, 252, 255))
        y += 84
    d.line((int(w*.08), y+10, int(w*.08)+180, y+10), fill=pal["accent"][0], width=5)
    d.text((int(w*.08), int(h*.93)), "สร้างโดยทีมวิศวกร Zyphere · ไม่ใช้ API ภายนอก",
           font=font(22), fill=(180, 220, 230))
    return img


def wrap(d, text, fnt, maxw):
    out, cur = [], ""
    for wd in str(text or "").split():
        t = (cur + " " + wd).strip()
        if d.textlength(t, font=fnt) > maxw and cur:
            out.append(cur); cur = wd
        else:
            cur = t
    if cur:
        out.append(cur)
    return out[:6]


# --- engineer 10: film grain + vignette ---------------------------------------
def finish(img):
    d = ImageDraw.Draw(img)
    w, h = img.size
    ov = Image.new("L", (w, h), 0)
    od = ImageDraw.Draw(ov)
    od.ellipse((int(-w*.16), int(-h*.16), int(w*1.16), int(h*1.16)), fill=225)
    ov = ov.filter(ImageFilter.GaussianBlur(int(min(w, h)*.11)))
    img = Image.composite(img, Image.new("RGB", img.size, (2, 8, 14)), ov)
    img = ImageEnhance.Contrast(img).enhance(1.10)
    img = ImageEnhance.Sharpness(img).enhance(1.10)
    return img


# --- engineer 11: self-critique ------------------------------------------------
def critique(img):
    issues = []
    if img.width < 900 or img.height < 900:
        issues.append("resolution")
    px = img.convert("RGB")
    a = px.getpixel((int(img.width*.1), int(img.height*.18)))
    b = px.getpixel((int(img.width*.75), int(img.height*.18)))
    if sum(abs(x-y) for x, y in zip(a, b)) < 25:
        issues.append("low-contrast")
    return {"ok": not issues, "issues": issues, "score": 100-25*len(issues)}


# --- engineer 12: export -------------------------------------------------------
def generate(prompt, apply=True):
    seed = int(hashlib.md5(prompt.encode()).hexdigest()[:8], 16)
    p = parse_prompt(prompt)
    pal = palette(p["mood"], seed)
    img = mesh(W, H, pal)
    img = texture(img, seed)
    img = depth(img, pal)
    img = silhouette(img, pal)
    img = ornaments(img, pal)
    layout = guide_layout(prompt, pal)
    img = typography(img, prompt, pal)
    img = finish(img)
    q = critique(img)
    out = None
    if apply:
        os.makedirs(MEDIA, exist_ok=True)
        name = "ownlab_%d.png" % int(time.time())
        out = os.path.join(MEDIA, name)
        img.save(out)
        json.dump({"prompt": prompt, "seed": seed, "palette": pal, "layout": layout,
                   "quality": q, "file": out, "note": "in-house algorithmic design, not diffusion"},
                  open(os.path.join(MEDIA, name + ".json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
    return {"ok": q["ok"], "quality": q, "file": out,
            "engines": ["01 parse", "02 palette", "03 lighting", "04 texture", "05 depth",
                        "06 subject", "07 ornament", "08 layout", "09 type", "10 finish",
                        "11 critique", "12 export"]}


if __name__ == "__main__":
    print(json.dumps(generate("Zyphere สายลมสร้างสรรค์"), ensure_ascii=False)[:700])
