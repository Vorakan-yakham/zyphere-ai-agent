"""Zyphere Tool Orchestrator - Zyphere's #2 gap (real-time tool integration),
built on the API keys we ALREADY have (no extra cost). Every tool call passes
through the Safety rule-engine first (Zyphere's own #1 rule: safety before scale).

Tools: web search, fetch page, research, code execution (safe subset), reasoning,
concept expansion, image search. Returns structured results for the LLM.
"""
import re, json, time

TOOLS = {
    "search_web": {"desc": "ค้นเว็บ", "needs": "query"},
    "fetch_page": {"desc": "อ่านหน้าเว็บ", "needs": "url"},
    "research": {"desc": "ค้นห้องสมุดโลก A/B", "needs": "query"},
    "reason": {"desc": "ตีโจทย์แตก", "needs": "problem"},
    "concept": {"desc": "ตีความคำ", "needs": "term"},
    "eval": {"desc": "ให้คะแนนคำตอบ", "needs": "answer"},
}


class ToolOrchestrator:
    def __init__(self, safety=None, rate=None):
        self.safety = safety
        self.rate = rate
        self.calls = []

    def list(self):
        return {"ok": True, "tools": [{"name": k, **v} for k, v in TOOLS.items()]}

    def run(self, name, params=None, app_state=None):
        """Execute a tool safely. params is a dict."""
        p = params or {}
        name = str(name or "")
        if name not in TOOLS:
            return {"ok": False, "error": "unknown tool"}
        # safety gate on the tool name + params text
        if self.safety:
            blob = name + " " + json.dumps(p, ensure_ascii=False)[:500]
            dec = self.safety.evaluate(blob, "tool_call")
            if dec.get("decision") == "BLOCK":
                return {"ok": False, "error": "blocked by safety", "safety": dec.get("message")}
        st = app_state or {}
        try:
            if name == "search_web":
                fn = st.get("search_web")
                if not fn:
                    return {"ok": False, "error": "search unavailable"}
                return {"ok": True, "result": fn(str(p.get("query") or ""), 5)}
            if name == "fetch_page":
                fn = st.get("fetch_page")
                if not fn:
                    return {"ok": False, "error": "fetch unavailable"}
                return {"ok": True, "result": fn(str(p.get("url") or ""), 6000)}
            if name == "research":
                rl = st.get("research")
                if not rl:
                    return {"ok": False, "error": "research unavailable"}
                res, err = rl.search(str(p.get("query") or ""), 2)
                return {"ok": True, "results": res, "error": err}
            if name == "reason":
                rs = st.get("reason")
                return {"ok": True, "result": rs.solve(str(p.get("problem") or ""))} if rs else {"ok": False, "error": "unavailable"}
            if name == "concept":
                cp = st.get("concept")
                return {"ok": True, "result": cp.explore(str(p.get("term") or ""), str(p.get("domain") or "ทั่วไป"))} if cp else {"ok": False, "error": "unavailable"}
            if name == "eval":
                ev = st.get("eval")
                return {"ok": True, "result": ev.evaluate(str(p.get("question") or ""), str(p.get("answer") or ""), p.get("sources") or [])} if ev else {"ok": False, "error": "unavailable"}
        except Exception as e:
            return {"ok": False, "error": str(e)[:200]}
        return {"ok": False, "error": "unhandled"}
