# IT Integration Review — ตรวจครบวงจรโดยวิศวกร IT

ผ่าน **22/22** · ไม่ผ่าน **0**

| ตรวจ | ผล | หลักฐาน |
|---|---|---|
| login stores zy_token | PASS | index.html setK/setItem zy_token |
| chat logout clears local BEFORE backend call | PASS | zyDoLogout order |
| chat popup logout wired | PASS | amLogout -> zyDoLogout |
| no stale logout alert shipped | PASS | old alert string absent |
| logout button bound to handler | PASS | logoutBtn onclick |
| store account bar present | PASS | STORE.html acctbar + /api/store/me |
| store has my-orders / owner / logout | PASS | 3 store account actions |
| store logout clears local first | PASS | zyLogout order |
| order attaches buyer login | PASS | app.py new_order email |
| order persisted locally + remote KV | PASS | remote KV + merge helper |
| declare reads shared store | PASS | app.py declare |
| fail-closed: no file on self declaration | PASS | payment proof gate |
| owner download receives token | PASS | index.html owner download |
| catalogue has exactly 46 unique books | PASS | rows=46 unique=46 |
| store uses 46 real photographic covers | PASS | real images=46 |
| progress dashboard has 12 departments | PASS | PROGRESS.html cards |
| all 46 sample files exist | PASS | samples/s_*.html count |
| prices come from measured content (<=50) | PASS | price set [20, 30, 40, 50] |
| live /api/store/me gate | PASS | 200 {"ok": false, "error": "not logged in"} |
| live /api/store/my-orders 401 | PASS | 401 |
| live /api/auth/logout reachable | PASS | 200 |
| live UI ships instant logout | PASS | HTTP 200 |

วิศวกร IT ตรวจครบวงจรจริง — ไม่ใช่รายงานสวย ๆ ถ้า Fail ต้องเข้า relearn
