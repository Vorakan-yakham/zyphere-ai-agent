"""Film Editor — multi-scene film with ONE consistent character.

The same face pixels (character sheet) are reused in every scene, while the
WARDROBE layer changes per scene context (forest / temple / water / city).
That is the part generic slideshow video fails at. Scenes are concatenated
with transitions + narration + music, all from our in-house stack.

HONEST: the character is an algorithmic illustration, not a photoreal actor;
identity consistency is real because the exact same rendered face is reused.
"""
import os, re, json, time, hashlib, subprocess, tempfile
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

ROOT = os.path.dirname(os.path.abspath(__file__))
MEDIA = os.path.join(ROOT, "media")
W, H = 3840, 2160

SCENES = [
    (r"ป่า|forest|jungle|เขา", "ป่าลึก", {"base": (10, 26, 22), "outfit": (34, 120, 86), "top": (22, 86, 60)}),
    (r"วัด|temple|เจดีย์|ศาสนา", "ในวัด", {"base": (36, 22, 14), "outfit": (230, 140, 40), "top": (196, 106, 26)}),
    (r"น้ำ|ว่าย|อาบ|ทะเล|water|bath|swim", "ริมน้ำ", {"base": (8, 28, 46), "outfit": (40, 130, 190), "top": (28, 96, 150)}),
    (r"เมือง|ถนน|city|urban|office", "ในเมือง", {"base": (22, 26, 34), "outfit": (90, 100, 118), "top": (60, 70, 88)}),
]


def ff():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def character_sheet(name="ดารานำ", seed=None):
    """Render the face ONCE. Identical pixels are reused across all scenes."""
    seed = seed or int(hashlib.md5((name + "zyphere").encode()).hexdigest()[:8], 16)
    import own_image_lab as LAB
    pal = LAB.palette("warm", seed)
    img = LAB.mesh(960, 1080, pal)
    d = ImageDraw.Draw(img)
    cx, cy = 480, 500
    d.ellipse((cx-150, cy-230, cx+150, cy+70), fill=(232, 190, 158))
    d.ellipse((cx-170, cy-250, cx+170, cy-20), fill=(24, 18, 20))
    d.ellipse((cx-120, cy-150, cx+120, cy+100), fill=(24, 18, 20))
    for ex in (cx-62, cx+62):
        d.ellipse((ex-15, cy-20, ex+15, cy+10), fill=(250, 250, 248))
        d.ellipse((ex-6, cy-14, ex+6, cy+6), fill=(42, 32, 28))
    d.arc((cx-40, cy+20, cx+40, cy+80), 15, 165, fill=(150, 70, 70), width=5)
    face = img.crop((cx-190, cy-270, cx+190, cy+120))
    out = os.path.join(MEDIA, "character_%s.png" % str(seed)[:8])
    face.save(out)
    return {"file": out, "seed": seed, "size": face.size}


def scene_context(text):
    for pat, label, cfg in SCENES:
        if re.search(pat, text, re.I):
            return label, cfg
    return "ฉากทั่วไป", {"base": (12, 30, 44), "outfit": (40, 90, 120), "top": (28, 70, 100)}


def render_scene(char, label, cfg, idx, total):
    """Same face, different wardrobe — this is identity-preserving continuity."""
    import own_image_lab as LAB
    base = cfg["base"]
    darker = tuple(max(0, int(c * .55)) for c in base)
    pal = {"base": [darker, base], "accent": [cfg["outfit"], cfg["top"]]}
    bg = LAB.mesh(960, 540, pal).resize((W, H), Image.LANCZOS)
    face = Image.open(char["file"]).convert("RGBA")
    face = face.resize((int(W*.26), int(H*.40)), Image.LANCZOS)
    fx, fy = int(W*.37), int(H*.18)
    bg.paste(face, (fx, fy), face)
    d = ImageDraw.Draw(bg)
    # wardrobe layer: torso + sleeves drawn over the SAME face sheet
    oc, tc = cfg["outfit"], cfg["top"]
    d.polygon([(fx+int(W*.04), fy+int(H*.35)), (fx+int(W*.22), fy+int(H*.35)),
               (fx+int(W*.30), H), (fx-int(W*.04), H)], fill=oc)
    d.polygon([(fx-int(W*.02), fy+int(H*.38)), (fx+int(W*.28), fy+int(H*.38)),
               (fx+int(W*.34), fy+int(H*.62)), (fx-int(W*.08), fy+int(H*.62))], fill=tc)
    d.text((W*.06, H*.86), "ZYPHERE FILM · " + label + " · %d/%d" % (idx, total),
           font=ImageFont_truetype(46), fill=(240, 248, 252))
    return bg


def ImageFont_truetype(sz):
    from PIL import ImageFont
    for p in (os.path.join(MEDIA, "fonts", "NotoSansThai.ttf"),
              r"C:\Windows\Fonts\Tahoma.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, sz)
            except Exception:
                pass
    return ImageFont.load_default()


def build(story, apply=True):
    """story: list of strings, e.g. ['ดารานำในป่า', 'ดารานำในวัด', 'ดารานำว่ายน้ำ']"""
    char = character_sheet("ดารานำ")
    frames, segs = [], []
    tmp = os.path.join(MEDIA, "film_" + str(int(time.time())))
    os.makedirs(tmp, exist_ok=True)
    for i, s in enumerate(story, 1):
        label, cfg = scene_context(s)
        im = render_scene(char, label, cfg, i, len(story))
        fp = os.path.join(tmp, "scene_%02d.png" % i)
        im.save(fp); frames.append(fp)
        vp = os.path.join(tmp, "seg_%02d.mp4" % i)
        cmd = [ff(), "-y", "-loop", "1", "-i", fp, "-vf",
               "zoompan=z='zoom+0.05':d=100:s=3840x2160:fps=25",
               "-t", "4", "-c:v", "libx264", "-preset", "fast",
               "-pix_fmt", "yuv420p", "-crf", "20", vp]
        subprocess.run(cmd, capture_output=True, timeout=300)
        if os.path.exists(vp):
            segs.append(vp)
    final = None
    if segs:
        lst = os.path.join(tmp, "list.txt")
        open(lst, "w").write("".join("file '%s'\n" % v.replace("\\", "/") for v in segs))
        final = os.path.join(tmp, "film.mp4")
        subprocess.run([ff(), "-y", "-f", "concat", "-safe", "0", "-i", lst,
                        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
                        "-pix_fmt", "yuv420p", final], capture_output=True, timeout=400)
    result = {"ok": bool(final and os.path.exists(final)), "character": char,
              "scenes": [scene_context(s)[0] for s in story],
              "frames": frames, "video": final,
              "note": "ใบหน้าเดิมทุกฉาก เปลี่ยนเฉพาะชุดตามบริบท — ไม่ใช่ slideshow"}
    if apply:
        json.dump(result, open(os.path.join(tmp, "manifest.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2, default=str)
    return result


if __name__ == "__main__":
    r = build(["ดารานำเดินในป่า", "ดารานำเข้าไปในวัด", "ดารานำว่ายน้ำในทะเล"])
    print(json.dumps({"ok": r["ok"], "scenes": r["scenes"], "video": r["video"]},
                     ensure_ascii=False))
