"""Zyphere Notebook - NotebookLM-style grounded document analysis.

Load documents (text/url/file), index them into chunks, then answer questions
using ONLY the provided sources with citations. No invented facts. This is the
core of NotebookLM and it makes analysis far more accurate and verifiable.

Works offline for indexing/search; optional ensemble LLM can synthesize.
"""
import json, os, re, time, threading


class Notebook:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.docs = []      # {id, name, text, chunks:[{i,text}], t}
        self.notes = []     # saved Q/A grounded analyses
        self._load()

    def _load(self):
        try:
            d = json.load(open(self.path, encoding="utf-8"))
            self.docs = d.get("docs", [])
            self.notes = d.get("notes", [])
        except Exception:
            pass

    def save(self):
        with self.lock:
            try:
                os.makedirs(os.path.dirname(self.path), exist_ok=True)
                json.dump({"docs": self.docs[-100:], "notes": self.notes[-200:]},
                          open(self.path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            except Exception:
                pass

    def _chunk(self, text, size=900):
        text = re.sub(r"\s+", " ", str(text or "")).strip()
        if not text:
            return []
        parts = re.split(r"(?<=[.!?。！？\n])\s+", text)
        out, cur = [], ""
        for p in parts:
            if len(cur) + len(p) > size and cur:
                out.append(cur.strip())
                cur = p
            else:
                cur = (cur + " " + p).strip()
        if cur:
            out.append(cur.strip())
        return out

    def add(self, name, text):
        name = str(name or "doc_%d" % int(time.time()))[:120]
        chunks = [{"i": i, "text": c} for i, c in enumerate(self._chunk(text))]
        if not chunks:
            return {"ok": False, "error": "empty document"}
        did = "%s_%d" % (abs(hash(name)) % 100000, int(time.time()) % 100000)
        with self.lock:
            self.docs.append({"id": did, "name": name, "chunks": chunks,
                              "size": len(str(text)), "t": int(time.time())})
        self.save()
        return {"ok": True, "id": did, "name": name, "chunks": len(chunks)}

    def _score(self, query, chunk):
        """Grounded relevance. Thai has no spaces, so also use n-gram substrings."""
        q = query.lower()
        blob = chunk.lower()
        toks = [w for w in re.findall(r"[\u0E00-\u0E7FA-Za-z0-9]{2,}", q)]
        score = 0
        for t in toks:
            if len(t) >= 3:
                if t in blob:
                    score += 2
                # sliding 3-char substrings for Thai run-on words
                for i in range(len(t) - 2):
                    g = t[i:i + 3]
                    if g in blob:
                        score += 1
            elif t in blob:
                score += 1
        return score

    def search(self, query, top=6):
        with self.lock:
            docs = list(self.docs)
        hits = []
        for d in docs:
            for c in d["chunks"]:
                s = self._score(query, c["text"])
                if s > 0:
                    hits.append((s, d, c))
        hits.sort(key=lambda x: -x[0])
        out = []
        for s, d, c in hits[:top]:
            out.append({"doc": d["name"], "doc_id": d["id"], "chunk": c["i"],
                        "text": c["text"], "score": s})
        return out

    def grounded_context(self, query, max_chars=5000):
        """Return grounded excerpts with citations, for the LLM to synthesize."""
        hits = self.search(query)
        if not hits:
            return None, []
        parts, cites = [], []
        n = 0
        for h in hits:
            seg = "[%s | part %d]\n%s" % (h["doc"], h["chunk"] + 1, h["text"])
            if n + len(seg) > max_chars:
                break
            parts.append(seg)
            cites.append({"doc": h["doc"], "chunk": h["chunk"] + 1})
            n += len(seg)
        return "\n\n".join(parts), cites

    def analyze(self, query, llm_synth=None):
        """Grounded analysis. If llm_synth provided, use it; else extractive."""
        ctx, cites = self.grounded_context(query)
        if not ctx:
            return {"ok": False, "error": "ไม่พบข้อมูลในสมุด Notes — เพิ่มเอกสารก่อนครับ", "citations": []}
        if llm_synth:
            try:
                text = llm_synth(query, ctx)
            except Exception:
                text = None
        else:
            text = None
        if not text:
            # extractive fallback: top sentences from grounded excerpts
            sents = re.split(r"(?<=[.!?。！？])\s+", ctx)
            text = "\n".join("• " + s.strip() for s in sents[:8] if s.strip())
        rec = {"q": query, "answer": text, "citations": cites, "t": int(time.time())}
        with self.lock:
            self.notes.append(rec)
        self.save()
        return {"ok": True, "answer": text, "citations": cites,
                "sources_used": len(cites)}

    def list_docs(self):
        with self.lock:
            return [{"id": d["id"], "name": d["name"], "chunks": len(d["chunks"]),
                     "size": d["size"], "t": d["t"]} for d in self.docs]

    def remove(self, did):
        with self.lock:
            before = len(self.docs)
            self.docs = [d for d in self.docs if d["id"] != did]
        self.save()
        return {"ok": True, "removed": before - len(self.docs)}

    def snapshot(self):
        with self.lock:
            return {"docs": self.docs[-100:], "notes": self.notes[-200:]}

    def restore(self, data):
        with self.lock:
            if isinstance(data, dict) and "docs" in data:
                self.docs = data.get("docs", [])
                self.notes = data.get("notes", [])
                self.save()
                return True
        return False

    def stats(self):
        with self.lock:
            return {"documents": len(self.docs), "notes": len(self.notes),
                    "chunks": sum(len(d["chunks"]) for d in self.docs)}
