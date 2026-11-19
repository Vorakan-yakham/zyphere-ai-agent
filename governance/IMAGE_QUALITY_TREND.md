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
| 7 | 426.6 | 34.2% |
| 8 | 426.6 | 34.2% |

## ทีมเรียนรู้เพิ่มเติม

รอบนี้กระตุ้นการเรียนรู้ — ดู IMAGE_ALGORITHM_RESEARCH.md

## ข้อเสนอของสภาฯ รอบล่าสุด

ในฐานะที่ปรึกษาทีมวิศวกรภาพ ผมวิเคราะห์ผลวัดรอบนี้ว่า:
*   **Sharpness:** เพิ่มขึ้นจาก 317.82 เป็น 426.6 (+34.2%) ซึ่งถือว่าดีเยี่ยม
*   **Lab Score:** 100 (เพอร์เฟกต์ตามเกณฑ์ภายใน)
*   **Source:** ใช้ Algorithm ในบ้านล้วนๆ

เนื่องจากเราห้ามใช้ API ภายนอกและต้องเน้นความเฉพาะเจาะจงในโค้ด `own_image_lab.py` และ `photo_enhancement.py` ที่ใช้ Pillow เท่านั้น ผมขอเสนอ 5 ข้อปรับปรุงเพื่อรักษาความคมชัดที่ได้มา และเพิ่มคุณภาพสี/รายละเอียดที่อาจขาดหายไปในขั้นตอนก่อนหน้า:

### 1. ปรับพารามิเตอร์ `UnsharpMask` ให้เป็นแบบ Adaptive (ใน `photo_enhancement.py`)
**ปัญหา:** การ Sharpen แบบคงที่ (Fixed Radius/Amount) มักทำให้ขอบวัตถุ (Edge) มี Halo หรือ Noise สูงเกินไปในบริเวณพื้นหลังเรียบ
**วิธีแก้:** เปลี่ยนจาก `ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3)` เป็นการใช้ `radius` ที่แปรผันตามความละเอียดของภาพ หรือใช้ `threshold` ที่สูงขึ้นเล็กน้อยเพื่อลด Noise ในพื้นที่เรียบ
**โค้ดตัวอย่าง:**
```python
# ในฟังก์ชัน enhance_sharpness()
# แทนที่จะใช้ค่าคงที่ ให้คำนวณ radius ตามขนาดภาพ
width, height = img.size
base_radius = 1.5
# ปรับ radius ให้สัมพันธ์กับขนาดภาพ (ยิ่งภาพใหญ่ radius ยิ่งใหญ่ขึ้นเล็กน้อย)
dynamic_radius = base_radius * (width / 1000.0)
dynamic_radius = max(1.0, min(dynamic_radius, 3.0)) # จำกัดค่าระหว่าง 1.0 - 3.0

# ใช้ threshold สูงขึ้นเล็กน้อย (เช่น 4-6) เพื่อลด Noise ในพื้นที่เรียบ
enhanced = img.filter(ImageFilter.UnsharpMask(
    radius=dynamic_radius,
    percent=180,  # เพิ่ม percent เล็กน้อยเพื่อชดเชย radius ที่อาจเปลี่ยนไป
    threshold=5   # ปรับ threshold จาก 3 เป็น 5 เพื่อลด Halo
))
```

### 2. เพิ่มขั้นตอน "Local Contrast Enhancement" ด้วย `PIL.ImageOps.autocontrast` แบบแยก Channel (ใน `own_image_lab.py`)
**ปัญหา:** ภาพที่ Sharpen แล้วอาจดูแบน (Flat) ในบริเวณที่มี Dynamic Range ต่ำ
**วิธีแก้:** ใช้ `ImageOps.autocontrast` แต่ทำแยกตาม Channel (R, G, B) หรือใช้ `cutoff` parameter เพื่อปรับ Contrast เฉพาะส่วนที่จำเป็น
**โค้ดตัวอย่าง:**
```python
# ในฟังก์ชัน enhance_contrast()
# ใช้ cutoff=1% เพื่อตัดค่าที่มืดที่สุดและสว่างที่สุดออกเล็กน้อยก่อนปรับ Contrast
# ซึ่งช่วยเพิ่มรายละเอียดในเงาและไฮไลท์โดยไม่ทำให้ภาพดูแข็งเกินไป
enhanced = ImageOps.autocontrast(img, cutoff=1)
```

### 3. ปรับปรุงการลด Noise ก่อน Sharpen ด้วย `ImageFilter.MedianFilter` (ใน `photo_enhancement.py`)
**ปัญหา:** การ Sharpen ที่แรง (+34%) มักจะขยาย Noise เดิมที่มีอยู่ให้ชัดเจนขึ้น
**วิธีแก้:** เพิ่มขั้นตอนการลด Noise แบบ Non-Linear ก่อน Sharpen โดยใช้ `MedianFilter` ซึ่งรักษาขอบวัตถุได้ดีกว่า Gaussian Blur
**โค้ดตัวอย่าง:**
```python
# ในฟังก์ชัน pre_process() หรือก่

## รายงาน self-coder

<<<<<<< HEAD
{"ok": "False", "file": "photo_enhancement.py", "reason": "push failed, reverted: y.\nOmit --global to set the identity only in this repository.\n\nfatal: empty ident name (for <runner@runnervm0hi8g.r50ted", "t": "1795060851", "sources": "['local-brain', 'own-brain']", "focus": "photo_enhancement.py"}
=======
{"ok": "True", "file": "photo_enhancement.py", "reason": "pushed: local-brain", "t": "1795060836", "sources": "['local-brain', 'own-brain']", "focus": "photo_enhancement.py"}
>>>>>>> 7f872f3 (Replace PUBLIC STORE.html with new design; auto-write both files every pulse)
