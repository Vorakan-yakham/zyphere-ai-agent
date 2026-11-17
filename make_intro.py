from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math, os

W, H = 1080, 1920
D = r"C:\Users\vornl\Documents\zyphere\Downloads_zyphere_intro"
os.makedirs(D, exist_ok=True)
FB = r"C:\Users\vornl\Documents\zyphere\fonts\NotoSansThai-Bold.ttf"
FR = r"C:\Users\vornl\Documents\zyphere\fonts\NotoSansThai-Regular.ttf"
LB = r"C:\Windows\Fonts\segoeuib.ttf"
LR = r"C:\Windows\Fonts\segoeui.ttf"

def font(p, s): return ImageFont.truetype(p, s)

img = Image.new("RGB", (W, H), (8, 12, 24))
d = ImageDraw.Draw(img)
for y in range(H):
    t = y / H
    d.line([(0, y), (W, y)], fill=(int(10+30*math.sin(t*3.1)**2), int(14+20*math.sin(t*2.3+1)**2), int(30+60*t)))

glow = Image.new("RGBA", (W, H), (0,0,0,0))
gd = ImageDraw.Draw(glow)
for cx,cy,rad,col in [(540,520,380,(61,224,255,60)),(540,520,240,(139,92,246,70)),(540,1500,300,(236,72,153,40))]:
    gd.ellipse([cx-rad,cy-rad,cx+rad,cy+rad], fill=col)
img = Image.alpha_composite(img.convert("RGBA"), glow.filter(ImageFilter.GaussianBlur(90)))
d = ImageDraw.Draw(img)

cx,cy,R = 540,520,210
d.ellipse([cx-R-14,cy-R-14,cx+R+14,cy+R+14], fill=(61,224,255,40))
d.ellipse([cx-R,cy-R,cx+R,cy+R], fill=(16,24,48), outline=(61,224,255), width=8)
zf = font(LB,230); bb=d.textbbox((0,0),"Z",font=zf)
d.text((cx-(bb[2]-bb[0])/2-bb[0], cy-(bb[3]-bb[1])/2-bb[1]-10), "Z", font=zf, fill=(235,252,255))

def draw_center_mixed(parts, y):
    # parts = list of (text, font); measure total width then draw centered
    widths=[d.textlength(t,font=f) for t,f in parts]; total=sum(widths)
    x=(W-total)/2
    for (t,f),w in zip(parts,widths):
        d.text((x,y),t,font=f,fill=(223,252,255)); x+=w

draw_center_mixed([("Zyphere",font(LB,96))],800)
# Thai + Latin mixed without middle-dot / exotic glyphs
draw_center_mixed([("ไซเฟอร์ ",font(FB,62)),("AI",font(LB,60)),(" ส่วนตัวของคุณ",font(FB,62))],940)
draw_center_mixed([("สวัสดีครับ ผมคือไซเฟอร์",font(FB,56))],1120)

features=[("แชท",(61,224,255)),("โค้ด",(139,92,246)),("รูป",(236,72,153)),("วิดีโอ",(245,158,11)),("เว็บ",(52,211,153))]
fx,gap,fy=150,195,1420; fi=font(FR,36)
for i,(name,col) in enumerate(features):
    x=fx+i*gap
    d.rounded_rectangle([x-70,fy,x+70,fy+140],radius=28,fill=(20,30,60),outline=col,width=4)
    d.text((x-d.textlength(name,font=fi)/2,fy+50),name,font=fi,fill=(235,245,255))

draw_center_mixed([("สนทนา   เรียนรู้   จำได้   สร้างสรรค์",font(FR,34))],1680)
out=os.path.join(D,"zyphere_intro_1080x1920.png")
img.convert("RGB").save(out,"PNG")
print(out, os.path.getsize(out))
