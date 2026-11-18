"""Write local mail credentials from ENVIRONMENT VARIABLES only.

SECURITY FIX (Phase 1 audit): this file previously contained a plaintext
password. Never commit credentials. Set MAIL_USER / MAIL_APP_PASSWORD in the
Render Environment or a local gitignored file, then run this script.
"""
import json, os

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "credentials.json")
os.makedirs(os.path.dirname(path), exist_ok=True)
d = {}
try:
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
except Exception:
    pass
user = os.environ.get("MAIL_USER", "").strip()
pw = os.environ.get("MAIL_APP_PASSWORD", "").strip()
if user:
    d["email"] = user
if pw:
    d["password"] = pw
with open(path, "w", encoding="utf-8") as f:
    json.dump(d, f, ensure_ascii=False, indent=2)
print("saved from env vars to data/credentials.json (gitignored)")
