"""Zyphere Users - minimal auth & feedback store (offline, no external API).
Free tier: email + password (PBKDF2), sessions persisted to data/users.json.
"""
import json, os, hashlib, hmac, secrets, time, threading

def _hash(pw, salt=None):
    salt = salt or secrets.token_hex(16)
    d = hashlib.pbkdf2_hmac("sha256", str(pw).encode(), bytes.fromhex(salt), 120000)
    return salt + ":" + d.hex()

def _verify(pw, stored):
    try:
        salt, h = stored.split(":", 1)
        return hmac.compare_digest(_hash(pw, salt).split(":", 1)[1], h)
    except Exception:
        return False

class Users:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.users = {}
        self.feedback = []
        self.sessions = {}
        self.attempts = {}
        self._load()

    def _load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                d = json.load(f)
            self.users = d.get("users", {})
            self.feedback = d.get("feedback", [])
            self.sessions = d.get("sessions", {})
            if "vorayakham@gmail.com" in self.users:
                self.users["vorayakham@gmail.com"]["role"] = "admin"
        except Exception:
            pass

    def save(self):
        with self.lock:
            try:
                with open(self.path, "w", encoding="utf-8") as f:
                    json.dump({"users": self.users, "feedback": self.feedback[-2000:],
                               "sessions": self.sessions}, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

    def register(self, email, password, name="", ref=""):
        email = str(email or "").strip().lower()
        if not email or "@" not in email or len(password or "") < 6:
            return {"ok": False, "error": "อีเมลไม่ถูกต้อง หรือรหัสผ่านสั้นเกิน 6 ตัว"}
        with self.lock:
            if email in self.users:
                return {"ok": False, "error": "อีเมลนี้มีอยู่แล้ว"}
            import secrets as _s
            code = _s.token_urlsafe(6)
            while any(u.get("code") == code for u in self.users.values()):
                code = _s.token_urlsafe(6)
            self.users[email] = {"email": email, "name": str(name or "")[:80],
                                  "pw": _hash(password), "created": int(time.time()),
                                  "plan": "free", "role": "user", "code": code, "ref": str(ref or "")[:32],
                                  "invites": 0}
            # credit inviter
            if ref:
                for u in self.users.values():
                    if u.get("code") == ref:
                        u["invites"] = int(u.get("invites") or 0) + 1
            self.save()
            return {"ok": True, "email": email, "code": code}

    def login(self, email, password):
        email = str(email or "").strip().lower()
        now = time.time()
        with self.lock:
            at = self.attempts.get(email, [])
            at = [x for x in at if now - x < 300]
            if len(at) >= 10:
                return {"ok": False, "error": "ลองหลายครั้งเกินไป รอ 5 นาที"}
            at.append(now); self.attempts[email] = at
            u = self.users.get(email)
            if not u or not _verify(password, u.get("pw", "")):
                return {"ok": False, "error": "อีเมลหรือรหัสผ่านไม่ถูกต้อง"}
            tok = secrets.token_urlsafe(24)
            self.sessions[tok] = {"email": email, "t": int(now)}
            self.attempts.pop(email, None)
            self.save()
            return {"ok": True, "token": tok, "email": email, "name": u.get("name", "")}

    def oauth_login(self, email, name="", provider="google", picture=""):
        """Login/register a user authenticated by a trusted OAuth provider.
        No password is stored; the provider verified the email for us.
        """
        email = str(email or "").strip().lower()
        if not email or "@" not in email:
            return {"ok": False, "error": "invalid email"}
        with self.lock:
            u = self.users.get(email)
            if not u:
                import secrets as _s
                code = _s.token_urlsafe(6)
                while any(x.get("code") == code for x in self.users.values()):
                    code = _s.token_urlsafe(6)
                u = {"email": email, "name": str(name or "")[:80],
                     "pw": "", "created": int(time.time()), "plan": "free",
                     "role": "admin" if email == "vorayakham@gmail.com" else "user",
                     "code": code, "ref": "", "invites": 0,
                     "oauth": provider, "picture": str(picture or "")[:400]}
                self.users[email] = u
            else:
                if name and not u.get("name"):
                    u["name"] = str(name)[:80]
                u["oauth"] = provider
                if picture:
                    u["picture"] = str(picture)[:400]
            tok = secrets.token_urlsafe(24)
            self.sessions[tok] = {"email": email, "t": int(time.time())}
            self.save()
            return {"ok": True, "token": tok, "email": email,
                    "name": u.get("name", ""), "code": u.get("code", "")}

    def session(self, tok):
        with self.lock:
            s = self.sessions.get(str(tok or ""))
            if not s or time.time() - s["t"] > 30 * 86400:
                return None
            return s

    def logout(self, tok):
        with self.lock:
            self.sessions.pop(str(tok or ""), None)
            self.save()

    def add_feedback(self, email, kind, text):
        with self.lock:
            self.feedback.append({"email": email, "kind": str(kind)[:40],
                                  "text": str(text)[:500], "t": int(time.time())})
            self.save()
            return {"ok": True}

    def me(self, token):
        s = self.session(token)
        if not s:
            return None
        u = self.users.get(s["email"], {})
        return {"email": s["email"], "name": u.get("name", ""),
                "code": u.get("code", ""), "role": u.get("role", "user"),
                "invites": int(u.get("invites") or 0),
                "ref": u.get("ref", ""), "picture": u.get("picture", "")}

    def role(self, token):
        sess = self.session(token)
        if not sess:
            return "guest"
        return self.users.get(sess["email"], {}).get("role", "user")

    def stats(self):
        with self.lock:
            return {"users": len(self.users), "feedback": len(self.feedback),
                    "sessions": len(self.sessions)}
