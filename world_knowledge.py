"""World Knowledge Harvester — learn from many OPEN sources, then OWN the facts.

Sources (free/open, no paid key): Wikipedia, Wikidata, OpenAlex (scholarly
works), arXiv, Wikimedia Commons (image credits). Every fact stores its URL so
it is auditable. Harvested facts are written into our LOCAL brain so future
answers work even if every external API disappears.

HONEST: coverage is measured (topics x sources), never claimed as "everything".
"""
import os, json, re, time, html, threading, urllib.parse
import requests

ROOT = os.path.dirname(os.path.abspath(__file__))
STORE = os.path.join(ROOT, "data", "world_knowledge.json")
BRAIN = os.path.join(ROOT, "data", "dept_brains", "world.json")
LOCK = threading.RLock()
UA = {"User-Agent": "Zyphere-WorldKnowledge/1.0 (research; contact: owner)"}


def _get(url, params=None, timeout=25):
    try:
        r = requests.get(url, params=params, headers=UA, timeout=timeout)
        return r.json() if r.ok else None
    except Exception:
        return None


def wikipedia(q):
    d = _get("https://en.wikipedia.org/w/api.php", {
        "action": "query", "list": "search", "srsearch": q, "format": "json",
        "srlimit": 3})
    out = []
    for it in (d or {}).get("query", {}).get("search", []):
        title = it.get("title")
        s = _get("https://en.wikipedia.org/w/api.php", {
            "action": "query", "prop": "extracts", "exintro": 1,
            "explaintext": 1, "titles": title, "format": "json"})
        pages = (s or {}).get("query", {}).get("pages", {})
        ex = next(iter(pages.values()), {}).get("extract", "")
        if ex:
            out.append({"source": "Wikipedia", "title": title,
                        "text": ex[:1200],
                        "url": "https://en.wikipedia.org/wiki/" +
                               urllib.parse.quote(title.replace(" ", "_"))})
    return out


def wikidata(q):
    d = _get("https://www.wikidata.org/w/api.php", {
        "action": "wbsearchentities", "search": q, "language": "th",
        "format": "json", "limit": 3})
    return [{"source": "Wikidata", "title": x.get("label"),
             "text": str(x.get("description", ""))[:400],
             "url": x.get("concepturi", "")}
            for x in (d or {}).get("search", []) if x.get("label")]


def openalex(q):
    d = _get("https://api.openalex.org/works", {
        "search": q, "per-page": 3, "mailto": "zyphere@example.org"})
    return [{"source": "OpenAlex", "title": x.get("title"),
             "text": "Works cited: %s · Year: %s" % (x.get("cited_by_count"), x.get("publication_year")),
             "url": x.get("doi") or x.get("id", "")}
            for x in (d or {}).get("results", []) if x.get("title")]


def arxiv(q):
    import xml.etree.ElementTree as ET
    try:
        r = requests.get("https://export.arxiv.org/api/query",
                         params={"search_query": "all:" + q, "max_results": 3},
                         headers=UA, timeout=25)
        root = ET.fromstring(r.text)
        ns = {"a": "http://www.w3.org/2005/Atom"}
        return [{"source": "arXiv", "title": e.findtext("a:title", "", ns).strip(),
                 "text": e.findtext("a:summary", "", ns).strip()[:700],
                 "url": e.findtext("a:id", "", ns)}
                for e in root.findall("a:entry", ns)]
    except Exception:
        return []


def harvest(q, apply=True):
    hits = []
    for fn in (wikipedia, wikidata, openalex, arxiv):
        try:
            hits.extend(fn(q))
        except Exception:
            pass
    rec = {"q": q, "t": int(time.time()), "sources": sorted({h["source"] for h in hits}),
           "hits": hits}
    if apply:
        with LOCK:
            db = {"topics": []}
            if os.path.exists(STORE):
                try:
                    db = json.load(open(STORE, encoding="utf-8"))
                except Exception:
                    pass
            db.setdefault("topics", []).append(rec)
            json.dump(db, open(STORE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            # Teach the LOCAL brain so this knowledge survives API loss.
            try:
                from local_brain import LocalBrain
                os.makedirs(os.path.dirname(BRAIN), exist_ok=True)
                lb = LocalBrain(BRAIN)
                for h in hits:
                    lb.learn_text("%s (%s): %s [%s]" % (
                        h.get("title"), h["source"], h.get("text", "")[:400], h.get("url", "")),
                        source="world:" + h["source"])
            except Exception:
                pass
    return rec


def coverage():
    try:
        db = json.load(open(STORE, encoding="utf-8"))
    except Exception:
        return {"ok": False, "error": "no harvest yet"}
    topics = db.get("topics", [])
    src = set()
    for t in topics:
        src.update(t.get("sources", []))
    return {"ok": True, "topics": len(topics), "sources": sorted(src),
            "facts": sum(len(t.get("hits", [])) for t in topics),
            "note": "วัดจากสิ่งที่ดึงได้จริง — ไม่ได้อ้างว่ารู้ทุกอย่าง"}


def ask(q):
    try:
        db = json.load(open(STORE, encoding="utf-8"))
    except Exception:
        return {"ok": False, "answer": "ยังไม่มีความรู้ในเครื่อง — ต้อง harvest ก่อน"}
    words = [w.lower() for w in re.findall(r"[\w\u0E00-\u0E7F]{3,}", str(q))]
    out = []
    for t in db.get("topics", []):
        for h in t.get("hits", []):
            text = (str(h.get("title", "")) + " " + str(h.get("text", ""))).lower()
            score = sum(1 for w in words if w in text)
            if score:
                out.append((score, h))
    out.sort(key=lambda x: -x[0])
    return {"ok": bool(out), "engine": "zy-world-brain (local)",
            "answers": [h for _, h in out[:5]],
            "note": "มาจากความรู้ที่เก็บในเครื่องแล้ว — ไม่ต้องเรียก API"}


if __name__ == "__main__":
    r = harvest("quantum computing")
    print("harvested", r["sources"], len(r["hits"]))
    print(json.dumps(coverage(), ensure_ascii=False))


def run():
    return coverage()
