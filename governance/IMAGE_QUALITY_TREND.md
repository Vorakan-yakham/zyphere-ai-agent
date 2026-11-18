# ความคมชัดของภาพจากทีมวิศวกรในบ้าน (พัฒนาต่อรอบต่อรอบ)

ไม่ใช้ API ภายนอก — วัดจากโค้ดเราเองเท่านั้น

| รอบ | ความคมชัดหลังปรับ | เพิ่มขึ้น |
|---|---|---|
| 1 | 878.15 | 86.7% |
| 2 | 878.15 | 86.7% |
| 3 | 878.15 | 86.7% |
| 4 | 426.6 | 34.2% |
| 5 | 426.6 | 34.2% |
| 6 | 426.6 | 34.2% |

## ทีมเรียนรู้เพิ่มเติม

รอบนี้กระตุ้นการเรียนรู้ — ดู IMAGE_ALGORITHM_RESEARCH.md

## ข้อเสนอของสภาฯ รอบล่าสุด

สวัสดีครับ ในฐานะที่ปรึกษาทีมวิศวกรภาพ ผมได้วิเคราะห์ข้อมูลรอบล่าสุดแล้ว ผลลัพธ์ที่ `sharp_after` เพิ่มขึ้นจาก 317.82 เป็น 426.6 (Gain 34.2%) และ `lab_score` พุ่งขึ้นไปที่ 100 นั้น แสดงว่าอัลกอริทึมภายในของเรามีประสิทธิภาพสูงมากในการเพิ่มรายละเอียด (Detail Enhancement) โดยไม่ต้องพึ่งพาบริการภายนอก

อย่างไรก็ตาม การที่คะแนน Lab Score สูงถึง 100 อาจบ่งชี้ว่าภาพมีความ "จัด" (Over-enhanced) หรือมี Noise สูงขึ้นตามไปด้วย ซึ่งอาจส่งผลต่อความสวยงามตามธรรมชาติ (Naturalness) ในบางกรณี

เพื่อให้ระบบมีความเสถียรและรองรับภาพที่มีความซับซ้อนมากขึ้น ผมขอเสนอ 5 การปรับปรุงโค้ดที่ทำได้จริงด้วย **Pillow** โดยเจาะจงฟังก์ชันและพารามิเตอร์ ดังนี้:

### 1. ปรับปรุงการ Sharpening แบบ Selective ใน `photo_enhancement.py`
**ปัญหา:** การใช้ `ImageFilter.UnsharpMask` ทั่วไปอาจทำให้ Noise ในพื้นที่เรียบ (เช่น ฟ้าหรือผนัง) ถูกขยายตามไปด้วย
**แนวทาง:** ใช้ `UnsharpMask` ร่วมกับพารามิเตอร์ที่ละเอียดขึ้น และพิจารณาใช้ `ImageEnhance.Sharpness` สำหรับภาพที่มีความละเอียดต่ำ
**โค้ดตัวอย่าง:**
```python
from PIL import Image, ImageFilter, ImageEnhance

def enhance_sharpness(image, radius=2, percent=150, threshold=3):
    # radius: ความกว้างของขอบที่เน้น (2-4 เหมาะกับภาพมือถือ)
    # percent: ความแรงของการ sharpen (100-200)
    # threshold: ค่าความต่างขั้นต่ำที่จะถูก sharpen (ลด noise ได้)
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # ใช้ UnsharpMask แทน Sharpness filter ธรรมดา เพราะควบคุมได้ดีกว่า
    enhanced = image.filter(ImageFilter.UnsharpMask(radius=radius, percent=percent, threshold=threshold))
    return enhanced
```
**เหตุผล:** การตั้งค่า `threshold` ช่วยป้องกันไม่ให้พื้นที่ที่มีความต่างของสีน้อย (flat areas) ถูก sharpen ซึ่งลด Noise ได้ดี

### 2. ปรับสมดุลสีแบบ Local Contrast ใน `own_image_lab.py`
**ปัญหา:** ภาพที่ Sharpen มากอาจทำให้สีดูแข็ง (Harsh) หรือขาดความลึก
**แนวทาง:** ใช้ `ImageEnhance.Color` และ `ImageEnhance.Contrast` แบบปรับตามค่าเฉลี่ยของภาพ (Adaptive)
**โค้ดตัวอย่าง:**
```python
from PIL import ImageEnhance
import numpy as np

def adaptive_color_balance(image):
    # แปลงเป็น numpy เพื่อคำนวณค่าเฉลี่ยสี
    arr = np.array(image)
    mean_brightness = arr.mean()
    
    # ปรับ Contrast และ Color ตามความสว่าง
    contrast_enhancer = ImageEnhance.Contrast(image)
    color_enhancer = ImageEnhance.Color(image)
    
    # ถ้าภาพมืด (mean < 100) เพิ่ม Contrast น้อยลง เพื่อไม่ให้ดำสนิท
    # ถ้าภาพสว่าง (mean > 180) เพิ่ม Color น้อยลง เพื่อไม่ให้สีจัดเกินไป
    if mean_brightness < 100:
        contrast_factor = 1.1
        color_factor = 1.05
  

## รายงาน self-coder

{"ok": "True", "file": "photo_enhancement.py", "reason": "pushed: local-brain", "t": "1795043706", "sources": "['local-brain', 'own-brain']", "focus": "photo_enhancement.py"}
