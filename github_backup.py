"""Zyphere GitHub Backup - store REAL work as real files in a GitHub repo,
so results SURVIVE Render restarts and are visible to buyers. Uses the gh CLI
token the owner already authenticated (no new OTP, free, legal).

Why: Render free wipes local disk + Upstash restore is unreliable. GitHub is
durable, versioned, public, and already granted. This is the persistent store.

HONEST: uses owner's gh CLI auth (already logged in). No password/OTP stored.
No fake claims. Files = the actual knowledge products + quotes.
"""
import os, json, time, threading, subprocess, tempfile, shutil

REPO = "Vorakan-yakham/zyphere-scholar-product-pack"


class GitHubBackup:
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
                json.dump({"log": self.log[-500:]}, open(self.path, "w", encoding="utf-8"),
                          ensure_ascii=False, indent=2)
            except Exception:
                pass

    def token(self):
        return (os.environ.get("GITHUB_TOKEN", "")
                or os.environ.get("GH_TOKEN", "")).strip()

    def status(self):
        import requests as _rq
        tok = self.token()
        ok = False
        login = ""
        if tok:
            try:
                r = _rq.get("https://api.github.com/user",
                    headers={"Authorization": "Bearer " + tok, "Accept": "application/vnd.github+json"},
                    timeout=15)
                ok = r.ok
                login = (r.json() or {}).get("login", "")
            except Exception:
                pass
        return {"ok": True, "github_auth": ok, "login": login, "repo": REPO,
                "files_logged": len(self.log),
                "url": "https://github.com/" + REPO,
                "note": "ใช้ GITHUB_TOKEN (REST API) — ไม่ต้อง gh CLI"}

    def backup(self, files=None):
        """Write files via GitHub REST API (no gh CLI needed on Render).
        Uses Contents API: PUT /repos/{owner}/{repo}/contents/{path} with token.
        """
        import base64, requests as _rq
        files = files or []
        if not files:
            return {"ok": False, "error": "no files"}
        tok = self.token()
        if not tok:
            return {"ok": False, "error": "GITHUB_TOKEN not set in Render env"}
        api = "https://api.github.com/repos/" + REPO + "/contents/"
        headers = {"Authorization": "Bearer " + tok, "Accept": "application/vnd.github+json"}
        written, errors = [], []
        for item in files[:60]:
            name = str(item.get("name", "file.txt"))
            content = str(item.get("content", ""))
            name = "".join(c if c.isalnum() or c in "-_./" else "_" for c in name)[:180]
            # get existing sha (to update instead of create conflict)
            sha = None
            try:
                g = _rq.get(api + name, headers=headers, timeout=15)
                if g.ok:
                    sha = (g.json() or {}).get("sha")
            except Exception:
                pass
            payload = {"message": "Zyphere backup " + str(int(time.time())),
                       "content": base64.b64encode(content.encode("utf-8")).decode(),
                       "branch": "main"}
            if sha:
                payload["sha"] = sha
            try:
                r = _rq.put(api + name, headers=headers, json=payload, timeout=30)
                if r.ok:
                    written.append(name)
                else:
                    errors.append(name + ": " + str(r.status_code))
            except Exception as e:
                errors.append(name + ": " + str(e)[:60])
        rec = {"ok": bool(written), "files": written, "errors": errors, "t": int(time.time()),
               "url": "https://github.com/" + REPO}
        with self.lock:
            self.log.append(rec)
        self.save()
        return rec
