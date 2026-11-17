"""Zyphere Behavior Adapter + Cross-Modal Memory Alignment - local, free.

Zyphere proposed user-behavior adaptation + linking image/audio/text memory.
Implemented WITHOUT external analytics (no Firebase/Mixpanel, no cost):
- event log (click, playback, voice, topic interest) -> adapts interests
- modal memory: link text/image/audio by shared id -> recall across modalities
- feeds preferences so replies match observed behavior

HONEST: local lexical events, not neural embeddings. No hardware needed.
"""
import os, json, time, threading, re


class Behavior:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.events = []
        self.interests = {}
        self.modal = {}  # id -> {text, image, audio, t}
        self._load()

    def _load(self):
        try:
            d = json.load(open(self.path, encoding="utf-8"))
            self.events = d.get("events", [])
            self.interests = d.get("interests", {})
            self.modal = d.get("modal", {})
        except Exception:
            pass

    def save(self):
        with self.lock:
            try:
                os.makedirs(os.path.dirname(self.path), exist_ok=True)
                json.dump({"events": self.events[-2000:], "interests": self.interests,
                           "modal": self.modal[-500:] if isinstance(self.modal, list) else self.modal},
                          open(self.path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            except Exception:
                pass

    def track(self, event="view", target="", meta=None):
        e = {"event": str(event)[:40], "target": str(target)[:160],
             "meta": str(meta or "")[:300], "t": int(time.time())}
        with self.lock:
            self.events.append(e)
            for w in re.findall(r"[\u0E00-\u0E7FA-Za-z0-9]{3,}", e["target"].lower()):
                self.interests[w] = self.interests.get(w, 0) + 1
        self.save()
        return {"ok": True, "event": e["event"]}

    def link_modal(self, mid, text="", image="", audio=""):
        """Store one memory id linking text/image/audio (cross-modal alignment)."""
        with self.lock:
            cur = self.modal.get(str(mid), {"t": int(time.time())})
            if text: cur["text"] = str(text)[:1000]
            if image: cur["image"] = str(image)[:400]
            if audio: cur["audio"] = str(audio)[:400]
            cur["t"] = int(time.time())
            self.modal[str(mid)] = cur
            if len(self.modal) > 500:
                for k in list(self.modal)[:len(self.modal) - 500]:
                    self.modal.pop(k, None)
        self.save()
        return {"ok": True, "id": str(mid), "modal": cur}

    def recall_modal(self, query):
        """Find modal memories related to a query via text tokens."""
        qt = set(re.findall(r"[\u0E00-\u0E7FA-Za-z0-9]{3,}", str(query or "").lower()))
        hits = []
        for mid, m in self.modal.items():
            blob = str(m.get("text", "")).lower()
            overlap = len(qt & set(re.findall(r"[\u0E00-\u0E7FA-Za-z0-9]{3,}", blob)))
            if overlap:
                hits.append({"id": mid, "overlap": overlap, **m})
        hits.sort(key=lambda x: -x["overlap"])
        return {"ok": True, "hits": hits[:5]}

    def profile(self):
        top = sorted(self.interests.items(), key=lambda x: -x[1])[:10]
        return {"ok": True, "events": len(self.events), "top_interests": top,
                "modal_memories": len(self.modal)}

    def snapshot(self):
        with self.lock:
            return {"events": self.events[-2000:], "interests": self.interests, "modal": self.modal}

    def restore(self, data):
        with self.lock:
            if isinstance(data, dict) and "events" in data:
                self.events = data.get("events", [])
                self.interests = data.get("interests", {})
                self.modal = data.get("modal", {})
                self.save()
                return True
        return False
