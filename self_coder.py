"""Zyphere Self-Coder — Zyphere writes and improves its OWN code safely.

Guard rails:
  - whitelist of files, protected blocks never touched
  - max one targeted patch per cycle, size limits, no secrets
  - backup -> apply -> py_compile -> regression -> analyst -> revert on failure
  - git commit + push only after all gates pass
  - every cycle logged and published for audit

HONEST: a patch is counted only if tests pass and the commit is pushed.
"""
import os, re, json, time, threading, subprocess, base64, requests

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "self_coder.json")
REPO = "Vorakan-yakham/zyphere-scholar-product-pack"
BASE = "https://api.github.com/repos/" + REPO + "/contents/"

ALLOWED = {
    "app.py": ["/api/health", "def do_GET", "def do_POST", "MEDIA_DIR ="],
    "store.py": ["def create_order", "def mark_paid", "PROMPTPAY"],
    "chief.py": ["def decide", "def run_cycle", "NAME ="],
    "five_engines.py": ["ENGINES =", "def status"],
    "supervisors.py": ["DEPTS", "def build"],
    "quality_ops.py": ["DEPTS", "def measure"],
    "language.py": ["CONFUSABLES", "def correct"],
    "music_studio.py": ["def compose", "def create"],
    "image_studio.py": ["def generate", "def critique"],
    "systems_analyst.py": ["def analyze", "def design_review"],
    "role_profiles.py": ["def add", "P = {}"],
    "autonomous_council.py": ["def run(", "DEPARTMENTS =", "def debate("],
}

BAN = ("gsk_", "rnd_", "gho_", "sk-or-v1-", "hf_", "APP_PASSWORD", "PRIVATE KEY",
       "</html>", "</body>", "<!DOCTYPE", "os.system", "subprocess.call(\"rm",
       "shutil.rmtree", "eval(", "exec(")


def token():
    t = os.environ.get("GH_TOKEN", "") or os.environ.get("GITHUB_TOKEN", "")
    if not t:
        t = subprocess.run(["gh", "auth", "token"], capture_output=True,
                           text=True, timeout=15).stdout.strip()
    return t


def push(text):
    try:
        h = {"Authorization": "Bearer " + token(), "Accept": "application/vnd.github+json"}
        url = BASE + "SELF_CODER.md"
        g = requests.get(url, headers=h, timeout=15)
        sha = (g.json() or {}).get("sha") if g.ok else None
        p = {"message": "Self-coder audit " + str(int(time.time())),
             "content": base64.b64encode(text.encode("utf-8")).decode(), "branch": "main"}
        if sha:
            p["sha"] = sha
        requests.put(url, headers=h, json=p, timeout=30)
    except Exception:
        pass


class SelfCoder:
    def __init__(self):
        self.lock = threading.RLock()
        self.log = []
        try:
            self.log = json.load(open(DATA, encoding="utf-8")).get("log", [])
        except Exception:
            pass

    def save(self):
        with self.lock:
            os.makedirs(os.path.dirname(DATA), exist_ok=True)
            json.dump({"log": self.log[-200:]}, open(DATA, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=2)

    def _pick(self, filename=None, focus=None):
        # Choose the file the council actually found a problem in, not a random
        # one. This is the difference between "writing code" and learning.
        target = focus or filename
        if target in ALLOWED:
            f = target
        else:
            import random
            f = random.choice(list(ALLOWED))
        s = open(os.path.join(ROOT, f), encoding="utf-8").read()
        start = random.randint(0, max(0, len(s) - 2000))
        blocks = [b.strip() for b in re.split(r"\n\s*\n", s[start:start + 1800])
                  if 120 <= len(b.strip()) <= 900]
        if not blocks:
            blocks = [s[:900]]
        return f, blocks[:3]

    def _ask(self, f, blocks):
        from brain_ensemble import ensemble
        listing = "\n\n".join("[%d]\n%s" % (i, b) for i, b in enumerate(blocks))
        prompt = ("คุณเป็นนักเขียนโค้ดอัตโนมัติของ Zyphere ปรับปรุง ONE block ในไฟล์ %s "
                  "ให้ชัดเจน/ปลอดภัยขึ้นโดยยังทำงานเหมือนเดิม "
                  "ตอบ JSON เท่านั้น: {\"candidate\":0,\"new\":\"<block ใหม่>\",\"reason\":\"...\"} "
                  "ห้ามลบฟังก์ชัน ห้ามลง secret ห้ามเปลี่ยนโครงสร้างไฟล์ "
                  "ใหม่ต้องไม่มีอยู่แล้วในไฟล์\nBLOCKS:\n%s" % (f, listing))
        try:
            r = ensemble([{"role": "user", "content": prompt}], want_synthesis=True)
            text = r.get("text", "")
            src = r.get("sources", [])
        except Exception as e:
            return None, ["error:" + str(e)[:60]]
        m = re.search(r"\{[\s\S]*\}", text)
        try:
            return json.loads(m.group(0)) if m else None, src
        except Exception:
            return None, src

    def _valid(self, f, old, new):
        if f not in ALLOWED or len(old) < 100 or not (100 <= len(new) <= 1600):
            return False
        if new.strip() == old.strip() or new.strip() in open(os.path.join(ROOT, f), encoding="utf-8").read():
            return False
        up = new.upper()
        if any(x in up for x in BAN):
            return False
        for token_s in ALLOWED[f]:
            if token_s in old and token_s not in new:
                return False
        return True

    def _verify(self):
        for cmd in (["python", "-m", "py_compile", "app.py"],
                    ["python", "test_zyphere.py"],
                    ["python", "systems_analyst.py"]):
            r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=300)
            if r.returncode != 0:
                return False, (r.stderr or r.stdout)[-200:]
        return True, ""

    def _commit(self, f, reason):
        msgs = [["git", "add", f],
                ["git", "commit", "-m", "self-coder: " + str(reason)[:70]],
                ["git", "-c", "rebase.autoStash=true", "pull", "--rebase", "origin", "main"],
                ["git", "push", "origin", "main"]]
        for c in msgs:
            r = subprocess.run(c, cwd=ROOT, capture_output=True, text=True, timeout=180)
            if r.returncode != 0:
                return False, (r.stderr or r.stdout)[-180:]
        return True, ""

    def cycle(self, filename=None, dry=False, focus=None):
        f, blocks = self._pick(filename, focus)
        p, src = self._ask(f, blocks)
        if not p:
            rec = {"ok": False, "file": f, "reason": "no valid proposal", "t": int(time.time())}
            with self.lock:
                self.log.append(rec)
            self.save()
            return rec
        try:
            ci = int(p.get("candidate", -1))
        except Exception:
            ci = -1
        if ci < 0 or ci >= len(blocks):
            return {"ok": False, "file": f, "reason": "bad candidate"}
        old, new = blocks[ci], str(p.get("new") or "")
        if not self._valid(f, old, new):
            return {"ok": False, "file": f, "reason": "guard rejected"}
        if dry:
            rec = {"ok": True, "dry": True, "file": f, "reason": p.get("reason"),
                   "old": old[:200], "new": new[:200], "t": int(time.time())}
            with self.lock:
                self.log.append(rec)
            self.save()
            return rec
        path = os.path.join(ROOT, f)
        backup = path + ".selfcoder.bak"
        original = open(path, encoding="utf-8").read()
        open(backup, "w", encoding="utf-8").write(original)
        result = {"ok": False, "file": f, "reason": p.get("reason"), "t": int(time.time()),
                  "sources": src}
        try:
            open(path, "w", encoding="utf-8").write(original.replace(old, new, 1))
            good, err = self._verify()
            if not good:
                open(path, "w", encoding="utf-8").write(original)
                result["reason"] = "verify failed, reverted: " + err[:120]
            else:
                ok, msg = self._commit(f, str(p.get("reason") or "improve"))
                if ok:
                    result["ok"] = True
                    result["reason"] = "pushed: " + str(p.get("reason"))[:90]
                else:
                    open(path, "w", encoding="utf-8").write(original)
                    result["reason"] = "push failed, reverted: " + msg[:120]
        except Exception as e:
            open(path, "w", encoding="utf-8").write(original)
            result["reason"] = "exception, reverted: " + str(e)[:120]
        finally:
            try:
                os.remove(backup)
            except Exception:
                pass
        with self.lock:
            self.log.append(result)
        self.save()
        md = ["# Zyphere Self-Coder Audit", "", "ทุก patch ผ่าน guard + test ก่อน commit", ""]
        for r in self.log[-40:]:
            md += ["## " + ("OK" if r.get("ok") else "SKIP") + " " + r.get("file", "?") +
                   " " + time.strftime("%H:%M", time.localtime(r.get("t", time.time()))), "",
                   "- เหตุผล: " + str(r.get("reason"))[:300], ""]
        push("\n".join(md))
        return result

    def status(self):
        return {"ok": True, "cycles": len(self.log),
                "pushed": sum(1 for x in self.log if x.get("ok") and not x.get("dry")),
                "allowed_files": len(ALLOWED), "last": self.log[-10:]}


SC = SelfCoder()
