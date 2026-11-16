"""Uploaded-file handling: text, PDF and images become neutral content blocks (core.llm converts them for the local model)."""
import base64
import csv
import io
import json
from dataclasses import dataclass
from typing import List, Optional

TEXT_TYPES = ["txt", "md", "py", "csv", "json", "cpp", "ino", "js", "html"]
IMAGE_TYPES = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}
SUPPORTED_TYPES = TEXT_TYPES + ["pdf"] + list(IMAGE_TYPES)
MAX_BYTES = 10 * 1024 * 1024
MAX_TEXT_CHARS = 150_000


@dataclass
class Attachment:
    name: str
    kind: str  # "text" | "pdf" | "image"
    text: str = ""
    data_b64: str = ""
    media_type: str = ""

    def to_blocks(self) -> List[dict]:
        if self.kind == "text":
            return [{"type": "text", "text": f"[Attached file: {self.name}]\n{self.text}\n[End of file: {self.name}]"}]
        if self.kind == "pdf":
            return [
                {"type": "text", "text": f"[Attached PDF: {self.name}]"},
                {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": self.data_b64}},
            ]
        return [
            {"type": "text", "text": f"[Attached image: {self.name}]"},
            {"type": "image", "source": {"type": "base64", "media_type": self.media_type, "data": self.data_b64}},
        ]


def parse_uploaded_file(uploaded_file) -> Optional[Attachment]:
    """Returns an Attachment, or None if nothing uploaded. Raises ValueError for unusable files."""
    if uploaded_file is None:
        return None
    name = uploaded_file.name
    raw = uploaded_file.getvalue()
    if len(raw) > MAX_BYTES:
        raise ValueError(f"ไฟล์ {name} ใหญ่เกิน {MAX_BYTES // (1024 * 1024)} MB")
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""

    if ext in IMAGE_TYPES:
        return Attachment(name, "image", data_b64=base64.b64encode(raw).decode(), media_type=IMAGE_TYPES[ext])
    if ext == "pdf":
        return Attachment(name, "pdf", data_b64=base64.b64encode(raw).decode())

    for enc in ("utf-8", "tis-620"):  # tis-620: legacy Thai encoding
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError(f"อ่านไฟล์ {name} ไม่ได้ (ไม่ใช่ข้อความ)")

    truncated = len(text) > MAX_TEXT_CHARS
    text = text[:MAX_TEXT_CHARS]
    if ext == "json":
        try:
            text = json.dumps(json.loads(text), indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            pass
    elif ext == "csv":
        try:
            rows = list(csv.reader(io.StringIO(text)))
            if rows:
                text = f"[CSV summary: {len(rows)} rows x {len(rows[0])} columns; header={rows[0]}]\n{text}"
        except csv.Error:
            pass
    if truncated:
        text += "\n[... file truncated ...]"
    return Attachment(name, "text", text=text)
