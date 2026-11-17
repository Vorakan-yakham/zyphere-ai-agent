"""Zyphere Visualizer - turn knowledge/status into a downloadable chart image
(JARVIS trait: show information visually, but owner asked: no inline media in
chat -> produce a downloadable PNG instead). Uses Pillow, offline.
"""
import os, math


def make_chart(path, title="Zyphere Status", bars=None, width=1000, height=600):
    """Generate a simple bar chart PNG (downloadable, not inline)."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        return {"ok": False, "error": "Pillow unavailable"}
    bars = bars or []
    im = Image.new("RGB", (width, height), (248, 249, 251))
    d = ImageDraw.Draw(im)
    try:
        f_title = ImageFont.truetype("arial.ttf", 34)
        f = ImageFont.truetype("arial.ttf", 24)
    except Exception:
        f_title = f = ImageFont.load_default()
    d.text((40, 30), title, fill=(32, 33, 36), font=f_title)
    d.line([(40, 85), (width - 40, 85)], fill=(218, 220, 224), width=2)
    if not bars:
        d.text((40, 140), "ไม่มีข้อมูลแสดงผล", fill=(95, 99, 104), font=f)
    else:
        n = min(len(bars), 10)
        maxv = max([float(b.get("value", 0)) for b in bars] + [1])
        base = height - 70
        avail = width - 140
        bw = avail / n * 0.6
        gap = avail / n
        for i, b in enumerate(bars):
            v = float(b.get("value", 0))
            h = (v / maxv) * (height - 200)
            x = 70 + i * gap + (gap - bw) / 2
            y = base - h
            d.rectangle([x, y, x + bw, base], fill=(26, 115, 232))
            label = str(b.get("label", ""))[:12]
            d.text((x, base + 8), label, fill=(95, 99, 104), font=f)
            d.text((x, y - 32), str(int(v)), fill=(32, 33, 36), font=f)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path, "PNG")
    return {"ok": True, "path": path, "size": os.path.getsize(path)}


def status_bars(data):
    """Convert a status dict to chart bars."""
    out = []
    for k in ("facts", "rules", "documents", "works", "skills", "languages"):
        if k in (data or {}):
            try:
                out.append({"label": k, "value": float(data[k])})
            except Exception:
                pass
    return out
