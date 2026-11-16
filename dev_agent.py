import json, os, re, subprocess, sys, time, urllib.request
ROOT = os.path.dirname(os.path.abspath(__file__))
ALLOWED = {"app.py", "index.html"}
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
    body = json.dumps({"model": "openai/gpt-oss-120b", "messages": [{"role": "user", "content": prompt}], "temperature": 0.3, "max_tokens": 1500, "response_format": {"type": "json_object"}}).encode()
    req = urllib.request.Request("https://api.groq.com/openai/v1/chat/completions", data=body, headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json", "User-Agent": "Zyphere-Dev-Agent/1.0"})
    return json.load(urllib.request.urlopen(req, timeout=60))["choices"][0]["message"]["content"]

def apply_patch(p):
    f = str(p.get("file") or "")
    old = str(p.get("old") or "")
    new = str(p.get("new") or "")
    if f not in ALLOWED or len(old) < 30 or len(new) > 1200 or old.strip() == new.strip():
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
                with urllib.request.urlopen("http://127.0.0.1:" + port + "/api/health", timeout=2) as r:
                    return r.status == 200
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
    app = open(os.path.join(ROOT, "app.py"), encoding="utf-8").read()
    idx = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    m = re.search(r'"version": \d+,.*?],[^\n]*', app)
    a = m.group(0)[:400] if m else app[:400]
    m2 = re.search(r"function renderLearnStats.*?\n", idx)
    b = m2.group(0)[:400] if m2 else ""
    return ("You are the autonomous developer of Zyphere, a Thai/English AI assistant. "
            "Propose ONE tiny, safe improvement. Return JSON only: "
            "{\"file\":\"app.py|index.html\",\"old\":\"<exact text that exists>\",\"new\":\"<replacement>\",\"reason\":\"...\"}. "
            "Rules: old must match exactly and be at least 40 chars; new under 800 chars and must add real value, not duplicate existing text; no secrets, no deletion, no new files, no network calls, no changes to requirements; keep code valid. "
            "Focus on clarity, memory, learning, language or voice. Context app: " + a + " Context ui: " + b)

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
