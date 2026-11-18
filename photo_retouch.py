"""Photo Retouch Studio — open an EXISTING image (new or old), retouch it,
and add professional typography. Works entirely in-house with Pillow.

Outputs: retouched 4K PNG + a transparent overlay PNG containing only the
typography/decorations, so a human designer can lift it straight into
Photoshop/Illustrator and keep editing.
"""
import os, io, re, json, time, hashlib
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps

ROOT = os.path.dirname(os.path.abspath(__file__))
MEDIA = os.path.join(ROOT, "media")
FONT_REG = os.path.join(MEDIA, "fonts", "NotoSansThai.ttf")
OUTFIT_FONTS = ["NotoSansThai.ttf"]


_FONT_CACHE = {}


def font(sz):
    if sz in _FONT_CACHE: return _FONT_CACHE[sz]
    for p in (FONT_REG, r"C:\Windows\Fonts\Tahoma.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, sz)
            except Exception:
                pass
    return ImageFont.load_default()


def find_image(path_or_url):
    if not path_or_url:
        return None
    if path_or_url.startswith("/media/"):
        p = os.path.join(ROOT, path_or_url.lstrip("/"))
        return p if os.path.exists(p) else None
    if os.path.exists(path_or_url):
        return path_or_url
    try:
        import requests
        r = requests.get(path_or_url, timeout=30)
        if r.ok and len(r.content) > 8000:
            p = os.path.join(MEDIA, "source_%d.jpg" % int(time.time()))
            open(p, "wb").write(r.content)
            return p
    except Exception:
        pass
    return None


def retouch(src, brief="", apply=True):
    path = find_image(src)
    if not path:
        return {"ok": False, "error": "ไม่พบภาพต้นฉบับที่ระบุ"}
    im = Image.open(path).convert("RGB")
    before = im.size
    im = ImageOps.exif_transpose(im)
    im = ImageOps.fit(im, (2160, 3840), method=Image.LANCZOS, centering=(0.5, 0.35))
    im = ImageEnhance.Contrast(im).enhance(1.06)
    im = ImageEnhance.Color(im).enhance(1.04)
    im = im.filter(ImageFilter.UnsharpMask(radius=1.4, percent=130, threshold=3))
    # professional typography overlay
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    w, h = im.size
    m = int(w * .075)
    grad = Image.new("RGBA", im.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    for y in range(int(h*.68), h):
        t = (y-h*.68)/(h*.32)
        gd.line((0, y, w, y), fill=(3, 12, 20, int(200*t)))
    ov = Image.alpha_composite(ov, grad)
    d = ImageDraw.Draw(ov)
    d.ellipse((m, h-330, m+18, h-312), fill=(34, 211, 238, 255))
    d.text((m+36, h-340), "ZYPHERE  ·  RETOUCHED", font=font(26), fill=(220, 248, 255, 255))
    title = (brief or os.path.basename(path))[:48]
    for i, ln in enumerate(_wrap(d, title, font(72), w-m*2)[:3]):
        d.text((m, h-280+i*90), ln, font=font(72), fill=(255, 255, 255, 255))
    d.line((m, h-40, m+180, h-40), fill=(34, 211, 238, 255), width=6)
    final = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")
    out = {"ok": True, "before": list(before), "after": [w, h], "source": path}
    if apply:
        os.makedirs(MEDIA, exist_ok=True)
        nid = str(int(time.time()))
        fp = os.path.join(MEDIA, "retouch_%s.png" % nid)
        op = os.path.join(MEDIA, "retouch_overlay_%s.png" % nid)
        final.save(fp); ov.save(op)
        out.update({"file": fp, "overlay": op,
                    "url": "/media/" + os.path.basename(fp),
                    "overlay_url": "/media/" + os.path.basename(op)})
        json.dump(out, open(fp + ".json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return out


def _wrap(d, text, fnt, maxw):
    out, cur = [], ""
    for wd in str(text).split():
        t = (cur+" "+wd).strip()
        if d.textlength(t, font=fnt) > maxw and cur:
            out.append(cur); cur = wd
        else:
            cur = t
    if cur: out.append(cur)
    return out


if __name__ == "__main__":
    import own_image_lab as LAB
    base = LAB.generate("ฐานภาพสำหรับ retouch", apply=True)
    print(json.dumps(retouch(base["file"], "สายลมยามเย็น"), ensure_ascii=False)[:500])
