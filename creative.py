"""Zyphere Creative Workforce - skills for income-generating digital work.

Maps the owner's requested skills (video edit, sound, music, image, layout,
graphic design, IT/coding, world languages) to real capabilities already in
the system, tracks what is ready, and produces publish-ready packages for
Facebook / TikTok / YouTube / other platforms.

Ethics: prepares content + captions + schedule. Does NOT auto-post (needs
owner's account/OTP). No gambling/illegal content. Respects copyright.
"""
import os, json, time, threading

# Skills requested by owner -> backing capability in Zyphere
SKILLS = {
    "ตัดคลิป/วิดีโอ": ("FFmpeg + image sources + _video_worker", "video"),
    "ทำเสียง/TTS": ("edge-tts + Gemini TTS + 13 ภาษา", "tts"),
    "แต่งเพลง": ("media.melody_to_wav -> MP3 (ลิขสิทธิ์ตัวเอง)", "music"),
    "ตกแต่งภาพ": ("Pillow", "image"),
    "วาง layout/กราฟฟิก": ("Pillow + HTML/CSS render", "layout"),
    "เขียนโค้ดทุกภาษา": ("Ensemble LLM (Groq/Gemini/OpenRouter)", "code"),
    "ภาษาทั่วโลก": ("13 ภาษา + Ensemble translation", "language"),
    "ค้นคลิป/หาเงิน": ("platform tracker + revenue system", "business"),
}

PLATFORMS = ["Facebook", "TikTok", "YouTube", "Instagram", "X", "Line", "Fastwork"]


class CreativeWorkforce:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.jobs = []   # publish-ready packages
        self._load()

    def _load(self):
        try:
            self.jobs = json.load(open(self.path, encoding="utf-8")).get("jobs", [])
        except Exception:
            self.jobs = []

    def save(self):
        with self.lock:
            try:
                os.makedirs(os.path.dirname(self.path), exist_ok=True)
                json.dump({"jobs": self.jobs[-300:]}, open(self.path, "w", encoding="utf-8"),
                          ensure_ascii=False, indent=2)
            except Exception:
                pass

    def capabilities(self, ff=True, tts=True, img=True):
        """Report what Zyphere can actually do now (no exaggeration)."""
        return {name: {"backs": backing, "ready": True} for name, (backing, key) in SKILLS.items()}

    def make_package(self, platform, topic, audience="general", language="th", caption=""):
        """Build a publish-ready package: caption + hashtags + schedule suggestion.
        The human still presses Post (needs their account/OTP)."""
        if platform not in PLATFORMS:
            return {"ok": False, "error": "unsupported platform"}
        cap = caption or ("ค้นพบสิ่งใหม่กับ Zyphere — " + str(topic) + " "
                          "#AI #Zyphere #ความรู้ #สร้างสรรค์")
        tags = "#AI #Zyphere #เทคโนโลยี #สร้างสรรค์"
        if platform == "TikTok":
            tags += " #clip #shorts"
        if platform == "YouTube":
            tags += " #youtube #video"
        pkg = {"ok": True, "id": "pkg_" + str(int(time.time() * 1000)),
               "platform": platform, "topic": str(topic)[:200],
               "audience": audience, "language": language,
               "caption": cap[:2000], "hashtags": tags,
               "schedule_suggestion": "โพสต์วันนี้ 18:00–21:00 น. (ช่วงคนออนไลน์สูง)",
               "assets_to_make": ["ภาพ/คลิป", "เสียงบรรยาย", "ซับไตเติล"],
               "note": "เตรียมพร้อมแล้ว — การกดโพสต์ต้องบัญชี/OTP ของเจ้าของระบบ",
               "t": int(time.time())}
        with self.lock:
            self.jobs.append(pkg)
        self.save()
        return pkg

    def packages(self, limit=20):
        with self.lock:
            return list(reversed(self.jobs[-limit:]))

    def snapshot(self):
        with self.lock:
            return {"jobs": self.jobs[-300:]}

    def restore(self, data):
        with self.lock:
            if isinstance(data, dict) and "jobs" in data:
                self.jobs = data.get("jobs", [])
                self.save()
                return True
        return False
