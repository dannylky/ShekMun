import numpy as np, os, sys
from PIL import Image, ImageDraw
sys.path.insert(0, r"C:\Work\Projects\ShekMun\[Buddy]")
import av_scan

D = r"C:\Work\Projects\ShekMun\[Buddy]\.workbuddy\tmp\live6b"
BOX = (474, 12, 765, 196)

rgbs = [np.asarray(Image.open(os.path.join(D, f'g{i}.jpg')).convert('RGB'), dtype=np.uint8) for i in range(3)]
print("OCR full panel (box %s):" % (BOX,))
z = av_scan.panel_zoom_ocr(rgbs, BOX)
for ln in z:
    print("   ", ln)
if not z:
    print("    <no AVoIP keyword read>")

im = Image.open(os.path.join(D, 'g0.jpg')).convert('RGB')
im.crop(BOX).save(os.path.join(D, 'r6_box.jpg'), quality=92)
c2 = im.crop((BOX[0]-40, BOX[1]-40, BOX[2]+40, BOX[3]+40))
c2.resize((c2.width*2, c2.height*2), Image.LANCZOS).save(os.path.join(D, 'r6_box_zoom.png'))
ov = im.copy(); d = ImageDraw.Draw(ov)
d.rectangle(BOX, outline=(255,0,0), width=3)
d.rectangle((457,8,772,225), outline=(0,255,0), width=2)
ov.save(os.path.join(D, 'r6_overlay.png'))
print("saved r6_box.jpg / r6_box_zoom.png / r6_overlay.png (red=measured, green=mapped)")
