import json, os, random, re, subprocess, sys, time, urllib.request, urllib.error
ROOT = os.path.dirname(os.path.abspath(__file__))
ALLOWED = {"app.py", "index.html"}
CANDIDATES = []
INTERVAL = int(os.environ.get("DEV_INTERVAL", "900"))
MAX = int(os.environ.get("DEV_MAX", "6"))
DRY = os.environ.get("DEV_DRY") == "1"
LOG = os.path.join(ROOT, "data", "dev_agent.log")
KEY = os.environ.get("GROQ_API_KEY", "").strip()
if not KEY:
    try:
        KEY = open(r"C:\Users\vornl\Documents\API-Zyphere.txt", encoding="utf-8").read().splitlines()[1].strip()
    except Exception:
        KEY = ""

def log(m):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(time.strftime("%H:%M:%S ") + str(m) + "\n")
    print(m, flush=True)

def ask(prompt):
    body = json.dumps({"model": "openai/gpt-oss-120b", "messages": [{"role": "user", "content": prompt}], "temperature": 0.3, "max_tokens": 3000, "response_format": {"type": "json_object"}}).encode()
    req = urllib.request.Request("https://api.groq.com/openai/v1/chat/completions", data=body, headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json", "User-Agent": "Zyphere-Dev-Agent/1.0"})
    try:
        return json.load(urllib.request.urlopen(req, timeout=60))["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        log("HTTP " + str(e.code) + " " + e.read().decode("utf-8", "replace")[:300])
        raise

def apply_patch(p):
    f = str(p.get("file") or "")
    old = str(p.get("old") or "")
    new = str(p.get("new") or "")
    bad = ("</html>", "</body>", "<body", "<!DOCTYPE", "</head>")
    if f not in ALLOWED or len(old) < 80 or len(new) > 1200 or old.strip() == new.strip():
        return False
    if any(x in new.upper() for x in bad):
        return False
    path = os.path.join(ROOT, f)
    s = open(path, encoding="utf-8").read()
    if old not in s or new.strip() in s:
        return False
    open(path, "w", encoding="utf-8").write(s.replace(old, new, 1))
    return True

def verify():
    r = subprocess.run([sys.executable, "-m", "py_compile", "app.py"], cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        return False
    port = "8149"
    env = dict(os.environ, PORT=port)
    srv = subprocess.Popen([sys.executable, "app.py"], cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(30):
            time.sleep(0.4)
            try:
                base = "http://127.0.0.1:" + port
                with urllib.request.urlopen(base + "/api/health", timeout=2) as r:
                    if r.status != 200:
                        continue
                with urllib.request.urlopen(base + "/", timeout=2) as r:
                    html = r.read().decode("utf-8", "replace")
                return html.count("<body") <= 1 and html.count("</body>") <= 1 and 'id="sendBtn"' in html and 'id="know"' in html
            except Exception:
                pass
        return False
    finally:
        srv.terminate()

def commit(msg):
    for a in (["git", "add", "-A"], ["git", "commit", "-m", msg], ["git", "push", "origin", "main"]):
        r = subprocess.run(a, cwd=ROOT, capture_output=True, text=True)
        if r.returncode != 0:
            log("git fail: " + (r.stderr or "")[:160])
            return False
    return True

def make_prompt():
    global CANDIDATES
    f = random.choice(["app.py", "index.html"])
    s = open(os.path.join(ROOT, f), encoding="utf-8").read()
    start = random.randint(0, max(0, len(s) - 2500))
    blocks = [b.strip() for b in re.split(r"\n\s*\n", s[start:start + 2400]) if 80 <= len(b.strip()) <= 600]
    CANDIDATES = [{"file": f, "text": b} for b in blocks[:3]]
    if not CANDIDATES:
        CANDIDATES = [{"file": f, "text": s[:600]}]
    listing = "\n\n".join("[" + str(i) + "] file=" + c["file"] + "\n" + c["text"] for i, c in enumerate(CANDIDATES))
    return ("You are the autonomous developer of Zyphere. Choose ONE block below and improve it. "
            "Return JSON only: {\"candidate\":0,\"new\":\"<replacement block>\",\"reason\":\"...\"}. "
            "Rules: new under 500 chars, must keep the same purpose but be clearer or safer, must not already exist, no secrets, no deletion, no new files, no network calls, no requirements changes, keep code valid. "
            "Focus on clarity, memory, learning, language or voice.\nBLOCKS:\n" + listing)

def main():
    log("dev agent start MAX=" + str(MAX) + " DRY=" + str(DRY))
    for i in range(MAX):
        log("cycle " + str(i + 1))
        try:
            raw = ask(make_prompt())
            m = re.search(r"\{[\s\S]*\}", raw)
            p = json.loads(m.group(0)) if m else {}
            if DRY:
                log("DRY " + json.dumps(p, ensure_ascii=False)[:400])
                break
            try:
                ci = int(p.get("candidate", -1))
            except Exception:
                ci = -1
            if ci < 0 or ci >= len(CANDIDATES):
                log("skip bad candidate")
                time.sleep(INTERVAL)
                continue
            p["file"] = CANDIDATES[ci]["file"]
            p["old"] = CANDIDATES[ci]["text"]
            log("patch candidate " + str(ci) + " " + str(p.get("reason") or "")[:100])
            f = str(p.get("file") or "")
            if not apply_patch(p):
                log("skip invalid patch")
                time.sleep(INTERVAL)
                continue
            if not verify():
                subprocess.run(["git", "checkout", "--", f], cwd=ROOT)
                log("verify failed, reverted")
                time.sleep(INTERVAL)
                continue
            if commit("dev-agent: " + str(p.get("reason") or "improve")[:80]):
                log("pushed " + f)
            time.sleep(INTERVAL)
        except Exception as e:
            log("error " + str(e)[:200])
            time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
