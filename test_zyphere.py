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
        import media
        s = media.srt_from_text("สวัสดีครับ นี่คือคำบรรยายภาษาไทย")
        assert "-->" in s, "SRT generation failed"
        wavp = os.path.join(tempfile.gettempdir(), "zy_mel_test.wav")
        mr = media.melody_to_wav(wavp)
        assert mr.get("ok") and os.path.getsize(wavp) > 1000, "melody synth failed"
        import elibrary
        q = elibrary.to_en("ปัญญาประดิษฐ์ทางการแพทย์")
        assert "artificial intelligence" in q and "medicine" in q, "Thai->EN translation failed"
        import curriculum
        assert curriculum.total() >= 100, "master curriculum too small"
        assert len(curriculum.LEARN_STEPS) == 15, "15-step method missing"
        cur, pairs = curriculum.pick(2, 0)
        assert len(pairs) == 2 and pairs[0][0], "curriculum pick failed"
        import research
        rp = os.path.join(tempfile.gettempdir(), "zy_research_test.json")
        if os.path.exists(rp): os.remove(rp)
        rl = research.ResearchLibrary(rp)
        fake = [{"title":"T","author":"A","institution":"I","url":"u","published":"2020",
                 "type":"paper","reliability":"A","field":"science","summary":"s"}]
        rec = rl.record("quantum computing", fake, "physics")
        assert rec.get("ok") and rl.stats()["documents"] >= 1, "research record failed"
        assert not rl.record("เว็บพนัน บาคาร่า", fake).get("ok"), "gambling must be refused"
        import expansion
        assert expansion.total_topics() >= 100, "expansion curriculum too small"
        cov = expansion.coverage_matrix(core_topics=150)
        assert cov["not_complete"] and len(cov["axes"]) == 5, "coverage matrix/self-check missing"
        assert len(expansion.NEW_SOURCES) == 8, "new sources missing"
        db.experience("ออกกำลังกายช่วยลดความเสี่ยงโรคหัวใจ", "elder_teacher")
        tb = db.teach_back("ออกกำลังกาย")
        assert tb.get("ok") and "ผมเข้าใจว่า" in tb.get("explanation", ""), "teach-back failed"
        cr = db.self_critique()
        assert cr.get("ok") and "checked" in cr, "self-critique failed"
        gr = db.link_graph()
        assert gr.get("ok") and "links" in gr, "knowledge graph failed"
        import academic
        r0 = academic.evaluate(facts=0)
        rg = academic.evaluate(facts=800, rules=140, links=130, documents=70, works=40)
        assert r0["rank"] == "แรกเกิด" and rg["is_genius"], "academic rank failed"
        import director
        pl = director.plan("จักรวาล", 4)
        assert pl.get("ok") and len(pl["shots"]) == 4 and pl["shots"][0]["image_query"], "director plan failed"
        qq = director.quality("4k")
        assert qq["w"] == 3840 and qq["h"] == 2160, "4k preset failed"
        import human_art
        cs = human_art.character_spec("hero", "medium", "wavy_medium", "soft")
        assert cs["proportions"]["head_to_body"] in (7.5, 8.0) and cs["skin"], "character spec failed"
        ms = human_art.melody_spec("lofi", 4)
        assert ms.get("ok") and len(ms["notes"]) >= 8 and ms["bpm"] > 0, "melody spec failed"
        import applied
        bp = applied.blueprint("robot")
        assert bp.get("ok") and len(bp["parts"]) >= 4, "robot blueprint failed"
        bs = applied.blueprint("suit")
        assert bs.get("ok") and bs["kind"] == "exosuit", "exosuit blueprint failed"
        import aerospace
        rn = aerospace.design("rocket", 1000, 400)
        assert rn.get("ok") and rn["orbital_speed_kms"] > 7, "rocket design failed"
        sa = aerospace.design("saucer")
        assert sa.get("ok") and sa["kind"] == "saucer", "saucer design failed"
        from work import WorkEngine
        wp = os.path.join(tempfile.gettempdir(), "zy_work_test.json")
        if os.path.exists(wp): os.remove(wp)
        we = WorkEngine(wp)
        w = we.produce("เขียนบทความเรื่องฟิสิกส์ควอนตัม", "physics")
        assert w.get("ok") and w["type"] == "article" and we.count() == 1, "work produce failed"
        assert not we.produce("เว็บพนัน บาคาร่า").get("ok"), "gambling work must be refused"
        from voice import VoiceIdentity
        vpath = os.path.join(tempfile.gettempdir(), "zy_voice_test.json")
        if os.path.exists(vpath): os.remove(vpath)
        vi = VoiceIdentity(vpath)
        lr = vi.learn()
        assert lr.get("ok") and lr["learned"] >= 6, "voice learn failed"
        tc = vi.tune(rate=0.94, pitch_ratio=-7)
        assert tc["rate"] == 0.94 and tc["pitch_ratio"] == -7, "voice tune failed"
        from language import LanguageMastery
        lm = LanguageMastery()
        lr = lm.learn()
        assert lr["learned"] >= 8, "language learn failed"
        cr = lm.correct("ฉันเเล้วว ควาาม")
        assert cr["changes"] and "แล้ว" in cr["text"], "language correct failed"
        from reasoning import ReasoningEngine
        re_ = ReasoningEngine()
        rs = re_.solve("ทำไมน้ำท่วมกรุงเทพทุกปี แก้ยังไง")
        assert rs.get("ok") and len(rs["thinking_map"]) >= 6, "reasoning solve failed"
        assert not re_.solve("เว็บพนัน บาคาร่า").get("ok"), "gambling reasoning refused"
        from concept import ConceptExpander
        ce = ConceptExpander()
        cx = ce.explore("entropy", "ฟิสิกส์")
        assert cx.get("ok") and len(cx["analysis"]) == 4 and cx["new_branches"], "concept explore failed"
        from metacognition import Metacognition
        mc = Metacognition()
        au = mc.audit([{"s":"a","r":"is","o":"b","reliability":"A"}, {"s":"x","r":"is","o":"y","reliability":"D"}])
        assert au.get("ok") and au["total"] == 2 and au["uncertain"] >= 1, "meta audit failed"
        qs = mc.ask_self("ควอนตัม")
        assert qs.get("ok") and len(qs["questions"]) >= 5, "meta ask-self failed"
        from selftest import SelfTest
        st = SelfTest()
        fz = st.feynman("entropy", [{"s":"entropy","r":"is","o":"degree of disorder"}])
        assert fz.get("ok") and fz["explanation"], "feynman failed"
        qz = st.quiz("entropy", 3)
        assert qz.get("ok") and len(qz["questions"]) == 3, "quiz failed"
        ev = st.evaluate("entropy", ["entropy is disorder"], [])
        assert ev.get("ok") and "score" in ev, "evaluate failed"
        print("ALL REGRESSION TESTS PASSED")
        return 0
    finally:
        srv.terminate()

if __name__ == "__main__":
    sys.exit(main())
