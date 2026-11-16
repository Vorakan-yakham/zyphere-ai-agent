"""ความคิดเชิงลึกแบบ draft -> วิจารณ์ตัวเอง -> แก้ไข ทำให้โมเดลเล็กตอบแม่นขึ้นโดยไม่ต้องใช้ API."""

CRITIC = ("คุณคือผู้ตรวจงานที่เข้มงวด หาข้อผิดพลาดเชิงข้อเท็จจริง ตรรกะที่หลุด ส่วนที่ขาด และสิ่งที่เดา "
          "ตอบเป็นข้อสั้นๆ ถ้าไม่มีข้อผิดพลาดให้ตอบว่า OK")


def deliberate(llm, history, question, system="", rounds=1):
    """คืน generator ของข้อความคำตอบสุดท้าย; ขั้นร่างและขั้นวิจารณ์รันเงียบๆ"""
    msgs = list(history) + [{"role": "user", "content": question}]
    draft = llm.complete(msgs, system=system, temperature=0.4, max_tokens=2048)
    for _ in range(rounds):
        review = llm.complete(
            [{"role": "user", "content": f"คำถาม:\n{question}\n\nคำตอบร่าง:\n{draft}\n\nตรวจคำตอบนี้"}],
            system=CRITIC, temperature=0.2, max_tokens=600)
        if review.strip().upper().startswith("OK"):
            break
        msgs2 = msgs + [{"role": "assistant", "content": draft},
                        {"role": "user", "content": f"ผู้ตรวจพบประเด็น:\n{review}\n\nเขียนคำตอบสุดท้ายใหม่ให้ถูกต้องและครบถ้วน"}]
        draft = llm.complete(msgs2, system=system, temperature=0.3, max_tokens=2048)
    yield draft
