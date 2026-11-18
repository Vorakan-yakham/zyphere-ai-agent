"""Zyphere Mailer - send email via Gmail SMTP using an App Password from a local file (never in GitHub)."""
import os, smtplib, ssl, re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

KEYFILE = os.environ.get("API_ZYPHERE_FILE", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "API-Zyphere.txt"))

def get_mail_creds():
    sender = os.environ.get("MAIL_USER", "")
    pw = os.environ.get("MAIL_APP_PASSWORD", "")
    try:
        for line in open(KEYFILE, encoding="utf-8"):
            s = line.strip()
            low = s.lower()
            if not sender and ("mail=" in low or "gmail=" in low):
                sender = s.split("=", 1)[1].strip()
            if not pw and any(x in low for x in ("app password", "app_password", "mailpass", "smtp=")):
                pw = s.split("=", 1)[1].strip() if "=" in s else ""
    except Exception:
        pass
    return sender, pw

def send_mail(to, subject, body, sender=None, pw=None):
    sender, pw = sender or get_mail_creds()[0], pw or get_mail_creds()[1]
    if not sender or not pw:
        return {"ok": False, "error": "MAIL_USER / MAIL_APP_PASSWORD not configured"}
    if not re.match(r"[^@]+@[^@]+\.[^@]+", str(to or "")):
        return {"ok": False, "error": "invalid recipient"}
    try:
        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = str(to)
        msg["Subject"] = str(subject or "Zyphere")[:200]
        msg.attach(MIMEText(str(body or "")[:8000], "plain", "utf-8"))
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx, timeout=30) as s:
            s.login(sender, pw)
            s.sendmail(sender, [str(to)], msg.as_string())
        return {"ok": True, "to": str(to)}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}
