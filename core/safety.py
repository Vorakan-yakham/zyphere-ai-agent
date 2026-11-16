"""Safety layer: permission tiers, kill switch, autonomous-call budget, secret redaction."""
import re
from enum import Enum
from typing import Tuple


class Verdict(str, Enum):
    ALLOW = "allow"        # autonomous, think/sandbox only
    APPROVAL = "approval"  # needs the user's explicit OK
    DENY = "deny"          # never


POLICY = {
    "think": Verdict.ALLOW,
    "note": Verdict.ALLOW,
    "skill_create": Verdict.ALLOW,   # runs only inside the restricted sandbox
    "skill_run": Verdict.ALLOW,
    "proposal": Verdict.APPROVAL,
    "device_command": Verdict.APPROVAL,
    "file_write": Verdict.APPROVAL,
    "network": Verdict.APPROVAL,
    "self_modify": Verdict.APPROVAL,
}


def authorize(action: str) -> Verdict:
    """Unknown actions are denied by default."""
    return POLICY.get(action, Verdict.DENY)


class BudgetExceeded(Exception):
    pass


SECRET_RE = re.compile(r"(sk-ant-[A-Za-z0-9_\-]{8,}|sk-[A-Za-z0-9]{20,}|gsk_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}"
                       r"|ghp_[A-Za-z0-9]{30,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)")


def redact(text: str) -> str:
    return SECRET_RE.sub("[REDACTED]", text or "")


class Guard:
    DEFAULT_CAP = 30

    def __init__(self, store):
        self.store = store

    def killed(self) -> bool:
        return bool(self.store.get_setting("kill_switch", False))

    def kill(self) -> None:
        self.store.set_setting("kill_switch", True)
        self.store.set_setting("autonomy_enabled", False)

    def resume(self) -> None:
        self.store.set_setting("kill_switch", False)

    def autonomy_enabled(self) -> bool:
        return bool(self.store.get_setting("autonomy_enabled", False)) and not self.killed()

    def cap(self) -> int:
        try:
            return max(0, int(self.store.get_setting("daily_cap", self.DEFAULT_CAP)))
        except (TypeError, ValueError):
            return self.DEFAULT_CAP

    def used(self, source: str = "auto") -> int:
        return self.store.usage_today(source)["calls"]

    def can_call(self, source: str = "auto") -> Tuple[bool, str]:
        if source == "auto":
            if self.killed():
                return False, "kill switch is active"
            if self.used("auto") >= self.cap():
                return False, "daily autonomous budget reached"
        return True, ""

    def record(self, source: str, usage=(0, 0)) -> None:
        try:
            i, o = int(usage[0]), int(usage[1])
        except (TypeError, ValueError, IndexError):
            i, o = 0, 0
        self.store.add_usage(source, 1, i, o)
