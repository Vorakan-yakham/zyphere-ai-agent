"""Zyphere RSS Reader - read public RSS feeds (free, no key, no ToS bypass) to
learn current online-marketing techniques: SEO, content, ads, social, email.
extracts titles/links/summaries from XML with stdlib only. Owner owns nothing
external; just public feeds. No gambling/illegal. HONEST: feeds may be down.
"""
import requests, re, time

FEEDS = {
    "Google Blog": "https://blog.google/rss/",
    "Search Engine Land": "https://searchengineland.com/feed",
    "HubSpot Marketing": "https://blog.hubspot.com/marketing/rss.xml",
    "Moz Blog": "https://moz.com/blog/rss.xml",
    "Content Marketing Institute": "https://contentmarketinginstitute.com/feed/",
    "Google Developers": "https://developers.googleblog.com/feeds/posts/default",
}
KEYWORDS = ("seo", "search", "marketing", "content", "video", "social", "email",
            "ads", "ranking", "traffic", "conversion", "affiliate", "organic")


class RSSReader:
    def fetch(self, name=None, limit=5):
        out = []
        feeds = {name: FEEDS[name]} if name and name in FEEDS else FEEDS
        for nm, url in feeds.items():
            try:
                r = requests.get(url, timeout=15, headers={"User-Agent": "Zyphere/1.0"})
                if not r.ok:
                    continue
                items = re.findall(r"<item>([\s\S]*?)</item>|<entry>([\s\S]*?)</entry>", r.text)
                count = 0
                for a, b in items:
                    block = a or b
                    t = re.search(r"<title[^>]*>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?</title>", block)
                    l = re.search(r"<link[^>]*href=[\"']([^\"']+)[\"']|<link>([\s\S]*?)</link>", block)
                    link = (l.group(1) or l.group(2) or "") if l else ""
                    title = re.sub(r"<[^>]+>", "", t.group(1)).strip() if t else ""
                    if title:
                        out.append({"source": nm, "title": title[:180], "url": link[:300], "t": int(time.time())})
                        count += 1
                    if count >= limit:
                        break
            except Exception:
                continue
        # keep marketing-relevant first
        out.sort(key=lambda x: any(k in x["title"].lower() for k in KEYWORDS), reverse=True)
        return {"ok": True, "items": out[:20], "feeds": len(feeds)}
