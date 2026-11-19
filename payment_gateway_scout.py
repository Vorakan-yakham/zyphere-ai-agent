"""Payment Verification Scout — find an AUTO path that does not require the
owner to press 'approve' each time, while respecting the owner's hard rules:
NO OTP handling, NO auto account creation, NO bank actions. The only honest
auto path is a PSP webhook (Omise/Stripe) with keys the owner configures once;
PromptPay QR alone has no callback and CANNOT be auto-verified.
"""
import os, json, re, time, hashlib

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "governance", "PAYMENT_AUTO_VERIFICATION.md")
DATA = os.path.join(ROOT, "data", "payment_auto.json")


def config():
    """Report presence only — NEVER values or secrets."""
    keys = {
        "GROQ_API_KEY": os.environ.get("GROQ_API_KEY"),
        "OMISE_PUBLIC_KEY": os.environ.get("OMISE_PUBLIC_KEY") or os.environ.get("OMISE_PKEY"),
        "OMISE_SECRET_KEY": os.environ.get("OMISE_SECRET_KEY") or os.environ.get("OMISE_SKEY"),
        "STRIPE_SECRET_KEY": os.environ.get("STRIPE_SECRET_KEY"),
        "STRIPE_WEBHOOK_SECRET": os.environ.get("STRIPE_WEBHOOK_SECRET"),
    }
    return {k: ("SET" if v else "NOT SET") for k, v in keys.items()}


def paths():
    cfg = config()
    omise_ready = cfg["OMISE_SECRET_KEY"] == "SET" and cfg["OMISE_PUBLIC_KEY"] == "SET"
    stripe_ready = cfg["STRIPE_SECRET_KEY"] == "SET" and cfg["STRIPE_WEBHOOK_SECRET"] == "SET"
    return [
        {"method": "Omise PromptPay Charge + webhook",
         "auto": omise_ready,
         "why": "PSP ยืนยันการชำระแล้วส่ง webhook → ระบบ unlock ไฟล์เอง ท่านเจ้าของไม่ต้องกด",
         "needs": "OMISE_PUBLIC_KEY + OMISE_SECRET_KEY (ตั้งครั้งเดียวใน Render env)"},
        {"method": "Stripe Checkout + webhook",
         "auto": stripe_ready,
         "why": "checkout.sessions.completed → ตรวจ amount/currency → ส่งลิงก์ดาวน์โหลดอัตโนมัติ",
         "needs": "STRIPE_SECRET_KEY + STRIPE_WEBHOOK_SECRET"},
        {"method": "PromptPay QR ธรรมดา + slip",
         "auto": False,
         "why": "QR ไม่มี callback → ต้องมีคนตรวจสลิป/บัญชี (ห้าม auto ตามกฎของคุณ)",
         "needs": "Owner manual — ทางนี้ยังใช้ต่อได้แต่ไม่ auto"},
        {"method": "OTP email + กดยืนยัน",
         "auto": False,
         "why": "ขัดกฎที่คุณตั้งไว้: ห้ามจัดการ OTP / bank action แทนเจ้าของ — จะไม่ทำให้",
         "needs": "ไม่พัฒนาตามข้อจำกัดด้านความปลอดภัย"},
    ]


def run(apply=True):
    cfg = config()
    routes = paths()
    rec = {"t": int(time.time()), "config_presence": cfg, "routes": routes,
           "verdict": "AUTO_POSSIBLE" if any(r["auto"] for r in routes) else "MANUAL_REQUIRED",
           "rule": "ไม่มี PSP key → ไม่มีทาง auto ที่ซื่อสัตย์ได้ — ต้องตั้ง key ครั้งเดียว (owner) แล้วระบบทำต่อเอง"}
    if apply:
        json.dump(rec, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        md = ["# การยืนยันจ่ายแบบไม่ต้องเจ้าของกดทุกครั้ง", "",
              "ผลลัพธ์: **%s**" % rec["verdict"], "",
              "| วิธี | auto ได้ไหม | เหตุผล | สิ่งที่ต้องมี |", "|---|---|---|---|"]
        for r in routes:
            md += ["| %s | %s | %s | %s |" % (
                r["method"], "ได้" if r["auto"] else "ไม่ได้", r["why"], r["needs"])]
        md += ["", "## สถานะ key (เฉพาะว่ามี/ไม่มี — ไม่เปิดค่า)", ""]
        for k, v in cfg.items():
            md += ["- %s: %s" % (k, v)]
        md += ["", rec["rule"], "",
               "หมายเหตุ: ระบบมี endpoint `/api/store/config` ตรวจ Omise อยู่แล้ว — "
               "เมื่อตั้ง key ครั้งเดียว webhook จะผลักสถานะเองโดยไม่ต้องมีคำสั่งเพิ่ม", ""]
        open(OUT, "w", encoding="utf-8").write("\n".join(md))
    return rec


if __name__ == "__main__":
    r = run()
    print(json.dumps({"verdict": r["verdict"],
                      "keys": r["config_presence"]}, ensure_ascii=False))
