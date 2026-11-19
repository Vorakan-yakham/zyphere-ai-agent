# System Design — สัญญาสถาปัตยกรรมที่บังคับใช้ได้

ตรวจ **14/15** invariant · ฝ่าฝืน **1**

## องค์ประกอบและเจ้าของ

- **frontend_chat** (`วิศวกรแชท`) — UI + session · ตรวจ: login persists zy_token; logout clears local state first; owner-only controls gated by role
- **storefront** (`วิศวกรร้านค้า`) — browse/sample/buy · ตรวจ: account bar wired to auth API; 46 free samples render as HTML; price shown comes from measured content
- **auth** (`วิศวกรAPI`) — identity + session lifecycle · ตรวจ: anonymous cannot see orders; logout reachable; session cleared client-side even if backend is slow
- **ordering** (`วิศวกรฐานข้อมูล`) — create/decide/fulfil · ตรวจ: order persisted on create; declare finds order across instances; buyer email attached from login
- **payment_gate** (`วิศวกรQA`) — fail-closed release · ตรวจ: self declaration NEVER releases file; status awaiting_payment_proof
- **brain** (`วิศวกรสมอง`) — local-first learning · ตรวจ: source of truth is local + durable GitHub/KV; no fabricated sales or capability claims
- **automation** (`วิศวกรอัตโนมัติ`) — unattended pulses · ตรวจ: every department runs each pulse; assembly verifies outputs

## การตัดสินใจออกแบบ (ทำก่อนเขียนโค้ด)

- **Local-first brain + GitHub + KV**: of line local files are fast; GitHub is the durable visible store; Upstash KV shares state across Render instances.
- **Fail-closed payment**: a browser click is NOT payment proof. File release requires PSP webhook or owner slip check; self-declaration only records intent.
- **Shared order state in KV**: Render can run multiple instances; a per-process JSON file makes /api/pay/declare miss orders created by another instance.
- **Logout clears locally first**: await on a slow backend blocks the client cleanup — invalidate session immediately, fire backend logout in background.
- **Design -> validate -> relearn**: prose plans are not enough; every invariant is checked against real files/HTTP in this module and violations feed the relearn loop.

## ผลตรวจกับของจริง

| ระบบ | invariant | ผล | หลักฐาน |
|---|---|---|---|
| frontend_chat | login persists zy_token | PASS | index.html |
| frontend_chat | logout clears local state first | PASS | zyDoLogout |
| frontend_chat | owner-only controls gated by role | PASS | applyPopupVis |
| storefront | account bar wired to auth API | PASS | STORE.html |
| storefront | 46 free samples render as HTML | PASS | samples/ |
| storefront | price from measured content | FAIL | card facts |
| auth | anonymous cannot see orders | PASS | /api/store/my-orders |
| auth | logout reachable | PASS | app.py |
| ordering | order persisted on create | PASS | /api/pay/order |
| ordering | declare finds order across instances | PASS | /api/pay/declare |
| ordering | buyer email attached from login | PASS | /api/pay/order |
| payment_gate | self declaration NEVER releases file | PASS | declare |
| brain | durable store configured | PASS | remote KV |
| automation | QA + IT review gate wired | PASS | autonomy.yml |
| auth | live: anonymous orders blocked | PASS | HTTP 401 |

แผนที่เขียนไว้ต้องถูกตรวจกับของจริง — ถ้า Fail ห้ามปล่อย เข้า relearn
