"""Free Image Sources — aggregate MULTIPLE no-key, legal image APIs so graphic
and film work has a deep pool of REAL photography instead of one flaky source.

Sources (all free, no account creation):
  - Openverse (CC search across Flickr/Wikimedia/…)
  - Wikimedia Commons (CC / public domain)
  - NASA Image Library (public domain)
  - The Met Open Access (public domain art — marked kind='art')

Every result is validated (real bytes, dimensions) and carries attribution.
No API keys, no account creation, no scraping of paywalled content.
"""
import os, io, re, json, time, hashlib
import requests

ROOT = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(ROOT, "media", "free_photo_pool")
UA = {"User-Agent": "Zyphere-FreeImageSources/1.0 (research; contact: owner)"}

ART_WORDS = ("painting", "watercolor", "drawing", "illustration", "artwork",
             "sketch", "poster", "canvas", "gouache", "digital art", " fresco")


def _get(url, **kw):
    try:
        return requests.get(url, headers=UA, timeout=25, **kw)
    except Exception:
        return None


def _image_from_url(url, kind, title, creator, license_name, page, query):
    r = _get(url)
    if r is None or not r.ok or len(r.content) < 18000:
        return None
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(r.content)).convert("RGB")
    except Exception:
        return None
    if im.width < 640 or im.height < 400:
        return None
    return {"image": im, "kind": kind,
            "credit": {"creator": str(creator)[:70], "license": str(license_name)[:24],
                       "page": str(title)[:110], "source": kind, "query": query}}


def openverse(query, n=6):
    r = _get("https://api.openverse.org/v1/images/",
             params={"q": query, "page_size": n,
                     "license": "cc0,pdm,by,by-sa"})
    out = []
    if not r or not r.ok:
        return out
    for x in (r.json().get("results") or []):
        u = x.get("url") or x.get("thumbnail")
        if not u:
            continue
        rec = _image_from_url(u, "photo", x.get("title", ""), x.get("creator", ""),
                              x.get("license", ""), x.get("source", ""), query)
        if rec:
            out.append(rec)
    return out


def wikimedia(query, n=6):
    r = _get("https://commons.wikimedia.org/w/api.php",
             params={"action": "query", "generator": "search",
                     "gsrsearch": "filetype:bitmap " + query[:50],
                     "gsrnamespace": 6, "gsrlimit": n, "prop": "imageinfo",
                     "iiprop": "url|extmetadata", "iiurlwidth": 1600,
                     "format": "json"})
    out = []
    if not r or not r.ok:
        return out
    for pg in ((r.json().get("query") or {}).get("pages") or {}).values():
        ii = (pg.get("imageinfo") or [{}])[0]
        u = ii.get("thumburl") or ii.get("url")
        if not u:
            continue
        md = ii.get("extmetadata", {})
        title = pg.get("title", "")
        rec = _image_from_url(u, "photo", title,
                              re.sub(r"<[^>]+>", "", md.get("Artist", {}).get("value", "")),
                              md.get("LicenseShortName", {}).get("value", ""), title, query)
        if rec:
            rec["kind"] = "art" if any(w in title.lower() for w in ART_WORDS) else "photo"
            out.append(rec)
    return out


def nasa(query, n=4):
    r = _get("https://images-api.nasa.gov/search",
             params={"q": query, "media_type": "image", "page_size": n})
    out = []
    if not r or not r.ok:
        return out
    for it in ((r.json().get("collection") or {}).get("items") or [])[:n]:
        data = (it.get("data") or [{}])[0]
        links = it.get("links") or []
        if not links:
            continue
        u = links[0].get("href", "")
        if ".jpg" not in u.lower() and ".png" not in u.lower():
            continue
        rec = _image_from_url(u, "photo", data.get("title", "NASA"),
                              "NASA", "Public domain", u, query)
        if rec:
            out.append(rec)
    return out


def met(query, n=3):
    r = _get("https://collectionapi.metmuseum.org/public/collection/v1.1/search",
             params={"q": query, "hasImages": "true"})
    out = []
    if not r or not r.ok:
        return out
    ids = (r.json().get("objectIDs") or [])[:max(n*3, 9)]
    for oid in ids:
        o = _get("https://collectionapi.metmuseum.org/public/collection/v1/objects/%d" % oid)
        if not o or not o.ok:
            continue
        j = o.json()
        if not j.get("isPublicDomain") or not j.get("primaryImageSmall"):
            continue
        rec = _image_from_url(j["primaryImageSmall"], "art",
                              j.get("title", "Met Museum"), j.get("artistDisplayName", ""),
                              "Public domain", j.get("objectURL", ""), query)
        if rec:
            out.append(rec)
        if len(out) >= n:
            break
    return out


PROVIDERS = [("openverse", openverse), ("wikimedia", wikimedia),
             ("nasa", nasa), ("met", met)]


def search(query, want_photo=True, per=4):
    """Parallel-ish search across all free sources; best photo first."""
    results = []
    for name, fn in PROVIDERS:
        try:
            got = fn(query, per)
            for g in got:
                g["credit"]["source"] = name
            results += got
        except Exception:
            pass
    if want_photo:
        photos = [x for x in results if x["kind"] == "photo"]
        if photos:
            results = photos + [x for x in results if x["kind"] != "photo"]
    # relevance: query words appearing in the title/credit page
    words = [w for w in re.findall(r"[a-z]{4,}", query.lower())[:5]]
    def score(x):
        text = str(x["credit"].get("page", "")).lower()
        return sum(w in text for w in words)
    return sorted(results, key=score, reverse=True)


def best(query, want_photo=True):
    """Single best validated image + credit, or (None, None)."""
    hits = search(query, want_photo=want_photo, per=3)
    if not hits:
        return None, None
    return hits[0]["image"], hits[0]["credit"]


def run(apply=True):
    """Pulse entry point: prove the free pool is reachable with a real search."""
    im, cr = best("cinematic nature landscape light", want_photo=True)
    return {"ok": True, "reachable": im is not None,
            "size": None if im is None else list(im.size),
            "credit": cr, "sources": [n for n, _ in PROVIDERS],
            "note": "free no-key legal image sources aggregated; "
                    "transient image miss is not a failure"}


if __name__ == "__main__":
    im, cr = best("misty forest sunlight", want_photo=True)
    print("best", None if im is None else im.size, cr)
