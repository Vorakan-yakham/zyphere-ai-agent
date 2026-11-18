# ความคมชัดของภาพจากทีมวิศวกรในบ้าน (พัฒนาต่อรอบต่อรอบ)

ไม่ใช้ API ภายนอก — วัดจากโค้ดเราเองเท่านั้น

| รอบ | ความคมชัดหลังปรับ | เพิ่มขึ้น |
|---|---|---|
| 1 | 878.15 | 86.7% |
| 2 | 878.15 | 86.7% |
| 3 | 878.15 | 86.7% |

## ทีมเรียนรู้เพิ่มเติม

รอบนี้กระตุ้นการเรียนรู้ — ดู IMAGE_ALGORITHM_RESEARCH.md

## ข้อเสนอของสภาฯ รอบล่าสุด

สวัสดีครับ ในฐานะที่ปรึกษาทีมวิศวกรภาพ ผมขอชื่นชมผลลัพธ์รอบนี้ครับ การเพิ่ม Sharpness จาก 470.35 เป็น 878.15 (Gain 86.7%) โดยใช้ Algorithm ในบ้านล้วนๆ เป็นสัญญาณที่ดีมากว่าพื้นฐานของ Pipeline ของเราแข็งแรง อย่างไรก็ตาม เพื่อให้มั่นใจว่าภาพมีความคมชัดแบบ "Natural" ไม่เกิด Artifacts (เช่น Ringing หรือ Noise Amplification) และรักษาความละเอียดของรายละเอียด (Detail Preservation) ไว้ได้ ผมขอเสนอ 5 การปรับปรุงเฉพาะเจาะจงในโค้ด `own_image_lab.py` และ `photo_enhancement.py` โดยใช้ Pillow เท่านั้น ดังนี้ครับ

### 1. เปลี่ยนจาก `ImageFilter.SHARPEN` แบบเดียวไปใช้ `UnsharpMask` แบบ Adaptive
**ไฟล์:** `photo_enhancement.py`
**ฟังก์ชัน:** `apply_sharpening()`
**ปัญหาปัจจุบัน:** การใช้ `ImageFilter.SHARPEN` หรือ `UnsharpMask` ด้วยพารามิเตอร์คงที่ (Fixed Radius/Amount) มักจะทำให้ภาพดูแข็งเกินไปในบริเวณที่มี Contrast สูง และคมไม่พอในบริเวณ Contrast ต่ำ
**การปรับปรุง:**
ใช้ `ImageFilter.UnsharpMask(radius, percent, threshold)` โดยปรับพารามิเตอร์ดังนี้:
- `radius`: ตั้งค่าเป็น `1.5` ถึง `2.0` (แทนที่จะเป็น 1.0) เพื่อขยายขอบเขตการคำนวณให้ครอบคลุมรายละเอียดมากขึ้น
- `percent`: ตั้งค่าเริ่มต้นที่ `150` แล้วลดตามความสว่างของภาพ (ดูข้อ 2)
- `threshold`: ตั้งค่าเป็น `3` ถึง `5` (0-255) เพื่อป้องกันไม่ให้ Noise ในบริเวณที่มืดหรือสว่างจัดถูก Sharpen ตามไปด้วย
```python
# ตัวอย่างโค้ดปรับปรุง
def apply_sharpening(image, base_percent=150):
    # ปรับ threshold เพื่อลด Noise
    threshold = 4 
    radius = 1.8
    return image.filter(ImageFilter.UnsharpMask(radius=radius, percent=base_percent, threshold=threshold))
```

### 2. Implement Local Contrast Normalization ก่อน Sharpening
**ไฟล์:** `own_image_lab.py`
**ฟังก์ชัน:** `preprocess_for_sharpening()`
**ปัญหาปัจจุบัน:** หากภาพมี Dynamic Range แคบ (Flat) การ Sharpen โดยตรงจะดูไม่ชัดเจน หากภาพมี Contrast สูงอยู่แล้ว การ Sharpen จะทำให้เกิด Over-shoot
**การปรับปรุง:**
เพิ่มขั้นตอนการปรับ Contrast แบบ Local (Local Histogram Equalization) เบาๆ ก่อน Sharpen โดยใช้ `ImageOps.autocontrast()` หรือคำนวณ Contrast ต่อ Block
- ใช้ `ImageOps.autocontrast(image, cutoff=1)` เพื่อปรับ Contrast ให้อยู่ในสเกลที่เหมาะสมก่อนนำไป Sharpen
- หรือใช้ `image.point(lambda x: 1.2 * x - 10)` (Linear Stretch) แบบเบาๆ เพื่อขยาย Dynamic Range ก่อนเข้าขั้นตอน Sharpen
```python
# ตัวอย่างโค้ดปรับปรุง
from PIL import ImageOps

def preprocess_for_sharpening(image):
    # ปรับ Contrast เบาๆ เพื่อให้ Sharpening มีประสิทธิภาพมากขึ้น
    # cutoff=1 ตัดค่าที่มืดที่สุด/สว่างที่สุด 1% ออกก่อนปรับ
    return ImageOps.autocontrast(image, cutoff=1)
```

### 3. เพิ่ม Noise Reducti

## รายงาน self-coder

{"ok": "True", "file": "photo_enhancement.py", "reason": "pushed: Replaced the original anonymous block with a well‑documented function that:\n1. Adds a clea", "t": "1795014956", "sources": "['groq']", "focus": "photo_enhancement.py"}
