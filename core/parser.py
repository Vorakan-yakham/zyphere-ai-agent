"""Uploaded-file parsing: returns (filename, text) for the engine."""
import csv
import io
import json
from typing import Optional, Tuple

SUPPORTED_TYPES = ["txt", "py", "csv", "json", "md", "cpp", "ino"]
MAX_CHARS = 200_000


def parse_uploaded_file(uploaded_file) -> Optional[Tuple[str, str]]:
    if uploaded_file is None:
        return None
    name = uploaded_file.name
    raw = uploaded_file.getvalue()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = raw.decode("tis-620")  # common Thai legacy encoding
        except UnicodeDecodeError:
            return name, "[Binary or unsupported encoding]"

    text = text[:MAX_CHARS]
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""

    if ext == "json":
        try:
            text = json.dumps(json.loads(text), indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            pass
    elif ext == "csv":
        try:
            rows = list(csv.reader(io.StringIO(text)))
            if rows:
                text = f"[CSV: {len(rows)} rows x {len(rows[0])} cols] header={rows[0]}\n" + text
        except csv.Error:
            pass
    return name, text
