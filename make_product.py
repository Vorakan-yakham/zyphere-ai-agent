"""Create a sellable digital-product package from Zyphere's generated assets."""
import os, json, shutil, zipfile

BASE = r"C:\Users\vornl\Documents\zyphere"
OUT = r"C:\Users\vornl\Downloads\zyphere_product_pack"
os.makedirs(OUT, exist_ok=True)

items = [
    (r"C:\Users\vornl\Downloads\zyphere_promo.mp4", "zyphere_promo.mp4"),
    (r"C:\Users\vornl\Downloads\zyphere_intro.png", "zyphere_intro.png"),
    (r"C:\Users\vornl\Downloads\zyphere_chud_khai.txt", "chud_khai.txt"),
]
for src, name in items:
    if os.path.exists(src):
        shutil.copy(src, os.path.join(OUT, name))

readme = """========================================
ZYPHERE Digital Pack — ชุดของขาย
========================================
สิ่งที่ได้:
1. zyphere_promo.mp4 — คลิปโปรโมต 15 วิ (เสียง+ภาพ)
2. zyphere_intro.png — การ์ด 1080x1920 สำหรับมือถือ
3. chud_khai.txt — ข้อความโพสต์ FB/X/TikTok/Line + วิธีขาย

ลอง AI: https://tinyurl.com/zyphere-ai

ราคา: 99 บาท (สนับสนุนการพัฒนา)
ชำระ: PromptPay 0941939686 / กสิกรไทย 007 8 468 262
หลังชำระ แจ้งหลักฐานผ่าน Inbox/Line เพื่อรับไฟล์เพิ่มเติม
"""
open(os.path.join(OUT, "README.txt"), "w", encoding="utf-8").write(readme)

zpath = os.path.join(OUT, "zyphere_digital_pack.zip")
with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
    for f in os.listdir(OUT):
        if f.endswith(".zip"):
            continue
        z.write(os.path.join(OUT, f), f)
print("created", zpath, os.path.getsize(zpath))
