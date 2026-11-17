"""Zyphere Ensemble Brain - run all available LLM providers in parallel and
synthesize one answer. Each model has different strengths; working together
gives broader, more robust answers than any single model.

Keys come ONLY from environment variables (set on Render). Never hardcoded.
"""
import os, re, json, time
import requests

TIMEOUT = 45


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


def _call_groq(key, messages, model="openai/gpt-oss-120b", max_tokens=2048):
    r = requests.post("https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        json={"model": model, "messages": messages, "temperature": 0.4, "max_tokens": max_tokens},
        timeout=TIMEOUT)
    r.raise_for_status()
    return str(((r.json().get("choices") or [{}])[0].get("message") or {}).get("content") or "")


def _call_openrouter(key, messages, model="deepseek/deepseek-chat-v3.1:free", max_tokens=2048):
    r = requests.post("https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json",
                 "HTTP-Referer": "https://github.com/Vorakan-yakham/zyphere-ai-agent",
                 "X-Title": "Zyphere"},
        json={"model": model, "messages": messages, "temperature": 0.4, "max_tokens": max_tokens},
        timeout=TIMEOUT)
    r.raise_for_status()
    return str(((r.json().get("choices") or [{}])[0].get("message") or {}).get("content") or "")


def _call_gemini(key, messages, model="gemini-flash-lite-latest", max_tokens=2048):
    # Gemini uses a single prompt; flatten system+user turns.
    flat = "\n\n".join(("%s: %s" % (m.get("role", "user"), m.get("content", ""))) for m in messages)
    r = requests.post(
        "https://generativelanguage.googleapis.com/v1beta/models/" + model + ":generateContent?key=" + key,
        headers={"Content-Type": "application/json"},
        json={"contents": [{"role": "user", "parts": [{"text": flat}]}],
              "generationConfig": {"temperature": 0.4, "maxOutputTokens": max_tokens}},
        timeout=TIMEOUT)
    r.raise_for_status()
    parts = (((r.json().get("candidates") or [{}])[0].get("content") or {}).get("parts") or [])
    return "".join(str(p.get("text") or "") for p in parts)


CALLERS = {"groq": _call_groq, "openrouter": _call_openrouter, "gemini": _call_gemini}


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
            return name, None, "no caller"
        try:
            return name, fn(key, messages), None
        except Exception as e:
            return name, None, str(e)[:200]
    with ThreadPoolExecutor(max_workers=len(keys)) as ex:
        futs = {ex.submit(run, n, k): n for n, k in keys.items()}
        for f in as_completed(futs):
            n, txt, err = f.result()
            if txt:
                answers[n] = txt.strip()
            if err:
                errors[n] = err

    if not answers:
        return {"ok": False, "error": "all providers failed", "sources": [], "errors": errors}

    names = list(answers.keys())
    text = ""
    synthesized = False
    # Synthesize when >1 provider answered: use the first successful provider
    # as judge to combine all answers into one coherent answer.
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
        # single provider answers, or synthesis failed -> use the longest answer
        text = max(answers.values(), key=len)
    return {"ok": True, "text": text, "sources": names, "errors": errors,
            "synthesized": synthesized}
