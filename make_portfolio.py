"""Create a real freelance portfolio pack Zyphere can produce for the owner."""
import os, zipfile
BASE = os.path.join(os.environ.get("USERPROFILE", os.path.expanduser("~")), "Downloads", "zyphere_portfolio")
os.makedirs(BASE, exist_ok=True)

files = {
"01_เขียนคอนเทนต์_ตัวอย่าง.txt": """ตัวอย่างงานเขียนคอนเทนต์สำหรับเพจร้านอาหาร
หัวข้อ: 5 เหตุผลที่ควรลอง 'ข้าวซอย' ในวันฝนตก
1) ความอุ่นจากน้ำซุปที่เคี่ยวนานชวนให้คลายหนาว
2) กลิ่นเครื่องแกงเครื่องเทศที่กระตุ้นความอยากอาหาร
3) เส้นหมี่สดที่ดูดซึมน้ำซุปได้พอดี
4) ผักดองและหอม紅 Associate ช่วยตัดเลี่ยนได้ลงตัว
5) อร่อยได้ในราคาประหยัด เหมาะกับทุกวัย
ปิดท้าย: วันฝนตกแบบนี้ ถ้ายังไม่รู้จะกินอะไร ลองแวะร้านเราได้เลยครับ
""",
"02_แปล_ตัวอย่าง.txt": """ตัวอย่างงานแปล อังกฤษ → ไทย
EN: Our AI assistant helps teams work faster by automating repetitive tasks and summarizing long documents.
TH: ผู้ช่วย AI ของเราช่วยให้ทีมทำงานได้เร็วขึ้น ด้วยการทำให้งานที่ซ้ำซากเป็นอัตโนมัติ และสรุปเอกสารยาวให้เข้าใจง่าย
EN: Clear communication builds trust with customers.
TH: การสื่อสารที่ชัดเจนช่วยสร้างความเชื่อมั่นกับลูกค้า
""",
"03_วิเคราะห์ข้อมูล_ตัวอย่าง.txt": """ตัวอย่างงานวิเคราะห์ข้อมูล (ยอดขายร้านกาแฟ 7 วัน)
วันจันทร์ 4,200 | อังคาร 3,800 | พุธ 5,100 | พฤหัส 4,600 | ศุกร์ 7,200 | เสาร์ 9,500 | อาทิตย์ 8,800
พบว่า: ยอดขายวันเสาร์-อาทิตย์สูงกว่าวันธรรมดา ~2 เท่า
คำแนะนำ: เพิ่มพนักงานช่วงสุดสัปดาห์ และจัดโปรโมชันวันพุธเพื่อกระตุ้นยอดกลางสัปดาห์
""",
"04_โค้ด_ตัวอย่าง.py": """# ตัวอย่างงานเขียนโค้ด: ระบบนับคำในไฟล์ข้อความ
from collections import Counter
import re

def count_words(text):
    words = re.findall(r"[\\u0E00-\\u0E7FA-Za-z0-9]{2,}", text or "")
    return Counter(words).most_common(10)

if __name__ == "__main__":
    sample = "Zyphere ช่วยเขียนโค้ด ไซเฟอร์ช่วยเขียนโค้ด AI ทำงานได้"
    for word, n in count_words(sample):
        print(word, n)
""",
}
for name, content in files.items():
    with open(os.path.join(BASE, name), "w", encoding="utf-8") as f:
        f.write(content)

readme = """พอร์ตโฟลิโอตัวอย่างงานที่ Zyphere ผลิตได้จริง
----------------------------------------
1. เขียนคอนเทนต์โปรโมต (01_เขียนคอนเทนต์_ตัวอย่าง.txt)
2. แปล อังกฤษ-ไทย (02_แปล_ตัวอย่าง.txt)
3. วิเคราะห์ข้อมูล + คำแนะนำ (03_วิเคราะห์ข้อมูล_ตัวอย่าง.txt)
4. เขียนโค้ด Python (04_โค้ด_ตัวอย่าง.py)

ราคาแนะนำสำหรับส่งงาน freelance:
- เขียนคอนเทนต์ 300-800 บาท/ชิ้น
- แปล 1-3 บาท/คำ
- วิเคราะห์ข้อมูล 500-1500 บาท/งาน
- เขียนโค้ด 500-3000 บาท/งาน

วิธีใช้: เปิด Fastwork/Fiverr → สมัครเป็นผู้ให้บริการ → ใช้ตัวอย่างเหล่านี้เป็นผลงาน → รับงานแล้วให้ Zyphere ผลิตผลงานส่งลูกค้า
"""
with open(os.path.join(BASE, "README.txt"), "w", encoding="utf-8") as f:
    f.write(readme)

z = os.path.join(BASE, "zyphere_portfolio.zip")
with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
    for n in os.listdir(BASE):
        if not n.endswith(".zip"):
            zf.write(os.path.join(BASE, n), n)
print("created", z, os.path.getsize(z))
