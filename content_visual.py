"""Content-Aware Visuals — cover art derived from the book's ACTUAL text.

The visual engineer reads the source chapter headings/keywords and draws a
motif for those concepts (waveform, orbit, lattice, helix, network...). No
generic silhouette, no external API. The chosen keywords are stored in the
cover metadata so editors can verify relevance.
"""
import re, math, hashlib
from PIL import Image, ImageDraw, ImageFilter

MOTIFS = [
    ("wave", r"wave|oscill|frequency|spectrum|คลื่น|ความถี่"),
    ("orbit", r"orbit|quantum|electron|atom|superposition|ควอนตัม|อิเล็กตรอน|วงโคจร"),
    ("lattice", r"lattice|crystal|structure|grid|โครงสร้าง|ผลึก"),
    ("helix", r"helix|dna|gene|cell|พันธุกรรม|เซลล์|จีน"),
    ("network", r"network|node|graph|neural|ai|algorithm|โครงข่าย|โปรแกรม"),
    ("cosmos", r"star|galaxy|cosmos|universe|ดารา|จักรวาล"),
]


def analyse(md):
    heads = [re.sub(r"^#+\s*", "", ln).strip() for ln in md.splitlines()
             if re.match(r"(?m)^#{2,4} ", ln)][:24]
    text = " ".join(heads) + " " + md[:12000]
    found = []
    for name, pat in MOTIFS:
        if re.search(pat, text, re.I):
            found.append(name)
    words = []
    for h in heads:
        for w in re.findall(r"[A-Za-z]{4,}", h):
            if w.lower() not in [x.lower() for x in words]:
                words.append(w)
    return {"motifs": found or ["abstract"], "keywords": words[:8], "headings": heads[:8]}


def draw_wave(d, w, h, c):
    for k in range(3):
        pts = []
        for x in range(0, w, 8):
            y = int(h*0.52 + (k-1)*70*math.sin(x/95.0 + k) + 18*math.sin(x/23.0))
            pts.append((x, y))
        d.line(pts, fill=(*c, 190 - k*45), width=3)


def draw_orbit(d, w, h, c):
    cx, cy = int(w*.5), int(h*.47)
    for r in (110, 190, 280, 370):
        d.ellipse((cx-r, cy-r//2, cx+r, cy+r//2), outline=(*c, 120), width=2)
    for i in range(9):
        a = 2*math.pi*i/9
        x, y = cx + 280*math.cos(a), cy + 140*math.sin(a)
        d.ellipse((x-5, y-5, x+5, y+5), fill=(*c, 230))


def draw_lattice(d, w, h, c):
    for x in range(80, w-60, 92):
        for y in range(int(h*.25), int(h*.72), 92):
            d.rectangle((x-16, y-16, x+16, y+16), outline=(*c, 90), width=2)
            d.ellipse((x-3, y-3, x+3, y+3), fill=(*c, 200))


def draw_helix(d, w, h, c):
    for step in range(90):
        y = int(h*.22 + step*8)
        if y > h*.75:
            break
        x1 = int(w*.5 + 130*math.sin(step/9.0))
        x2 = int(w*.5 - 130*math.sin(step/9.0))
        d.ellipse((x1-7, y-7, x1+7, y+7), fill=(*c, 220))
        d.ellipse((x2-7, y-7, x2+7, y+7), fill=(*((c[0]//2+60, c[1], c[2])), 220))
        d.line((x1, y, x2, y), fill=(*c, 80), width=2)


def draw_network(d, w, h, c):
    import random
    rnd = random.Random(7)
    pts = [(rnd.randrange(90, w-90), rnd.randrange(int(h*.24), int(h*.72)))
           for _ in range(34)]
    for i, p in enumerate(pts):
        for q in pts[i+1:]:
            if abs(p[0]-q[0]) + abs(p[1]-q[1]) < 180:
                d.line((p, q), fill=(*c, 60), width=1)
        d.ellipse((p[0]-5, p[1]-5, p[0]+5, p[1]+5), fill=(*c, 210))


def draw_cosmos(d, w, h, c):
    import random
    rnd = random.Random(11)
    for _ in range(130):
        x, y = rnd.randrange(w), rnd.randrange(int(h*.2), int(h*.78))
        r = rnd.choice((1, 1, 2, 3))
        d.ellipse((x-r, y-r, x+r, y+r), fill=(255, 245, 220, rnd.randrange(120, 240)))
    cx, cy = int(w*.72), int(h*.28)
    d.ellipse((cx-70, cy-70, cx+70, cy+70), outline=(*c, 180), width=3)


DRAW = {"wave": draw_wave, "orbit": draw_orbit, "lattice": draw_lattice,
        "helix": draw_helix, "network": draw_network, "cosmos": draw_cosmos}


def render(md, base=None, accent=(34, 211, 238)):
    info = analyse(md)
    img = base.copy() if base is not None else Image.new("RGB", (1200, 1500), (8, 24, 38))
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for m in info["motifs"][:2]:
        if m in DRAW:
            DRAW[m](d, img.width, img.height, accent)
    lay = lay.filter(ImageFilter.GaussianBlur(0.6))
    img = Image.alpha_composite(img.convert("RGBA"), lay).convert("RGB")
    return img, info
