# Zyphere - Fix Login 405 LocalStorage Only

## Fix 405
Login / Signup / API Key save no longer calls server API.
On GitHub Pages (static) it no longer hits 405 - login proceeds instantly.
- Button "เข้าใช้งานเลย ไม่ต้อง Login" - instant entry
- Button "เข้าสู่ระบบด้วยบัญชี Whisp (เดโม)" - instant as Whisp
- Gmail / Email - works even if empty, auto guest@

## Brains (Auto-Save)
1 Grok (xai-), 2 Gemini (AIza), 3 OpenRouter (sk-or-), 4 Hugging Face (hf_)
Paste key -> shows ✓ บันทึกอัตโนมัติแล้ว instantly

## Sidebar
Tab hides to 64px icon rail, Logo click toggles 280px <-> 64px
Icons animate on hover, logo spins

## Upload
Upload index.html + app.py + requirements.txt to Vorakan-yakham/zyphere-ai-agent, Replace old files, wait 1-2 min, Ctrl+Shift+R
Keys stay in browser only, never uploaded to GitHub.
