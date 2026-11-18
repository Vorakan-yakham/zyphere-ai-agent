"""Regression tests: Zyphere must think and self-code WITHOUT any external AI.

No Groq / Gemini / OpenRouter key or quota is required for any check here.
"""
import json
import os
import sys


def test_harvest():
    import own_brain
    lessons = own_brain.harvest()
    assert isinstance(lessons, list) and len(lessons) > 0, "harvest() found no lessons"


def test_grow_returns_actions():
    import own_brain
    # Keep the round deterministic and side-effect free: one harmless gap.
    original = own_brain.weaknesses
    own_brain.weaknesses = lambda kb: [{"gap": "unit-test", "action": "observe", "module": None}]
    try:
        r = own_brain.grow(apply=False)
    finally:
        own_brain.weaknesses = original
    assert r.get("ok") is True and isinstance(r.get("actions"), list) and r["actions"], \
        "grow() must return actions"
    assert r["actions"][0]["action"] == "observe"


def test_ask_local_answers():
    import own_brain
    r = own_brain.ask("ภาพ")
    assert r.get("ok") and r.get("engine") == "zy-own-brain", "ask() must use local engine"
    assert isinstance(r.get("answers"), list) and r["answers"], \
        "ask('ภาพ') must return local answers without an API"


def test_self_coder_local_without_external_ai():
    import brain_ensemble
    import self_coder
    sc = self_coder.SelfCoder()

    original = brain_ensemble.ensemble

    def _boom(*args, **kwargs):
        raise RuntimeError("external AI unavailable (simulated quota loss)")

    brain_ensemble.ensemble = _boom
    try:
        got = None
        for f in ("app.py", "language.py", "chief.py"):
            _, blocks = sc._pick(f)
            proposal, sources = sc._ask(f, blocks)
            if isinstance(proposal, dict) and proposal.get("reason") == "local-brain":
                got = (f, blocks, proposal, sources)
                break
        assert got, "self_coder._ask() did not fall back to the local brain"
        f, blocks, proposal, sources = got
        assert 0 <= int(proposal.get("candidate", -1)) < len(blocks)
        assert isinstance(proposal.get("new"), str) and len(proposal["new"]) >= 100
        assert "local-brain" in sources, "local patch must be tagged local-brain"
        assert sc._valid(f, blocks[proposal["candidate"]], proposal["new"]), \
            "local patch must pass every existing guard in _valid"
        assert not any(s in proposal["new"] for s in ("gsk_", "sk-or-v1-", "PRIVATE KEY")), \
            "local patch must never contain secrets"
    finally:
        brain_ensemble.ensemble = original


def main():
    tests = [test_harvest, test_grow_returns_actions, test_ask_local_answers,
             test_self_coder_local_without_external_ai]
    for t in tests:
        t()
        print("PASS", t.__name__)
    print("ALL OWN-BRAIN TESTS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
