"""ZyphereAdvancedEngine: 4-axis intent classification and code synthesis."""
from datetime import datetime
from typing import Optional, Tuple

AXIS_KNOWLEDGE = "Knowledge & Full-Stack Architecture"
AXIS_AEROSPACE = "Aerospace & CAD Engine"
AXIS_ROBOTICS = "Robotics Core"
AXIS_CONTENT = "Content Automation"

KEYWORDS = [
    (AXIS_AEROSPACE, ["cad", "aerospace", "drone", "3d", "part", "flight", "stl", "step"]),
    (AXIS_ROBOTICS, ["robot", "arm", "kinematics", "motor", "sensor", "plc", "firmware"]),
    (AXIS_CONTENT, ["content", "video", "script", "marketing", "automation"]),
]
FILE_AXIS = {
    (".cpp", ".ino", ".hex"): AXIS_ROBOTICS,
    (".stl", ".step", ".iges"): AXIS_AEROSPACE,
}

CODE_TEMPLATE = '''# ===================================================
# ZYPHERE AUTONOMOUS PRODUCTION MODULE (v3.0)
# Target Intent: {intent_comment}
# Processing Axis: {axis}
# ===================================================
{file_snippet}
import json
import logging
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")


class EnterpriseExecutionPipeline:
    def __init__(self):
        self.intent = {intent_repr}
        self.engine_axis = {axis_repr}
        self.execution_id = os.urandom(4).hex()

    def initialize_runtime(self):
        logging.info("Initializing runtime for axis: %s", self.engine_axis)
        logging.info("Execution ID: %s", self.execution_id)
        return True

    def compute_autonomous_payload(self):
        payload = {{
            "status": "SCAFFOLD",
            "target_intent": self.intent,
            "axis_target": self.engine_axis,
            "timestamp": datetime.now().isoformat(),
        }}
        return json.dumps(payload, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    pipeline = EnterpriseExecutionPipeline()
    if pipeline.initialize_runtime():
        print(pipeline.compute_autonomous_payload())
'''


class ZyphereAdvancedEngine:
    def __init__(self, memory_bank):
        self.memory = memory_bank

    def execute_pipeline(self, prompt: str, file_data: Optional[Tuple[str, str]] = None) -> dict:
        axis = self._classify_axis(prompt, file_data)
        file_name, file_content = file_data if file_data else (None, "")

        self.memory.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "goal": prompt,
            "axis": axis,
            "file_info": f"Attached File: {file_name}" if file_name else "No file attached",
            "status": "COMPUTED",
        })

        return {
            "axis": axis,
            "code": self._synthesize_code(prompt, axis, file_content),
            "summary": f"ระบบได้วิเคราะห์เป้าหมายผ่านแกน **{axis}** "
                       + ("พร้อมประมวลผลข้อมูลจากไฟล์ของคุณเรียบร้อยแล้วครับ" if file_name
                          else "เรียบร้อยแล้วครับ"),
        }

    def _classify_axis(self, text: str, file_data: Optional[Tuple[str, str]]) -> str:
        t = text.lower()
        # Prompt keywords take priority; file extension is a fallback signal.
        for axis, words in KEYWORDS:
            if any(k in t for k in words):
                return axis
        if file_data:
            name = file_data[0].lower()
            for exts, axis in FILE_AXIS.items():
                if name.endswith(exts):
                    return axis
        return AXIS_KNOWLEDGE

    def _synthesize_code(self, prompt: str, axis: str, file_content: str) -> str:
        snippet = ""
        if file_content:
            first = " ".join(file_content[:150].split())
            snippet = f"# Analyzed File Content Snippet:\n# {first}...\n"
        return CODE_TEMPLATE.format(
            intent_comment=" ".join(prompt.split())[:120],  # single line: can't break the comment
            axis=axis,
            file_snippet=snippet,
            intent_repr=repr(prompt),
            axis_repr=repr(axis),
        )
