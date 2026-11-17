import json, os, random, re, shutil, subprocess, sys, tempfile, time, urllib.request
PORT = str(random.randint(8300, 8900))
BASE = "http://127.0.0.1:" + PORT

def get(path):
    with urllib.request.urlopen(BASE + path, timeout=6) as r:
        return r.read()

def jget(path):
    return json.loads(get(path).decode("utf-8"))

def jpost(path, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(BASE + path, data=data,
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=6) as r:
        return json.loads(r.read().decode("utf-8"))

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
        for tok in ("zy_greet_i", "function send(", "localAns", "api/goals", "api/transcribe", "ttsNorm", "GREET", "greetLang", "async function readSSE(", "feedStreamSpeak", "drainTTS", "async function getWeather(", "function selfTest(", "function localSong(", "function localStory(", "id=\"sendBtn\"", "id=\"know\""):
            assert tok in html, "missing UI token " + tok
        assert html.count("<body") <= 1 and html.count("</body>") <= 1, "broken body structure"
        assert jget("/api/goals").get("ok"), "goals endpoint failed"
        cfg = jget("/api/learn/config").get("config", {})
        assert cfg.get("dev_total", 0) >= 100, "curriculum too small"
        assert cfg.get("learn_count", 0) >= 1, "learn_count missing"
        assert jget("/api/briefing?since=0&limit=1").get("ok"), "briefing failed"
        p = jget("/api/preferences")
        assert p.get("ok") and "preferences" in p, "preferences endpoint failed"
        auto = jpost("/api/brain/auto", {"q": "สวัสดี", "a": "สวัสดีครับ", "voice": True, "lang": "th"})
        assert auto.get("ok") and "preferences" in auto, "brain/auto preferences wiring failed"
        from preferences import Preferences
        assert hasattr(Preferences, "observe") and hasattr(Preferences, "profile"), "Preferences methods missing"
        from ratelimit import RateLimit
        assert hasattr(RateLimit, "allow"), "RateLimit.allow missing"
        from platforms import Platforms
        import tempfile
        pp = Platforms(os.path.join(tempfile.gettempdir(), "zy_platform_test.json"))
        assert pp.log("Fastwork").get("ok"), "platform log failed"
        assert not pp.log("เว็บพนันบาคาร่า").get("ok"), "gambling must be refused"
        assert pp.report().get("total", 0) >= 1, "platform report failed"
        from brain_ensemble import load_keys
        k = load_keys()
        assert "groq" in k and k["groq"].startswith("gsk_"), "Groq key not loaded from file"
        assert len([x for x in k if k[x]]) >= 3, "expected 3+ provider keys from file"
        from dev_brain import DevBrain
        db = DevBrain(os.path.join(tempfile.gettempdir(), "zy_devbrain_test.json"))
        db.experience("ผมชื่อไซเฟอร์", "user")
        db.experience("คุณคือ Zyphere ผู้ช่วย AI ครับ", "teacher")
        db.grow()
        sn = db.self_narrative()
        assert sn.get("stage") and sn.get("experiences", 0) >= 2, "dev brain growth failed"
        from notebook import Notebook
        nbpath = os.path.join(tempfile.gettempdir(), "zy_notebook_test.json")
        if os.path.exists(nbpath):
            os.remove(nbpath)
        nb = Notebook(nbpath)
        nb.add("รายงาน", "ไซเฟอร์มีรายได้ 500 บาท จากการขายงานเขียนคอนเทนต์ในเดือนมกราคม")
        r = nb.analyze("รายได้ของไซเฟอร์เท่าไหร่")
        assert r.get("ok") and r.get("citations"), "notebook grounded analysis failed"
        assert "500" in r.get("answer", ""), "notebook answer not grounded in source"
        print("ALL REGRESSION TESTS PASSED")
        return 0
    finally:
        srv.terminate()

if __name__ == "__main__":
    sys.exit(main())
