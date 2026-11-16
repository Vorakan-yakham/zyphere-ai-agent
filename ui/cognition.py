"""Cognition and Skills views: autonomy controls, live thought log, approvals, lessons, skills, backup."""
import html
import json

import streamlit as st

from core.sandbox import run_code

KIND_LABEL = {"think": "THINK", "skill": "SKILL", "system": "SYSTEM", "error": "ERROR"}


def state_of(guard) -> str:
    return "KILLED" if guard.killed() else ("ON" if guard.autonomy_enabled() else "OFF")


def _label(text: str) -> None:
    st.markdown(f"<div class='zy-eyebrow' style='margin:18px 0 8px'>{html.escape(text)}</div>", unsafe_allow_html=True)


@st.fragment(run_every=5)
def _live_log(store) -> None:
    rows = store.events(kinds=["think", "skill", "system", "error"], limit=14)
    if not rows:
        st.markdown("<div class='zy-muted' style='font-size:13px'>ยังไม่มีกิจกรรม — เปิด Autonomous mode หรือกด Think now</div>",
                    unsafe_allow_html=True)
        return
    out = []
    for e in rows:
        solid = " solid" if e["status"] in ("kill", "error", "failed") else ""
        out.append(f"<div class='zy-log'><span class='ts'>{html.escape(e['ts'][5:16])}</span>"
                   f"<span class='zy-chip{solid}'>{KIND_LABEL.get(e['kind'], e['kind'].upper())}</span>"
                   f"<span><b>{html.escape(e['goal'][:60])}</b> {html.escape(e['summary'][:260])}</span></div>")
    st.markdown("".join(out), unsafe_allow_html=True)


def _on_toggle(store, guard) -> None:
    want = bool(st.session_state.get("auto_toggle"))
    if guard.killed():  # never let the UI re-arm a killed system
        want = False
    store.set_setting("autonomy_enabled", want)
    store.add_event("system", goal="AUTONOMY", summary="เปิดการทำงานเอง" if want else "ปิดการทำงานเอง",
                    status="on" if want else "off")


def render_cognition(store, guard, scheduler, brain, online: bool) -> None:
    state = state_of(guard)
    cap, used = guard.cap(), guard.used("auto")
    alive = bool(scheduler and scheduler.alive)

    st.markdown(
        f"<div class='zy-notice'><div class='zy-eyebrow' style='margin-bottom:6px'>Autonomy core</div>"
        f"<span style='font-size:22px;letter-spacing:.2em;font-weight:300'>{state}</span> "
        f"<span class='zy-muted' style='font-size:12px'>· background loop {'running' if alive else 'stopped'} · "
        f"{used}/{cap} autonomous calls today</span></div>", unsafe_allow_html=True)
    if not online:
        st.info("ต้องตั้งค่า ANTHROPIC_API_KEY ก่อน จึงจะคิดเองได้")

    left, right = st.columns([3, 2])
    with left:
        # Single source of truth is the store. Sync the widget FROM the store before drawing it, and push user
        # clicks back through a callback (a stale widget value vs store caused an endless st.rerun() loop).
        st.session_state["auto_toggle"] = guard.autonomy_enabled()
        st.toggle("Autonomous mode — คิด/เรียนรู้เองเป็นรอบ ๆ", key="auto_toggle", on_change=_on_toggle, args=(store, guard),
                  disabled=guard.killed() or not online)
        st.progress(min(1.0, used / cap) if cap else 1.0, text=f"งบอัตโนมัติวันนี้ {used}/{cap} ครั้ง")
        if st.button("Think now — ไตร่ตรอง 1 รอบ", icon=":material/psychology:", disabled=not online):
            with st.spinner("กำลังไตร่ตรอง…"):
                res = scheduler.run_once(force=True) if scheduler else brain.cycle(force=True)
            st.caption(f"ผล: {res['reason']}")
            st.rerun()
    with right:
        if guard.killed():
            if st.button("Resume — ปลดสวิตช์", icon=":material/play_arrow:"):
                guard.resume()
                store.add_event("system", goal="RESUME", summary="ปลดสวิตช์หยุดฉุกเฉิน", status="ok")
                st.rerun()
        elif st.button("EMERGENCY STOP", type="primary", icon=":material/stop_circle:"):
            guard.kill()
            store.add_event("system", goal="KILL SWITCH", summary="หยุดฉุกเฉินโดยผู้ใช้", status="kill")
            st.rerun()
        interval = st.select_slider("รอบการคิด (นาที)", [5, 10, 30, 60, 180],
                                    value=min([5, 10, 30, 60, 180], key=lambda x: abs(x - int(store.get_setting("interval_min", 10)))))
        if interval != store.get_setting("interval_min", 10):
            store.set_setting("interval_min", interval)
        new_cap = st.number_input("งบต่อวัน (ครั้ง)", 0, 500, cap, step=5)
        if new_cap != cap:
            store.set_setting("daily_cap", int(new_cap))
            st.rerun()

    _label("Thought log · live")
    _live_log(store)

    pend = store.tasks(["awaiting_approval"])
    _label(f"Awaiting your approval · {len(pend):02d}")
    if not pend:
        st.markdown("<div class='zy-muted' style='font-size:13px'>ไม่มีรายการรออนุมัติ</div>", unsafe_allow_html=True)
    for t in pend:
        st.markdown(f"<div class='zy-card' style='min-height:0'><div class='t'>{html.escape(t['title'])}</div>"
                    f"<div class='d'>{html.escape(t['type'].replace('proposal_', '').upper())} · {html.escape(t['detail'][:300])}</div></div>",
                    unsafe_allow_html=True)
        a, r, _ = st.columns([1, 1, 3])
        if a.button("Approve", key=f"ap_{t['id']}", icon=":material/check:"):
            store.update_task(t["id"], "approved")
            st.rerun()
        if r.button("Reject", key=f"rj_{t['id']}", icon=":material/close:"):
            store.update_task(t["id"], "rejected")
            st.rerun()
    if store.tasks(["approved"]):
        st.caption("รายการที่อนุมัติแล้วจะถูกดำเนินการในรอบคิดถัดไป (หรือกด Think now)")

    lessons = store.top_lessons(30)
    with st.expander(f"Lessons learned · {len(lessons)}"):
        if not lessons:
            st.caption("ยังไม่มีบทเรียน — จะเกิดขึ้นเมื่อ AI ไตร่ตรองจากบทสนทนาของคุณ")
        for l in lessons:
            c1, c2 = st.columns([12, 1])
            c1.markdown(f"{html.escape(l['text'])}  <span class='zy-muted'>×{l['score']} · {html.escape(l['source'])}</span>",
                        unsafe_allow_html=True)
            if c2.button("", key=f"dl_{l['id']}", icon=":material/close:", help="ลบบทเรียนนี้"):
                store.delete_lesson(l["id"])
                st.rerun()

    with st.expander("Backup / restore / erase"):
        st.caption("บน Streamlit Cloud ข้อมูลจะหายเมื่อแอปรีสตาร์ต — ดาวน์โหลดสำรองไว้เป็นระยะ")
        st.download_button("Download backup (.json)", json.dumps(store.export_all(), ensure_ascii=False, indent=1),
                           file_name="zyphere_backup.json", mime="application/json", icon=":material/download:")
        up = st.file_uploader("Restore from backup", type=["json"], key="restore_up")
        if up is not None and st.button("Restore (แทนที่ข้อมูลปัจจุบันทั้งหมด)"):
            try:
                store.import_all(json.loads(up.getvalue().decode("utf-8")))
                st.success("กู้คืนแล้ว")
            except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
                st.error("ไฟล์สำรองไม่ถูกต้อง")
        if st.checkbox("ยืนยัน: ลบความจำ บทเรียน ทักษะ และงานทั้งหมด") and st.button("Erase everything"):
            store.erase_all()
            st.session_state.messages = []
            st.rerun()


def render_skills(store, brain, online: bool) -> None:
    _label("Create a skill")
    st.caption("AI จะเขียนฟังก์ชัน พร้อมเทสต์ แล้วรันใน sandbox — บันทึกเฉพาะที่เทสต์ผ่านเท่านั้น")
    with st.form("new_skill", clear_on_submit=True):
        spec = st.text_area("โจทย์", placeholder="เช่น ฟังก์ชันคำนวณ lift จากความหนาแน่นอากาศ ความเร็ว พื้นที่ปีก และ CL พร้อมตรวจค่าติดลบ",
                            label_visibility="collapsed", height=90)
        go = st.form_submit_button("Create skill", icon=":material/construction:", disabled=not online)
    if go:
        if len(spec.strip()) < 8:
            st.warning("ระบุโจทย์ให้ชัดขึ้น")
        else:
            with st.spinner("กำลังเขียนและทดสอบ…"):
                r = brain.learn_skill(spec.strip(), source="manual")
            st.success(f"สร้าง `{r['name']}` สำเร็จ — เทสต์ผ่าน") if r["ok"] else st.error(f"ไม่สำเร็จ: {r['error']}")

    skills = store.list_skills()
    _label(f"Skill library · {len(skills):02d}")
    if not skills:
        st.markdown("<div class='zy-muted' style='font-size:13px'>ยังไม่มีทักษะ</div>", unsafe_allow_html=True)
    for s in skills:
        with st.expander(f"{s['name']} · v{s['version']} · {s['passes']}/{s['runs']} pass"):
            st.markdown(html.escape(s["description"]))
            st.code(s["code"], language="python")
            with st.popover("Tests"):
                st.code(s["tests"], language="python")
            snippet = st.text_input("เรียกใช้ (นิพจน์ Python)", value=f"print({s['name']}())", key=f"snip_{s['name']}")
            c1, c2, _ = st.columns([1, 1, 3])
            if c1.button("Run", key=f"run_{s['name']}", icon=":material/play_arrow:"):
                res = run_code(s["code"], snippet)
                store.record_skill_run(s["name"], bool(res["ok"]))
                st.code(res["stdout"] or "(no output)", language="text") if res["ok"] else st.error(res["error"])
            if c2.button("Delete", key=f"del_{s['name']}", icon=":material/delete:"):
                store.delete_skill(s["name"])
                st.rerun()
