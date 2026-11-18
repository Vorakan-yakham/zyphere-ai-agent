"""Zyphere AutoPost - publish products/content to platforms AUTOMATICALLY using
the owner's own API tokens (given once, like Groq/Upstash keys). Zyphere posts
as the owner's account, legally, via official APIs. No OTP on every post.

Supported (official public APIs, owner supplies token):
- Gumroad: create a product (token)
- Dev.to / Medium: publish an article (token)
- Telegram: post to channel (bot token)
- Facebook Page: post via Graph API (page token)
- GitHub: create repo/gist (token) for code products
- Generic webhook: any endpoint the owner configures

HONEST: owner must obtain tokens ONCE from each platform (their account).
System never asks for password/OTP, never bypasses CAPTCHA, never creates
accounts. Posting happens only where the owner granted a token.
No gambling/illegal content.
"""
import os, json, time, threading

TOKENS = {
    "gumroad": os.environ.get("GUMROAD_TOKEN", ""),
    "devto": os.environ.get("DEVTO_TOKEN", ""),
    "medium": os.environ.get("MEDIUM_TOKEN", ""),
    "telegram": os.environ.get("TELEGRAM_TOKEN", ""),
    "telegram_chat": os.environ.get("TELEGRAM_CHAT_ID", ""),
    "facebook": os.environ.get("FB_PAGE_TOKEN", ""),
    "facebook_page": os.environ.get("FB_PAGE_ID", ""),
    "github": os.environ.get("GITHUB_TOKEN", ""),
    "webhook": os.environ.get("ZY_WEBHOOK_URL", ""),
}


class AutoPost:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.log = []
        self._load()

    def _load(self):
        try:
            self.log = json.load(open(self.path, encoding="utf-8")).get("log", [])
        except Exception:
            pass

    def save(self):
        with self.lock:
            try:
                os.makedirs(os.path.dirname(self.path), exist_ok=True)
                json.dump({"log": self.log[-1000:]}, open(self.path, "w", encoding="utf-8"),
                          ensure_ascii=False, indent=2)
            except Exception:
                pass

    def configured(self):
        return {"ok": True,
                "platforms": {k: bool(v) for k, v in TOKENS.items()},
                "ready": [k for k, v in TOKENS.items() if v],
                "how": "เจ้าของเอา token มาใส่ครั้งเดียว (Render Environment) → Zyphere โพสต์เองต่ออัตโนมัติ"}

    def publish(self, platform="", title="", body="", url="", price=0):
        import requests
        platform = str(platform or "").lower()
        tok = TOKENS.get(platform)
        if not tok:
            rec = {"ok": False, "platform": platform, "error": "no token — owner must add token once",
                   "need": "Render Environment: " + platform.upper() + "_TOKEN", "t": int(time.time())}
            with self.lock:
                self.log.append(rec)
            self.save()
            return rec
        result = {"ok": False, "platform": platform}
        try:
            if platform == "gumroad":
                r = requests.post("https://api.gumroad.com/v2/products",
                    data={"access_token": tok, "name": title[:160], "description": body[:2000],
                          "price": int(price or 0) * 100, "published": "true"}, timeout=30)
                result = {"ok": r.ok, "platform": platform,
                          "response": str(r.text)[:300]}
            elif platform == "devto":
                r = requests.post("https://dev.to/api/articles",
                    headers={"api-key": tok},
                    json={"article": {"title": title[:120], "body_markdown": body[:5000],
                                      "published": True, "tags": ["ai", "zyphere"]}}, timeout=30)
                result = {"ok": r.ok, "platform": platform, "response": str(r.text)[:300]}
            elif platform == "telegram":
                chat = TOKENS.get("telegram_chat")
                r = requests.post("https://api.telegram.org/bot" + tok + "/sendMessage",
                    json={"chat_id": chat, "text": str(title) + "\n" + str(body)[:3000]}, timeout=30)
                result = {"ok": r.ok, "platform": platform, "response": str(r.text)[:200]}
            elif platform == "facebook":
                page = TOKENS.get("facebook_page")
                r = requests.post("https://graph.facebook.com/" + str(page) + "/feed",
                    data={"message": str(title) + "\n" + str(body)[:2000], "access_token": tok}, timeout=30)
                result = {"ok": r.ok, "platform": platform, "response": str(r.text)[:300]}
            elif platform == "github":
                import re as _re
                slug = _re.sub(r"[^a-z0-9\-]", "-", str(title).lower())[:60] or "zyphere-product"
                r = requests.post("https://api.github.com/user/repos",
                    headers={"Authorization": "Bearer " + tok, "Accept": "application/vnd.github+json"},
                    json={"name": slug, "description": str(body)[:200], "private": False}, timeout=30)
                result = {"ok": r.ok, "platform": platform, "response": str(r.text)[:300]}
            elif platform == "webhook":
                r = requests.post(tok, json={"title": title, "body": body, "url": url, "price": price}, timeout=30)
                result = {"ok": r.ok, "platform": platform, "response": str(r.text)[:200]}
        except Exception as e:
            result = {"ok": False, "platform": platform, "error": str(e)[:200]}
        result["t"] = int(time.time())
        with self.lock:
            self.log.append(result)
        self.save()
        return result

    def history(self, n=20):
        with self.lock:
            return list(reversed(self.log[-n:]))
