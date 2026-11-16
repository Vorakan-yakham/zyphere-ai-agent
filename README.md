# ZYPHERE — Autonomous Executive OS (Phase 1)

A personal AI that thinks between your requests, remembers, writes and tests its own helper functions, and takes
voice or text. Everything it does on its own is bounded by a permission policy, a daily budget and a kill switch.

## Run (your own machine — needed for the background loop to keep running)
```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml     # fill in ANTHROPIC_API_KEY + access_code
streamlit run app.py
```

## What is in Phase 1
| Module | Role |
|---|---|
| `core/brain.py` | reflect on chats -> lessons; idle thinking; writes skills; proposes ideas |
| `core/scheduler.py` | background thread that wakes the brain every N minutes (only while the app process runs) |
| `core/sandbox.py` | AST allowlist + isolated subprocess + rlimits/timeout for AI-written code |
| `core/safety.py` | permission policy (allow / approval / deny), kill switch, daily budget, secret redaction |
| `core/store.py` | SQLite: events, lessons, skills, tasks, settings, usage (`data/zyphere.db`) |
| `core/commands.py` | `/status /auto on|off /kill /resume /think /learn /skills /lessons` (also spoken: "หยุดฉุกเฉิน") |
| `core/voice.py` | microphone -> text (SpeechRecognition / Google web endpoint, needs internet) |

## Safety model
* AI may on its own: think, note lessons, write + test skills **inside the sandbox**.
* Anything else (ideas, files, network, devices, self-modification) becomes a proposal that waits for **Approve**.
* Unknown actions are denied. An unattended run never overwrites an existing skill.
* Autonomous calls stop at the daily cap; **EMERGENCY STOP** / `/kill` stops all autonomous activity and survives restarts.
* The sandbox is defence in depth for pure-computation helpers, not a hardened jail.

## Honest limits
* "Learning" = lessons + skills stored by this app. The model's weights are never changed.
* On Streamlit Community Cloud the app sleeps and its disk resets: use Cognition -> Backup, and don't expect 24/7 loops.
* No machine/device control yet (Phase 2: approval-gated device layer).
