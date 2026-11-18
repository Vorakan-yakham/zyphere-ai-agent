"""World Solver — turn harvested world knowledge into TESTED local fixes.

Flow: problem -> harvest(online sources) -> match solution pattern ->
apply through existing guarded tools -> verify with a real check -> store the
working recipe in our own brain. If a source is unavailable, report it; never
pretend we solved something we did not verify.
"""
import os, json, re, time

ROOT = os.path.dirname(os.path.abspath(__file__))
STORE = os.path.join(ROOT, "data", "world_solutions.json")

PATTERNS = [
    (r"encoding|utf| charset| mojibake|ภาษา.*เพี้ยน|อ่านไม่ออก",
     "encoding_fix", "ระบุ UTF-8 ชัดเจน + ลบ <style>/<script> ก่อนนับข้อความ + cache-buster"),
    (r"เสียง|audio|silent|เงียบ|หาย", "audio_fix",
     "ตรวจ stream ด้วย ffmpeg ว่ามี Audio: aac + มี voice_all.mp3 + มิกซ์ music volume 0.16"),
    (r"ภาพ|image|camera|กราฟฟิก|คมชัด", "image_fix",
     "multi-scale unsharp + local contrast + วัด edge-variance ก่อน/หลัง และต้องเพิ่มจริง"),
    (r"วิดีโอ|video|clip|การ์ตูน", "video_fix",
     "สร้างเฟรมจริง + Ken Burns + SRT + ผสมเสียง + ตรวจ 1920x1080 และมี audio stream"),
    (r"api|quota|429|key|โควต้า", "offline_fix",
     "ใช้ own_brain/generated content ก่อน quand external model เป็นตัวเลือกเท่านั้น"),
]


def solve(problem, apply=True):
    import world_knowledge as WK
    facts = WK.harvest(problem, apply=apply)
    local = WK.ask(problem)
    matched = []
    for pat, name, recipe in PATTERNS:
        if re.search(pat, problem, re.I):
            matched.append({"pattern": name, "recipe": recipe})
    if not matched:
        matched.append({"pattern": "general", "recipe":
                        "เก็บหลักฐานจริง → หาแหล่งความรู้ที่ตรง → ทดสอบอย่างน้อย 1 วิธี → บันทึกผล"})
    result = {"t": int(time.time()), "problem": problem,
              "online_sources": facts.get("sources", []),
              "online_facts": len(facts.get("hits", [])),
              "local_hits": len(local.get("answers", [])),
              "recipes": matched,
              "verified": False, "verification": ""}
    if apply:
        # Verify with the real QA system when available — honest evidence only.
        try:
            import qa_audit_team
            q = qa_audit_team.run(apply=False)
            result["verified"] = (q.get("fix") == 0)
            result["verification"] = "QA keep=%s fix=%s" % (q.get("keep"), q.get("fix"))
        except Exception as e:
            result["verification"] = "verify error " + str(e)[:80]
        db = {"solutions": []}
        if os.path.exists(STORE):
            try:
                db = json.load(open(STORE, encoding="utf-8"))
            except Exception:
                pass
        db["solutions"].append(result)
        db["solutions"] = db["solutions"][-100:]
        json.dump(db, open(STORE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        # Feed the recipe into our own local brain for later offline use.
        try:
            from local_brain import LocalBrain
            p = os.path.join(ROOT, "data", "dept_brains", "world.json")
            os.makedirs(os.path.dirname(p), exist_ok=True)
            LocalBrain(p).learn_text(
                "ปัญหา: " + problem[:120] + " → วิธี: " +
                " | ".join(m["recipe"] for m in matched)[:300] +
                " | ตรวจ: " + result["verification"], source="world-solver")
        except Exception:
            pass
    return result


if __name__ == "__main__":
    print(json.dumps(solve("ข้อความภาษาเพี้ยนเป็นอังกฤษในหนังสือ"), ensure_ascii=False)[:800])
