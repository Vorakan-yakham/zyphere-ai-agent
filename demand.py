"""Zyphere Demand Engine - MARKET FIRST, content second.

Owner's correction: an ebook succeeds because of MARKET DEMAND, not because
the content exists. So: gather real demand signals from FREE public sources,
score topics, and only produce ebooks for validated demand.

Free signals (no key, no ToS bypass):
- RSS feeds (HubSpot/Moz/Google) keyword frequency = what the market talks about
- OpenAlex/Crossref publication counts = active research interest
- Gumroad public discover page = what digital products are actually listed
HONEST: signals are proxies, not sales data. Owner-reported revenue is the
only real conversion proof. No fabricated "bestseller" claims.
"""
import os, json, time, re, threading
import requests

CANDIDATES = {
    "AI สำหรับงานสำนักงาน": ["ai", "productivity", "automation", "workflow"],
    "Prompt Engineering สำหรับมือใหม่": ["prompt", "llm", "chatgpt", "claude"],
    "คู่มือภาษาอังกฤษเพื่อทำงาน": ["english", "business english", "communication"],
    "กฎหมายรัฐธรรมนูญเบื้องต้น": ["law", "rights", "constitution"],
    "การเงินส่วนบุคคลสำหรับคนไทย": ["personal finance", "budget", "saving", "invest"],
    "สุขภาพจิตและความเครียด": ["mental health", "stress", "mindfulness", "burnout"],
    "คู่มือExcel/ข้อมูลสำหรับออฟฟิศ": ["excel", "spreadsheet", "data", "analysis"],
    "วิดีโอสั้น/TikTok สำหรับขายของ": ["tiktok", "short video", "reels", "content"],
    "Freelance หางานออนไลน์": ["freelance", "fiverr", "upwork", "side hustle"],
    "คู่มือสมัครงาน/เรซูเม่": ["resume", "cv", "interview", "job search"],
    "การยื่นภาษี/บัญชีเบื้องต้น": ["tax", "accounting", "bookkeeping"],
    "คู่มือใช้ AI วาดภาพ/แต่งเพลง": ["generative", "midjourney", "music ai", "image"],
}


class Demand:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.reports = []
        self._load()

    def _load(self):
        try:
            self.reports = json.load(open(self.path, encoding="utf-8")).get("reports", [])
        except Exception:
            pass

    def save(self):
        with self.lock:
            try:
                os.makedirs(os.path.dirname(self.path), exist_ok=True)
                json.dump({"reports": self.reports[-200:]}, open(self.path, "w", encoding="utf-8"),
                          ensure_ascii=False, indent=2)
            except Exception:
                pass

    def _rss_signals(self):
        """Count how often candidate keywords appear in free marketing feeds."""
        feeds = ["https://blog.hubspot.com/marketing/rss.xml",
                 "https://moz.com/blog/rss.xml",
                 "https://www.semrush.com/blog/feed/"]
        blob = ""
        for u in feeds:
            try:
                r = requests.get(u, timeout=12, headers={"User-Agent": "Zyphere/1.0"})
                if r.ok:
                    blob += " " + re.sub(r"<[^>]+>", " ", r.text).lower()
            except Exception:
                continue
        return blob

    def _openalex_signals(self):
        """Publication volume as a proxy for active interest."""
        counts = {}
        for name, kws in list(CANDIDATES.items())[:6]:
            q = kws[0]
            try:
                r = requests.get("https://api.openalex.org/works",
                    params={"search": q, "per-page": 1}, timeout=12)
                if r.ok:
                    counts[name] = int(r.json().get("meta", {}).get("count", 0))
            except Exception:
                counts[name] = 0
        return counts

    def scan(self):
        blob = self._rss_signals()
        oa = self._openalex_signals()
        scored = []
        for name, kws in CANDIDATES.items():
            hits = sum(blob.count(k) for k in kws)
            oa_count = oa.get(name, 0)
            score = hits * 3 + min(oa_count // 500, 20)
            scored.append({"topic": name, "rss_hits": hits, "openalex_works": oa_count,
                           "demand_score": score,
                           "verdict": "สูง" if score >= 12 else ("กลาง" if score >= 5 else "ต่ำ")})
        scored.sort(key=lambda x: -x["demand_score"])
        rep = {"ok": True, "ts": int(time.time()), "scored": scored,
               "top": scored[:5],
               "honest": "สัญญาณจาก RSS/งานวิจัย — ไม่ใช่ยอดขายจริง วัดconversion จากยอดที่เจ้าของแจ้ง"}
        with self.lock:
            self.reports.append(rep)
        self.save()
        return rep

    def ebook_spec(self, topic=""):
        """Only build an ebook for a topic that passed demand check."""
        t = str(topic or "").strip()
        rep = self.reports[-1] if self.reports else self.scan()
        row = next((r for r in rep["scored"] if r["topic"] == t), None)
        if not row or row["demand_score"] < 5:
            return {"ok": False, "error": "หัวข้อนี้ผ่านการตรวจตลาดไม่ผ่าน — อย่าเขียน ebook (ประหยัดเวลา)",
                    "topic": t}
        return {"ok": True, "topic": t, "demand_score": row["demand_score"],
                "title": t + " — คู่มือใช้งานจริงสำหรับคนไทย",
                "angle": "เขียนเพื่อแก้ปัญหาที่คนกำลังค้นหา ไม่ใช่เขียนเพื่อสะสมเนื้อหา",
                "price": 199, "cta": "PromptPay 0941939686",
                "note": "ผลิตเฉพาะหัวข้อที่มีสัญญาณความต้องการจริง"}

    def latest(self, n=5):
        with self.lock:
            return list(reversed(self.reports[-n:]))
