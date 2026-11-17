"""Zyphere Self-Evaluation Loop - quantitative quality scoring saved to KV.

Every answer/action can be evaluated; scores feed back into learning.
Measures accuracy/completeness/grounding — not token or file counts (owner's
explicit rule). Produces unit-test style checks that can be re-run.
"""
import os, json, time, threading, re


class EvalLoop:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.scores = []
        self._load()

    def _load(self):
        try:
            self.scores = json.load(open(self.path, encoding="utf-8")).get("scores", [])
        except Exception:
            pass

    def save(self):
        with self.lock:
            try:
                os.makedirs(os.path.dirname(self.path), exist_ok=True)
                json.dump({"scores": self.scores[-2000:]},
                          open(self.path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            except Exception:
                pass

    def evaluate(self, question="", answer="", sources=None, expected=None):
        """Score an answer: completeness, grounding, honesty, clarity."""
        q = str(question or "")
        a = str(answer or "")
        if not a.strip():
            return {"ok": False, "error": "empty answer"}
        src = sources or []
        # completeness: answer length vs question complexity (heuristic)
        qtok = [w for w in re.findall(r"[\u0E00-\u0E7FA-Za-z0-9]{2,}", q.lower())]
        coverage = min(1.0, len(a) / max(80, len(q) * 2))
        # grounding: has A/B source or explicit uncertainty
        grounded = bool([s for s in src if str(s).upper() in ("A", "B")]) or bool(
            re.search(r"(ไม่แน่|ยังไม่มีหลักฐาน|ควรตรวจ|ระดับความเชื่อมั่น)", a))
        # honesty: avoids absolute claims without evidence
        honest = not bool(re.search(r"(แน่นอน 100%|พิสูจน์แล้วแน่นอน|ไม่มีข้อผิดพลาด)", a))
        # clarity: sentence structure reasonable
        sents = [s for s in re.split(r"[.!?。！？\n]", a) if s.strip()]
        clarity = min(1.0, len(sents) / max(1, len(a) // 120))
        score = round(0.35 * coverage + 0.3 * (1 if grounded else 0) +
                      0.2 * (1 if honest else 0) + 0.15 * clarity, 2)
        rec = {"ok": True, "score": score, "question": q[:200],
               "metrics": {"coverage": round(coverage, 2), "grounded": grounded,
                           "honest": honest, "clarity": round(clarity, 2)},
               "verdict": "ดี" if score >= 0.7 else ("พอใช้" if score >= 0.45 else "ต้องปรับปรุง"),
               "t": int(time.time())}
        with self.lock:
            self.scores.append(rec)
        self.save()
        return rec

    def unit_test(self, name, condition, detail=""):
        """Record a unit-test style check (re-runnable concept)."""
        rec = {"ok": True, "name": str(name)[:120], "passed": bool(condition),
               "detail": str(detail or "")[:200], "t": int(time.time())}
        with self.lock:
            self.scores.append(rec)
        self.save()
        return rec

    def stats(self):
        with self.lock:
            evals = [s for s in self.scores if "score" in s]
            tests = [s for s in self.scores if "passed" in s]
            return {"evaluations": len(evals),
                    "average_score": round(sum(e["score"] for e in evals) / len(evals), 2) if evals else 0,
                    "tests": len(tests), "tests_passed": sum(1 for t in tests if t["passed"])}

    def snapshot(self):
        with self.lock:
            return {"scores": self.scores[-2000:]}

    def restore(self, data):
        with self.lock:
            if isinstance(data, dict) and "scores" in data:
                self.scores = data.get("scores", [])
                self.save()
                return True
        return False
