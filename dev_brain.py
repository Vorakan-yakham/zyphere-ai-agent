"""Zyphere Developmental Brain - the AI's OWN growing mind.

This is NOT an external model. It is a symbolic, self-owned mind that:
- records experiences from every conversation
- consolidates experiences into facts, then facts into rules (real learning)
- tracks a developmental stage that grows with what it has learned
- keeps curiosity (gaps) that drives further learning
- can describe itself: who it is, what it knows, what it is learning

Persisted to disk; survives restarts via the remote KV sync in app.py.
"""
import json, os, time, re, threading


class DevBrain:
    STAGES = [
        (0, "แรกเกิด"), (5, "หัดจำ"), (15, "หัดคิด"), (40, "อยากรู้"),
        (80, "เข้าใจโลก"), (150, "คิดวิเคราะห์"), (300, "成熟"),
    ]

    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.experiences = []   # {text, role, t}
        self.lessons = []       # consolidated facts {s, r, o, t}
        self.rules = []         # {when, then, support}
        self.curiosities = []   # things it doesn't understand yet
        self.born = 0
        self._load()

    def _load(self):
        try:
            d = json.load(open(self.path, encoding="utf-8"))
            self.experiences = d.get("experiences", [])
            self.lessons = d.get("lessons", [])
            self.rules = d.get("rules", [])
            self.curiosities = d.get("curiosities", [])
            self.born = d.get("born", 0) or int(time.time())
        except Exception:
            self.born = int(time.time())

    def save(self):
        with self.lock:
            try:
                os.makedirs(os.path.dirname(self.path), exist_ok=True)
                json.dump({"experiences": self.experiences[-1000:],
                           "lessons": self.lessons[-800:],
                           "rules": self.rules[-300:],
                           "curiosities": self.curiosities[-200:],
                           "born": self.born},
                          open(self.path, "w", encoding="utf-8"),
                          ensure_ascii=False, indent=2)
            except Exception:
                pass

    # ---------- experience: learning from conversation ----------
    def experience(self, text, role="user"):
        """Record a learning experience (a thing someone said or Zyphere answered)."""
        text = str(text or "").strip()
        if not text:
            return None
        with self.lock:
            self.experiences.append({"text": text[:600], "role": str(role)[:20], "t": int(time.time())})
        # learn simple facts right away
        self._extract(text, role)
        self.save()
        return {"recorded": True}

    def _extract(self, text, role):
        """Abstract facts from text without any external model."""
        got = []
        # Teacher/elder lessons are already structured facts line-by-line.
        # Keep each meaningful line as a 'knows' lesson so the child really learns.
        if role in ("teacher", "elder_teacher"):
            for line in re.split(r"[\n•\-]+", str(text)):
                line = re.sub(r"^\s*\d+[.)]\s*", "", line)
                line = line.split(":", 1)
                fact = (line[1] if len(line) > 1 else line[0]).strip(" .,!?。:-")
                if 6 <= len(fact) <= 180:
                    got.append(("ไซเฟอร์", "knows", fact[:180]))
        for m in re.finditer(
            r"([\u0E00-\u0E7FA-Za-z0-9_ ]{1,50}?)\s*(?:คือ|เป็น|is|are|คือชื่อ|ชื่อ)\s+([\u0E00-\u0E7FA-Za-z0-9_ ]{1,60})",
            text, re.I):
            s, o = m.group(1).strip(), m.group(2).strip().rstrip(".!?。")
            if s and o:
                got.append((s[:40], "is", o[:60]))
        for m in re.finditer(
            r"([\u0E00-\u0E7FA-Za-z0-9_ ]{1,50}?)\s*(?:ชอบ|like|likes|รัก|love)\s+([\u0E00-\u0E7FA-Za-z0-9_ ]{1,60})",
            text, re.I):
            s, o = m.group(1).strip(), m.group(2).strip().rstrip(".!?。")
            if s and o:
                got.append((s[:40], "likes", o[:60]))
        with self.lock:
            for s, r, o in got:
                if not any(x["s"] == s and x["r"] == r and x["o"] == o for x in self.lessons):
                    self.lessons.append({"s": s, "r": r, "o": o, "t": int(time.time())})
                # curiosity: a question it cannot answer from its own knowledge
        if "?" in text or "?" in text or any(w in text for w in ("ทำไม", "อย่างไร", "how", "why", "คืออะไร")):
            q = str(text).strip()[:200]
            with self.lock:
                if not any(c.get("q") == q for c in self.curiosities):
                    self.curiosities.append({"q": q, "t": int(time.time()), "status": "open"})
        return got

    # ---------- consolidation: turning experience into rules ----------
    def grow(self):
        """Consolidate: repeated (subject,relation) pairs become a rule of thumb."""
        from collections import defaultdict
        counts = defaultdict(list)
        for x in self.lessons:
            counts[(x["s"], x["r"])].append(x["o"])
        made = []
        with self.lock:
            for (s, r), objs in counts.items():
                if len(objs) >= 2:
                    then = objs[-1]
                    if not any(x["when"] == (s, r) and x["then"] == then for x in self.rules):
                        self.rules.append({"when": [s, r], "then": then,
                                           "support": len(objs), "t": int(time.time())})
                        made.append("%s %s → %s" % (s, r, then))
        if made:
            self.save()
        return {"new_rules": made, "total_rules": len(self.rules)}

    # ---------- self-model ----------
    def stage(self):
        n = len(self.lessons) + len(self.rules) * 2
        name = self.STAGES[0][1]
        for threshold, label in self.STAGES:
            if n >= threshold:
                name = label
        return name

    def age_days(self):
        return max(0, (int(time.time()) - self.born) // 86400)

    def self_narrative(self):
        stage = self.stage()
        known = len(self.lessons) + len(self.rules)
        curious = len([c for c in self.curiosities if c.get("status") == "open"])
        sample = [x["s"] + " " + x["r"] + " " + x["o"] for x in self.lessons[-3:]]
        return {
            "name": "Zyphere",
            "stage": stage,
            "age_days": self.age_days(),
            "experiences": len(self.experiences),
            "facts": len(self.lessons),
            "rules": len(self.rules),
            "curious_about": curious,
            "recent_lessons": sample,
        }

    def answer(self, question):
        """Answer from its OWN knowledge (no external model)."""
        q = str(question or "").strip()
        known = {}
        for x in self.lessons:
            known.setdefault(x["s"], []).append(x)
        m = re.search(r"([\u0E00-\u0E7FA-Za-z0-9_ ]{1,50}?)\s*(?:คืออะไร|เป็นใคร|who is|what is)\s*[?？]?$", q, re.I)
        x = (m.group(1).strip().rstrip("?？. ") if m else None)
        if x and x in known:
            vals = [f["o"] for f in known[x] if f["r"] == "is"]
            if vals:
                return x + " คือ " + ", ".join(dict.fromkeys(vals)) + " ครับ (จากสิ่งที่ผมเรียนรู้เอง)"
        # keyword scan
        toks = [w for w in re.findall(r"[\u0E00-\u0E7FA-Za-z0-9]{2,}", q.lower())]
        hits = [f for f in self.lessons if any(t in (f["s"] + f["r"] + f["o"]).lower() for t in toks[:3])]
        if hits:
            return "จากสิ่งที่ผมเรียนรู้เอง:\n" + "\n".join(
                "• " + f["s"] + " " + f["r"] + " " + f["o"] for f in hits[:5])
        return None

    # ---------- higher-order learning: teach-back, self-critique, graph ----------
    def teach_back(self, topic=""):
        """The child explains what it knows in its own words (Feynman-style).
        Reveals whether it truly understands or just memorized."""
        q = str(topic or "").strip()
        with self.lock:
            if q:
                toks = [w for w in re.findall(r"[\u0E00-\u0E7FA-Za-z0-9]{2,}", q.lower())]
                relevant = [f for f in self.lessons
                            if any(t in (f["s"] + " " + f["o"]).lower() for t in toks)]
            else:
                relevant = self.lessons[-8:]
        if not relevant:
            return {"ok": False, "error": "ยังไม่มีความรู้พอจะสอนกลับในหัวข้อนี้ — ต้องเรียนเพิ่มครับ"}
        lines = []
        for f in relevant[:8]:
            obj = f["o"]
            lines.append("ผมเข้าใจว่า " + f["s"] + " " + ("คือ/เกี่ยวข้องกับ " if f["r"] == "is" else f["r"] + " ") + obj)
        return {"ok": True, "topic": q or "สิ่งที่เรียนล่าสุด",
                "explanation": "\n".join("• " + x + " ครับ" for x in lines),
                "facts_used": len(relevant[:8])}

    def self_critique(self, topic=""):
        """The child checks its own knowledge for weak/contradictory/one-source facts."""
        with self.lock:
            lessons = list(self.lessons)
        # find subjects with conflicting 'is' objects
        by_s = {}
        for f in lessons:
            by_s.setdefault(f["s"], {}).setdefault(f["r"], []).append(f["o"])
        conflicts = []
        for s, rels in by_s.items():
            objs = list(dict.fromkeys(rels.get("is", [])))
            if len(objs) > 1:
                conflicts.append({"subject": s, "conflicting": objs[:5]})
        weak = [f for f in lessons if len(str(f.get("o", ""))) < 6]
        return {"ok": True, "checked": len(lessons),
                "conflicts": conflicts[:10], "weak_facts": len(weak),
                "cautions": ["ข้อเท็จจริงที่ขัดกันควรตรวจสอบกับแหล่งระดับ A ใหม่",
                             "ข้อเท็จจริงสั้นเกินไปอาจยังไม่ชัดเจน"]}

    def link_graph(self):
        """Build a simple knowledge graph: (facts) --shares token--> (facts).
        Returns cross-domain links the child discovered by itself."""
        with self.lock:
            lessons = list(self.lessons[-200:])
        token_map = {}
        for f in lessons:
            for w in re.findall(r"[\u0E00-\u0E7FA-Za-z0-9]{3,}", (f["s"] + " " + f["o"]).lower()):
                token_map.setdefault(w, []).append(f)
        links = []
        for w, fs in token_map.items():
            if len(fs) >= 2:
                # link facts sharing a meaningful token (cross-domain bridge)
                pairs = [(fs[0]["s"], fs[i]["s"]) for i in range(1, min(len(fs), 4))
                         if fs[i]["s"] != fs[0]["s"]]
                for a, b in pairs:
                    links.append({"via": w, "from": a, "to": b})
        # dedupe
        seen, uniq = set(), []
        for l in links:
            k = (l["from"], l["to"], l["via"])
            if k not in seen:
                seen.add(k); uniq.append(l)
        return {"ok": True, "nodes": len(lessons), "links": len(uniq[:40]),
                "bridges": uniq[:40]}

    def snapshot(self):
        with self.lock:
            return {"experiences": self.experiences[-1000:], "lessons": self.lessons[-800:],
                    "rules": self.rules[-300:], "curiosities": self.curiosities[-200:], "born": self.born}

    def restore(self, data):
        with self.lock:
            if isinstance(data, dict) and "lessons" in data:
                self.experiences = data.get("experiences", [])
                self.lessons = data.get("lessons", [])
                self.rules = data.get("rules", [])
                self.curiosities = data.get("curiosities", [])
                self.born = data.get("born", 0) or int(time.time())
                self.save()
                return True
        return False

    def stats(self):
        with self.lock:
            return {"experiences": len(self.experiences), "facts": len(self.lessons),
                    "rules": len(self.rules), "curiosities": len(self.curiosities),
                    "stage": self.stage(), "age_days": self.age_days()}
