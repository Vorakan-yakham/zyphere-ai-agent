"""Sample Publisher — publish REAL readable samples into the main repo so
GitHub Pages renders them as HTML (raw.githubusercontent only serves text/plain).

Each sample is keyed by a stable id derived from the book TITLE, so the
storefront and this publisher always agree even if catalogue order changes.
Only books with a real source on the product repo get a sample — no fakes.
"""
import os, re, json, time, hashlib

ROOT = os.path.dirname(os.path.abspath(__file__))
SAMPLES = os.path.join(ROOT, "samples")
DATA = os.path.join(ROOT, "data", "sample_publisher.json")
OUT = os.path.join(ROOT, "governance", "SAMPLE_PUBLISHER.md")


def sid(title):
    return "s_" + hashlib.md5(str(title).encode("utf-8")).hexdigest()[:10]


def source_map():
    """title -> product-repo folder, built from the real tree."""
    import autonomous_council as AC
    m = {}
    for p in AC.gh_tree():
        mm = re.match(r"books/(\d+_[^/]+)/content\.md$", p)
        if mm:
            folder = mm.group(1)
            m[folder.split("_", 1)[-1]] = folder
    return m


def build_sample(title, md):
    """Reuse the honest sample renderer from ebook_complete."""
    import ebook_complete as EC
    return EC.sample_html(title, md, "")


def run(apply=True, force=False):
    # Cache guard: avoid 90+ GitHub API calls every 1-minute pulse.
    if not force and os.path.exists(DATA):
        try:
            cached = json.load(open(DATA, encoding="utf-8"))
            files = [os.path.join(SAMPLES, i["file"]) for i in cached.get("items", [])]
            if (time.time() - cached.get("t", 0) < 86400 and
                    cached.get("published", 0) >= 40 and
                    all(os.path.exists(f) for f in files)):
                return cached
        except Exception:
            pass
    import storefront_rebuild as SR
    products = SR.load_products()
    folders = source_map()
    made, missing = [], []
    os.makedirs(SAMPLES, exist_ok=True)

    for row in products:
        title = str(row.get("title") or "").strip()
        if not title:
            continue
        folder = folders.get(title)
        if not folder:
            missing.append({"title": title, "why": "no source on product repo"})
            continue
        import autonomous_council as AC
        md = AC.gh_raw("books/%s/content.md" % folder) or ""
        if len(md) < 1200:
            missing.append({"title": title, "why": "source too short"})
            continue
        name = sid(title) + ".html"
        html = build_sample(title, md)
        if apply:
            open(os.path.join(SAMPLES, name), "w", encoding="utf-8").write(html)
        made.append({"title": title, "file": name, "url": "samples/" + name,
                     "chars": len(md)})

    rec = {"t": int(time.time()), "published": len(made), "missing": missing,
           "items": made,
           "note": "GitHub Pages render จริง — ไม่ใช้ raw (text/plain)"}
    if apply:
        json.dump(rec, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        open(OUT, "w", encoding="utf-8").write(
            "# ตัวอย่างฟรีที่อ่านได้จริง\n\n- Publish **%d** ตัวอย่าง\n" % len(made) +
            "\n".join("- [%s](%s)" % (m["title"], m["url"]) for m in made[:12]) +
            ("\n- ...\n" if len(made) > 12 else "") +
            "\n- ไม่มีต้นฉบับ: %d เล่ม (ไม่สร้างตัวอย่างปลอม)\n" % len(missing) +
            "- " + rec["note"] + "\n")
    return rec


if __name__ == "__main__":
    r = run()
    print(json.dumps({"published": r["published"], "missing": len(r["missing"])},
                     ensure_ascii=False))
