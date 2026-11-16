"""Autonomous cognition: reflect on interactions, learn lessons, write + test skills, propose ideas.

Every model call goes through Brain._ask, which enforces the kill switch and the daily budget.
Skills are only ever executed inside core.sandbox. Anything outside "think / note / sandboxed skill"
is turned into a proposal that waits for the user's approval (see core.safety.POLICY).
"""
import ast
import json
import re
import time
from typing import Callable, Dict, List, Optional

from core import prompts
from core.safety import BudgetExceeded, Guard, Verdict, authorize, redact
from core.sandbox import run_code, validate, SandboxViolation
from core.store import Store

NAME_RE = re.compile(r"^[a-z][a-z0-9_]{2,40}$")
SKILL_RE = re.compile(r"===NAME===\s*(.+?)\s*===DESCRIPTION===\s*(.+?)\s*===CODE===\s*(.*?)\s*===TESTS===\s*(.*)", re.S)
MAX_SKILLS = 40
KILL_PHRASES = {"หยุดฉุกเฉิน", "emergency stop", "kill switch"}


def extract_json(text: str) -> dict:
    a, b = text.find("{"), text.rfind("}")
    if a < 0 or b <= a:
        return {}
    try:
        data = json.loads(text[a:b + 1])
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def _strip_fence(s: str) -> str:
    s = s.strip()
    s = re.sub(r"^```[a-zA-Z]*\n?", "", s)
    return re.sub(r"\n?```$", "", s).strip()


def parse_skill(text: str) -> Optional[Dict[str, str]]:
    m = SKILL_RE.search(text or "")
    if not m:
        return None
    name, desc, code, tests = (g.strip() for g in m.groups())
    return {"name": name, "description": " ".join(desc.split())[:200],
            "code": _strip_fence(code), "tests": _strip_fence(tests)}


def check_skill(spec: Dict[str, str]) -> str:
    """Returns "" if the spec is acceptable, else a reason."""
    if not NAME_RE.match(spec["name"]):
        return "ชื่อต้องเป็น snake_case ภาษาอังกฤษ 3-41 ตัวอักษร"
    if not spec["code"] or not spec["tests"]:
        return "ไม่มีโค้ดหรือเทสต์"
    try:
        n_asserts = sum(isinstance(n, ast.Assert) for n in ast.walk(ast.parse(spec["tests"])))
    except SyntaxError as e:
        return f"tests syntax error: {e.msg}"
    if n_asserts < 3:
        return "เทสต์ต้องมี assert อย่างน้อย 3 ข้อ"
    try:
        validate(spec["code"])
        validate(spec["tests"])
    except SandboxViolation as e:
        return str(e)
    return ""


class Brain:
    def __init__(self, store: Store, guard: Guard, llm_factory: Callable[[str], object],
                 light_model: str = "claude-haiku-5-5", strong_model: str = "claude-sonnet-5-5"):
        self.store, self.guard, self.llm_factory = store, guard, llm_factory
        self.light_model, self.strong_model = light_model, strong_model

    # ---------- model access ----------
    def _ask(self, model: str, system: str, user: str, max_tokens: int, source: str) -> str:
        ok, why = self.guard.can_call(source)
        if not ok:
            raise BudgetExceeded(why)
        llm = self.llm_factory(model)
        text = llm.complete(system, [{"role": "user", "content": user}], max_tokens=max_tokens)
        self.guard.record(source, getattr(llm, "last_usage", (0, 0)))
        return text

    # ---------- skills ----------
    def learn_skill(self, request: str, source: str = "auto") -> Dict[str, object]:
        """Write -> static check -> sandbox test -> (one repair attempt) -> save. Never raises."""
        request = redact(request)[:1500]
        error = ""
        for attempt in (1, 2):
            user = f"Skill request:\n{request}"
            if error:
                user += f"\n\nYour previous attempt failed: {error}\nFix it and output the full format again."
            try:
                raw = self._ask(self.strong_model, prompts.SKILL_SYSTEM, user, 2500, source)
            except BudgetExceeded as e:
                return {"ok": False, "name": "", "error": f"budget/kill: {e}"}
            except Exception as e:
                return {"ok": False, "name": "", "error": redact(f"{type(e).__name__}: {e}")[:200]}

            spec = parse_skill(raw)
            if not spec:
                error = "output format wrong (use the exact ===NAME=== blocks)"
                continue
            bad = check_skill(spec)
            if bad:
                error = bad
                continue
            if source == "auto" and self.store.get_skill(spec["name"]):
                # an unattended run must never overwrite a skill the user may already rely on
                error = f"ชื่อ '{spec['name']}' มีอยู่แล้ว — ใช้ชื่ออื่นที่ต่างจากทักษะเดิม"
                continue
            res = run_code(spec["code"], spec["tests"])
            if not res["ok"]:
                error = f"tests failed: {res['error']}"[:300]
                continue
            version = self.store.save_skill(spec["name"], spec["description"], spec["code"], spec["tests"])
            self.store.record_skill_run(spec["name"], True)
            self.store.add_event("skill", goal=spec["name"], status="ok",
                                 summary=f"v{version} · {spec['description']} · tests PASS (attempt {attempt})")
            return {"ok": True, "name": spec["name"], "error": "", "version": version}

        self.store.add_event("skill", goal=request[:80], status="failed", summary=f"ล้มเหลว: {error}"[:300])
        return {"ok": False, "name": "", "error": error}

    # ---------- ideas ----------
    def _known_titles(self) -> set:
        return {t["title"].strip().lower() for t in self.store.tasks(limit=60)}

    def _handle_idea(self, idea: dict, source: str) -> str:
        title = " ".join(str(idea.get("title", "")).split())[:120]
        detail = str(idea.get("detail", ""))[:1500]
        kind = "skill" if idea.get("kind") == "skill" else "idea"
        if not title or title.lower() in self._known_titles():
            return ""
        if kind == "skill" and authorize("skill_create") == Verdict.ALLOW \
                and len(self.store.list_skills()) < MAX_SKILLS:
            tid = self.store.add_task("skill_auto", title, detail, "running")
            r = self.learn_skill(detail or title, source)
            self.store.update_task(tid, "done" if r["ok"] else "failed",
                                   f"skill {r.get('name')}" if r["ok"] else str(r["error"]))
            return f"skill:{title}"
        # everything else needs the user's approval
        self.store.add_task("proposal_skill" if kind == "skill" else "proposal_idea", title, detail, "awaiting_approval")
        return f"proposal:{title}"

    # ---------- thinking ----------
    def reflect(self, events: List[dict], source: str) -> str:
        log = "\n".join(f"- ({e['axis']}) USER: {redact(e['goal'])[:300]} | AI: {redact(e['summary'])[:160]}"
                        for e in reversed(events))
        raw = self._ask(self.light_model, prompts.REFLECT_SYSTEM, f"Recent interactions:\n{log}", 900, source)
        return self._apply(extract_json(raw), "Reflection", source, max(e["id"] for e in events))

    def idle_think(self, source: str) -> str:
        lessons = "\n".join(f"- {l['text']}" for l in self.store.top_lessons(10)) or "(none yet)"
        skills = "\n".join(f"- {s['name']}: {s['description']}" for s in self.store.list_skills()) or "(none yet)"
        raw = self._ask(self.light_model, prompts.IDLE_SYSTEM, f"LESSONS:\n{lessons}\n\nSKILLS:\n{skills}", 700, source)
        self.store.set_setting("last_idle_ts", time.time())
        return self._apply(extract_json(raw), "Idle thought", source, None)

    def _apply(self, data: dict, label: str, source: str, last_id: Optional[int]) -> str:
        added = []
        for item in (data.get("lessons") or [])[:3]:
            if isinstance(item, dict) and self.store.add_lesson(str(item.get("text", "")), str(item.get("topic", ""))):
                added.append(" ".join(str(item["text"]).split())[:100])
        acted = []
        for idea in (data.get("ideas") or [])[:2]:
            if isinstance(idea, dict):
                r = self._handle_idea(idea, source)
                if r:
                    acted.append(r)
        if last_id is not None:
            self.store.set_setting("last_reflected_id", last_id)
        summary = (f"+{len(added)} บทเรียน" + (": " + "; ".join(added) if added else "")
                   + (f" · {len(acted)} ไอเดีย: " + ", ".join(acted) if acted else ""))
        self.store.add_event("think", goal=label, summary=summary[:400], status="ok")
        return summary

    def _execute_approved(self, task: dict, source: str) -> None:
        if task["type"] == "proposal_skill":
            r = self.learn_skill(task["detail"] or task["title"], source)
            self.store.update_task(task["id"], "done" if r["ok"] else "failed",
                                   f"skill {r.get('name')}" if r["ok"] else str(r["error"]))
        else:
            self.store.add_lesson(f"ผู้ใช้อนุมัติแนวคิด: {task['title']}", topic="approved", source="approval")
            self.store.update_task(task["id"], "done", "รับทราบ — บันทึกเป็นบทเรียนแล้ว")

    def cycle(self, force: bool = False) -> Dict[str, object]:
        """One autonomous step. force=True is a manual 'think now' by the user (budget is not the autonomous one)."""
        source = "manual" if force else "auto"
        if not force:
            if self.guard.killed():
                return {"ran": False, "reason": "kill switch active"}
            if not self.guard.autonomy_enabled():
                return {"ran": False, "reason": "autonomy off"}
        ok, why = self.guard.can_call(source)
        if not ok:
            return {"ran": False, "reason": why}
        did = []
        try:
            for t in self.store.tasks(["approved"], limit=3):
                self._execute_approved(t, source)
                did.append(f"approved:{t['title']}")
            last = int(self.store.get_setting("last_reflected_id", 0) or 0)
            new = self.store.events(kind="chat", since_id=last, limit=15)
            if new:
                did.append(self.reflect(new, source))
            else:
                idle_h = float(self.store.get_setting("idle_hours", 6) or 6)
                due = time.time() - float(self.store.get_setting("last_idle_ts", 0) or 0) >= idle_h * 3600
                if force or (due and len(self.store.list_skills()) + len(self.store.tasks(["awaiting_approval"])) < MAX_SKILLS):
                    did.append(self.idle_think(source))
        except BudgetExceeded as e:
            return {"ran": bool(did), "reason": f"stopped: {e}"}
        except Exception as e:
            msg = redact(f"{type(e).__name__}: {e}")[:200]
            self.store.add_event("error", goal="cycle", summary=msg, status="error")
            return {"ran": bool(did), "reason": msg}
        return {"ran": bool(did), "reason": "; ".join(did) if did else "nothing to do"}
