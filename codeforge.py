"""Zyphere Code-Product Forge - write REAL runnable code and package it into
a sellable zip (README + LICENSE + quote + quote sheet). Owner's simplest path:
"have it write code and sell it". Zyphere writes; owner lists/gets paid.

HONEST: generates ready-to-sell code products; does NOT auto-post to marketplaces
(owner account/OTP) and does NOT touch bank accounts. Ethical only, no gambling/
illegal. No fake claims about earnings.
"""
import os, time, threading, zipfile, json

TEMPLATES = {
    "โค้ด/สคริปต์": ("text_processor", '''"""Text utility: count words & save report."""
import re, json, sys
from collections import Counter

def analyze(text):
    words = re.findall(r"[\\u0E00-\\u0E7FA-Za-z0-9]{2,}", text or "")
    return {"total": len(words), "top": Counter(words).most_common(10)}

if __name__ == "__main__":
    text = sys.stdin.read() or "Zyphere code product demo"
    print(json.dumps(analyze(text), ensure_ascii=False, indent=2))
'''),
    "เว็บแอป": ("mini_dashboard", '''"""Tiny zero-dependency HTTP dashboard (stdlib only)."""
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        data = {"service": "Zyphere mini dashboard", "ok": True, "version": 1}
        b = json.dumps(data).encode()
        self.send_response(200); self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)
    def log_message(self, *a): pass

if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 8080), H).serve_forever()
'''),
    "เครื่องมือ/CLI": ("file_renamer", '''"""Safe batch file prefixer (dry-run by default)."""
import os, sys, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder"); ap.add_argument("--prefix", default="doc_")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    for f in sorted(os.listdir(a.folder)):
        new = a.prefix + f
        print(("RENAME" if a.apply else "DRY") , f, "->", new)
        if a.apply:
            os.rename(os.path.join(a.folder,f), os.path.join(a.folder,new))
if __name__ == "__main__": main()
'''),
}


class CodeForge:
    def __init__(self, out_dir):
        self.out_dir = out_dir
        self.lock = threading.RLock()
        self.products = []
        self._load()

    def _load(self):
        try:
            p = os.path.join(self.out_dir, "products.json")
            self.products = json.load(open(p, encoding="utf-8")).get("products", [])
        except Exception:
            pass

    def save(self):
        with self.lock:
            try:
                os.makedirs(self.out_dir, exist_ok=True)
                json.dump({"products": self.products[-500:]},
                          open(os.path.join(self.out_dir, "products.json"), "w", encoding="utf-8"),
                          ensure_ascii=False, indent=2)
            except Exception:
                pass

    def readme(self, name, desc, price):
        return ("# %s\n\nโดย Zyphere\n\n%s\n\n## ติดตั้ง/ใช้\n```bash\npython %s.py --help\n```\n\n"
                "## ราคา\n%d บาท — ชำระ PromptPay 0941939686 แล้วแจ้งสลิป\n\n"
                "## เงื่อนไข\nโค้ดส่งเป็นไฟล์ zip · ปรับแต่งเพิ่มได้ · งดนำไปใช้ผิดกฎหมาย/เว็บพนัน\n"
                % (name, desc, name, price))

    def forge(self, kind="โค้ด/สคริปต์", title=None, price=499):
        key = kind if kind in TEMPLATES else "โค้ด/สคริปต์"
        mod, code = TEMPLATES[key]
        name = title or mod
        os.makedirs(self.out_dir, exist_ok=True)
        fn = mod + "_" + str(int(time.time())) + ".zip"
        path = os.path.join(self.out_dir, fn)
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr(mod + ".py", code)
            z.writestr("README.md", self.readme(name, "โค้ดพร้อมใช้ ผลิตโดย Zyphere", price))
            z.writestr("LICENSE.txt", "ฟรีสำหรับผู้ซื้อ · ห้ามจำหน่ายซ้ำโดยไม่ได้รับอนุญาต · ห้ามใช้ผิดกฎหมาย")
            z.writestr("QUOTE.txt", "ใบเสนอราคา %s · %d บาท · PromptPay 0941939686" % (name, price))
        rec = {"ok": True, "id": "cf_" + str(int(time.time() * 1000)), "kind": kind,
               "title": name, "price": price, "file": fn, "url": "/media/" + fn,
               "t": int(time.time())}
        with self.lock:
            self.products.append(rec)
        self.save()
        return rec

    def list_products(self):
        with self.lock:
            return list(reversed(self.products[-50:]))

    def stats(self):
        with self.lock:
            return {"products": len(self.products), "potential": sum(p.get("price",0) for p in self.products)}

    def snapshot(self):
        with self.lock:
            return {"products": self.products[-500:]}

    def restore(self, data):
        with self.lock:
            if isinstance(data, dict) and "products" in data:
                self.products = data.get("products", [])
                self.save()
                return True
        return False
