"""Zyphere ยาม (Guard / Sentinel) - software-only watchman, JARVIS-style.

Patrols what it CAN see on free tier: system health, security blocks, audit
anomalies, privacy decay due, remote KV, pending works, learning state.
Also accepts OWNER-APPROVED sensor events (future camera/motion) as abstract
events only — never raw video, never covert surveillance.

Ethics (owner's rules): owner consent only, no illegal/gambling, no spying on
people, event-only not raw footage, blur/forget/decay applied. No hardware
claim. HONEST: this is a monitor + alerter, not a physical guard.
"""
import os, json, time, threading


class Guard:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.patrols = []
        self.sensor_events = []
        self.consents = {}   # device -> {granted, t, scope, expires}
        self._load()

    def _load(self):
        try:
            d = json.load(open(self.path, encoding="utf-8"))
            self.patrols = d.get("patrols", [])
            self.sensor_events = d.get("sensor_events", [])
            self.consents = d.get("consents", {})
        except Exception:
            pass

    def save(self):
        with self.lock:
            try:
                os.makedirs(os.path.dirname(self.path), exist_ok=True)
                json.dump({"patrols": self.patrols[-300:], "sensor_events": self.sensor_events[-500:],
                           "consents": self.consents},
                          open(self.path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            except Exception:
                pass

    # ---------- Consent flow: ask -> grant -> connect -> revoke ----------
    def propose_connect(self, device="กล้องตรวจจับ", scope="motion_only"):
        """Zyphere ASKS first. No auto-connect, no covert access."""
        return {"ok": True, "question": ("เจ้าของครับ ผมตรวจพบอุปกรณ์ '%s' — ต้องการให้ผมเชื่อมเพื่อตรวจจับเหตุการณ์ไหมครับ? "
                                        "จะเก็บเฉพาะเหตุการณ์ (ไม่เก็บภาพคน) และคุณเพิกถอนได้ทุกเมื่อ" % device),
                "device": str(device)[:80], "scope": str(scope)[:40],
                "options": ["อนุญาต", "ไม่", "ถามทีหลัง"],
                "auto_connected": False,
                "ethics": "ต้องได้รับอนุญาตก่อนเสมอ — ไม่แอบเชื่อม"}

    def grant(self, device="กล้องตรวจจับ", scope="motion_only", hours=24):
        """Owner explicitly allows. Time-bounded consent by default."""
        with self.lock:
            self.consents[str(device)[:80]] = {"granted": True, "t": int(time.time()),
                                               "scope": str(scope)[:40],
                                               "expires": int(time.time()) + int(hours) * 3600}
        self.save()
        return {"ok": True, "connected": True, "device": device,
                "scope": scope, "expires_in_hours": hours,
                "note": "เชื่อมแล้วเฉพาะเหตุการณ์ — ไม่เก็บภาพดิบ"}

    def revoke(self, device="กล้องตรวจจับ"):
        with self.lock:
            prev = self.consents.pop(str(device)[:80], None)
        self.save()
        return {"ok": True, "disconnected": True, "device": device,
                "was_granted": bool(prev)}

    def is_allowed(self, device="กล้องตรวจจับ"):
        c = self.consents.get(str(device)[:80])
        if not c or not c.get("granted"):
            return False
        if c.get("expires") and time.time() > c["expires"]:
            return False
        return True

    def consent_status(self):
        with self.lock:
            return {"ok": True, "devices": {k: {"granted": v.get("granted"),
                    "scope": v.get("scope"), "expires": v.get("expires")}
                    for k, v in self.consents.items()},
                    "principle": "ถามก่อน → อนุญาต → เชื่อม → เพิกถอนได้"}

    def patrol(self, state=None):
        """Inspect current state and return alerts + guard status."""
        s = state or {}
        alerts = []
        if not s.get("remote", True):
            alerts.append({"level": "warn", "msg": "Remote KV ปิด — ข้อมูลอาจหายตอน restart"})
        if int(s.get("safety_blocks", 0)) > 0:
            alerts.append({"level": "info", "msg": "ยามกันสิ่งผิดกฎหมาย/พนันไปแล้ว %d ครั้ง" % s["safety_blocks"]})
        if not s.get("integrity", True):
            alerts.append({"level": "high", "msg": "Audit hash chain ไม่สมบูรณ์ — ต้องตรวจสอบ"})
        if int(s.get("pending_decay", 0)) > 0:
            alerts.append({"level": "info", "msg": "มีข้อมูลส่วนตัวครบกำหนดจางหาย %d รายการ" % s["pending_decay"]})
        if int(s.get("failures", 0)) > 0:
            alerts.append({"level": "high", "msg": "พบความล้มเหลวของระบบ %d รายการ" % s["failures"]})
        if not alerts:
            alerts.append({"level": "ok", "msg": "ทุกอย่างปกติครับ เจ้าของวางใจได้"})
        rec = {"ok": True, "ts": int(time.time()), "status": "ยามเฝ้าอยู่", "alerts": alerts,
               "scanned": {k: s.get(k) for k in ("facts", "documents", "works", "remote", "providers")}}
        with self.lock:
            self.patrols.append(rec)
        self.save()
        return rec

    def sensor_event(self, kind="motion", detail="", approved=False):
        """Accept an OWNER-APPROVED abstract sensor event (no raw media)."""
        if not approved:
            return {"ok": False, "error": "ต้องได้รับอนุญาตจากเจ้าของก่อน — ยามไม่แอบดูครับ"}
        k = str(kind)[:40]
        allowed = ("motion", "door", "temperature", "sound", "light", "smoke")
        if k not in allowed:
            return {"ok": False, "error": "event ประเภทไม่รองรับ"}
        rec = {"ok": True, "kind": k, "detail": str(detail)[:200], "t": int(time.time()),
               "note": "event-only — ไม่เก็บภาพ/เสียงดิบ blur+forget+decay ตามนโยบาย"}
        with self.lock:
            self.sensor_events.append(rec)
        self.save()
        return rec

    def alert_owner(self, kind="suspicious", detail="", confidence=0.0, evidence=None):
        """Alert the OWNER only. Never auto-contact police/emergency services.

        Human makes the final call. False alarms are possible; the system must
        state uncertainty and hand the decision back to the owner.
        """
        k = str(kind)[:60]
        conf = max(0.0, min(1.0, float(confidence or 0)))
        level = "high" if conf >= 0.8 else ("medium" if conf >= 0.5 else "low")
        return {"ok": True, "to": "owner_only", "kind": k,
                "message": ("มีเหตุการณ์ที่ควรให้เจ้าของตรวจสอบครับ: " + str(detail)[:200]),
                "confidence": round(conf, 2), "level": level,
                "evidence": evidence or [],
                "recommendation": ("หากคุณยืนยันเองแล้วว่าน่าสงสัย โปรดโทรแจ้งเจ้าหน้าที่ด้วยตัวคุณครับ",
                                   "ระบบไม่โทรแจ้งตำรวจแทน — การแจ้งความเท็จอาจผิดกฎหมาย"),
                "auto_dispatch": False,
                "ethics": "แจ้งเจ้าของเท่านั้น · มนุษย์ตัดสินใจ · ไม่แอบเฝ้าผู้อื่น"}

    def status(self):
        with self.lock:
            return {"ok": True, "role": "ยาม (Sentinel)", "on_duty": True,
                    "patrols": len(self.patrols), "sensor_events": len(self.sensor_events),
                    "scope": "ระบบ/ความปลอดภัย/ข้อมูล/เหตุการณ์",
                    "physical": "ต้องกล้อง+อนุญาตจากเจ้าของ — ไม่แอบเฝ้าผู้ใด",
                    "ethics": "งดพนัน/ผิดกฎหมาย · event-only · blur/forget/decay"}

    def latest(self, n=5):
        with self.lock:
            return {"ok": True, "patrols": list(reversed(self.patrols[-n:]))}

    def snapshot(self):
        with self.lock:
            return {"patrols": self.patrols[-300:], "sensor_events": self.sensor_events[-500:]}

    def restore(self, data):
        with self.lock:
            if isinstance(data, dict) and "patrols" in data:
                self.patrols = data.get("patrols", [])
                self.sensor_events = data.get("sensor_events", [])
                self.save()
                return True
        return False
