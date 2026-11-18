# การเพิ่มฝ่าย/ความสามารถอัตโนมัติ

ระบบตรวจความขาดจากหลักฐานจริง แล้วสร้างโมดulersโค้ดที่เรียกใช้ได้

| ความสามารถที่ขาด | โมดูล | เหตุผล |
|---|---|---|
| quality_gate | `generated/quality_gate.py` | กันไม่ให้ของไม่ผ่านเกณฑ์ปล่อยขาย |
| editorial | `generated/editorial.py` | ตรวจทานข้อความของแต่ละฝ่าย |
| income | `generated/income.py` | คิดหาช่องทางรายได้จากของจริง |
| division_pressure | `generated/division_pressure.py` | หัวหน้าแผนกกดดันหัวหน้าฝ่าย |
