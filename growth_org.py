"""Zyphere Growth & Digital Marketing org for an IT product.

Maps the 4 sub-teams / 8 roles into the EXISTING 12 divisions (no duplicate
divisions). Provides a SEARCH interface so the owner can see results inside the
system, not just in a document.

HONEST: 'current' means a module already exists in this repo; 'gap' means it
does not. Outsource/in-house advice follows the owner's brief.
"""
import os, json, time, threading

ROOT = os.path.dirname(os.path.abspath(__file__))

TEAMS = [
    {
        "team": "1. Growth & Data Analytics", "th": "ฝ่ายวางกลยุทธ์และวิเคราะห์ข้อมูล",
        "division": "12 / 03", "role": "สมองของทีม — ดูตัวเลข หาจุดโต อุดรอยรั่ว",
        "members": [
            {"role": "Growth Manager / Growth Hacker",
             "duty": "วางกลยุทธ์ แคมเปญแนะนำเพื่อน A/B Test",
             "current": "demand.py, market.py, marketing_promoter.py",
             "gap": "ยังไม่มี A/B testing framework จริง", "mode": "in-house",
             "priority": 1},
            {"role": "Data Analyst",
             "duty": "ติดตั้ง tracking วิเคราะห์พฤติกรรม Churn และ ROI",
             "current": "store.py stats, /api/store/stats, LEARNING.html",
             "gap": "ยังไม่มี event tracking / funnel จริง", "mode": "in-house",
             "priority": 1},
        ],
    },
    {
        "team": "2. Performance Marketing / User Acquisition", "th": "ฝ่ายหาลูกค้าใหม่ผ่านช่องทางออนไลน์",
        "division": "07 / 12", "role": "ดึงคนเข้าสมัครให้เร็วที่สุดด้วยต้นทุนต่ำ",
        "members": [
            {"role": "Paid Ads Specialist (Media Buyer)",
             "duty": "ซื้อโฆษณา Facebook/TikTok/Google/YouTube",
             "current": "autopost.py (โพสต์ด้วย token เจ้าของ)",
             "gap": "ยังไม่มี API โฆษณา — ต้องใช้บัญชีเจ้าของ/งบ", "mode": "in-house",
             "priority": 1},
            {"role": "SEO & ASO Specialist",
             "duty": "ทำอันดับ Google และ App Store/Google Play",
             "current": "GitHub Pages + meta/短 link tinyurl",
             "gap": "ยังไม่มี ASO (ไม่มีแอป) · SEO ยังไม่มี tools", "mode": "outsource",
             "priority": 2},
        ],
    },
    {
        "team": "3. Content & Creative", "th": "ฝ่ายสร้างคอนเทนต์และสื่อสารแบรนด์",
        "division": "07 / 04", "role": "แปลเรื่อง IT ให้เข้าใจง่าย น่าเชื่อถือ ดึงดูด",
        "members": [
            {"role": "Content Creator / Copywriter",
             "duty": "บทความ รีวิว คู่มือ สคริปต์วิดีโอ แคปชัน",
             "current": "marketing_promoter.py, language.py, council_review.py",
             "gap": "ยังไม่มี editor calendar", "mode": "in-house", "priority": 1},
            {"role": "Graphic Designer & Video Editor",
             "duty": "แบนเนอร์ วิดีโอสั้น Reels/TikTok สื่อสอนใช้งาน",
             "current": "image_studio.py, creative_director.py, media.py (FFmpeg)",
             "gap": "video เป็น slideshow ยังไม่มี generative", "mode": "in-house",
             "priority": 1},
        ],
    },
    {
        "team": "4. CRM & Community", "th": "ฝ่ายดูแลฐานลูกค้าและสร้างความสัมพันธ์",
        "division": "11 / 12", "role": "รักษาคนเก่าให้อยู่ต่อและบอกต่อ",
        "members": [
            {"role": "CRM Specialist",
             "duty": "อัตโนมัติ Email/LINE OA/Push กระตุ้น inactive user",
             "current": "gmail_oauth.py, users.py, preferences.py",
             "gap": "ยังไม่มี LINE OA / Push / ticket workflow", "mode": "in-house",
             "priority": 2},
            {"role": "Community & Partnership Manager",
             "duty": "ดูแลกลุ่มผู้ใช้ ติดต่อ Influencer/KOL/พาร์ทเนอร์",
             "current": "autopost.py, support.json",
             "gap": "ยังไม่มี community moderation", "mode": "outsource",
             "priority": 2},
        ],
    },
]


class GrowthOrg:
    def all(self):
        return {"ok": True, "teams": len(TEAMS),
                "roles": sum(len(t["members"]) for t in TEAMS),
                "in_house": sum(1 for t in TEAMS for m in t["members"] if m["mode"] == "in-house"),
                "outsource": sum(1 for t in TEAMS for m in t["members"] if m["mode"] == "outsource"),
                "teams_detail": TEAMS, "t": int(time.time())}

    def search(self, q=""):
        """Search results for the owner's query, returned as structured hits."""
        term = str(q or "").strip().lower()
        broad = any(k in term for k in ("ฝ่ายโปรโมท", "โปรโมท", "growth",
                                        "การตลาด", "marketing", "ด้าน it"))
        hits = []
        for t in TEAMS:
            for m in t["members"]:
                blob = " ".join([t["team"], t["th"], t["division"], t["role"],
                                 m["role"], m["duty"], m["current"], m["gap"],
                                 m["mode"]]).lower()
                if not term or broad or any(w in blob for w in term.split()):
                    hits.append({"team": t["th"], "division": t["division"],
                                 "role": m["role"], "duty": m["duty"],
                                 "current": m["current"], "gap": m["gap"],
                                 "mode": m["mode"], "priority": m["priority"]})
        hits.sort(key=lambda x: (x["priority"], x["role"]))
        return {"ok": True, "query": q, "count": len(hits), "results": hits,
                "advice": ("เริ่มต้นด้วย Growth Manager + Content/Creative + Paid Ads "
                           "ในทีม (in-house) และจ้าง outsource SEO/Video/Influencer ก่อน")}


GO = GrowthOrg()
