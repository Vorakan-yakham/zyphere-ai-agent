"""Zyphere Ebook Studio - build a REAL, submission-ready ebook:
cover image (Pillow), formatted HTML content (beautiful typography),
and metadata for Amazon KDP / MEB / Gumroad / PromptPay.

Market-first: only build for demand-validated topics. No fake sales claims.
Owner uploads to KDP/MEB (needs their account/OTP). System prepares everything.
HONEST: content is AI-authored from public knowledge; needs human review.
"""
import os, json, time, re, threading

KDP = {
    "categories": ["Self-Help", "Business & Economics", "Computers & Technology", "Health"],
    "language": "th", "price_range": [99, 199, 299],
    "requirements": ["ปก 1600x2560 px (JPEG)", "เนื้อหา HTML/EPUB", "คำอธิบาย <4000 ตัว", "keyword 7 ช่อง"],
}
MEB = {"name": "MEB / market", "formats": ["EPUB", "PDF"], "price_range": [99, 299]}


class EbookStudio:
    def __init__(self, out_dir):
        self.out_dir = out_dir
        self.lock = threading.RLock()
        self.books = []
        self._load()

    def _load(self):
        try:
            self.books = json.load(open(os.path.join(self.out_dir, "books.json"), encoding="utf-8")).get("books", [])
        except Exception:
            pass

    def save(self):
        with self.lock:
            try:
                os.makedirs(self.out_dir, exist_ok=True)
                json.dump({"books": self.books[-200:]}, open(os.path.join(self.out_dir, "books.json"), "w",
                          encoding="utf-8"), ensure_ascii=False, indent=2)
            except Exception:
                pass

    def cover(self, title, author="Zyphere", path=None, palette=None):
        """Draw a clean professional cover PNG via Pillow (gradient + typography)."""
        try:
            from PIL import Image, ImageDraw, ImageFont
        except Exception:
            return {"ok": False, "error": "Pillow unavailable"}
        W, H = 1600, 2560  # KDP recommended ratio
        im = Image.new("RGB", (W, H), (18, 22, 34))
        d = ImageDraw.Draw(im)
        # elegant diagonal gradient bands
        (r0, g0, b0) = (palette or ((37, 99, 235), (124, 58, 237), (236, 72, 153)))[0]
        for y in range(H):
            t = y / H
            r = int(b0 + (r0 - b0) * t)
            g = int(g0 + (20 - g0) * t)
            b = int(b0 * (1 - t) + 40 * t)
            d.line([(0, y), (W, y)], fill=(max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))))
        d.rounded_rectangle([90, 90, W - 90, H - 90], radius=40, outline=(255, 255, 255), width=4)
        def font(sz, bold=False):
            for f in (("C:/Windows/Fonts/NotoSansThai-Bold.ttf" if bold else "C:/Windows/Fonts/NotoSansThai-Regular.ttf"),
                      "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"):
                try:
                    return ImageFont.truetype(f, sz)
                except Exception:
                    continue
            return ImageFont.load_default()
        # title (wrap)
        words = str(title).split()
        lines, cur = [], ""
        for w in words:
            if len(cur + " " + w) > 22 and cur:
                lines.append(cur); cur = w
            else:
                cur = (cur + " " + w).strip()
        if cur:
            lines.append(cur)
        f_title = font(96, True)
        y = 700
        for ln in lines[:6]:
            d.text((140, y), ln, font=f_title, fill=(255, 255, 255))
            y += 130
        d.line([(140, y + 40), (W - 140, y + 40)], fill=(255, 255, 255), width=3)
        d.text((140, H - 400), str(author), font=font(64), fill=(240, 240, 245))
        d.text((140, H - 300), "zyphere.ai · ผลิตโดย AI", font=font(42), fill=(210, 215, 225))
        p = path or os.path.join(self.out_dir, "cover_" + str(int(time.time())) + ".png")
        im.save(p, "PNG")
        return {"ok": True, "path": p, "size": os.path.getsize(p), "w": W, "h": H}

    def content_html(self, title, chapters=None, author="Zyphere"):
        """Beautifully formatted, readable HTML - not raw text."""
        ch = chapters or []
        css = """<style>
 body{font-family:'Noto Sans Thai',system-ui,sans-serif;max-width:720px;margin:0 auto;
 padding:40px 24px;color:#1f2430;line-height:1.9;font-size:17px}
 h1{font-size:34px;line-height:1.3;border-bottom:3px solid #2563eb;padding-bottom:16px}
 h2{font-size:24px;margin-top:48px;color:#1e40af}
 .lead{font-size:19px;color:#475569}
 .box{background:#f8fafc;border:1px solid #e2e8f0;border-radius:14px;padding:18px 22px;margin:22px 0}
 .foot{border-top:1px solid #e2e8f0;margin-top:60px;padding-top:20px;color:#64748b;font-size:14px}
 </style>"""
        body = [f"<h1>{title}</h1>", f'<p class="lead">คู่มือที่อ่านง่าย นำไปใช้ได้จริง — ผลิตโดย {author}</p>',
                '<div class="box">อ่านเพื่อเข้าใจหลักการ แล้วลองทำจริงในบริบทของคุณ</div>']
        for i, c in enumerate(ch, 1):
            ct = c.get("title", f"บทที่ {i}") if isinstance(c, dict) else str(c)
            tx = c.get("body", "") if isinstance(c, dict) else ""
            body.append(f"<h2>{i}. {ct}</h2>")
            for p in str(tx).split("\n"):
                if p.strip():
                    body.append(f"<p>{p.strip()}</p>")
        body.append('<div class="foot">ลิขสิทธิ์ Zyphere · งดนำไปใช้ผิดกฎหมาย/เว็บพนัน · สอบถาม: PromptPay 0941939686</div>')
        return {"ok": True, "html": "<!doctype html><html><head><meta charset='utf-8'>" + css + "</head><body>" +
                "\n".join(body) + "</body></html>"}

    def create(self, title="", chapters=None, price=199, category="Self-Help", demand_score=0):
        t = str(title or "").strip()
        if not t:
            return {"ok": False, "error": "missing title"}
        cov = self.cover(t)
        html = self.content_html(t, chapters)
        base = "ebook_" + str(int(time.time()))
        hp = os.path.join(self.out_dir, base + ".html")
        open(hp, "w", encoding="utf-8").write(html["html"])
        rec = {"ok": True, "id": "eb_" + str(int(time.time() * 1000)), "title": t,
               "price": int(price or 199), "category": category,
               "cover": cov.get("path"), "html": hp, "demand_score": demand_score,
               "kdp": {"title": t[:200], "keywords": ["zyphere", "AI", category.lower()][:7],
                       "category": category, "price": int(price or 199), "cover": cov.get("path")},
               "meb": {"title": t[:200], "format": "HTML/PDF", "price": int(price or 199)},
               "gumroad": {"name": t[:160], "price": int(price or 199)},
               "promptpay": "0941939686", "t": int(time.time()),
               "honest": "ไฟล์พร้อม upload — เจ้าของต้องกดส่งบน KDP/MEB (บัญชี/OTP)"}
        with self.lock:
            self.books.append(rec)
        self.save()
        return rec

    def catalog(self):
        with self.lock:
            return list(reversed(self.books[-50:]))
