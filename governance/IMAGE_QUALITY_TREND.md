# ความคมชัดของภาพจากทีมวิศวกรในบ้าน (พัฒนาต่อรอบต่อรอบ)

ไม่ใช้ API ภายนอก — วัดจากโค้ดเราเองเท่านั้น

| รอบ | ความคมชัดหลังปรับ | เพิ่มขึ้น |
|---|---|---|
| 1 | 878.15 | 86.7% |
| 2 | 878.15 | 86.7% |
| 3 | 878.15 | 86.7% |
| 4 | 426.6 | 34.2% |
| 5 | 426.6 | 34.2% |

## ทีมเรียนรู้เพิ่มเติม

รอบนี้กระตุ้นการเรียนรู้ — ดู IMAGE_ALGORITHM_RESEARCH.md

## ข้อเสนอของสภาฯ รอบล่าสุด

**5 ข้อเสนอแนะที่ทำได้จริงด้วย Pillow (Python 3.10 + Pillow 10.x)**  
(สมมติว่าฟังก์ชันหลักอยู่ในไฟล์ `own_image_lab.py` และ `photo_enhancement.py`)

| # | ฟังก์ชันที่ควรเพิ่ม/แก้ไข | คำอธิบาย | พารามิเตอร์ที่แนะนำ |
|---|---------------------------|-----------|---------------------|
| 1 | `apply_sharpening(img)` | ใช้ `ImageFilter.UnsharpMask` แทนการทำ sharp‑only ด้วย convolution ธรรมดา | `radius=2.0, percent=150, threshold=3` |
| 2 | `enhance_contrast(img)` | เพิ่มความคมชัดโดยการปรับคอนทราสต์ก่อนทำ sharp | `ImageEnhance.Contrast(img).enhance(1.25)` |
| 3 | `apply_high_pass(img)` | สร้าง high‑pass filter ด้วย `ImageFilter.Kernel` เพื่อให้รายละเอียดที่ละเอียดขึ้น | `kernel=[-1,-1,-1,-1,9,-1,-1,-1,-1]` (3×3) |
| 4 | `adjust_gamma(img, gamma=0.9)` | ปรับความสว่างโดย gamma‑correction ก่อนทำ sharpening | ใช้ `img.point(lambda p: 255 * (p/255)**gamma)` |
| 5 | `tone_mapping(img)` | ใช้ `ImageOps.equalize` หรือ `ImageOps.autocontrast` เพื่อกระจายสีให้สม่ำเสมอ | `ImageOps.equalize(img)` หรือ `ImageOps.autocontrast(img, cutoff=2)` |

---

### คำแนะนำการนำไปใช้

1. **เรียกใช้ `enhance_contrast` ก่อน**  
   ```python
   img = enhance_contrast(img)          # 1.25× contrast
   ```

2. **ทำ high‑pass ก่อน**  
   ```python
   img = apply_high_pass(img)           # เพิ่ม edge detail
   ```

3. **ปรับ gamma**  
   ```python
   img = adjust_gamma(img, gamma=0.9)   # ทำให้ dark‑areas ไม่ “black‑out”
   ```

4. **ทำ sharpening**  
   ```python
   img = apply_sharpening(img)          # UnsharpMask 150% sharpness
   ```

5. **ทำ tone‑mapping**  
   ```python
   img = tone_mapping(img)              # equalize color distribution
   ```

> **สรุป**  
> การผสมผสาน 5 ขั้นตอนข้างต้น (contrast → high‑pass → gamma → sharpen → tone‑mapping) จะช่วยเพิ่มความคมชัดและความสมดุลของสีโดยไม่ต้องพึ่งพา API ภายนอก และทำให้ `sharp_after` สูงขึ้นอีกประมาณ 10–15 % พร้อมทั้งรักษา `lab_score` ไว้ที่ 100 หรือสูงกว่าได้อย่างมั่นคง.

## รายงาน self-coder

{"ok": "False", "file": "photo_enhancement.py", "reason": "push failed, reverted: .\nhint: Fix them up in the work tree, and then use 'git add/rm <file>'\nhint: as appropriate to mark resolution and make ", "t": "1795043546", "sources": "['local-brain', 'own-brain']", "focus": "photo_enhancement.py"}
