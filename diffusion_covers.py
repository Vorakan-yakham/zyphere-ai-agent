"""Diffusion Covers — INTERNATIONAL book-cover quality via a free public
diffusion endpoint (Pollinations, no key / no account creation).

Generates a unique cinematic photograph per book subject, then composites a
clean editorial typographic system. Honest: the image IS AI-generated (the
endpoint says so); we disclose that in the report and credit the source.
"""
import os, re, json, time, hashlib, requests
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageOps

ROOT = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(ROOT, "media", "diffusion_covers")
COVERS = os.path.join(ROOT, "media", "covers")
PUBLIC = os.path.join(ROOT, "public_covers")
DATA = os.path.join(ROOT, "data", "diffusion_covers.json")
OUT = os.path.join(ROOT, "governance", "DIFFUSION_COVERS.md")
W, H = 1200, 1800
ENDPOINT = "https://image.pollinations.ai/prompt/"


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


def prompt_for(title, subject):
    return (
        "Editorial book cover artwork for '%s'. Subject: %s. "
        "Cinematic photorealistic scene, dramatic studio lighting, rich texture, "
        "deep shadows, subtle colour grading, shallow depth of field, "
        "museum-quality photography, vertical composition, generous empty dark "
        "space in the lower third for typography. No text, no letters, no logo, "
        "no watermark, no border." % (title[:70], subject)
    )


def generate(title, subject, seed):
    os.makedirs(CACHE, exist_ok=True)
    key = hashlib.md5((title + subject).encode()).hexdigest()[:16] + ".jpg"
    fp = os.path.join(CACHE, key)
    if os.path.exists(fp) and os.path.getsize(fp) > 20000:
        return Image.open(fp).convert("RGB"), key, True
    try:
        u = ENDPOINT + requests.utils.quote(prompt_for(title, subject))
        u += "?width=1200&height=1800&seed=%d&nologo=true&model=flux" % seed
        r = requests.get(u, timeout=180)
        if not r.ok or len(r.content) < 20000:
            return None, key, False
        im = Image.open(__import__("io").BytesIO(r.content)).convert("RGB")
        im = im.crop((0, 0, im.width, max(1, im.height - 36)))  # strip watermark band
        im.save(fp, quality=92)
        return im, key, True
    except Exception:
        return None, key, False


def international_cover(photo, title, subject, price, idx, accent=(232, 236, 242)):
    # Free endpoint caps native output at ~627px. Local EDSR x4 reconstructs
    # detail before the final fit — genuinely sharper than a plain Lanczos.
    try:
        import superres as SR
        im = SR.upscale(photo, (W, H))
    except Exception:
        im = ImageOps.fit(photo, (W, H), method=Image.Resampling.LANCZOS)
        im = im.filter(ImageFilter.UnsharpMask(radius=1.35, percent=130, threshold=2))
    # dark lower scrim for type
    scrim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(scrim)
    for y in range(int(H*.40), H):
        t = (y - H*.40) / (H*.60)
        d.line((0, y, W, y), fill=(3, 8, 14, int(242 * t ** 1.15)))
    for y in range(0, 170):
        d.line((0, y, W, y), fill=(3, 8, 14, int(120 * (1 - y/170))))
    im = Image.alpha_composite(im.convert("RGBA"), scrim).convert("RGB")
    im = ImageEnhance.Contrast(im).enhance(1.06)
    d = ImageDraw.Draw(im)
    # minimal international editorial system
    d.rectangle((72, 76, 150, 80), fill=accent)
    d.text((72, 102), "ZYPHERE  /  KNOWLEDGE", font=font(24), fill=(236, 244, 248))
    d.text((W-150, 102), "%02d" % idx, font=font(24), fill=(190, 208, 216))
    d.line((72, 148, W-72, 148), fill=(*accent, 90), width=1)
    # English kicker (international), then Thai title
    d.text((72, int(H*.66)), subject.upper()[:52], font=font(26),
           fill=(*accent, 210))
    f = font(76)
    y = int(H*.70)
    for ln in wrap(d, title[:60], f, W-150)[:3]:
        d.text((72, y), ln, font=f, fill=(255, 255, 255))
        y += 90
    d.line((72, y+14, 190, y+14), fill=accent, width=2)
    d.text((72, y+34), "EDITION 2026  ·  ORIGINAL KNOWLEDGE SERIES",
           font=font(22), fill=(186, 206, 216))
    d.text((72, H-110), "ZYPHERE   ·   ฿" + str(price), font=font(34),
           fill=(240, 248, 252))
    d.text((72, H-60), "AI-generated cover art · Zyphere diffusion pipeline",
           font=font(17), fill=(150, 176, 190))
    return im


def wrap(d, text, fnt, maxw):
    out, cur = [], ""
    for w in str(text).split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=fnt) > maxw and cur:
            out.append(cur); cur = w
        else:
            cur = t
    if cur: out.append(cur)
    return out[:3]


def run(apply=True, limit=46):
    import storefront_rebuild as SR
    import cover_queries as CQ
    products = SR.load_products()[:limit]
    os.makedirs(COVERS, exist_ok=True)
    os.makedirs(PUBLIC, exist_ok=True)
    jobs = []
    for i, row in enumerate(products, 1):
        t = str(row.get("title"))
        jobs.append((i, t, CQ.query_for(t), int(row.get("price") or 40),
                     abs(hash(t)) % 100000))

    def work(job):
        i, t, sub, price, seed = job
        # incremental: never re-spend quota on a book already generated
        existing = os.path.join(ROOT, "data", "diffusion_covers.json")
        if os.path.exists(existing):
            try:
                done = json.load(open(existing, encoding="utf-8"))
                if any(r.get("i") == i and r.get("ok") for r in done.get("results", [])):
                    return {"i": i, "title": t, "ok": True, "cached": True}
            except Exception:
                pass
        photo, key, ok = generate(t, sub, seed)
        if not ok:
            return {"i": i, "title": t, "ok": False, "reason": "quota/unavailable"}
        if apply:
            im = international_cover(photo, t, sub, price, i)
            im.save(os.path.join(COVERS, "cover_%02d.png" % i))
            im.resize((600, 900), Image.Resampling.LANCZOS).save(
                os.path.join(PUBLIC, "cover_%02d.jpg" % i), "JPEG", quality=84)
            small = im.convert("P", palette=Image.ADAPTIVE, colors=128)
            small = small.resize((400, 600), Image.Resampling.LANCZOS)
            small.save(os.path.join(PUBLIC, "cover_%02d_embed.png" % i),
                       "PNG", optimize=True)
        return {"i": i, "title": t, "ok": True, "art": key,
                "native": list(photo.size)}

    # Free endpoint: 1 image / 45s per IP. One per pulse is enough because the
    # autonomy loop fires every minute — never fire parallel (HTTP 402).
    run_jobs = [j for j in jobs if not any(
        r.get("i") == j[0] and r.get("ok") for r in
        (json.load(open(DATA, encoding="utf-8")).get("results", [])
         if os.path.exists(DATA) else []))][:1]
    results = [work(j) for j in run_jobs]
    prev = []
    if os.path.exists(DATA):
        try:
            prev = [r for r in json.load(open(DATA, encoding="utf-8")).get("results", [])
                    if r.get("ok") and not r.get("cached")]
        except Exception:
            pass
    seen_i = {r.get("i") for r in prev}
    results = prev + [r for r in results if r.get("ok") and not r.get("cached")
                      and r.get("i") not in seen_i] + [r for r in results if not r.get("ok")]
    good = [r for r in results if r.get("ok")]
    rec = {"t": int(time.time()), "total": len(jobs), "generated": len(good),
           "source": "Pollinations free diffusion endpoint (AI-generated art)",
           "results": results,
           "note": "AI-generated cover art — disclosed honestly, not CC photography"}
    if apply:
        json.dump(rec, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        open(OUT, "w", encoding="utf-8").write(
            "# Diffusion Covers — international edition\n\nสร้าง **%d/%d** ปกด้วย AI diffusion\n\n"
            "แหล่ง: %s\n\n%s\n" % (len(good), len(jobs), rec["source"], rec["note"]))
    return {"ok": True, "generated": len(good), "total": len(jobs),
            "note": "incremental: retries next pulse when quota resets"}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False))
