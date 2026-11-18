"""Zyphere Department Editors — proofreaders for every division.

Each editor owns the actual written output of one division (store descriptions,
promotions, reports, docs) and checks it with the real LanguageMastery engine
plus deterministic checks. Findings are written to a review file and fed into
that department's own brain, so editors do not share one generic knowledge.

HONEST: counts come from text actually fetched; no invented quality scores.
"""
import os, re, json, time, threading
import autonomous_council as AC

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "department_editors.json")
OUT = os.path.join(ROOT, "governance", "EDITORIAL_REVIEW.md")

# division -> (editor role, real document it proofreads)
EDITORS = [
    ("01 Global Intelligence", "บรรณาธิการข้อมูล", "PRODUCTS.md"),
    ("02 Scientific Discovery", "บรรณาธิการวิชาการ", "REVIEW.md"),
    ("03 Simulation", "บรรณาธิการสื่อ", "PROMO.md"),
    ("04 Knowledge Systems", "บรรณาธิการความรู้", "SCHOLAR_RESEARCH.md"),
    ("05 Learning", "บรรณาธิการเรียนรู้", "CO_LEARNING.md"),
    ("06 Engineering", "บรรณาธิการเทคนิค", "README.md"),
    ("07 Quality", "บรรณาธิการคุณภาพ", "QUALITY_REPORT.md"),
    ("08 Product Design", "บรรณาธิการหน้าร้าน", "ZY_TEMPLATE_V2.html"),
    ("09 Market & Revenue", "บรรณาธิการรายได้", "INCOME_PLAN.md"),
    ("10 Operations", "บรรณาธิการปฏิบัติการ", "DEPARTMENTS.md"),
    ("11 Governance", "บรรณาธิการกำกับดูแล", "BOOK_DESIGN_STANDARD.md"),
    ("12 Autonomy", "บรรณาธิการพัฒนาตัวเอง", "SELF_IMPROVEMENT.md"),
]


class DepartmentEditors:
    def __init__(self):
        self.lock = threading.RLock()
        self.log = []
        try:
            self.log = json.load(open(DATA, encoding="utf-8")).get("log", [])
        except Exception:
            pass

    def save(self):
        with self.lock:
            try:
                os.makedirs(os.path.dirname(DATA), exist_ok=True)
                json.dump({"log": self.log[-150:]}, open(DATA, "w", encoding="utf-8"),
                          ensure_ascii=False, indent=2)
            except Exception:
                pass

    def _check(self, text, path):
        issues = []
        if not text:
            return ["ไม่พบไฟล์จริง"], None
        # Deterministic checks on actual text
        for m in re.finditer(r"(.{2,40}?)\s+\1", text):
            issues.append("คำซ้ำ: " + m.group(1)[:40])
            if len(issues) >= 4:
                break
        if re.search(r"[\U0001F300-\U0001FAFF]", text):
            issues.append("มี emoji ในเนื้อหาที่ต้องอ่าน/แสดงผล")
        if path.lower().endswith(".md") and re.search(r"<(script|style|div)\b", text, re.I):
            issues.append("มี HTML tag ปนในเอกสารข้อความ")
        if re.search(r"\b\d{1,2}(?=[\s,]*(บาท|วัน|เดือน|ปี))", text):
            issues.append("มีตัวเลขที่ต้องตรวจคำอ่าน (เช่น 18 -> สิบแปด)")
        try:
            from language import LanguageMastery
            out = LanguageMastery().correct(text[:6000])
            if isinstance(out, dict):
                issues += ["language: " + str(x)[:90] for x in
                           (out.get("issues") or out.get("changes") or [])[:3]]
            elif isinstance(out, str) and out.strip() and out.strip() != text[:6000].strip():
                issues.append("LanguageMastery เสนอการแก้ไขจริง")
        except Exception as e:
            issues.append("language engine unavailable: " + str(e)[:60])
        return issues[:8], out

    def run(self, apply=True):
        results = []
        for div, role, path in EDITORS:
            text = AC.gh_raw(path) or ""
            issues, _ = self._check(text, path)
            results.append({"division": div, "editor": role, "file": path,
                            "bytes": len(text), "issues": issues,
                            "ok": not issues, "t": int(time.time())})
            # Each editor teaches its own department brain only.
            try:
                from local_brain import LocalBrain
                code = div[:2]
                p = os.path.join(ROOT, "data", "dept_brains", code + ".json")
                os.makedirs(os.path.dirname(p), exist_ok=True)
                LocalBrain(p).learn_text(
                    role + " ตรวจ " + path + ": " + (", ".join(issues) if issues else "ผ่าน"),
                    source="editor:" + code)
            except Exception:
                pass
        with self.lock:
            self.log.append({"t": int(time.time()), "results": results})
        self.save()
        if apply:
            md = ["# รายงานตรวจทานข้อความตามฝ่าย (Department Editors)", "",
                  "ตรวจจากไฟล์จริงด้วย LanguageMastery + กฎตรวจจับ", ""]
            for r in results:
                md += ["## %s — %s" % (r["division"], r["editor"]), "",
                       "- ไฟล์: `%s` (%d bytes)" % (r["file"], r["bytes"]),
                       "- ผล: " + ("ผ่าน" if r["ok"] else "มีประเด็น %d" % len(r["issues"]))]
                for i in r["issues"]:
                    md += ["  - " + i]
                md += [""]
            os.makedirs(os.path.dirname(OUT), exist_ok=True)
            open(OUT, "w", encoding="utf-8").write("\n".join(md))
            AC.gh_put("EDITORIAL_REVIEW.md", "\n".join(md) + "\n",
                      "Auto-Grow: department editors proofread real documents")
        return {"ok": True, "editors": len(EDITORS), "results": results}

    def status(self):
        last = self.log[-1] if self.log else {}
        return {"ok": True, "editors": len(EDITORS), "rounds": len(self.log),
                "last": last.get("results", [])}


ED = DepartmentEditors()
