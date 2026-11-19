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

## ทีมเรียนรู้เพิ่มเติม

รอบนี้กระตุ้นการเรียนรู้ — ดู IMAGE_ALGORITHM_RESEARCH.md

## ข้อเสนอของสภาฯ รอบล่าสุด

สวัสดีครับ ในฐานะที่ปรึกษาทีมวิศวกรภาพ ผมวิเคราะห์ผลวัดรอบนี้ว่า **Sharpness เพิ่มขึ้น 34.2% (จาก 317.82 เป็น 426.6)** ซึ่งถือว่าผลลัพธ์ดีมาก และ **Lab Score เต็ม 100** แสดงว่าความถูกต้องของสีและโครงสร้างภาพอยู่ในระดับที่รับได้

อย่างไรก็ตาม การที่ Source เป็น "in-house algorithm only" และ Sharpness สูงขึ้นมาก อาจมีความเสี่ยงเรื่อง **Artifacts (เช่น ringing หรือ noise amplification)** หากไม่ควบคุมดีพอ ดังนั้น 5 ข้อเสนอแนะเพื่อปรับปรุงโค้ดใน `own_image_lab.py` และ `photo_enhancement.py` โดยใช้ **Pillow เท่านั้น** เพื่อรักษาคุณภาพและเสถียรภาพ มีดังนี้:

### 1. ปรับพารามิเตอร์ `UnsharpMask` แบบ Adaptive แทนค่าคงที่
**ไฟล์:** `photo_enhancement.py`  
**ฟังก์ชัน:** `enhance_sharpness()`  
**ปัญหา:** การใช้ `radius` และ `percent` คงที่อาจทำให้ภาพบางจุดคมเกินไป (over-sharpened) หรือไม่คมพอ  
**การปรับปรุง:**  
- แทนที่จะใช้ค่าคงที่ เช่น `radius=2, percent=150` ให้คำนวณค่าเหล่านี้จาก **Local Variance** หรือ **Edge Strength** ของภาพ  
- ตัวอย่างโค้ด:
  ```python
  from PIL import ImageFilter, ImageEnhance
  import numpy as np

  def adaptive_unsharp_mask(img, base_radius=1.5, base_percent=120):
      # คำนวณ edge strength โดยประมาณ (ใช้ Sobel หรือ Laplacian)
      gray = img.convert('L')
      laplacian = gray.filter(ImageFilter.Kernel(
          size=3,
          kernel=[0, -1, 0, -1, 5, -1, 0, -1, 0],
          scale=1,
          offset=128
      ))
      # คำนวณค่าเฉลี่ยของความเข้มของขอบ
      edge_strength = np.mean(laplacian)
      
      # ปรับ radius และ percent ตาม edge_strength
      # ถ้าขอบมาก -> ลด percent เพื่อลด ringing
      # ถ้าขอบน้อย -> เพิ่ม percent เพื่อเพิ่มความคม
      adjusted_percent = base_percent - (edge_strength * 0.5)  # ปรับตามความเหมาะสม
      adjusted_radius = base_radius + (edge_strength * 0.1)
      
      # ใช้ UnsharpMask
      return img.filter(ImageFilter.UnsharpMask(
          radius=adjusted_radius,
          percent=adjusted_percent,
          threshold=3  # เพิ่ม threshold เพื่อลด noise ในพื้นที่เรียบ
      ))
  ```

### 2. เพิ่มขั้นตอน `Noise Reduction` ก่อน Sharpening
**ไฟล์:** `own_image_lab.py`  
**ฟังก์ชัน:** `preprocess_image()`  
**ปัญหา:** Sharpening จะขยาย Noise ไปด้วยเสมอ หากภาพต้นทางมี Noise สูง ผลลัพธ์จะดู "หยาบ" แม้ Sharpness score สูง  
**การปรับปรุง:**  
- ใช้ `ImageFilter.MedianFilter` หรือ `ImageFilter.GaussianBlur` (ค่าเล็กมาก) เพื่อลด Noise ก่อน Sharpening  
- ตัวอย่าง:
  ```python
  from PIL import ImageFilter

  def reduce_noise_before_sharpen(img, noise_level=1):
      # ใช้ MedianFilter เพื่อลด salt-a

## รายงาน self-coder

{"ok": "False", "file": "photo_enhancement.py", "reason": "push failed, reverted: fatal: unable to access 'https://github.com/Vorakan-yakham/zyphere-ai-agent.git/': Empty reply from server\n", "t": "1795058624", "sources": "['local-brain', 'own-brain']", "focus": "photo_enhancement.py"}
