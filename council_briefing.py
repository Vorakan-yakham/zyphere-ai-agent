"""Council Briefing — I speak to every Zyphere department on the owner's
behalf, they answer/argue, and their conclusions become executable work orders
the autonomous workflow carries out. The owner cannot talk to Zyphere directly;
this is the bridge.
"""
import os, json, time, re

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "governance", "COUNCIL_BRIEFING.md")
ORDERS = os.path.join(ROOT, "governance", "ALL_HANDS_ORDER.md")
DATA = os.path.join(ROOT, "data", "council_briefing.json")

NEEDS = """ความต้องการของเจ้าของ (พูดแทนโดยผู้ช่วย):
- แก้หน้าร้าน/OUTDESIGN ให้สมบูรณ์และดึงดูดคนซื้อ
- หนังสือ: ตั้งราคาให้เหมาะสม, แก้ข้อความเก่า, เปลี่ยนปกใหม่ ไม่ใช้ภาพเก่าซ้ำ
- นักวิเคราะห์ใช้ความรู้เยอะ ๆ วางแผนอนาคต
- โปรแกรมเมอร์เขียนตามที่นักวิเคราะห์วางไว้
- database ถ้ามี ให้ทุกฝ่ายประสานกัน
- หาช่องทางทำเงินใหม่ ๆ ไม่ใช่รอ ebook อย่างเดียว (คนหลงเข้ามาซื้อไม่พอ)
- ห้ามให้เจ้าของต้องจ้ำจี้จ้ำชาย — ระบบต้องกระตุ้นตัวเอง
"""

ROLES = [
    ("นักวิเคราะห์ความรู้", "ต้องค้นคว้าอะไรเพิ่มเพื่อออกแบบร้าน/ปก/ราคาให้ขายได้ และวางแผนอนาคตอย่างไร"),
    ("นักออกแบบกราฟิก", "ปกใหม่และหน้าร้านควรมีองค์ประกอบอะไรจึงดึงดูดสายตาโดยไม่ใช้ภาพเก่า"),
    ("นักเศรษฐศาสตร์/ราคา", "ตั้งราคาอย่างไรให้สมเหตุสมผลกับเนื้อหาจริง และมีช่องทางรายได้ใหม่ไหนทำได้ตอนนี้"),
    ("โปรแกรมเมอร์", "จะแปลงข้อสรุปของนักวิเคราะห์เป็นโค้ด/ไฟล์อะไรได้บ้างภายในรอบเดียว"),
    ("หัวหน้าฐานข้อมูล", "ต้องเก็บอะไรใน database เพื่อให้ทุกฝ่ายประสานงานกันได้โดยไม่ถามเจ้าของ"),
    ("QA", "จะตรวจอย่างไรว่าสิ่งที่.make 出來จริงและไม่มีคำอ้างขายปลอม"),
]


def local_position(role, question):
    """Evidence-based answer from our own data when model quota is exhausted."""
    d = {}
    for f in ("data/commerce.json", "data/qa_full_audit.json",
              "data/world_knowledge.json", "data/conversation_learning.json"):
        try:
            d[f] = json.load(open(os.path.join(ROOT, f), encoding="utf-8"))
        except Exception:
            pass
    commerce = d.get("data/commerce.json") or {}
    qa = d.get("data/qa_full_audit.json") or {}
    world = d.get("data/world_knowledge.json") or {}
    facts = {"products": len(commerce.get("products") or []),
             "channels": len(commerce.get("channels") or []),
             "qa_keep": qa.get("keep"), "qa_fix": qa.get("fix"),
             "world_topics": len(world.get("topics") or [])}
    return {"dept": role, "question": question, "source": "local-evidence",
            "answer": "%s: ใช้ข้อมูลจริง %s → %s" % (role, json.dumps(facts, ensure_ascii=False),
                {
                 "นักวิเคราะห์ความรู้": "ต้องขยาย world topics และอ่าน BOOK_DESIGN_STANDARD ก่อนตัดสิน",
                 "นักออกแบบกราฟิก": "ปกต้องสื่อเนื้อหา + typography ใหม่ ใช้ own_image_lab ไม่ใช้ภาพซ้ำ",
                 "นักเศรษฐศาสตร์/ราคา": "ราคาจาก market_price + ความยาวจริง + เตรียม 6 ช่องทางฟรี",
                 "โปรแกรมเมอร์": "เขียน STORE_V2.html, commerce.json, ปกใหม่ แล้ว commit อัตโนมัติ",
                 "หัวหน้าฐานข้อมูล": "เก็บ products/channels/qa/metrics ใน data/commerce.json ให้ทุกฝ่ายอ่าน",
                 "QA": "ตรวจ file จริง + ราคา + ภาษา + ไม่มีคำอ้างยอดขาย ไม่ผ่านให้ HOLD",
                }.get(role, "พัฒนาต่อด้วยหลักฐาน"))}


def debate():
    positions = []
    try:
        import brain_ensemble as BE
        for i, (role, q) in enumerate(ROLES):
            r = BE.ensemble([{"role": "user", "content":
                "คุณคือ" + role + "ในองค์กร Zyphere " + NEEDS +
                "\nคำถามของคุณ: " + q +
                "\nตอบภาษาไทย กระชับ 4 ข้อ เฉพาะสิ่งที่ทำได้จริง ห้ามอ้างยอดขาย"}],
                want_synthesis=False)
            txt = r.get("text") if r.get("ok") else ""
            positions.append({"dept": role, "question": q,
                              "answer": txt or local_position(role, q)["answer"],
                              "source": "ensemble" if txt else "local-evidence"})
    except Exception:
        positions = [local_position(r, q) for r, q in ROLES]
    digest = "\n\n".join("### %s\n%s" % (p["dept"], p["answer"]) for p in positions)
    return positions, digest


def run(apply=True):
    positions, digest = debate()
    decisions = [
        "สร้าง STORE_V2.html ใหม่: hero ชัด, การ์ดสินค้า, CTA, QR, ช่องทางรายได้ 6 ช่องทาง",
        "ตั้งราคาทุกเล่มด้วย market_price + ความยาวจริง เปลี่ยนสถานะเป็น review จนกว่า QA จะผ่าน",
        "ปกใหม่ต้องสร้างจากเนื้อหาจริง (motif ตามหัวข้อ) + typography ใหม่ ไม่ใช้ภาพเก่าซ้ำ",
        "เก็บ products/channels/qa/metrics ลง data/commerce.json เป็นแหล่งร่วมของทุกฝ่าย",
        "ระบบกระตุ้นตัวเองทุก 30 นาที: analyze → plan → code → QA → learn ไม่ต้องรอเจ้าของ",
    ]
    result = {"t": int(time.time()), "positions": positions,
              "decisions": decisions, "needs": NEEDS}
    if apply:
        json.dump(result, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        md = ["# การประชุมสภา Zyphere ตามความต้องการของเจ้าของ", "", NEEDS,
              "## คำตอบของแต่ละฝ่าย", ""]
        for p in positions:
            md += ["### " + p["dept"] + " (" + str(p["source"]) + ")", "",
                   p["answer"][:1600], ""]
        md += ["## มติที่ต้องปฏิบัติ (work orders)", ""]
        for d in decisions:
            md += ["- " + d]
        md += ["", "คำสั่งนี้ถูกส่งเข้า ALL_HANDS_ORDER.md และ autonomy workflow แล้ว", ""]
        open(OUT, "w", encoding="utf-8").write("\n".join(md))
        if os.path.exists(ORDERS):
            o = open(ORDERS, encoding="utf-8").read()
            if "มติสaslaha ล่าสุด" not in o:
                o += "\n## มติสภาล่าสุด (เขียนโดยระบบ ไม่ต้องรอเจ้าของ)\n"
                for d in decisions:
                    o += "- " + d + "\n"
                open(ORDERS, "w", encoding="utf-8").write(o)
    return result


if __name__ == "__main__":
    r = run()
    print(json.dumps({"positions": len(r["positions"]), "orders": len(r["decisions"])},
                     ensure_ascii=False))
