import json, os, random, re, shutil, subprocess, sys, tempfile, time, urllib.request
PORT = str(random.randint(8300, 8900))
BASE = "http://127.0.0.1:" + PORT

def get(path):
    with urllib.request.urlopen(BASE + path, timeout=6) as r:
        return r.read()

def jget(path):
    return json.loads(get(path).decode("utf-8"))

def js_ok():
    src = open("index.html", encoding="utf-8").read()
    blocks = re.findall(r"<script(?![^>]*src)[^>]*>([\s\S]*?)</script>", src)
    node = shutil.which("node") or r"C:\Program Files\nodejs\node.exe"
    if not node or not os.path.exists(node):
        return True
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write("\n".join(blocks))
        path = f.name
    try:
        return subprocess.run([node, "--check", path], capture_output=True, text=True).returncode == 0
    finally:
        os.unlink(path)

def main():
    srv = subprocess.Popen([sys.executable, "app.py"], env=dict(os.environ, PORT=PORT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):
            try:
                jget("/api/health"); break
            except Exception:
                time.sleep(0.3)
        assert js_ok(), "JavaScript syntax error in index.html"
        h = jget("/api/health")
        assert h.get("version", 0) >= 22, "version too old"
        for f in ("stt", "goals", "feedback", "remote_kv"):
            assert f in h.get("features", []), "missing feature " + f
        html = get("/").decode("utf-8", "replace")
        for tok in ("zy_greet_i", "function send(", "localAns", "api/goals", "api/transcribe", "ttsNorm", "GREET", "greetLang", "async function readSSE(", "feedStreamSpeak", "drainTTS", "async function getWeather(", "id=\"sendBtn\"", "id=\"know\""):
            assert tok in html, "missing UI token " + tok
        assert html.count("<body") <= 1 and html.count("</body>") <= 1, "broken body structure"
        assert jget("/api/goals").get("ok"), "goals endpoint failed"
        cfg = jget("/api/learn/config").get("config", {})
        assert cfg.get("dev_total", 0) >= 100, "curriculum too small"
        assert jget("/api/briefing?since=0&limit=1").get("ok"), "briefing failed"
        print("ALL REGRESSION TESTS PASSED")
        return 0
    finally:
        srv.terminate()

if __name__ == "__main__":
    sys.exit(main())
