"""Persistent memory bank: records are kept in a JSON file so they survive page refreshes."""
import json
import os
import tempfile
from typing import List

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "memory.json")


class MemoryBank:
    def __init__(self, path: str = DEFAULT_PATH, max_records: int = 500):
        self.path = path
        self.max_records = max_records
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self.records: List[dict] = self._load()

    def _load(self) -> List[dict]:
        if not os.path.exists(self.path):
            return []
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []

    def _save(self) -> None:
        # Atomic write: write to temp file then replace, so a crash can't corrupt the store.
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(self.path), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self.records, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self.path)
        except OSError:
            if os.path.exists(tmp):
                os.remove(tmp)

    def append(self, record: dict) -> None:
        self.records.append(record)
        self.records = self.records[-self.max_records:]
        self._save()

    def recent(self, n: int = 6) -> List[dict]:
        return self.records[-n:]

    def clear(self) -> None:
        self.records = []
        self._save()

    def __len__(self) -> int:
        return len(self.records)
