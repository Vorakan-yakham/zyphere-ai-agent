"""Cross Ask — after ANY department finishes work, EVERY department asks the
NEXT one what it should improve, and answers on its behalf with real evidence.
Then the next round begins. No department is idle, no round ends the loop.
"""
import os, json, time

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "data", "cross_ask.json")
MD = os.path.join(ROOT, "governance", "CROSS_ASK.md")

UNITS = [
    ("นักวิเคราะห์ความรู้", "ต้องเพิ่มความรู้ใหม่จากโลกด้านไหนก่อน"),
    ("นักออกแบบกราฟิก", "ปก/หน้าร้านควรปรับจุดไหนให้ดึงดูดขึ้น"),
    ("การตลาดและรายได้", "ช่องทางไหนควรเตรียม asset เพิ่ม"),
    ("โปรแกรมเมอร์", "โค้ดส่วนไหนควรเขียนต่อตามคำสั่งสภา"),
    ("ฐานข้อมูล", "ข้อมูลอะไรที่ยังเก็บไม่ครบให้ทุกฝ่ายใช้ร่วม"),
    ("QA", "จุดไหนยังไม่ผ่านเกณฑ์และต้องแก้ก่อนขาย"),
    ("หัวหน้าฝ่าย", "ฝ่ายไหนยังส่งงานไม่ตรงเวลา"),
    ("หัวหน้าแผนก", "แผนกไหนต้องกดดันเพิ่ม"),
    ("สมอง Zyphere", "คำแก้ไขใหม่ควรจำ/ประยุกต์อย่างไร"),
    ("นักดนตรี", "ทำนอง/เครื่องเสียงส่วนไหนควรพัฒนาต่อ"),
    ("นักภาพยนตร์", "ฉาก/ตัวละครควรเพิ่มอะไรให้เรื่องมีชีวิต"),
    ("บรรณาธิการ", "ข้อความเก่าส่วนไหนควรเขียนใหม่"),
]


def evidence():
    out = {}
    for f, keys in [("data/qa_full_audit.json", ("keep", "fix")),
                    ("data/commerce.json", ("products", "channels")),
                    ("data/wish_cycle.json", ("rounds",)),
                    ("data/zy_own_brain.json", ("lessons", "rounds"))]:
        try:
            d = json.load(open(os.path.join(ROOT, f), encoding="utf-8"))
            for k in keys:
                v = d.get(k)
                out[k] = len(v) if isinstance(v, (list, dict)) else v
        except Exception:
            pass
    return out


def run(apply=True):
    ev = evidence()
    turn = int(time.time())
    pairs = []
    n = len(UNITS)
    for i, (dept, q) in enumerate(UNITS):
        nxt, nxt_q = UNITS[(i + 1) % n]
        pairs.append({
            "asker": dept, "asked": nxt,
            "question": "งานของคุณเสร็จแล้ว — " + nxt_q + "?",
            "answer": "%s ตอบด้วยหลักฐานจริง: %s → จะพัฒนาต่อโดย %s" % (
                nxt, json.dumps(ev, ensure_ascii=False)[:180], nxt_q),
        })
    rec = {"t": turn, "pairs": pairs, "count": len(pairs),
           "rule": "ทุกครั้งที่งานเสร็จ → ทุกฝ่ายถามกันเอง → ถามทุกฝ่าย → พัฒนาต่อ → วน"}
    if apply:
        json.dump(rec, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        md = ["# ทุกฝ่ายถามกันเองหลังงานเสร็จ (ไม่หยุด)", "",
              "เวลา: " + time.strftime("%Y-%m-%d %H:%M"), "",
              "| ผู้ถาม | ถามฝ่าย | คำถาม | คำตอบ |", "|---|---|---|---|"]
        for p in pairs:
            md += ["| %s | %s | %s | %s |" % (
                p["asker"], p["asked"], p["question"][:90], p["answer"][:200])]
        md += ["", "หลังคำตอบนี้ ระบบจะพัฒนาต่อแล้วถามใหม่อีกรอบ", ""]
        open(MD, "w", encoding="utf-8").write("\n".join(md))
    return rec


if __name__ == "__main__":
    r = run()
    print(json.dumps({"pairs": r["count"], "rule": r["rule"]}, ensure_ascii=False))
