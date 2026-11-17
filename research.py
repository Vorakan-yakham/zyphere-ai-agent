"""Zyphere Global Knowledge Research Library - Research Engine + Knowledge Base.

Per owner's directive: search across 4 levels (foundation -> discovery), store
knowledge WITH provenance metadata, rate source reliability A-D, respect
copyright/ToS (never bypass paywalls), and expose everything for the
Learning & Reasoning engine.

Public / Open-Access APIs only. No paywall circumvention. No illegal content.
"""
import json, os, re, time, threading
import requests

TIMEOUT = 18

# Source registry: (name, domain, field, level, reliability)
SOURCES = [
    ("arXiv", "https://arxiv.org", "ฟิสิกส์/คณิต/AI", 3, "A"),
    ("PubMed", "https://pubmed.ncbi.nlm.nih.gov", "การแพทย์/ชีววิทยา", 3, "A"),
    ("Europe PMC", "https://europepmc.org", "ชีวการแพทย์", 3, "A"),
    ("Crossref", "https://api.crossref.org", "สิ่งพิมพ์วิชาการ/DOI", 3, "A"),
    ("OpenAlex", "https://api.openalex.org", "ผลงานวิชาการ", 3, "A"),
    ("Semantic Scholar", "https://api.semanticscholar.org", "งานวิจัย/ความเชื่อมโยง", 3, "A"),
    ("CORE", "https://core.ac.uk", "งานวิจัย Open Access", 3, "A"),
    ("DOAJ", "https://doaj.org", "วารสาร Open Access", 2, "B"),
    ("Open Library", "https://openlibrary.org", "หนังสือ/ตำรา", 1, "B"),
    ("Project Gutenberg", "https://gutenberg.org", "หนังสือคลาสสิก Public Domain", 1, "B"),
    ("Internet Archive", "https://archive.org", "หนังสือ/เอกสารเก่า", 1, "B"),
    ("MIT OpenCourseWare", "https://ocw.mit.edu", "หลักสูตร MIT", 1, "C"),
    ("Stanford Encyclopedia of Philosophy", "https://plato.stanford.edu", "ปรัชญา", 2, "B"),
    ("NASA", "https://science.nasa.gov", "อวกาศ/ดาราศาสตร์", 3, "A"),
    ("WHO", "https://www.who.int", "สุขภาพโลก", 3, "A"),
    ("Our World in Data", "https://ourworldindata.org", "ข้อมูลโลก/เศรษฐกิจ", 3, "C"),
    ("World Bank", "https://www.worldbank.org", "เศรษฐกิจ/การพัฒนา", 3, "A"),
    ("WIPO", "https://www.wipo.int", "สิทธิบัตร", 4, "A"),
    ("Google Patents", "https://patents.google.com", "สิทธิบัตร", 4, "A"),
    ("Hugging Face", "https://huggingface.co", "โมเดล/ชุดข้อมูล AI", 3, "C"),
    ("GitHub", "https://github.com", "โค้ด/โปรเจกต์", 3, "C"),
]

BLOCK = ("พนัน", "casino", "gambling", "bet", "slot", "บาคาร่า", "สล็อต", "ผิดกฎหมาย")


def _clean(s, n=800):
    s = re.sub(r"<[^>]+>", " ", str(s or ""))
    s = re.sub(r"\s+", " ", s).strip()
    return s[:n]


def _safe(topic):
    t = str(topic or "")
    return not any(b in t.lower() for b in BLOCK)


class ResearchLibrary:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.records = []   # knowledge base with provenance
        self._load()

    def _load(self):
        try:
            self.records = json.load(open(self.path, encoding="utf-8")).get("records", [])
        except Exception:
            self.records = []

    def save(self):
        with self.lock:
            try:
                os.makedirs(os.path.dirname(self.path), exist_ok=True)
                json.dump({"records": self.records[-2000:]},
                          open(self.path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            except Exception:
                pass

    # ---------- Research Engine ----------
    def search(self, topic, max_per_source=2):
        """Search public/Open-Access APIs; return raw results (no paywall bypass)."""
        if not _safe(topic):
            return [], "งดเด็ดขาด: เนื้อหาผิดกฎหมาย/เว็บพนัน"
        import elibrary
        q = elibrary.to_en(topic)
        out = []
        try:
            for r in elibrary.search(q, per=max_per_source):
                out.append({"title": r.get("title", ""), "summary": r.get("text", ""),
                            "url": "", "author": "", "institution": r.get("source", ""),
                            "published": "", "type": "abstract", "reliability": "B",
                            "field": "", "source": r.get("source", "")})
        except Exception:
            pass
        # Crossref (DOI metadata) — reliability A
        try:
            r = requests.get("https://api.crossref.org/works",
                             params={"query": q, "rows": max_per_source}, timeout=TIMEOUT)
            if r.ok:
                for it in (r.json().get("message") or {}).get("items", []):
                    out.append({"title": _clean((it.get("title") or [""])[0], 200),
                                "summary": _clean(" ".join(it.get("abstract", "").split()) or it.get("title", [""])[0], 600),
                                "url": it.get("URL", ""), "author": ", ".join(
                                    (a.get("family", "") for a in (it.get("author") or [])[:3])),
                                "institution": _clean(" ".join(it.get("publisher", "").split()), 120),
                                "published": str((it.get("published-print") or it.get("published") or {}).get("date-parts", [[""]])[0][0]),
                                "type": "doi_publication", "reliability": "A",
                                "field": ", ".join((it.get("subject") or [])[:3]), "source": "Crossref"})
        except Exception:
            pass
        # OpenAlex — reliability A
        try:
            r = requests.get("https://api.openalex.org/works",
                             params={"search": q, "per-page": max_per_source}, timeout=TIMEOUT)
            if r.ok:
                for it in (r.json().get("results") or []):
                    out.append({"title": _clean(it.get("title") or it.get("display_name", ""), 200),
                                "summary": _clean(it.get("abstract_inverted_index") and " ".join(
                                    list(it.get("abstract_inverted_index", {}).keys())[:40]) or it.get("display_name", ""), 600),
                                "url": it.get("doi") or it.get("id", ""),
                                "author": "", "institution": "", "published": str(it.get("publication_year", "")),
                                "type": "work", "reliability": "A", "field": "", "source": "OpenAlex"})
        except Exception:
            pass
        return out, ""

    # ---------- Knowledge Base ----------
    def record(self, topic, results=None, field=""):
        """Store studied knowledge with full provenance metadata."""
        if not _safe(topic):
            return {"ok": False, "error": "งดเด็ดขาด"}
        results = results or []
        rec = {
            "topic": str(topic)[:200], "field": str(field or "")[:100],
            "records": [], "t": int(time.time()), "accessed": time.strftime("%Y-%m-%d"),
        }
        for r in results:
            rec["records"].append({
                "doc_title": str(r.get("title", ""))[:250],
                "author": str(r.get("author", ""))[:200],
                "institution": str(r.get("institution", ""))[:150],
                "url": str(r.get("url", ""))[:400],
                "published": str(r.get("published", ""))[:40],
                "accessed": rec["accessed"],
                "doc_type": str(r.get("type", ""))[:60],
                "reliability": str(r.get("reliability", "D"))[:2],
                "field": str(r.get("field", ""))[:120],
                "summary": str(r.get("summary", ""))[:800],
                "theory": "", "evidence": "", "limitations": "", "extend": "",
            })
        with self.lock:
            self.records.append(rec)
        self.save()
        return {"ok": True, "topic": rec["topic"], "sources": len(rec["records"]), "id": len(self.records) - 1}

    def library(self, limit=20):
        with self.lock:
            return list(reversed(self.records[-limit:]))

    def stats(self):
        with self.lock:
            by_rel = {}
            for rec in self.records:
                for r in rec.get("records", []):
                    by_rel[r.get("reliability", "?")] = by_rel.get(r.get("reliability", "?"), 0) + 1
            return {"topics": len(self.records),
                    "documents": sum(len(r.get("records", [])) for r in self.records),
                    "by_reliability": by_rel}

    def snapshot(self):
        with self.lock:
            return {"records": self.records[-2000:]}

    def restore(self, data):
        with self.lock:
            if isinstance(data, dict) and "records" in data:
                self.records = data.get("records", [])
                self.save()
                return True
        return False
