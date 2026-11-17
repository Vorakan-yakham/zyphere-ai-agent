"""Zyphere Fine-Grained Authorization - Zyphere's final gap.

The system has authentication (users.py, OAuth) and 3 roles, but no PER-ACTION
permission scopes. This adds a policy layer: who may do what, checked before
sensitive endpoints. Free, local, no external service.

Roles: guest < user < admin < owner
Default-deny for sensitive actions; explicit allow lists.
"""
from functools import wraps

LEVEL = {"guest": 0, "user": 1, "admin": 2, "owner": 3}

# action -> minimum role
POLICY = {
    "chat": "guest", "ask": "guest", "tts": "guest", "briefing": "guest",
    "learn_public": "guest", "knowledge_read": "guest", "plans": "guest",
    "memory": "user", "goals": "user", "notebook": "user", "research": "user",
    "vision": "user", "stt": "user", "video": "user", "work": "user",
    "feedback": "user", "preferences": "user", "family_read": "user",
    "backup": "admin", "restore": "admin", "admin": "admin", "support": "admin",
    "email_send": "admin", "user_delete": "user", "family_set": "admin",
    "billing_revenue": "admin", "storage_sync": "admin",
}


class Authz:
    def __init__(self, users=None):
        self.users = users

    def role_of(self, token=""):
        if not self.users or not token:
            return "guest"
        try:
            r = self.users.role(token)
            return r if r in LEVEL else "guest"
        except Exception:
            return "guest"

    def can(self, role, action):
        need = POLICY.get(action, "admin")  # default-deny
        return LEVEL.get(role, 0) >= LEVEL.get(need, 3)

    def check(self, token, action):
        role = self.role_of(token)
        allowed = self.can(role, action)
        return {"ok": True, "allowed": allowed, "role": role, "action": action,
                "need": POLICY.get(action, "admin")}

    def policy(self):
        return {"ok": True, "roles": LEVEL, "policy": POLICY,
                "default": "deny (unknown action requires admin)"}
