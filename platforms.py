"""Zyphere Platform Tracker - log platforms we sign up for, generate reports.
Ethics: gambling / illegal platforms are refused outright (owner rule).
"""
import json, os, time, threading

BLOCK = ("พนัน", "casino", "gambling", "bet", "slot", "บาคาร่า", "สล็อต", "พนันออนไลน์")


class Platforms:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.items = []
        self._load()

    def _load(self):
        try:
            self.items = json.load(open(self.path, encoding="utf-8")).get("items", [])
        except Exception:
            self.items = []

    def save(self):
        with self.lock:
            try:
                os.makedirs(os.path.dirname(self.path), exist_ok=True)
                with open(self.path, "w", encoding="utf-8") as f:
                    json.dump({"items": self.items[-500:]}, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

    def log(self, name, note="", status="prepared"):
        name = str(name or "").strip()[:80]
        if not name:
            return {"ok": False, "error": "missing platform name"}
        low = name.lower()
        if any(b in low for b in BLOCK):
            return {"ok": False, "error": "งดเด็ดขาด: เว็บพนัน/ผิดกฎหมาย (ตามกฎเจ้าของระบบ)"}
        with self.lock:
            hit = next((x for x in self.items if x.get("name", "").lower() == low), None)
            if hit:
                hit["updated"] = int(time.time())
                hit["status"] = str(status or hit.get("status"))[:40]
                if note:
                    hit["note"] = str(note)[:300]
            else:
                self.items.append({"name": name, "note": str(note or "")[:300],
                                   "status": str(status or "prepared")[:40],
                                   "created": int(time.time()), "updated": int(time.time())})
            self.save()
            return {"ok": True, "name": name, "total": len(self.items)}

    def report(self):
        with self.lock:
            return {"ok": True, "total": len(self.items), "items": list(reversed(self.items[-50:]))}

    def snapshot(self):
        with self.lock:
            return {"items": self.items[-500:]}

    def restore(self, data):
        with self.lock:
            items = (data or {}).get("items") if isinstance(data, dict) else None
            if isinstance(items, list):
                self.items = items[-500:]
                self.save()
                return True
        return False
