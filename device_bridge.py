"""Zypher Device Bridge — connect real external devices safely, learn from
their telemetry, and turn that into new products. No fake device claims.

Detected honestly: HTTP webhook endpoints (env), serial ports (pyserial if
installed), GPIO (if library present), local JSON telemetry drop, camera/mic
through existing media modules. Actions are a SAFE whitelist only.
"""
import os, json, re, time, glob, threading

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "devices.json")
INBOX = os.path.join(ROOT, "data", "device_inbox")
OUT = os.path.join(ROOT, "governance", "DEVICE_PRODUCTS.md")
LOCK = threading.RLock()

SAFE_ACTIONS = {"capture_image": "สร้างภาพจากข้อความ/ข้อมูล Sensor",
                "capture_video": "สร้างวิดีโอสั้นจากข้อมูล",
                "create_ebook": "สร้าง ebook จากข้อมูลจริงที่ได้รับ",
                "learn_telemetry": "เก็บข้อมูล Sensor เข้าสมองในเครื่อง",
                "report_status": "รายงานสถานะอุปกรณ์เป็นไฟล์จริง"}


def detect():
    found = []
    for k in ("ZY_DEVICE_WEBHOOK", "DEVICE_WEBHOOK_URL", "MQTT_BROKER", "SERIAL_PORT"):
        if os.environ.get(k):
            found.append({"type": k.split("_")[0].lower(), "via": k, "configured": True})
    try:
        import serial
        ports = list(serial.tools.list_ports.comports())
        if ports:
            found.append({"type": "serial", "via": "pyserial",
                          "ports": [p.device for p in ports][:5]})
    except Exception:
        pass
    try:
        import RPi.GPIO  # noqa
        found.append({"type": "gpio", "via": "RPi.GPIO"})
    except Exception:
        pass
    if os.path.isdir(INBOX):
        files = [f for f in os.listdir(INBOX) if f.endswith(".json")]
        if files:
            found.append({"type": "telemetry-drop", "via": "data/device_inbox/*.json",
                          "files": files[:5]})
    return found


def read_telemetry():
    rows = []
    if not os.path.isdir(INBOX):
        return rows
    for f in sorted(os.listdir(INBOX)):
        if not f.endswith(".json"):
            continue
        try:
            d = json.load(open(os.path.join(INBOX, f), encoding="utf-8"))
            rows.append({"file": f, "data": d})
        except Exception:
            pass
    return rows[-10:]


def act(action, payload=None):
    if action not in SAFE_ACTIONS:
        return {"ok": False, "error": "action not in safe whitelist"}
    try:
        if action == "learn_telemetry":
            from local_brain import LocalBrain
            p = os.path.join(ROOT, "data", "dept_brains", "device.json")
            os.makedirs(os.path.dirname(p), exist_ok=True)
            lb = LocalBrain(p)
            for r in read_telemetry():
                lb.learn_text("telemetry " + r["file"] + ": " +
                              json.dumps(r["data"], ensure_ascii=False)[:500],
                              source="device")
            return {"ok": True, "learned": len(read_telemetry())}
        if action == "capture_image":
            import own_image_lab as LAB
            r = LAB.generate(str((payload or {}).get("brief", "sensor data"))[:120], apply=True)
            return {"ok": bool(r.get("ok")), "file": r.get("file")}
        if action == "capture_video":
            import cinema_studio
            r = cinema_studio.run(str((payload or {}).get("brief", "sensor data"))[:120], 12, "th")
            return {"ok": bool(r.get("ok")), "file": r.get("video")}
        if action == "create_ebook":
            import ebook_design_team
            r = ebook_design_team.run(apply=True)
            return {"ok": bool(r.get("ok")), "book": r.get("book")}
        if action == "report_status":
            return {"ok": True, "devices": detect(), "telemetry": len(read_telemetry())}
    except Exception as e:
        return {"ok": False, "error": str(e)[:160]}
    return {"ok": False, "error": "unreachable"}


def auto_product(apply=True):
    """When a device exists, brain builds a product from its real data."""
    devices = detect()
    tel = read_telemetry()
    if not devices and not tel:
        return {"ok": False, "error": "no connected device or telemetry — nothing to build from"}
    import world_knowledge as WK
    brief = "ข้อมูลจากอุปกรณ์จริง: " + json.dumps(tel[-1]["data"], ensure_ascii=False)[:160] if tel else \
            "อุปกรณ์ที่เชื่อมต่อ: " + str(devices[0].get("type"))
    facts = WK.harvest(brief[:180], apply=apply)
    image = act("capture_image", {"brief": brief[:120]})
    result = {"t": int(time.time()), "devices": devices, "telemetry": len(tel),
              "brief": brief[:200], "online_sources": facts.get("sources", []),
              "product": image,
              "note": "สร้างจากข้อมูลจริง — ถ้าไม่มีอุปกร์รายงานตรง ๆ ไม่แต่ง"}
    if apply:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        open(OUT, "w", encoding="utf-8").write(
            "# ผลิตภัณฑ์จากอุปกรณ์ที่เชื่อมต่อ\n\n" + json.dumps(result, ensure_ascii=False, indent=2))
        json.dump(result, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return result


if __name__ == "__main__":
    print(json.dumps({"devices": detect(), "auto": auto_product(False)}, ensure_ascii=False)[:700])
