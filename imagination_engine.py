"""Imagination Engine — user says it in chat; Zyphere imagines the shot.

NO fixed script, NO external image API. The engine reads the natural-language
brief, derives a visual concept (subject, mood, palette, camera, composition,
motion, caption), enriches it with our local/world knowledge, then hands that
direction to our own image lab or cinema studio.

HONEST: 'imagination' = deterministic interpretation + our own algorithmic
rendering. It is not a diffusion model and is never claimed as one.
"""
import os, re, json, time, hashlib

ROOT = os.path.dirname(os.path.abspath(__file__))
STORE = os.path.join(ROOT, "data", "imagination.json")

MOODS = [
    (r"อบอุ่น|แดด|เย็น|golden|sunset|พระอาทิตย์ตก|ทอง", "warm",
     {"base": (42, 22, 16), "accent": [(255, 176, 74), (236, 110, 54)]}),
    (r"สงบ|เย็นสบาย|ทะเล|น้ำ|calm|ocean|sea", "calm",
     {"base": (8, 30, 44), "accent": [(34, 211, 238), (45, 212, 191)]}),
    (r"มืด|ลึกลับ|night|dark|กลางคืน|ดาว", "mystic",
     {"base": (10, 12, 32), "accent": [(139, 120, 246), (80, 180, 240)]}),
    (r"สดใส|ร้อน|พลัง|epic|red|แดง", "bold",
     {"base": (36, 12, 18), "accent": [(239, 68, 68), (250, 204, 21)]}),
]

SUBJECTS = [
    (r"ผู้หญิง|หญิง|woman|girl|ใบหน้า|portrait", "portrait", "portrait silhouette with soft rim light"),
    (r"ทะเล|น้ำตก|แม่น้ำ|ocean|sea|water", "water", "layered water horizon and reflections"),
    (r"ภูเขา|หุบเขา|ทิวเขา|mountain", "mountain", "layered mountain ridges"),
    (r"ดารา|จักรวาล|อวกาศ|space|galaxy|star", "cosmos", "star field and orbital rings"),
    (r"ควอนตัม|อะตอม|quantum|atom|อนุภาค", "quantum", "orbit paths with nodes and superposition rings"),
    (r"เสียง|คลื่น|wave|audio|music", "wave", "multi-frequency waveform lines"),
    (r"ป่า|ต้นไม้|forest|nature", "forest", "vertical trunks with light shafts"),
    (r"เมือง|ตึก|city|urban", "city", "architectural silhouettes and light grids"),
]

CAMERAS = [
    (r"ใกล้|หน้า|close|macro|ระยะสั้น", "close-up", "shallow depth, detail emphasis"),
    (r"กว้าง|วิว|wide|landscape| panorama", "wide", "establishing wide composition"),
    (r"สูง|บิน|drone|aerial|มุมสูง", "aerial", "high angle, layered horizon"),
]


def interpret(brief, kind="auto"):
    t = str(brief or "").strip()
    mood_name, pal = "calm", {"base": (8, 30, 44), "accent": [(34, 211, 238), (45, 212, 191)]}
    for pat, name, p in MOODS:
        if re.search(pat, t, re.I):
            mood_name, pal = name, p
            break
    subj = "abstract"
    motif = "geometric motif from concept"
    for pat, name, m in SUBJECTS:
        if re.search(pat, t, re.I):
            subj, motif = name, m
            break
    cam = "medium"
    cam_note = "balanced framing"
    for pat, name, note in CAMERAS:
        if re.search(pat, t, re.I):
            cam, cam_note = name, note
            break
    want_video = bool(re.search(r"วิดีโอ|คลิป|video|film|เคลื่อนไหว|motion", t, re.I)) or kind == "video"
    # enrich with local + world knowledge, never invent facts
    refs = []
    try:
        import world_knowledge as WK
        r = WK.ask(t)
        refs = [{"source": h.get("source"), "title": h.get("title")}
                for h in r.get("answers", [])[:3]]
    except Exception:
        pass
    try:
        import own_brain
        r2 = own_brain.ask(t, top=2)
        refs += [{"source": "own-brain", "title": str(x.get("text"))[:80]}
                 for x in r2.get("answers", [])]
    except Exception:
        pass
    direction = {
        "brief": t[:240], "kind": "video" if want_video else "image",
        "subject": subj, "motif": motif, "mood": mood_name,
        "palette": pal, "camera": cam, "composition_note": cam_note,
        "motion": "slow Ken Burns push-in" if want_video else "still",
        "caption": t[:80], "references": refs,
        "seed": int(hashlib.md5(t.encode()).hexdigest()[:8], 16),
        "t": int(time.time()),
        "note": "จินตนาการจากคำสั่งผู้ใช้ด้วยสมอง Zyphere — ไม่ใช้ diffusion model",
    }
    return direction


def create(brief, kind="auto", apply=True):
    d = interpret(brief, kind)
    result = {"direction": d, "artefact": None}
    if d["kind"] == "video":
        try:
            import cinema_studio
            r = cinema_studio.run(brief, 18, "th")
            result["artefact"] = {"ok": r.get("ok"), "video": r.get("video"),
                                  "urls": r.get("urls")}
        except Exception as e:
            result["artefact"] = {"ok": False, "error": str(e)[:120]}
    else:
        try:
            import own_image_lab as LAB
            r = LAB.generate(brief, apply=apply)
            result["artefact"] = {"ok": r.get("ok"), "file": r.get("file"),
                                  "quality": r.get("quality")}
        except Exception as e:
            result["artefact"] = {"ok": False, "error": str(e)[:120]}
    if apply:
        os.makedirs(os.path.dirname(STORE), exist_ok=True)
        db = {"items": []}
        if os.path.exists(STORE):
            try:
                db = json.load(open(STORE, encoding="utf-8"))
            except Exception:
                pass
        db["items"].append(result)
        db["items"] = db["items"][-80:]
        json.dump(db, open(STORE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return result


if __name__ == "__main__":
    r = create("ภาพหญิงสายลมยามเย็น กล้องระยะใกล้", apply=False)
    print(json.dumps({"direction": r["direction"], "artefact": r["artefact"]},
                     ensure_ascii=False)[:900])
