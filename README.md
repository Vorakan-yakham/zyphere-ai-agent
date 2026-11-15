# ⚡ Zyphere Autonomous Executive OS

Streamlit app with 4-axis routing (Knowledge/Full-Stack, Aerospace/CAD, Robotics, Content), Claude-powered
analysis, Deep Analysis mode, file/PDF/image attachments, persistent memory and optional Thai voice.

## Run locally
```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # then edit it
streamlit run app.py
```

## Secrets (required)
| Key | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API key (console.anthropic.com) |
| `access_code` | Passphrase needed at login (protects your API credits) |
| `allowed_emails` | Optional list of permitted emails |

On Streamlit Community Cloud: App → Settings → Secrets. Never commit `secrets.toml`.

> `data/memory.json` is ephemeral on Streamlit Cloud (reset on restart).
