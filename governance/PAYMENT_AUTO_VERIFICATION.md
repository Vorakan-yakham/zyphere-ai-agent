# การยืนยันจ่ายแบบไม่ต้องเจ้าของกดทุกครั้ง

ผลลัพธ์: **MANUAL_REQUIRED**

| วิธี | auto ได้ไหม | เหตุผล | สิ่งที่ต้องมี |
|---|---|---|---|
| Omise PromptPay Charge + webhook | ไม่ได้ | PSP ยืนยันการชำระแล้วส่ง webhook → ระบบ unlock ไฟล์เอง ท่านเจ้าของไม่ต้องกด | OMISE_PUBLIC_KEY + OMISE_SECRET_KEY (ตั้งครั้งเดียวใน Render env) |
| Stripe Checkout + webhook | ไม่ได้ | checkout.sessions.completed → ตรวจ amount/currency → ส่งลิงก์ดาวน์โหลดอัตโนมัติ | STRIPE_SECRET_KEY + STRIPE_WEBHOOK_SECRET |
| PromptPay QR ธรรมดา + slip | ไม่ได้ | QR ไม่มี callback → ต้องมีคนตรวจสลิป/บัญชี (ห้าม auto ตามกฎของคุณ) | Owner manual — ทางนี้ยังใช้ต่อได้แต่ไม่ auto |
| OTP email + กดยืนยัน | ไม่ได้ | ขัดกฎที่คุณตั้งไว้: ห้ามจัดการ OTP / bank action แทนเจ้าของ — จะไม่ทำให้ | ไม่พัฒนาตามข้อจำกัดด้านความปลอดภัย |

## สถานะ key (เฉพาะว่ามี/ไม่มี — ไม่เปิดค่า)

- GROQ_API_KEY: NOT SET
- OMISE_PUBLIC_KEY: NOT SET
- OMISE_SECRET_KEY: NOT SET
- STRIPE_SECRET_KEY: NOT SET
- STRIPE_WEBHOOK_SECRET: NOT SET

ไม่มี PSP key → ไม่มีทาง auto ที่ซื่อสัตย์ได้ — ต้องตั้ง key ครั้งเดียว (owner) แล้วระบบทำต่อเอง

หมายเหตุ: ระบบมี endpoint `/api/store/config` ตรวจ Omise อยู่แล้ว — เมื่อตั้ง key ครั้งเดียว webhook จะผลักสถานะเองโดยไม่ต้องมีคำสั่งเพิ่ม
