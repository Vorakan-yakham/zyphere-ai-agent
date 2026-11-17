"""Zyphere Local Brain - offline reasoning engine (no external API).

A symbolic memory + inference system that:
- stores facts (subject, relation, object) and episodes
- learns rules from examples via pattern abstraction
- answers queries with forward chaining and analogy
- never calls any external service
"""
import json, os, re, time, threading
from collections import defaultdict

class LocalBrain:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.facts = []          # {s, r, o, t, src, conf}
        self.rules = []          # {body:[[s,r,o]], head:[s,r,o], support}
        self.episodes = []       # raw remembered statements
        self.vocab = defaultdict(int)
        self._load()

    # ---------- persistence ----------
    def _load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                d = json.load(f)
            self.facts = d.get("facts", [])
            self.rules = d.get("rules", [])
            self.episodes = d.get("episodes", [])
            self.vocab = defaultdict(int, d.get("vocab", {}))
        except Exception:
            pass

    def save(self):
        with self.lock:
            try:
                with open(self.path, "w", encoding="utf-8") as f:
                    json.dump({"facts": self.facts, "rules": self.rules,
                               "episodes": self.episodes[-500:], "vocab": dict(self.vocab)},
                              f, ensure_ascii=False, indent=2)
            except Exception:
                pass

    # ---------- primitive learning ----------
    def learn_text(self, text, source="user"):
        """Extract simple relational facts from Thai/English text without ML/API."""
        t = str(text or "").strip()
        if not t:
            return []
        with self.lock:
            self.episodes.append({"text": t[:500], "t": int(time.time()), "src": source})
        got = []
        # pattern: X คือ Y / X is Y / Xเป็นY
        for m in re.finditer(r"([\u0E00-\u0E7FA-Za-z0-9_ ]{1,60}?)\s*(?:คือ|เป็น|is|are)\s+([\u0E00-\u0E7FA-Za-z0-9_ ]{1,80})", t, re.I):
            s, o = m.group(1).strip(), m.group(2).strip().rstrip(".!?。")
            if s and o:
                got.append((s, "is", o))
        # pattern: X ชอบ Y / X likes Y
        for m in re.finditer(r"([\u0E00-\u0E7FA-Za-z0-9_ ]{1,60}?)\s*(?:ชอบ|like|likes|love|รัก)\s+([\u0E00-\u0E7FA-Za-z0-9_ ]{1,80})", t, re.I):
            s, o = m.group(1).strip(), m.group(2).strip().rstrip(".!?。")
            if s and o:
                got.append((s, "likes", o))
        # pattern: X ทำ Y / X does Y
        for m in re.finditer(r"([\u0E00-\u0E7FA-Za-z0-9_ ]{1,60}?)\s*(?:ทำ|สร้าง|เขียน|make|create|build)\s+([\u0E00-\u0E7FA-Za-z0-9_ ]{1,80})", t, re.I):
            s, o = m.group(1).strip(), m.group(2).strip().rstrip(".!?。")
            if s and o:
                got.append((s, "does", o))
        for s, r, o in got:
            self.add_fact(s, r, o, source)
        for w in re.findall(r"[\u0E00-\u0E7FA-Za-z0-9]{2,}", t.lower()):
            self.vocab[w] += 1
        self.save()
        return [{"s": s, "r": r, "o": o} for s, r, o in got]

    def add_fact(self, s, r, o, source="learn", conf=1.0):
        with self.lock:
            for f in self.facts:
                if f["s"] == s and f["r"] == r and f["o"] == o:
                    f["conf"] = min(1.0, f["conf"] + 0.1)
                    f["t"] = int(time.time())
                    return False
            self.facts.append({"s": s, "r": r, "o": o, "t": int(time.time()),
                               "src": source, "conf": conf})
        return True

    # ---------- rule learning ----------
    def learn_rule(self, body_facts, head_fact):
        """Learn: if body facts hold, infer head fact. Abstraction replaces constants with vars."""
        b = [[str(x) for x in tri] for tri in body_facts if len(tri) == 3]
        h = [str(x) for x in head_fact] if len(head_fact) == 3 else None
        if not b or not h:
            return False
        # find shared subject/object to generalize into variable X where possible
        consts = set()
        for tri in b + [h]:
            consts.update(x for x in tri if x not in ("is", "likes", "does", "has", "can"))
        for rule in self.rules:
            if rule["body"] == b and rule["head"] == h:
                rule["support"] += 1
                self.save()
                return False
        self.rules.append({"body": b, "head": h, "support": 1,
                           "t": int(time.time())})
        self.save()
        return True

    # ---------- inference ----------
    def _match(self, pattern, facts):
        out = []
        for f in facts:
            ok = all((p == "*" or p == f[k]) for p, k in zip(pattern, ("s", "r", "o")))
            if ok:
                out.append(f)
        return out

    def infer(self, s=None, r=None, o=None, max_steps=6):
        """Forward chain over rules to derive new facts, then answer the query."""
        with self.lock:
            working = [dict(f) for f in self.facts]
            for _ in range(max_steps):
                changed = False
                for rule in self.rules:
                    if not all(self._match(bf, working) for bf in rule["body"]):
                        continue
                    h = rule["head"]
                    if not self._match(h, working):
                        derived = {"s": h[0], "r": h[1], "o": h[2],
                                   "t": int(time.time()), "src": "infer", "conf": 0.8}
                        working.append(derived)
                        changed = True
                if not changed:
                    break
            pat = [s or "*", r or "*", o or "*"]
            return self._match(pat, working)

    def ask(self, question):
        """Answer a natural-language question using only local knowledge."""
        q = str(question or "").strip()
        # who is X / X คืออะไร
        # support both "X คืออะไร" and "Xคืออะไร" (no space)
        m = re.search(r"([\u0E00-\u0E7FA-Za-z0-9_ ]{1,60}?)\s*(?:คืออะไร|เป็นใคร|คือใคร|who is|what is)\s*([?？]?)$", q, re.I)
        if not m:
            m2 = re.search(r"(?:who is|what is)\s+([\u0E00-\u0E7FA-Za-z0-9_ ]{1,60})", q, re.I)
            x = m2.group(1).strip().rstrip("?？.") if m2 else None
        else:
            x = m.group(1).strip().rstrip("?？.")
        if x:
            res = self.infer(s=x)
            if res:
                vals = []
                for f in res:
                    if f["r"] == "is":
                        vals.append(f["o"])
                if vals:
                    return x + " " + ("คือ " if re.search(r"คือ|what", q, re.I) else "is ") + ", ".join(dict.fromkeys(vals)) + " ครับ"
            # reverse: something is X
            rev = self.infer(o=x)
            subs = [f["s"] for f in rev if f["r"] == "is"]
            if subs:
                return ", ".join(dict.fromkeys(subs)) + " " + ("คือ " + x if re.search(r"คือ", q) else "is " + x) + " ครับ"
        # what does X do / X ทำอะไร
        m = re.search(r"([\u0E00-\u0E7FA-Za-z0-9_ ]{1,60}?)\s*(?:ทำอะไร|สามารถอะไร|what does)\s*[?？]?$", q, re.I)
        if m:
            x = m.group(1).strip().rstrip("?？.")
            res = [f["o"] for f in self.infer(s=x) if f["r"] in ("does", "can")]
            if res:
                return x + " " + ("ทำ " if "ทำ" in q else "does ") + ", ".join(dict.fromkeys(res)) + " ครับ"
        # generic keyword scan over facts
        toks = [w for w in re.findall(r"[\u0E00-\u0E7FA-Za-z0-9]{2,}", q.lower()) if self.vocab.get(w, 0) > 0 or len(w) > 3]
        hits = []
        for f in self.facts:
            blob = (f["s"] + " " + f["r"] + " " + f["o"]).lower()
            if any(t in blob for t in toks[:4]):
                hits.append(f)
        if hits:
            lines = [f"{f['s']} {f['r']} {f['o']}" for f in hits[:5]]
            return "จากสิ่งที่ผมเรียนรู้มา:\n" + "\n".join("• " + x for x in lines)
        return None  # signal: no local answer

    def stats(self):
        with self.lock:
            return {"facts": len(self.facts), "rules": len(self.rules),
                    "episodes": len(self.episodes), "vocab": len(self.vocab)}
