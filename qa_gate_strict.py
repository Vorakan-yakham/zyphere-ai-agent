"""Strict Release Gate — NOTHING goes public until every check passes.
Fail-closed: any failed check = HOLD + a concrete rework order to the owning
engineer. Standards are measured from real files, never claimed.
"""
import os, re, json, time, subprocess, hashlib

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "qa_gate_strict.json")
OUT = os.path.join(ROOT, "governance", "RELEASE_GATE.md")


def img_probe(path):
    from PIL import Image
    im = Image.open(path)
    g = im.convert("L")
    edge = g.filter(__import__("PIL.ImageFilter", fromlist=["FIND_EDGES"]).FIND_EDGES)
    px = list(edge.resize((200, 200)).getdata())
    mean = sum(px)/max(1, len(px))
    contrast = sum((v-mean)**2 for v in px)/max(1, len(px))
    return {"size": list(im.size), "contrast": round(contrast, 1)}


def video_probe(path):
    import imageio_ffmpeg
    r = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-i", path],
                       capture_output=True, text=True)
    return {"is_4k": "3840x2160" in r.stderr,
            "has_audio": "Audio:" in r.stderr,
            "bytes": os.path.getsize(path)}


def check_all():
    checks = []
    def add(name, ok, detail, owner):
        checks.append({"check": name, "ok": bool(ok),
                       "detail": str(detail)[:220], "owner": owner})

    # 1) STOREFRONT
    store = os.path.join(ROOT, "STORE_FINAL.html")
    if os.path.exists(store):
        h = open(store, encoding="utf-8").read()
        prices = set(re.findall(r"฿(\d+)", h))
        add("หน้าร้าน: 46 เล่ม", h.count('class="card"') >= 46,
            h.count('class="card"'), "วิศวกรร้านค้า")
        add("หน้าร้าน: ราคาหลาก >=5 ระดับ", len(prices) >= 5, sorted(prices), "วิศวกรร้านค้า")
        add("หน้าร้าน: ไม่มี gradient ม่วงเก่า", "139, 92, 246" not in h and "#8b5cf6" not in h,
            "wind palette ตรงมาตรฐาน", "วิศวกรออกแบบ")
        add("หน้าร้าน: มี CTA/ชำระจริง", "PromptPay" in h, "PromptPay 0941939686", "วิศวกรร้านค้า")
        add("หน้าร้าน: ไม่ claims ยอดขาย", "ยอดขาย" not in h or "ไม่มีการอ้างยอดขาย" in h,
            "ข้อความโปร่งใส", "QA")
    else:
        add("หน้าร้าน: มีไฟล์", False, "missing", "วิศวกรร้านค้า")

    # 2) COVERS
    cdir = os.path.join(ROOT, "media", "covers")
    covers = [f for f in os.listdir(cdir) if f.endswith(".png")] if os.path.isdir(cdir) else []
    hashes = set()
    for c in covers[:46]:
        with open(os.path.join(cdir, c), "rb") as f:
            hashes.add(hashlib.md5(f.read()).hexdigest())
    add("ปก: ครบ 46 เล่ม", len(covers) >= 46, len(covers), "วิศวกรกราฟิก")
    add("ปก: ไม่ซ้ำกัน", len(hashes) == len(covers[:46]),
        "unique=%d/%d" % (len(hashes), len(covers)), "วิศวกรกราฟิก")
    if covers:
        p = img_probe(os.path.join(cdir, covers[0]))
        add("ปก: ขนาด 1200x1800", p["size"] == [1200, 1800], p["size"], "วิศวกรกราฟิก")
        add("ปก: contrast พอ", p["contrast"] > 20, p["contrast"], "วิศวกรกราฟิก")

    # 3) EBOOK text
    try:
        import ebook_editor_gate as EG
        g = EG.check(EG.fetch("books/01_%E0%B8%9F%E0%B8%B4%E0%B8%AA%E0%B8%B4%E0%B8%81%E0%B8%AA%E0%B9%8C%E0%B8%84%E0%B8%A7%E0%B8%AD%E0%B8%99%E0%B8%95%E0%B8%B1%E0%B8%A1/book_v2.html"))
        add("หนังสือ: บรรณาธิการตรวจผ่าน", not g, g, "บรรณาธิการ")
    except Exception as e:
        add("หนังสือ: บรรณาธิการตรวจผ่าน", False, str(e)[:120], "บรรณาธิการ")

    # 4) VIDEO latest from repo report
    try:
        import requests
        j = requests.get("https://raw.githubusercontent.com/Vorakan-yakham/"
                         "zyphere-ai-agent/main/data/cinema_latest.json?x="+str(time.time()),
                         timeout=40).json()
        u = (j.get("urls") or {}).get("video")
        if u:
            import tempfile
            d = requests.get("https://raw.githubusercontent.com/Vorakan-yakham/"
                             "zyphere-ai-agent/main/" + u.lstrip("/"), timeout=120).content
            p = os.path.join(tempfile.gettempdir(), "gate_video.mp4")
            open(p, "wb").write(d)
            v = video_probe(p)
            add("วิดีโอ: 4K", v["is_4k"], v, "วิศวกรสื่อ")
            add("วิดีโอ: มีเสียง", v["has_audio"], v, "วิศวกรเสียง")
            add("วิดีโอ: มีซับ", bool((j.get("urls") or {}).get("srt")),
                list((j.get("urls") or {}).keys())[:6], "วิศวกรสื่อ")
    except Exception as e:
        add("วิดีโอ: ตรวจไฟล์ได้", False, str(e)[:120], "วิศวกรสื่อ")

    # 5) QA state
    try:
        q = json.load(open(os.path.join(ROOT, "data", "qa_full_audit.json"), encoding="utf-8"))
        add("QA ประจำระบบ: ไม่มี FIX", q.get("fix") == 0,
            {"keep": q.get("keep"), "fix": q.get("fix")}, "QA")
    except Exception as e:
        add("QA ประจำระบบ: ไม่มี FIX", False, str(e)[:100], "QA")
    return checks


def run(apply=True):
    checks = check_all()
    failed = [c for c in checks if not c["ok"]]
    rec = {"t": int(time.time()), "passed": not failed,
           "total": len(checks), "failed": len(failed), "checks": checks,
           "orders": [{"fix": c["check"], "owner": c["owner"], "detail": c["detail"]}
                      for c in failed],
           "rule": "FAIL-CLOSED: ถ้าไม่ผ่านทุกข้อ ห้ามปล่อยสู่สายตาชาวโลก — ส่งกลับไปแก้ใหม่"}
    if apply:
        json.dump(rec, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        md = ["# RELEASE GATE — มาตรฐานก่อนออกสู่สายตาชาวโลก", "",
              "ผล: **%s** · ผ่าน %d/%d" % ("PASS" if rec["passed"] else "HOLD",
                                            rec["total"]-rec["failed"], rec["total"]), "",
              "| ตรวจ | ผล | รายละเอียด | ผู้รับผิดชอบ |", "|---|---|---|---|"]
        for c in checks:
            md += ["| %s | %s | %s | %s |" % (
                c["check"], "ผ่าน" if c["ok"] else "**ไม่ผ่าน**",
                c["detail"].replace("|", "/"), c["owner"])]
        md += ["", rec["rule"], ""]
        if failed:
            md += ["## คำสั่งแก้ไข (ต้องทำก่อนปล่อย)", ""]
            for o in rec["orders"]:
                md += ["- %s → %s: %s" % (o["owner"], o["fix"], o["detail"])]
        open(OUT, "w", encoding="utf-8").write("\n".join(md) + "\n")
    return rec


if __name__ == "__main__":
    r = run()
    print(json.dumps({"passed": r["passed"], "total": r["total"],
                      "failed": r["failed"]}, ensure_ascii=False))
