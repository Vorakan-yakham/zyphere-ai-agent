"""Slash commands and exact voice phrases handled locally, before anything reaches the LLM."""
from typing import Optional

from core.brain import KILL_PHRASES

HELP = """**คำสั่งที่ใช้ได้** (พิมพ์หรือพูดก็ได้)

| คำสั่ง | ทำอะไร |
|---|---|
| `/status` | สถานะระบบ งบ และจำนวนความรู้ |
| `/auto on` / `/auto off` | เปิด/ปิดการทำงานเอง |
| `/kill` หรือพูดว่า "หยุดฉุกเฉิน" | หยุดทุกอย่างที่ทำเองทันที |
| `/resume` | ปลดสวิตช์หยุดฉุกเฉิน (ยังไม่เปิดทำงานเองจนกว่าจะสั่ง `/auto on`) |
| `/think` | ให้ไตร่ตรองตอนนี้ 1 รอบ |
| `/learn <โจทย์>` | ให้สร้างทักษะ (ฟังก์ชันที่ทดสอบผ่านใน sandbox) |
| `/skills` · `/lessons` | ดูทักษะ / บทเรียนที่เรียนรู้ |"""


def is_command(text: str) -> bool:
    t = text.strip()
    return t.startswith("/") or t.lower() in KILL_PHRASES


def handle(text: str, store, guard, brain, scheduler=None) -> Optional[str]:
    """Returns a markdown reply, or None if `text` is not a command."""
    t = text.strip()
    if not is_command(t):
        return None
    if t.lower() in KILL_PHRASES:
        t = "/kill"
    cmd, _, arg = t.partition(" ")
    cmd, arg = cmd.lower(), arg.strip()

    if cmd in ("/kill", "/stop"):
        guard.kill()
        store.add_event("system", goal="KILL SWITCH", summary="หยุดฉุกเฉินโดยผู้ใช้ — ปิดการทำงานเองทั้งหมด", status="kill")
        return "**หยุดฉุกเฉินแล้ว** — ปิดการทำงานเองทั้งหมด พิมพ์ `/resume` เมื่อพร้อมปลดสวิตช์"
    if cmd == "/resume":
        guard.resume()
        store.add_event("system", goal="RESUME", summary="ปลดสวิตช์หยุดฉุกเฉิน (การทำงานเองยังปิดอยู่)", status="ok")
        return "ปลดสวิตช์หยุดฉุกเฉินแล้ว การทำงานเอง **ยังปิดอยู่** สั่ง `/auto on` เมื่อต้องการเปิด"
    if cmd == "/auto":
        if arg.lower() == "on":
            if guard.killed():
                return "สวิตช์หยุดฉุกเฉินยังทำงานอยู่ — พิมพ์ `/resume` ก่อน"
            store.set_setting("autonomy_enabled", True)
            store.add_event("system", goal="AUTONOMY", summary="เปิดการทำงานเอง", status="on")
            return f"เปิดการทำงานเองแล้ว (งบ {guard.cap()} ครั้ง/วัน)"
        if arg.lower() == "off":
            store.set_setting("autonomy_enabled", False)
            store.add_event("system", goal="AUTONOMY", summary="ปิดการทำงานเอง", status="off")
            return "ปิดการทำงานเองแล้ว"
        return "ใช้ `/auto on` หรือ `/auto off`"
    if cmd == "/status":
        state = "KILLED" if guard.killed() else ("ON" if guard.autonomy_enabled() else "OFF")
        alive = "ทำงาน" if (scheduler and scheduler.alive) else "ไม่ทำงาน"
        return (f"- การทำงานเอง: **{state}** (ลูปเบื้องหลัง: {alive})\n"
                f"- งบวันนี้: {guard.used('auto')}/{guard.cap()} ครั้ง\n"
                f"- บทเรียน: {len(store.top_lessons(1000))} · ทักษะ: {len(store.list_skills())} · "
                f"รออนุมัติ: {len(store.tasks(['awaiting_approval']))}")
    if cmd == "/skills":
        sk = store.list_skills()
        return "\n".join(f"- `{s['name']}` v{s['version']} — {s['description']}" for s in sk) or "ยังไม่มีทักษะ"
    if cmd == "/lessons":
        ls = store.top_lessons(15)
        return "\n".join(f"- {l['text']} (×{l['score']})" for l in ls) or "ยังไม่มีบทเรียน"
    if cmd == "/think":
        if brain is None:
            return "ยังไม่ได้เชื่อมต่อ API key"
        r = brain.cycle(force=True)
        return f"ไตร่ตรองเสร็จ: {r['reason']}"
    if cmd == "/learn":
        if brain is None:
            return "ยังไม่ได้เชื่อมต่อ API key"
        if len(arg) < 8:
            return "ระบุโจทย์ให้ชัดขึ้น เช่น `/learn ฟังก์ชันแปลงองศาเป็นเรเดียนพร้อมตรวจช่วงค่า`"
        r = brain.learn_skill(arg, source="manual")
        return (f"สร้างทักษะ `{r['name']}` สำเร็จ — เทสต์ผ่านใน sandbox" if r["ok"]
                else f"สร้างทักษะไม่สำเร็จ: {r['error']}")
    return HELP
