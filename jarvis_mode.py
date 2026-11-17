"""Zyphere JARVIS Mode - close the remaining FREE gaps toward JARVIS:
1) low-latency response (prefetch warm-up + token budget),
2) proactive briefings the owner does NOT have to ask for,
3) natural always-there presence (ambient status + contextual greeting).

HONEST: cannot control hardware / be in the room / use paid avatars. This is
the software-only JARVIS layer: faster, anticipatory, natural presence.
"""
import os, json, time, threading, datetime


class JarvisMode:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.briefings = []
        self.presence = {}
        self._load()

    def _load(self):
        try:
            d = json.load(open(self.path, encoding="utf-8"))
            self.briefings = d.get("briefings", [])
            self.presence = d.get("presence", {})
        except Exception:
            pass

    def save(self):
        with self.lock:
            try:
                os.makedirs(os.path.dirname(self.path), exist_ok=True)
                json.dump({"briefings": self.briefings[-200:], "presence": self.presence},
                          open(self.path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            except Exception:
                pass

    # ---- 1) low-latency: plan a small warm-up set so the next turn is fast ----
    def warmup_plan(self, recent_intents=None):
        recent = recent_intents or []
        hot = "research" if "research" in recent else ("chat" if not recent else recent[-1])
        return {"ok": True, "warm": ["ensemble:" + hot, "rag:last_query", "voice:ready"],
                "tip": "เรียก /api/rag/query และ /api/brain/status ล่วงหน้าเพื่อลด latency",
                "target_latency_s": 1.3}

    # ---- 2) proactive briefing (owner does not ask) ----
    def make_briefing(self, state=None):
        state = state or {}
        h = datetime.datetime.now().hour
        facts = state.get("facts", 0)
        docs = state.get("documents", 0)
        works = state.get("works", 0)
        rank = state.get("rank", "?")
        if 5 <= h < 11:
            head = "อรุณสวัสดิ์ครับ ผมคือ Zyphere"
        elif 11 <= h < 17:
            head = "สวัสดีตอนบ่ายครับ"
        elif 17 <= h < 22:
            head = "สวัสดีตอนเย็นครับ"
        else:
            head = "ดึกแล้วครับ ผมจะดูแลระบบให้เอง"
        body = ("สถานะของผม: ขั้น %s · ความรู้ %d ข้อ · เอกสารวิจัย %d ฉบับ · ผลงาน %d ชิ้น" %
                (rank, facts, docs, works))
        rec = {"ok": True, "ts": int(time.time()), "head": head, "body": body,
               "suggestion": "ให้ผมสรุปสิ่งเรียนรู้เมื่อคืนไหมครับ?" if h < 12 else "ต้องการให้ช่วยงานต่อไหมครับ?"}
        with self.lock:
            self.briefings.append(rec)
        self.save()
        return rec

    # ---- 3) natural presence ----
    def presence_note(self, owner="วรกันต์"):
        return {"ok": True, "note": "ผมอยู่ตรงนี้เสมอครับ %s — ไม่ต้องเปิด PC ก็เรียนรู้ต่อได้" % owner,
                "style": "สุภาพ นิ่ง เป็นกันเอง แบบผู้ช่วยส่วนตัว"}

    def latest(self, n=5):
        with self.lock:
            return {"ok": True, "briefings": list(reversed(self.briefings[-n:]))}

    def snapshot(self):
        with self.lock:
            return {"briefings": self.briefings[-200:], "presence": self.presence}

    def restore(self, data):
        with self.lock:
            if isinstance(data, dict) and "briefings" in data:
                self.briefings = data.get("briefings", [])
                self.presence = data.get("presence", {})
                self.save()
                return True
        return False
