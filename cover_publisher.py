"""Cover Publisher — publish the REAL generated book covers for the storefront.

GitHub Pages cannot read media/covers if it is gitignored, and a 1.8MB PNG x46
is too heavy for a web page. This produces 600x900 optimised JPEGs in
public_covers/ (a few MB total) with a manifest, so every store card shows the
actual photographic cover instead of a generic SVG shape.
"""
import os, json, time
from PIL import Image

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "media", "covers")
DST = os.path.join(ROOT, "public_covers")
DATA = os.path.join(ROOT, "data", "cover_publisher.json")


def run(apply=True):
    os.makedirs(DST, exist_ok=True)
    made, total = [], 0
    for i in range(1, 47):
        p = os.path.join(SRC, "cover_%02d.png" % i)
        if not os.path.exists(p):
            continue
        try:
            im = Image.open(p).convert("RGB")
            im = im.resize((600, 900), Image.Resampling.LANCZOS)
            out = os.path.join(DST, "cover_%02d.jpg" % i)
            if apply:
                im.save(out, "JPEG", quality=82, optimize=True)
                total += os.path.getsize(out)
            made.append("public_covers/cover_%02d.jpg" % i)
        except Exception:
            pass
    rec = {"t": int(time.time()), "published": len(made),
           "total_mb": round(total / 1048576, 2), "files": made,
           "note": "real photographic covers for the public storefront"}
    if apply:
        json.dump(rec, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return rec


if __name__ == "__main__":
    r = run()
    print(json.dumps({"published": r["published"], "mb": r["total_mb"]},
                     ensure_ascii=False))
