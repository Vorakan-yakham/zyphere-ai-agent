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

    def status(self):
        try:
            r = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True, timeout=20)
            ok = r.returncode == 0 and "Logged in" in (r.stdout + r.stderr)
        except Exception:
            ok = False
        return {"ok": True, "github_auth": ok, "repo": REPO,
                "files_logged": len(self.log),
                "url": "https://github.com/" + REPO}

    def backup(self, files=None):
        """Write files into a fresh clone and push (durable, visible store)."""
        files = files or []
        if not files:
            return {"ok": False, "error": "no files"}
        tmp = tempfile.mkdtemp(prefix="zy_backup_")
        env = dict(os.environ)
        for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
            env.pop(k, None)
        try:
            r = subprocess.run(["gh", "repo", "clone", REPO, tmp, "--", "--depth", "1"],
                               capture_output=True, text=True, timeout=90, env=env)
            if r.returncode != 0:
                return {"ok": False, "error": "clone: " + str(r.stderr)[:200]}
            written = []
            for item in files:
                name = str(item.get("name", "file.txt"))
                content = str(item.get("content", ""))
                # safe filename
                name = "".join(c if c.isalnum() or c in "-_./" else "_" for c in name)[:180]
                fp = os.path.join(tmp, name)
                os.makedirs(os.path.dirname(fp), exist_ok=True)
                open(fp, "w", encoding="utf-8").write(content)
                written.append(name)
            subprocess.run(["git", "-C", tmp, "add", "-A"], capture_output=True, env=env)
            c = subprocess.run(["git", "-C", tmp, "-c", "user.email=zyphere@local",
                                "-c", "user.name=Zyphere", "commit",
                                "-m", "Zyphere backup " + str(int(time.time()))],
                               capture_output=True, text=True, env=env)
            if "nothing to commit" in (c.stdout + c.stderr):
                return {"ok": True, "nothing_new": True, "url": "https://github.com/" + REPO}
            p = subprocess.run(["git", "-C", tmp, "push", "origin", "main"],
                               capture_output=True, text=True, env=env, timeout=120)
            if p.returncode != 0:
                return {"ok": False, "error": "push: " + str(p.stderr)[:200]}
            rec = {"ok": True, "files": written, "t": int(time.time()),
                   "url": "https://github.com/" + REPO}
            with self.lock:
                self.log.append(rec)
            self.save()
            return rec
        except Exception as e:
            return {"ok": False, "error": str(e)[:200]}
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
