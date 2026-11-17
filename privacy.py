"""Zyphere Privacy Layer - the FREE JARVIS-grade gap Zyphere identified.

Long-term personal memory MUST be:
- encrypted at rest (not plaintext on disk / in remote KV)
- forgettable on request (right to be forgotten, GDPR-style)
- time-decaying (old personal facts fade unless reinforced)

Implemented with stdlib only (no paid lib): XOR stream + HMAC-like checksum.
HONEST: lightweight obfuscation for personal fields, NOT military-grade crypto.
Owner's data stays owner's. No gambling/illegal.
"""
import os, json, time, threading, hashlib, base64


class Privacy:
    def __init__(self, path, secret=""):
        self.path = path
        self.secret = secret or os.environ.get("ZY_PRIVACY_KEY", "zyphere-owner-2026")
        self.lock = threading.RLock()
        self.vault = {}      # id -> {ct, tag, t, ttl}
        self.forget_log = []
        self._load()

    def _key(self):
        return hashlib.sha256(self.secret.encode()).digest()

    def _crypt(self, data):
        """XOR stream + checksum (reversible). Lightweight, stdlib-only."""
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        k = self._key()
        out = bytearray()
        for i, b in enumerate(raw):
            out.append(b ^ k[i % len(k)])
        ct = base64.urlsafe_b64encode(bytes(out)).decode()
        tag = hashlib.sha256(raw + k).hexdigest()[:16]
        return ct, tag

    def _decrypt(self, ct, tag):
        try:
            raw = bytearray(base64.urlsafe_b64decode(ct.encode()))
            k = self._key()
            dec = bytes(b ^ k[i % len(k)] for i, b in enumerate(raw))
            if hashlib.sha256(dec + k).hexdigest()[:16] != tag:
                return None  # tampered
            return json.loads(dec.decode("utf-8"))
        except Exception:
            return None

    def _load(self):
        try:
            d = json.load(open(self.path, encoding="utf-8"))
            self.vault = d.get("vault", {})
            self.forget_log = d.get("forget_log", [])
        except Exception:
            pass

    def save(self):
        with self.lock:
            try:
                os.makedirs(os.path.dirname(self.path), exist_ok=True)
                json.dump({"vault": self.vault, "forget_log": self.forget_log[-500:]},
                          open(self.path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            except Exception:
                pass

    def store(self, mid, data, ttl_days=365):
        """Encrypt a personal memory into the vault."""
        ct, tag = self._crypt(data)
        with self.lock:
            self.vault[str(mid)] = {"ct": ct, "tag": tag, "t": int(time.time()),
                                    "ttl": int(ttl_days) * 86400}
        self.save()
        return {"ok": True, "id": str(mid), "encrypted": True}

    def recall(self, mid):
        with self.lock:
            e = self.vault.get(str(mid))
            if not e:
                return {"ok": False, "error": "not found"}
            # time-based decay: expired -> forget automatically
            if e.get("ttl") and time.time() - e["t"] > e["ttl"]:
                self.vault.pop(str(mid), None)
                self.save()
                return {"ok": False, "error": "expired (time-decayed)", "decayed": True}
            data = self._decrypt(e["ct"], e["tag"])
            if data is None:
                return {"ok": False, "error": "integrity check failed"}
            return {"ok": True, "id": str(mid), "data": data, "age_days": int((time.time() - e["t"]) // 86400)}

    def forget(self, mid):
        """Right to be forgotten — remove one or ALL personal memories."""
        with self.lock:
            if str(mid).lower() in ("all", "*", "ทุกอัน"):
                n = len(self.vault)
                self.vault = {}
            else:
                n = 1 if self.vault.pop(str(mid), None) else 0
            self.forget_log.append({"action": "forget", "target": str(mid)[:80],
                                    "removed": n, "t": int(time.time())})
        self.save()
        return {"ok": True, "removed": n, "forgotten": True}

    def decay_sweep(self):
        """Auto-forget everything past its TTL."""
        now = time.time()
        removed = []
        with self.lock:
            for k, e in list(self.vault.items()):
                if e.get("ttl") and now - e["t"] > e["ttl"]:
                    self.vault.pop(k, None)
                    removed.append(k)
        if removed:
            self.save()
        return {"ok": True, "decayed": len(removed), "ids": removed[:20]}

    def stats(self):
        with self.lock:
            return {"encrypted_memories": len(self.vault), "forget_events": len(self.forget_log),
                    "encryption": "XOR+HMAC(stdlib, lightweight)", "time_decay": True}

    def snapshot(self):
        with self.lock:
            return {"vault": self.vault, "forget_log": self.forget_log[-500:]}

    def restore(self, data):
        with self.lock:
            if isinstance(data, dict) and "vault" in data:
                self.vault = data.get("vault", {})
                self.forget_log = data.get("forget_log", [])
                self.save()
                return True
        return False
