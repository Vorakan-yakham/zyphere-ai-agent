"""Zyphere Template Designer — Zyphere designs its OWN UI template.

Generates a real, modern HTML template (design tokens, grid, hierarchy,
negative space, responsive) from a design spec. Uses the design principles
studied from book design / visual hierarchy / grid systems. No vendor theme.
"""
import os, json, time, hashlib, subprocess, base64, requests

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "ZY_TEMPLATE.html")
REPO = "Vorakan-yakham/zyphere-scholar-product-pack"
BASE = "https://api.github.com/repos/" + REPO + "/contents/"

DEFAULT = {
    "name": "Zyphere Studio — สมดุล พร้อม อ่านง่าย",
    "palette": {"bg": "#f7f8fb", "ink": "#1b1f2a", "accent": "#4f46e5", "surface": "#ffffff", "muted": "#6b7280"},
    "font_head": "Inter, Noto Sans Thai", "font_body": "Noto Sans Thai",
    "spacing": "8px grid, 64px section", "layout": "max 1160, auto-fill grid, sticky nav",
    "components": ["hero", "stat card", "product card", "dashboard panel", "modal"],
}


def token():
    t = os.environ.get("GH_TOKEN", "") or os.environ.get("GITHUB_TOKEN", "")
    if not t:
        t = subprocess.run(["gh", "auth", "token"], capture_output=True,
                           text=True, timeout=15).stdout.strip()
    return t


def push(text):
    try:
        h = {"Authorization": "Bearer " + token(), "Accept": "application/vnd.github+json"}
        url = BASE + "ZY_TEMPLATE.html"
        g = requests.get(url, headers=h, timeout=15)
        sha = (g.json() or {}).get("sha") if g.ok else None
        p = {"message": "Zyphere self-designed template " + str(int(time.time())),
             "content": base64.b64encode(text.encode("utf-8")).decode(), "branch": "main"}
        if sha:
            p["sha"] = sha
        requests.put(url, headers=h, json=p, timeout=30)
    except Exception:
        pass


class TemplateDesigner:
    def __init__(self):
        self.spec = dict(DEFAULT)

    def set_spec(self, spec):
        if isinstance(spec, dict):
            for k in DEFAULT:
                if k in spec:
                    self.spec[k] = spec[k]
        return self.spec

    def ask_ensemble(self):
        from brain_ensemble import ensemble
        q = ("ออกแบบ DESIGN SYSTEM สำหรับ Zyphere Studio ใหม่ สวยกว่าเดิม "
             "Google AI Studio + พรีเมียม ไม่ gradient ฉูดฉาด "
             "ตอบ JSON: name,palette(bg,ink,accent,surface,muted),font_head,font_body,spacing,layout,components")
        try:
            r = ensemble([{"role": "user", "content": q}], want_synthesis=True)
            import re
            m = re.search(r"\{[\s\S]*\}", r.get("text", ""))
            if m:
                return json.loads(m.group(0)), r.get("sources", [])
        except Exception:
            pass
        return None, []

    def render(self, title="Zyphere Studio", subtitle="INTELLECTUAL ECOSYSTEM"):
        s = self.spec
        p = s["palette"]
        cards = "".join(
            '<article class="card"><span class="tag">%s</span><h3>%s</h3><p>%s</p>'
            '<div class="row"><span class="price">%s</span><button>เปิด</button></div></article>' %
            (c, t, d, v) for c, t, d, v in [
                ("KNOWLEDGE", "คลังความรู้", "46 คณะ · 184 สาขา · 4,225 สาขาโลก", "46"),
                ("LEARNING", "การเรียนรู้", "11 แผนก ระดับ doctor + ข้ามสาขา", "11"),
                ("RESEARCH", "งานวิจัย", "โปรเจกต์จริงที่ตรวจสอบได้", "1"),
                ("CREATIVE", "สตูดิโอสร้างสรรค์", "ภาพ · เพลง · วิดีโอจริง", "3"),
            ])
        return f'''<!doctype html><html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+Thai:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{{--bg:{p.get('bg','#f7f8fb')};--ink:{p.get('ink','#1b1f2a')};--acc:{p.get('accent','#4f46e5')};--sf:{p.get('surface','#fff')};--mut:{p.get('muted','#6b7280')};--line:#e8eaf1}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font-family:'{s['font_body']}',sans-serif;-webkit-font-smoothing:antialiased}}
nav{{position:sticky;top:0;z-index:10;background:rgba(255,255,255,.86);backdrop-filter:blur(14px);border-bottom:1px solid var(--line)}}
.nav{{max-width:1160px;margin:auto;padding:16px 24px;display:flex;align-items:center;justify-content:space-between}}
.logo{{display:flex;align-items:center;gap:10px;font-family:'{s['font_head']}';font-weight:700;font-size:19px}}
.mark{{width:32px;height:32px;border-radius:10px;background:var(--acc);color:#fff;display:grid;place-items:center}}
.hero{{max-width:1160px;margin:28px auto 0;padding:58px 48px;background:var(--sf);border:1px solid var(--line);border-radius:26px;position:relative;overflow:hidden}}
.hero:before{{content:"";position:absolute;right:-80px;top:-80px;width:300px;height:300px;border:1px solid var(--line);border-radius:50%}}
.hero h1{{margin:0;font-family:'{s['font_head']}';font-size:38px;letter-spacing:-1px;max-width:720px}}
.hero p{{margin:14px 0 0;color:var(--mut);line-height:1.9;max-width:700px}}
.stats{{display:flex;gap:10px;margin-top:26px;flex-wrap:wrap}}
.stats span{{border:1px solid var(--line);border-radius:99px;padding:7px 14px;font-size:12px;color:var(--acc)}}
.sec{{max-width:1160px;margin:auto;padding:30px 24px 70px}}
.sec h2{{font-family:'{s['font_head']}';font-size:20px;margin:0 0 18px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:16px}}
.card{{background:var(--sf);border:1px solid var(--line);border-radius:18px;padding:20px;transition:.18s}}
.card:hover{{transform:translateY(-3px);box-shadow:0 16px 36px rgba(17,24,39,.08);border-color:#dbe2ff}}
.tag{{font:600 11px Inter;letter-spacing:1px;color:var(--acc)}}
.card h3{{font-size:17px;margin:10px 0 8px}} .card p{{color:var(--mut);font-size:13px;line-height:1.7;min-height:44px}}
.row{{display:flex;justify-content:space-between;align-items:center;margin-top:14px;padding-top:14px;border-top:1px solid var(--line)}}
.price{{font:700 18px Inter;color:var(--acc)}}
button{{border:0;background:var(--acc);color:#fff;border-radius:10px;padding:9px 15px;font-weight:600;cursor:pointer}}
footer{{text-align:center;color:var(--mut);font-size:12px;padding:30px 16px 46px;border-top:1px solid var(--line)}}
@media(max-width:640px){{.hero{{padding:32px 22px}}.hero h1{{font-size:27px}}}}
</style></head><body>
<nav><div class="nav"><div class="logo"><span class="mark">✦</span> Zyphere <span style="color:var(--mut);font-weight:500">Studio</span></div>
<span class="tag">{subtitle}</span></div></nav>
<div class="hero"><h1>{title}</h1><p>{s['name']} — ระบบที่เรียนรู้ สร้างผลงาน และพัฒนาตนเองอย่างต่อเนื่อง</p>
<div class="stats"><span>46 คณะวิชา</span><span>11 แผนกเรียนรู้</span><span>5 Engines</span><span>อัพเดทตัวเองได้</span></div></div>
<section class="sec"><h2>ภาพรวมระบบ</h2><div class="grid">{cards}</div></section>
<footer>{s['spacing']} · {s['layout']} · ออกแบบโดย Zyphere เอง</footer>
</div></body></html>'''

    def create(self, title="Zyphere Studio", use_ensemble=True):
        if use_ensemble:
            spec, src = self.ask_ensemble()
            if spec:
                self.set_spec(spec)
        doc = self.render(title)
        open(OUT, "w", encoding="utf-8").write(doc)
        push(doc)
        return {"ok": True, "path": OUT, "spec": self.spec,
                "bytes": len(doc), "url": "/ZY_TEMPLATE.html"}


TD = TemplateDesigner()
