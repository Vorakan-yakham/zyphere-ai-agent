"""Zyphere E-Library - fetch from free public digital libraries (no API key).

Sources:
- Open Library (openlibrary.org) - books & authors
- arXiv (export.arxiv.org) - academic papers
- PubMed / NCBI eutils - medical & life science abstracts
- Project Gutenberg (gutendex.com) - public-domain books

All are public, free, and ethically usable (metadata/abstracts, public domain).
"""
import requests, re, time

TIMEOUT = 20


def _clean(s, n=600):
    s = re.sub(r"<[^>]+>", " ", str(s or ""))
    s = re.sub(r"\s+", " ", s).strip()
    return s[:n]


def open_library(topic, limit=3):
    try:
        r = requests.get("https://openlibrary.org/search.json",
                         params={"q": topic, "limit": limit}, timeout=TIMEOUT)
        r.raise_for_status()
        docs = (r.json().get("docs") or [])[:limit]
        out = []
        for d in docs:
            title = d.get("title") or ""
            author = ", ".join((d.get("author_name") or [])[:2])
            year = d.get("first_publish_year")
            sub = d.get("subject") or []
            out.append({"source": "Open Library", "title": _clean(title, 150),
                        "text": _clean(" ".join([title, author, str(year or ""), " ".join(sub[:5])]), 500)})
        return out
    except Exception:
        return []


def arxiv(topic, limit=3):
    try:
        r = requests.get("https://export.arxiv.org/api/query",
                         params={"search_query": "all:" + str(topic), "max_results": limit,
                                 "sortBy": "relevance"}, timeout=TIMEOUT)
        r.raise_for_status()
        entries = re.findall(r"<entry>([\s\S]*?)</entry>", r.text)[:limit]
        out = []
        for e in entries:
            t = re.search(r"<title>([\s\S]*?)</title>", e)
            s = re.search(r"<summary>([\s\S]*?)</summary>", e)
            out.append({"source": "arXiv", "title": _clean(t.group(1) if t else "", 150),
                        "text": _clean((t.group(1) if t else "") + " " + (s.group(1) if s else ""), 700)})
        return out
    except Exception:
        return []


def pubmed(topic, limit=3):
    try:
        s = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                         params={"db": "pubmed", "term": topic, "retmax": limit, "retmode": "json"},
                         timeout=TIMEOUT).json()
        ids = (s.get("esearchresult") or {}).get("idlist") or []
        if not ids:
            return []
        d = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
                         params={"db": "pubmed", "id": ",".join(ids), "retmode": "json"},
                         timeout=TIMEOUT).json()
        out = []
        for i in ids:
            rec = (d.get("result") or {}).get(i) or {}
            out.append({"source": "PubMed", "title": _clean(rec.get("title", ""), 150),
                        "text": _clean(rec.get("title", "") + " " + rec.get("pubdate", ""), 400)})
        return out
    except Exception:
        return []


def gutenberg(topic, limit=3):
    try:
        r = requests.get("https://gutendex.com/books",
                         params={"search": topic}, timeout=TIMEOUT)
        r.raise_for_status()
        books = (r.json().get("results") or [])[:limit]
        out = []
        for b in books:
            t = b.get("title") or ""
            a = ", ".join(b.get("authors") or [])
            out.append({"source": "Gutenberg", "title": _clean(t, 150),
                        "text": _clean(t + " " + a, 300)})
        return out
    except Exception:
        return []


SEARCHERS = {"openlibrary": open_library, "arxiv": arxiv, "pubmed": pubmed, "gutenberg": gutenberg}

# Small Thai->English glossary for search terms (e-libraries index in English).
GLOSS = {
    "ปัญญาประดิษฐ์": "artificial intelligence", "AI": "artificial intelligence",
    "การแพทย์": "medicine medical", "การเรียนรู้": "learning", "เครื่องจักร": "machine",
    "ข้อมูล": "data", "วิทยาศาสตร์": "science", "เทคโนโลยี": "technology",
    "สุขภาพ": "health", "โรค": "disease", "การรักษา": "treatment",
    "หัวใจ": "heart", "สมอง": "brain", "เด็ก": "child children",
    "ประวัติศาสตร์": "history", "โลก": "world earth", "จักรวาล": "universe",
    "ดาราศาสตร์": "astronomy", "ฟิสิกส์": "physics", "เคมี": "chemistry",
    "ชีววิทยา": "biology", "คณิตศาสตร์": "mathematics", "สถิติ": "statistics",
    "ภาษา": "language", "การศึกษา": "education", "สภาพภูมิอากาศ": "climate",
    "สิ่งแวดล้อม": "environment", "พลังงาน": "energy", "เศรษฐกิจ": "economy",
    "การเมือง": "politics", "สังคม": "society", "วัฒนธรรม": "culture",
    "อาหาร": "food", "กีฬา": "sport", "ดนตรี": "music", "ศิลปะ": "art",
    "การบิน": "aviation", "อวกาศ": "space", "หุ่นยนต์": "robot robotics",
}


def to_en(text):
    """Turn a Thai/English topic into English search terms for e-libraries."""
    s = str(text or "").strip()
    if re.search(r"[a-zA-Z]", s) and not re.search(r"[\u0E00-\u0E7F]", s):
        return s  # already English
    # replace known Thai terms
    out = s
    for th, en in GLOSS.items():
        out = out.replace(th, en)
    # if still mostly Thai, ask Groq (if configured) for a clean translation
    if re.search(r"[\u0E00-\u0E7F]", out):
        try:
            import os
            key = os.environ.get("GROQ_API_KEY", "").strip()
            if key:
                r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
                    json={"model": "openai/gpt-oss-120b", "temperature": 0,
                          "messages": [{"role": "system", "content": "Translate to English search keywords only. No explanation."},
                                       {"role": "user", "content": s}]}, timeout=15)
                if r.ok:
                    t = str(((r.json().get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()
                    if t:
                        out = t[:120]
        except Exception:
            pass
    # drop remaining Thai chars, keep english words
    out = re.sub(r"[\u0E00-\u0E7F]+", " ", out)
    out = re.sub(r"\s+", " ", out).strip()
    return out or "science"


def search(topic, sources=None, per=2):
    """Search e-libraries. Auto-translates Thai topics to English keywords."""
    q = to_en(topic)
    sources = sources or list(SEARCHERS)
    out = []
    for name in sources:
        fn = SEARCHERS.get(name)
        if not fn:
            continue
        try:
            out.extend(fn(q, per))
        except Exception:
            pass
    return out


def to_texts(results):
    return [r["text"] for r in results if r.get("text")]
