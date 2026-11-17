import json, os, random, subprocess, sys, time, urllib.request
PORT = str(random.randint(8300, 8900))
BASE = "http://127.0.0.1:" + PORT

def get(path):
    with urllib.request.urlopen(BASE + path, timeout=6) as r:
        return r.read()

def jget(path):
    return json.loads(get(path).decode("utf-8"))

def main():
    srv = subprocess.Popen([sys.executable, "app.py"], env=dict(os.environ, PORT=PORT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):
            try:
                jget("/api/health"); break
            except Exception:
                time.sleep(0.3)
        h = jget("/api/health")
        assert h.get("version", 0) >= 22, "version too old"
        for f in ("stt", "goals", "feedback", "remote_kv"):
            assert f in h.get("features", []), "missing feature " + f
        html = get("/").decode("utf-8", "replace")
        for tok in ("zy_greet_i", "function send(", "localAns", "api/goals", "api/transcribe", "ttsNorm", "GREET", "greetLang", "async function readSSE(", "id=\"sendBtn\"", "id=\"know\""):
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
