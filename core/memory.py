"""MemoryBank: chat-facing view over the SQLite Store (chat history + lessons + skills context)."""
from typing import List

from core.store import Store


class MemoryBank(Store):
    def append(self, record: dict) -> None:
        self.add_event("chat", goal=record.get("goal", ""), summary=record.get("summary", ""),
                       axis=record.get("axis", ""), file_info=record.get("file_info", ""),
                       status=record.get("status", ""))

    def recent(self, n: int = 6) -> List[dict]:
        rows = list(reversed(self.events(kind="chat", limit=n)))  # oldest -> newest
        return [{**r, "timestamp": r["ts"]} for r in rows]

    def context_block(self, n: int = 5) -> str:
        parts = []
        lessons = self.top_lessons(8)
        if lessons:
            parts.append("LESSONS LEARNED about this user and their work (apply them silently):\n"
                         + "\n".join(f"- {l['text']}" for l in lessons))
        skills = self.list_skills()
        if skills:
            parts.append("VERIFIED SKILLS (sandbox-tested helper functions the user can run in the Skills tab):\n"
                         + "\n".join(f"- {s['name']}: {s['description']}" for s in skills[:12]))
        rows = self.recent(n)
        if rows:
            parts.append("MEMORY (earlier operations by this user, may be relevant):\n" + "\n".join(
                f"- [{r['ts']}] ({r['axis']}) {r['goal'][:160]}" + (f" -> {r['summary']}" if r["summary"] else "")
                for r in rows))
        return "\n\n".join(parts)

    def clear(self) -> None:
        """Clears chat memory only; lessons, skills and tasks are kept."""
        self.clear_events("chat")

    def __len__(self) -> int:
        return self.count_events("chat")
