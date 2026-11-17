"""Zyphere RAG - Retrieval-Augmented Generation from ALL internal stores.

Owner/Zyphere round-4: pull relevant internal knowledge BEFORE the LLM answers.
Unifies: knowledge items, notebook docs, research library, dev_brain lessons.
Ranking: token overlap + Thai n-gram (no external vector DB needed -> free).
Measure: precision@k against a Q&A set (via eval_loop / reported hits).

HONEST: lexical retrieval, not neural embeddings. Good enough for grounded
answers from our own stores; marks sources so claims are verifiable.
"""
import re


def _tokens(s):
    return [w for w in re.findall(r"[\u0E00-\u0E7FA-Za-z0-9]{2,}", str(s or "").lower())]


def _score(q, text):
    qt, tt = _tokens(q), _tokens(text)
    if not qt:
        return 0
    s = 0
    for w in qt:
        if w in tt:
            s += 2 if len(w) >= 4 else 1
        elif len(w) >= 3:
            for i in range(len(w) - 2):
                g = w[i:i + 3]
                if any(g in t for t in tt):
                    s += 1
                    break
    return s


class RAG:
    def retrieve(self, query, state=None, top=5, max_chars=4000):
        state = state or {}
        q = str(query or "")
        candidates = []
        # knowledge items
        for it in (state.get("knowledge") or []):
            blob = str(it.get("topic", "")) + " " + str(it.get("summary", ""))
            sc = _score(q, blob)
            if sc:
                candidates.append((sc, "knowledge", it.get("topic", ""), blob[:400]))
        # notebook docs
        for d in (state.get("notebook_docs") or []):
            for c in (d.get("chunks") or []):
                sc = _score(q, str(c.get("text", "")))
                if sc:
                    candidates.append((sc, "notebook:" + str(d.get("name", "")), "part " + str(c.get("i", 0)), str(c.get("text", ""))[:400]))
        # research records
        for rec in (state.get("research") or []):
            for r in (rec.get("records") or []):
                sc = _score(q, str(r.get("summary", "")) + str(r.get("doc_title", "")))
                if sc:
                    candidates.append((sc, "research:" + str(r.get("reliability", "D")), str(r.get("doc_title", ""))[:80], str(r.get("summary", ""))[:400]))
        # dev brain lessons
        for f in (state.get("lessons") or []):
            blob = str(f.get("s", "")) + " " + str(f.get("o", ""))
            sc = _score(q, blob)
            if sc:
                candidates.append((sc, "own_brain", str(f.get("s", "")), blob[:300]))
        candidates.sort(key=lambda x: -x[0])
        out, used = [], 0
        for sc, src, title, text in candidates[:top]:
            seg = "[%s | %s]\n%s" % (src, title, text)
            if used + len(seg) > max_chars:
                break
            out.append({"score": sc, "source": src, "title": title, "text": text})
            used += len(seg)
        return {"ok": True, "query": q, "hits": len(out), "chunks": out,
                "grounded": bool(out), "note": "Lexical RAG (free) — sources marked for verification"}

    def inject(self, base_sys, query, state):
        """Build system prompt with grounded internal knowledge."""
        r = self.retrieve(query, state)
        if not r["chunks"]:
            return base_sys, r
        lines = ["[ภายใน: ความรู้จากฐานของ Zyphere — ใช้ประกอบคำตอบและอ้างแหล่งเมื่อจำเป็น]"]
        for c in r["chunks"]:
            lines.append("- (%s) %s: %s" % (c["source"], c["title"], c["text"][:220]))
        return (base_sys + "\n" + "\n".join(lines)[:3000])[:10000], r
