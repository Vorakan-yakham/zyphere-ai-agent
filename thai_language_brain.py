"""Thai Language Brain — store knowledge from the SMALLEST unit upward:
consonants -> vowels -> tone marks -> syllables -> words -> sentences -> paragraphs -> articles.
Every unit is saved into our LOCAL brain (data/dept_brains/thai.json) so it
survives any API shutdown, and is usable by editors/QA without a network.
"""
import os, json, re, time

ROOT = os.path.dirname(os.path.abspath(__file__))
BRAIN = os.path.join(ROOT, "data", "dept_brains", "thai.json")
STORE = os.path.join(ROOT, "data", "thai_language.json")

CONSONANTS = list("กขฃคฅฆงจฉชซฌญฎฏฐฑฒณดตถทธนบปผฝพฟภมยรลวศษสหฬอฮ")
VOWELS = list("ะาิีึืุูัํฺฯๆ")
TONE_MARKS = {"่":"ไม้เอก","้":"ไม้โท","๊":"ไม้ตรี","๋":"ไม้จัตวา"}
PUNCT = "。，,.!?；;：:()\"'—-…"


def units():
    return {
        "consonants": CONSONANTS, "consonant_count": len(CONSONANTS),
        "vowels": VOWELS, "vowel_count": len(VOWELS),
        "tones": TONE_MARKS,
        "word_markers": ["สระ", "พยัญชนะ", "วรรณยุกต์", "คำ", "ประโยค", "ย่อหน้า", "บทความ"],
        "sentence_ends": list(".!?。！？"),
        "paragraph_break": "\n\n",
    }


def analyse(text):
    t = str(text or "")
    chars = [c for c in t if not c.isspace()]
    cons = [c for c in chars if c in CONSONANTS]
    vow = [c for c in chars if c in VOWELS]
    tones = [TONE_MARKS.get(c) for c in chars if c in TONE_MARKS]
    words = [w for w in re.findall(r"[\u0E00-\u0E7F]+|[A-Za-z]+|\d+", t) if w]
    sents = [s.strip() for s in re.split(r"(?<=[.!?。！？])\s+", t) if s.strip()]
    paras = [p.strip() for p in re.split(r"\n\s*\n", t) if p.strip()]
    issues = []
    if "\ufffd" in t: issues.append("มี replacement character")
    if any(c in t for c in "Ãâðï"): issues.append("อาจเป็น mojibake")
    if cons and not vow: issues.append("มีพยัญชนะแต่ไม่มีสระ")
    if len(words) > 200 and len(sents) < 3: issues.append("ยาวแต่ไม่มีจังหวะประโยค")
    return {"ok": not issues, "issues": issues,
            "layers": {"characters": len(chars), "consonants": len(cons),
                       "vowels": len(vow), "tones": [x for x in tones if x],
                       "words": len(words), "sentences": len(sents),
                       "paragraphs": len(paras)},
            "sample": {"consonants": cons[:12], "vowels": vow[:12], "words": words[:8]}}


def build(apply=True):
    u = units()
    kb = {"t": int(time.time()), "units": u,
          "rule": "เก็บความรู้ภาษาไทยทุกชั้น从小到大道ля use โดยไม่พึ่ง API"}
    if apply:
        os.makedirs(os.path.dirname(STORE), exist_ok=True)
        json.dump(kb, open(STORE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        try:
            from local_brain import LocalBrain
            os.makedirs(os.path.dirname(BRAIN), exist_ok=True)
            lb = LocalBrain(BRAIN)
            for group, val in u.items():
                lb.learn_text("ภาษาไทยชั้น " + group + ": " + str(val)[:600],
                              source="thai-language-brain")
        except Exception:
            pass
    return kb


if __name__ == "__main__":
    kb = build()
    print("units", kb["units"]["consonant_count"], kb["units"]["vowel_count"],
          len(kb["units"]["tones"]))
    print(json.dumps(analyse("สวัสดีครับ ผมชื่อไซเฟอร์"), ensure_ascii=False)[:400])
