"""Zyphere Ensemble Brain - run all available LLM providers in parallel and
synthesize one answer. Each model has different strengths; working together
gives broader, more robust answers than any single model.

Keys come ONLY from environment variables (set on Render). Never hardcoded.
Models are probed/rotated so an exhausted quota on one model does not take the
whole brain offline.
"""
import os, re, json, time
import requests

TIMEOUT = 30

# Verified working models (July 2026). Each provider has a fallback chain:
# if the first model returns 429/404 the next one is tried automatically.
MODELS = {
    "groq": ["qwen/qwen3.8-27b", "openai/gpt-oss-20b"],
    "openrouter": ["nvidia/nemotron-3.5-lightning:free", "inclusionai/ling-3.2-flash:free"],
    "gemini": ["gemini-3.1-flash-lite", "gemini-2.5-flash"],
}


def load_keys():
    """Read provider keys from env. Also accept local API-Zyphere.txt as fallback
    (for local dev only — Render has no such file)."""
    keys = {
        "groq": os.environ.get("GROQ_API_KEY", "").strip(),
        "openrouter": os.environ.get("OPENROUTER_API_KEY", "").strip(),
        "gemini": os.environ.get("GEMINI_API_KEY", "").strip(),
        "hf": os.environ.get("HF_API_KEY", "").strip() or os.environ.get("HUGGINGFACE_API_KEY", "").strip(),
    }
    if not any(keys.values()):
        try:
            p = os.path.join(os.path.dirname(os.path.dirname(__file__)), "API-Zyphere.txt")
            txt = open(p, encoding="utf-8", errors="ignore").read()
            gm = re.findall(r"gsk_[A-Za-z0-9]+", txt)
            if gm and not keys["groq"]:
                keys["groq"] = gm[0]
            am = re.findall(r"AQ\.[A-Za-z0-9_\-]+", txt)
            if am and not keys["gemini"]:
                keys["gemini"] = am[0]
            om = re.findall(r"sk-or-[A-Za-z0-9_\-]+", txt)
            if om and not keys["openrouter"]:
                keys["openrouter"] = om[0]
            hm = re.findall(r"hf_[A-Za-z0-9]+", txt)
            if hm and not keys["hf"]:
                keys["hf"] = hm[0]
        except Exception:
            pass
    return {k: v for k, v in keys.items() if v}


def _call_groq(key, messages, model=None, max_tokens=2048):
    r = requests.post("https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        json={"model": model or MODELS["groq"][0], "messages": messages,
              "temperature": 0.4, "max_tokens": max_tokens}, timeout=TIMEOUT)
    r.raise_for_status()
    return str(((r.json().get("choices") or [{}])[0].get("message") or {}).get("content") or "")


def _call_openrouter(key, messages, model=None, max_tokens=2048):
    r = requests.post("https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json",
                 "HTTP-Referer": "https://github.com/Vorakan-yakham/zyphere-ai-agent",
                 "X-Title": "Zyphere"},
        json={"model": model or MODELS["openrouter"][0], "messages": messages,
              "temperature": 0.4, "max_tokens": max_tokens}, timeout=TIMEOUT)
    r.raise_for_status()
    return str(((r.json().get("choices") or [{}])[0].get("message") or {}).get("content") or "")


def _call_gemini(key, messages, model=None, max_tokens=2048):
    flat = "\n\n".join(("%s: %s" % (m.get("role", "user"), m.get("content", ""))) for m in messages)
    r = requests.post(
        "https://generativelanguage.googleapis.com/v1beta/models/" +
        (model or MODELS["gemini"][0]) + ":generateContent?key=" + key,
        headers={"Content-Type": "application/json"},
        json={"contents": [{"role": "user", "parts": [{"text": flat}]}],
              "generationConfig": {"temperature": 0.4, "maxOutputTokens": max_tokens}},
        timeout=TIMEOUT)
    r.raise_for_status()
    parts = (((r.json().get("candidates") or [{}])[0].get("content") or {}).get("parts") or [])
    return "".join(str(p.get("text") or "") for p in parts)


CALLERS = {"groq": _call_groq, "openrouter": _call_openrouter, "gemini": _call_gemini}


def _local_fallback(messages, errors):
    """Honest last resort: try the in-machine brain, otherwise state the real
    problem. Never pretend work was done or fabricate an answer."""
    q = ""
    for m in reversed(messages or []):
        if m.get("role") == "user":
            q = str(m.get("content") or "")
            break
    try:
        from local_brain import LocalBrain
        p = os.path.join(os.path.dirname(__file__), "data", "brain.json")
        if os.path.exists(p):
            out = LocalBrain(p).ask(q)
            if out and str(out).strip():
                return str(out).strip()
    except Exception:
        pass
    reasons = []
    for name, err in (errors or {}).items():
        if "429" in err:
            reasons.append(name + " หมดโควต้า/ถูกจำกัดอัตรา")
        elif "404" in err:
            reasons.append(name + " โมเดลไม่พร้อม")
        elif err:
            reasons.append(name + " ไม่ตอบ")
    detail = ", ".join(reasons) if reasons else "ไม่มีผู้ให้บริการพร้อม"
    return ("ขออภัยครับ ขณะนี้โมเดล AI ภายนอกยังใช้ไม่ได้ชั่วคราว (%s) "
            "ผมยังทำงานอยู่และจะลองใหม่ในอีกสักครู่ — "
            "หากคุณต้องการให้ช่วยงานที่ใช้เครื่องมือในเครื่อง เช่น วิเคราะห์ไฟล์ "
            "ค้นความรู้ที่สะสมไว้ หรือสร้างสรรค์ผลงาน สามารถสั่งได้เลยครับ" % detail)


def ensemble(messages, want_synthesis=True):
    """Call all configured providers in parallel, synthesize their answers.
    Returns dict: ok, text, sources, errors, synthesized."""
    keys = load_keys()
    if not keys:
        return {"ok": False, "error": "no AI keys configured", "sources": []}
    from concurrent.futures import ThreadPoolExecutor, as_completed
    answers = {}
    errors = {}
    def run(name, key):
        fn = CALLERS.get(name)
        if not fn:
            return name, None, None  # no caller configured (e.g. hf) - skip silently
        errs = []
        for model in MODELS.get(name, [None]):
            try:
                txt = fn(key, messages, model=model, max_tokens=2048)
                if txt and txt.strip():
                    return name, txt.strip(), None
                errs.append(model + ":empty")
            except Exception as e:
                errs.append(str(e)[:110])
        return name, None, "; ".join(errs)
    with ThreadPoolExecutor(max_workers=max(1, len(keys))) as ex:
        futs = {ex.submit(run, n, k): n for n, k in keys.items()}
        for f in as_completed(futs):
            n, txt, err = f.result()
            if txt:
                answers[n] = txt
            if err:
                errors[n] = err

    if not answers:
        text = _local_fallback(messages, errors)
        return {"ok": True, "text": text, "sources": ["local-fallback"],
                "errors": errors, "local": True, "synthesized": False}

    names = list(answers.keys())
    text = ""
    synthesized = False
    if want_synthesis and len(answers) > 1:
        joined = "\n\n".join("--- %s ---\n%s" % (n, answers[n]) for n in names)
        judge_sys = ("You are the chief analyst (Zyphere). Several AI assistants answered the same "
                     "question. Compare them, keep what is correct and consistent across answers, "
                     "discard errors or contradictions, and write ONE final answer in the same "
                     "language as the question. Be concise but complete. Do not mention the other "
                     "assistants or this process.")
        judge_msgs = [{"role": "system", "content": judge_sys},
                      {"role": "user", "content": joined}]
        for n in names:
            try:
                out = CALLERS[n](keys.get(n, ""), judge_msgs, max_tokens=2048)
                if out and out.strip():
                    text = out.strip()
                    synthesized = True
                    break
            except Exception:
                continue
    if not text:
        text = max(answers.values(), key=len)
    return {"ok": True, "text": text, "sources": names, "errors": errors,
            "synthesized": synthesized}
