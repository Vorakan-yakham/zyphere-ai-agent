"""Book Value Audit — honest measurement: does each book's REAL content
justify its REAL price? No claims without numbers. Flags thin books and gives
a concrete fix (reprice or enrich) rather than marketing language.
"""
import os, re, json, time, hashlib

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "book_value_audit.json")
OUT = os.path.join(ROOT, "governance", "BOOK_VALUE_AUDIT.md")
CACHE_MAX = 6 * 3600


def audit(force=False):
    if not force and os.path.exists(DATA):
        c = json.load(open(DATA, encoding="utf-8"))
        if time.time() - c.get("t", 0) < CACHE_MAX:
            return c
    import storefront_rebuild as SR
    import sample_publisher as SP
    import autonomous_council as AC

    products = SR.load_products()
    folders = SP.source_map()
    rows = []
    for p in products:
        title = str(p.get("title") or "").strip()
        price = int(p.get("price") or 0)
        folder = folders.get(title)
        md = AC.gh_raw("books/%s/content.md" % folder) if folder else ""
        if not md:
            rows.append({"title": title, "price": price, "ok": False,
                         "why": "no real source"})
            continue
        chapters = re.findall(r"^## บทที่\s+\d+", md, re.M)
        thai = len(re.findall(r"[\u0E00-\u0E7F]", md))
        words = len(re.findall(r"\S+", md))
        sections = len(re.findall(r"^### ", md, re.M))
        exercises = len(re.findall(r"แบบฝึกหัด", md))
        summaries = len(re.findall(r"^### สรุป", md, re.M))
        # uniqueness: distinct chapter openers (detect copy-paste filler)
        openers = re.findall(r"เป็นหนึ่งในสาขาย่อยของ[^\n]{0,60}", md)
        dup_ratio = 1 - (len(set(openers)) / len(openers)) if openers else 0
        # value metrics — THAI characters are the actual readable content
        per_baht = round(thai / price, 1) if price else 0
        baht_per_1k = round(price / (thai / 1000), 2) if thai else 0
        verdict = ("FAIR" if per_baht >= 220 and dup_ratio < 0.5
                   else "THIN" if thai < 12000 or dup_ratio >= 0.5
                   else "WATCH")
        rows.append({"title": title, "price": price, "ok": True,
                     "chars": len(md), "thai_chars": thai, "words": words,
                     "chapters": len(chapters), "sections": sections,
                     "exercises": exercises, "summaries": summaries,
                     "dup_ratio": round(dup_ratio, 3),
                     "thai_per_baht": per_baht,
                     "baht_per_1k_thai": baht_per_1k,
                     "verdict": verdict})

    ok = [r for r in rows if r.get("ok")]
    summary = {
        "books": len(rows), "real": len(ok),
        "fair": sum(r["verdict"] == "FAIR" for r in ok),
        "thin": sum(r["verdict"] == "THIN" for r in ok),
        "watch": sum(r["verdict"] == "WATCH" for r in ok),
        "min_thai": min((r["thai_chars"] for r in ok), default=0),
        "max_thai": max((r["thai_chars"] for r in ok), default=0),
        "avg_thai_per_baht": round(sum(r["thai_per_baht"] for r in ok) / len(ok), 1) if ok else 0,
        "price_range": [min((r["price"] for r in ok), default=0),
                        max((r["price"] for r in ok), default=0)],
    }
    rec = {"t": int(time.time()), "summary": summary, "rows": rows,
           "method": " Thai characters / price + chapter structure + repeated-opener ratio; "
                     "no sales claims, only real manuscript measurement"}
    json.dump(rec, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    lines = ["# ตรวจความคุ้มค่าของหนังสือ (วัดจากต้นฉับจริง)", "",
             "หนังสือ **%d** เล่ม · มีต้นฉับจริง **%d** · FAIR **%d** · WATCH **%d** · THIN **%d**" %
             (summary["books"], summary["real"], summary["fair"],
              summary["watch"], summary["thin"]), "",
             "- ตัวอักษรไทย: %d–%d ตัว/เล่ม" % (summary["min_thai"], summary["max_thai"]),
             "- เฉลี่ย **%.1f ตัวอักษรไทยต่อบาท**" % summary["avg_thai_per_baht"],
             "- ราคา: ฿%d–฿%d" % tuple(summary["price_range"]), "",
             "| เล่ม | ราคา | ตัวอักษรไทย | บท | ซ้ำ | ไทย/บาท | ผล |",
             "|---|---|---|---|---|---|---|"]
    for r in rows:
        if not r.get("ok"):
            lines.append("| %s | %d | — | — | — | — | ไม่มีต้นฉับ |" %
                         (r["title"], r["price"]))
            continue
        lines.append("| %s | %d | %d | %d | %.0f%% | %d | %s |" %
                     (r["title"], r["price"], r["thai_chars"], r["chapters"],
                      r["dup_ratio"] * 100, r["thai_per_baht"], r["verdict"]))
    lines += ["", "หมายเหตุ: วัดปริมาณ/โครงสร้าง ไม่ใช่คุณภาพทางวิชาการ — "
              "ถ้าซ้ำสูงแปลว่าเนื้อหา template ซ้ำกัน ต้องเขียนเพิ่มหรือลดราคา", ""]
    open(OUT, "w", encoding="utf-8").write("\n".join(lines))
    return rec


if __name__ == "__main__":
    c = audit()
    print(json.dumps(c["summary"], ensure_ascii=False))
