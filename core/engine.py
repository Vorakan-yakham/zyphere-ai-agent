"""ZyphereAdvancedEngine: 4-axis routing, prompt assembly, optional deep-analysis pass."""
from datetime import datetime
from typing import Generator, List, Optional

from core.prompts import ANSWER_WITH_PLAN, AXES, BASE, PLAN_PROMPT

AXIS_KNOWLEDGE = "Knowledge & Full-Stack Architecture"
AXIS_AEROSPACE = "Aerospace & CAD Engine"
AXIS_ROBOTICS = "Robotics Core"
AXIS_CONTENT = "Content Automation"

KEYWORDS = [
    (AXIS_AEROSPACE, ["cad", "aerospace", "drone", "uav", "3d", "flight", "airfoil", "wing", "propeller", "stl",
                      "อากาศยาน", "โดรน", "ปีก", "ใบพัด"]),
    (AXIS_ROBOTICS, ["robot", "kinematic", "motor", "sensor", "plc", "firmware", "arduino", "servo", "pid",
                     "หุ่นยนต์", "มอเตอร์", "เซ็นเซอร์"]),
    (AXIS_CONTENT, ["content", "video", "script", "marketing", "automation", "caption", "youtube", "tiktok",
                    "คอนเทนต์", "วิดีโอ", "สคริปต์", "การตลาด"]),
]
FILE_AXIS = {
    (".cpp", ".ino", ".hex"): AXIS_ROBOTICS,
    (".stl", ".step", ".iges"): AXIS_AEROSPACE,
}
HISTORY_TURNS = 16


class ZyphereAdvancedEngine:
    def __init__(self, memory, llm):
        self.memory = memory
        self.llm = llm

    # ---------- routing ----------
    def classify_axis(self, text: str, attachments: Optional[list] = None) -> str:
        t = text.lower()
        for axis, words in KEYWORDS:
            if any(k in t for k in words):
                return axis
        for a in attachments or []:
            for exts, axis in FILE_AXIS.items():
                if a.name.lower().endswith(exts):
                    return axis
        return AXIS_KNOWLEDGE

    # ---------- prompt assembly ----------
    def build_system(self, axis: str, plan: Optional[str] = None) -> str:
        parts = [BASE, AXES[axis], f"Current date/time: {datetime.now():%Y-%m-%d %H:%M}"]
        mem = self.memory.context_block()
        if mem:
            parts.append(mem)
        if plan:
            parts.append(ANSWER_WITH_PLAN.format(plan=plan))
        return "\n\n".join(parts)

    @staticmethod
    def build_messages(history: List[dict], prompt: str, attachments: Optional[list] = None) -> List[dict]:
        past = [{"role": m["role"], "content": m["content"]} for m in history[-HISTORY_TURNS:]
                if m["role"] in ("user", "assistant") and m["content"]]
        while past and past[0]["role"] != "user":  # API requires first message from user
            past.pop(0)
        blocks = []
        for a in attachments or []:
            blocks.extend(a.to_blocks())
        blocks.append({"type": "text", "text": prompt})
        return past + [{"role": "user", "content": blocks}]

    # ---------- generation ----------
    def plan(self, history, prompt, attachments, axis) -> str:
        system = self.build_system(axis) + "\n\n" + PLAN_PROMPT
        return self.llm.complete(system, self.build_messages(history, prompt, attachments), max_tokens=900).strip()

    def stream_answer(self, history, prompt, attachments, axis, plan: Optional[str] = None,
                      max_tokens: int = 4096) -> Generator[str, None, None]:
        yield from self.llm.stream(self.build_system(axis, plan),
                                   self.build_messages(history, prompt, attachments), max_tokens)

    # ---------- memory ----------
    def record(self, prompt: str, axis: str, attachments: Optional[list], answer: str) -> None:
        self.memory.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "goal": prompt,
            "axis": axis,
            "file_info": ", ".join(a.name for a in attachments) if attachments else "No file attached",
            "summary": " ".join(answer.split())[:200],
            "status": "COMPUTED",
        })
