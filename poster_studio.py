"""Poster Studio — lift graphic work toward the reference level using REAL
photography (open CC) + professional multi-layer typography. No diffusion.

HONEST: this cannot produce AI photoreal faces like the samples. It CAN produce
a polished marketing poster with a real photo, strong hierarchy, price badge,
CTA and a clean brand mark — the 'minimum acceptable bar'.
"""
import os, re, json, time, hashlib, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps

ROOT = os.path.dirname(os.path.abspath(__file__))
MEDIA = os.path.join(ROOT, "media", "posters")
OUT = os.path.join(ROOT, "governance", "POSTER_STUDIO.md")
DATA = os.path.join(ROOT, "data", "poster_studio.json")
W, H = 1200, 1800


def font(sz):
    for p in (os.path.join(ROOT, "media", "fonts", "NotoSansThai.ttf"),
              r"C:\Windows\Fonts\Tahoma.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, sz)
            except Exception:
                pass
    return ImageFont.load_default()


def fetch_photo(query):
    """Search real CC photos by the ACTUAL subject; fall back only if empty."""
    # FIRST: aggregate Openverse + Wikimedia + NASA + Met (legal, no keys).
    # This gives far more on-topic real photography than one API alone.
    try:
        import free_image_sources as FIS
        im, credit = FIS.best(query, want_photo=True)
        if im is not None:
            return im, credit
    except Exception:
        pass
    import requests, io
    stop = {"file", "photographer", "taking", "photo", "image", "jpg", "students",
            "smiling", "portrait", "studio", "group", "front", "creative", "workshop"}
    def relevant(text):
        t = (text or "").lower()
        return any(w in t for w in re.findall(r"[a-z]{4,}", (query or "").lower())
                   if w not in stop)
    tries = [query]
    if query:
        tries += [query.split()[0], "photography", "nature landscape", "architecture"]
    for q in tries:
        try:
            r = requests.get("https://commons.wikimedia.org/w/api.php",
                params={"action": "query", "generator": "search",
                        "gsrsearch": "filetype:bitmap " + str(q)[:50], "gsrnamespace": 6,
                        "gsrlimit": 8, "prop": "imageinfo", "iiprop": "url|extmetadata",
                        "iiurlwidth": 1600, "format": "json"},
                headers={"User-Agent": "Zyphere-PosterStudio/1.0"}, timeout=30)
            pages = ((r.json().get("query") or {}).get("pages", {}) or {}).values()
            cands = []
            for pg in pages:
                ii = (pg.get("imageinfo") or [{}])[0]
                u = ii.get("thumburl") or ii.get("url")
                title = pg.get("title", "")
                if u:
                    cands.append((relevant(title), u, ii, title))
            # prefer on-topic results; accept any real photo on final fallback
            ordered = [c for c in cands if c[0]] or ([cands[0]] if cands else [])
            for _, u, ii, title in ordered:
                d = requests.get(u, headers={"User-Agent": "Zyphere-PosterStudio/1.0"},
                                 timeout=30).content
                if len(d) > 20000:
                    md = ii.get("extmetadata", {})
                    return Image.open(io.BytesIO(d)).convert("RGB"), {
                        "creator": re.sub(r"<[^>]+>", "", md.get("Artist", {}).get("value", ""))[:70],
                        "license": md.get("LicenseShortName", {}).get("value", ""),
                        "page": title, "query": q}
        except Exception:
            continue
    return None, None


def wrap(d, text, fnt, maxw):
    out, cur = [], ""
    for w in str(text).split():
        t = (cur+" "+w).strip()
        if d.textlength(t, font=fnt) > maxw and cur:
            out.append(cur); cur = w
        else:
            cur = t
    if cur: out.append(cur)
    return out[:4]


def build(title, subtitle, price, brief):
    # Search by the ACTUAL subject, not a generic portrait query.
    subject = ("graphic design workshop creative studio designer"
               if any(k in (title+subtitle).lower() for k in
                      ("ออกแบบ", "design", "workshop", "grap"))
               else (brief or title))
    photo, credit = fetch_photo(subject)
    if photo is None:
        return {"ok": False, "error": "ไม่พบภาพถ่ายจริง — ไม่สร้าง poster ปลอม"}
    im = ImageOps.fit(photo, (W, H), method=Image.LANCZOS, centering=(0.5, 0.3))
    # DETAIL PIPELINE (no diffusion): multi-scale local contrast + edge-aware
    # smoothing + colour harmony + procedural texture from our own filters,
    # then 4K upscale with Lanczos. Real photo detail stays intact.
    try:
        import advanced_filters as AF
        im, _ = AF.apply_pipeline(im, seed=abs(hash(title)) % 9999,
                                  palette={"base": [(7,24,36),(10,48,62)],
                                           "accent": [(34,211,238),(45,212,191)]})
    except Exception:
        im = ImageEnhance.Contrast(im).enhance(1.08)
        im = ImageEnhance.Color(im).enhance(1.05)
        im = im.filter(ImageFilter.UnsharpMask(1.2, 120, 3))
    if im.size != (1200, 1800):
        im = im.resize((1200, 1800), Image.LANCZOS)
    im = im.filter(ImageFilter.UnsharpMask(radius=1.1, percent=115, threshold=2))
    # dark gradient for text legibility
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d0 = ImageDraw.Draw(ov)
    for y in range(int(H*.32), H):
        t = (y-H*.32)/(H*.68)
        d0.line((0, y, W, y), fill=(3, 12, 20, int(220*t)))
    im = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")
    d = ImageDraw.Draw(im)
    # brand mark
    d.ellipse((60, 55, 90, 85), fill=(34, 211, 238))
    d.text((104, 48), "ZYPHERE  ·  CREATIVE LAB", font=font(26), fill=(235, 248, 252))
    d.line((60, 105, 1140, 105), fill=(120, 200, 220, 160), width=2)
    # eyebrow badge
    f_eyebrow = font(24)
    tw = d.textlength("ZYPHERE ORIGINAL", font=f_eyebrow)+40
    d.rounded_rectangle((60, 1180, 60+tw, 1230), radius=24,
                        fill=(34, 211, 238, 220))
    d.text((80, 1190), "ZYPHERE ORIGINAL", font=f_eyebrow, fill=(4, 20, 28))
    # headline hierarchy
    y = 1250
    f_title = font(88)
    for ln in wrap(d, title[:52], f_title, W-120)[:2]:
        d.text((60, y), ln, font=f_title, fill=(255, 255, 255))
        y += 100
    f_sub = font(38)
    for ln in wrap(d, subtitle[:90], f_sub, W-120)[:2]:
        d.text((62, y), ln, font=f_sub, fill=(210, 236, 244))
        y += 54
    # price badge + CTA
    d.rounded_rectangle((60, H-260, 500, H-190), radius=35,
                        fill=(34, 211, 238))
    d.text((90, H-248), "เริ่มต้น ฿"+str(price), font=font(42), fill=(6, 24, 32))
    d.rounded_rectangle((60, H-160, 620, H-95), radius=35,
                        outline=(255, 255, 255), width=3)
    d.text((90, H-148), "สั่งซื้อ · PromptPay 0941939686",
           font=font(32), fill=(255, 255, 255))
    d.text((60, H-60), "photo: " + credit["creator"] + " · " + credit["license"],
           font=font(18), fill=(190, 218, 228))
    return im, credit


def run(apply=True):
    brief = "portrait photography studio"
    title, sub, price = "WORKSHOP ออกแบบกราฟฟิก", "เรียนรู้จากงานจริง · มีผลงานเป็นรูปธรรม", 490
    result = build(title, sub, price, brief)
    if isinstance(result, tuple):
        im, credit = result
        rec = {"ok": True, "brief": brief, "credit": credit, "size": [W, H],
               "level": "real photography + pro typography (not diffusion)"}
        if apply:
            os.makedirs(MEDIA, exist_ok=True)
            p = os.path.join(MEDIA, "poster_%d.png" % int(time.time()))
            im.save(p)
            rec["file"] = p
            json.dump(rec, open(DATA, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=2, default=str)
            open(OUT, "w", encoding="utf-8").write(
                "# Poster Studio — ระดับที่ทำได้จริง\n\n" +
                "- ใช้ภาพถ่ายจริง (CC) + retouch + typography หลายชั้น\n" +
                "- **ยังไม่มี diffusion** — ไม่สามารถสร้างใบหน้า AI แบบตัวอย่างได้\n" +
                "- เครดิต: " + str(credit) + "\n")
        return rec
    return {"ok": False, "error": result.get("error")}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False)[:600])
