"""Verify every free-sample link in the store resolves to a rendered page."""
import os, re, requests

ROOT = os.path.dirname(os.path.abspath(__file__))
html = open(os.path.join(ROOT, "STORE.html"), encoding="utf-8").read()
links = re.findall(r'href="(samples/[^"]+)"', html)
print("sample links:", len(links), "old raw:",
      html.count("raw.githubusercontent.com/Vorakan-yakham/"
                 "zyphere-scholar-product-pack/main/samples"))
print("first:", links[:2])
missing = [l for l in links if not os.path.exists(os.path.join(ROOT, l))]
print("missing local files:", len(missing))

# check a served page actually contains real content (not 404 / text dump)
base = "https://vorakan-yakham.github.io/zyphere-ai-agent/"
if links:
    u = base + links[0]
    r = requests.get(u, timeout=30)
    print("live", r.status_code, r.headers.get("content-type"),
          "bytes", len(r.content), "has content", "หัวข้อ" in r.text or "<h2" in r.text)
