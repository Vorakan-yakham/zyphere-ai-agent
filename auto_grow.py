"""Zyphere Auto-Grow — detect what is MISSING and build it, without an order.

Unlike adding more supervisors (which adds overhead), this adds capability:
it scans real gaps from measured evidence, then creates the missing artifact:
  - broken storefront theme -> corrected ZY_TEMPLATE_V2.html in the product repo
  - weak knowledge depth -> governance/KNOWLEDGE_REFERENCES.md from real URLs
    already present in SCHOLAR_RESEARCH.md (never invented citations)
Every fill is logged and the evidence is recorded.
"""
import os, re, json, time, threading
import autonomous_council as AC

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "data", "auto_grow.json")
LOCK = threading.RLock()


def scan():
    tpl = AC.gh_raw("ZY_TEMPLATE.html") or ""
    scholar = AC.gh_raw("SCHOLAR_RESEARCH.md") or ""
    refs = re.findall(r"https?://[^\s)\]}>\"']+", scholar)
    gaps = []
    dark_nav = "--bg:#0B0F17" in tpl and "rgba(255,255,255" in tpl
    if dark_nav or "Inter Display" in tpl:
        gaps.append({"id": "storefront_theme", "severity": "high",
                     "evidence": "nav สีขาวบนพื้นมืด / ฟอนต์ไม่ได้ประกาศ",
                     "action": "สร้าง ZY_TEMPLATE_V2.html ที่แก้ contrast จริง"})
    if len(refs) < 20:
        gaps.append({"id": "knowledge_references", "severity": "high",
                     "evidence": "SCHOLAR_RESEARCH.md มี URL จริง %d แห่ง" % len(refs),
                     "action": "สร้าง KNOWLEDGE_REFERENCES.md จาก URL จริงที่มีอยู่"})
    return gaps, refs, tpl


def fixed_template(tpl):
    """Real CSS fixes, not a placeholder: nav matches dark theme, font declared."""
    s = tpl
    s = s.replace("background:rgba(255,255,255,.86)", "background:rgba(11,15,23,.92)")
    s = s.replace("border-bottom:1px solid var(--line)", "border-bottom:1px solid #26324a")
    s = s.replace("--line:#e8eaf1", "--line:#26324a")
    s = s.replace("--acc:#38BDF8", "--acc:#22d3ee")
    if "font-family:'Inter Display'" in s:
        s = s.replace("font-family:'Inter Display'", "font-family:'Inter',sans-serif")
    return s


def references_doc(refs):
    uniq = []
    for u in refs:
        u = u.rstrip(".,")
        if u not in uniq:
            uniq.append(u)
    lines = ["# แหล่งอ้างอิงจริงของ Zyphere", "",
             "อัตโนมัติจาก SCHOLAR_RESEARCH.md — ไม่ได้แต่ง URL ขึ้นมา", "",
             "จำนวนแหล่ง: %d" % len(uniq), ""]
    for u in uniq[:250]:
        lines.append("- " + u)
    return "\n".join(lines) + "\n"


def run(apply=True):
    gaps, refs, tpl = scan()
    fills = []
    if any(g["id"] == "storefront_theme" for g in gaps) and tpl:
        r = AC.gh_put("ZY_TEMPLATE_V2.html", fixed_template(tpl),
                      "Auto-Grow: corrected storefront theme (real CSS fix)") if apply else {"ok": False, "dry": True}
        fills.append({"gap": "storefront_theme", "result": r})
    if any(g["id"] == "knowledge_references" for g in gaps) and refs:
        doc = references_doc(refs)
        local = os.path.join(ROOT, "governance", "KNOWLEDGE_REFERENCES.md")
        if apply:
            os.makedirs(os.path.dirname(local), exist_ok=True)
            open(local, "w", encoding="utf-8").write(doc)
        r = AC.gh_put("KNOWLEDGE_REFERENCES.md", doc,
                      "Auto-Grow: publish real citations from scholar research") if apply else {"ok": False, "dry": True}
        fills.append({"gap": "knowledge_references", "result": r, "urls": len(refs)})
    result = {"ok": True, "t": int(time.time()), "gaps": gaps, "fills": fills}
    with LOCK:
        json.dump(result, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return result


if __name__ == "__main__":
    r = run(apply="--dry" not in __import__("sys").argv)
    print("gaps", [g["id"] for g in r["gaps"]])
    for f in r["fills"]:
        print("fill", f["gap"], f["result"])
