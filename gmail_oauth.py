"""Zyphere Gmail via OAuth (no App Password needed).

Owner's Google account blocks App Passwords (Google disabled it for this
account). We already have Google OAuth Client ID/Secret in Render. This module
sends email via Gmail API using an OAuth access token obtained with those
credentials. Free, legal, uses owner's own granted permission.

HONEST: requires the owner to complete Google consent ONCE for gmail.send
scope (browser flow). System never stores the owner's Google password.
"""
import os, json, requests

CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "").strip()
CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "").strip()
REDIRECT = os.environ.get("GOOGLE_REDIRECT_URI", "https://zyphere-ai-agent.onrender.com/api/auth/google/callback").strip()
TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_SEND = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"


def auth_url(state="zyphere-mail"):
    """URL for owner to grant gmail.send permission once."""
    if not CLIENT_ID:
        return {"ok": False, "error": "GOOGLE_CLIENT_ID not configured"}
    from urllib.parse import urlencode
    params = {"client_id": CLIENT_ID, "redirect_uri": REDIRECT, "response_type": "code",
              "scope": "openid email profile https://www.googleapis.com/auth/gmail.send",
              "access_type": "offline", "prompt": "consent", "state": state}
    return {"ok": True, "url": "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params),
            "note": "เจ้าของกดอนุญาตครั้งเดียว — ไม่ใช้ App Password"}


def exchange(code):
    if not CLIENT_ID or not CLIENT_SECRET:
        return {"ok": False, "error": "OAuth not configured"}
    r = requests.post(TOKEN_URL, data={"code": code, "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET, "redirect_uri": REDIRECT,
        "grant_type": "authorization_code"}, timeout=30)
    if not r.ok:
        return {"ok": False, "error": str(r.text)[:200]}
    t = r.json()
    return {"ok": True, "access_token": t.get("access_token"),
            "refresh_token": t.get("refresh_token"), "scope": t.get("scope", "")}


def _refresh(rt):
    r = requests.post(TOKEN_URL, data={"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
        "refresh_token": rt, "grant_type": "refresh_token"}, timeout=30)
    return r.json().get("access_token") if r.ok else None


def send(to, subject, body, token=None, refresh=None):
    """Send via Gmail API. token = access token; refresh = refresh token."""
    if token is None and refresh:
        token = _refresh(refresh)
    if not token:
        return {"ok": False, "error": "no Gmail OAuth token — owner must grant gmail.send once"}
    import base64
    from email.mime.text import MIMEText
    msg = MIMEText(str(body or "")[:20000], "plain", "utf-8")
    msg["To"] = str(to or "")
    msg["Subject"] = str(subject or "Zyphere")[:200]
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    r = requests.post(GMAIL_SEND, headers={"Authorization": "Bearer " + token,
        "Content-Type": "application/json"}, json={"raw": raw}, timeout=30)
    if r.ok:
        return {"ok": True, "id": r.json().get("id"), "via": "gmail_api_oauth"}
    return {"ok": False, "error": str(r.text)[:250]}
