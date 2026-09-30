import numpy as np, os, sys
from PIL import Image, ImageDraw
sys.path.insert(0, r"C:\Work\Projects\ShekMun\[Buddy]")
import av_scan

D = r"C:\Work\Projects\ShekMun\[Buddy]\.workbuddy\tmp\live3"
MAPPED = (153, 86, 530, 305)

rgbs = [np.asarray(Image.open(os.path.join(D, f'g{i}.jpg')).convert('RGB'), dtype=np.float32) for i in range(3)]
g0, g1, g2 = rgbs
lum = g0.mean(axis=2); br = g0[:,:,2]-g0[:,:,0]
print("frame", g0.shape[1], g0.shape[0])

x0,y0,x1,y1 = MAPPED
print("\n== column scan x %d..%d ==" % (x0-45, x1+45))
for x in range(x0-45, x1+46, 6):
    c = slice(y0+5, y1-5)
    print("  x=%3d lum %6.1f  B-R %+7.1f" % (x, lum[c,x].mean(), br[c,x].mean()))
print("\n== row scan y %d..%d ==" % (y0-40, y1+40))
for y in range(max(0,y0-40), min(720,y1+41), 6):
    c = slice(x0+5, x1-5)
    print("  y=%3d lum %6.1f  B-R %+7.1f" % (y, lum[y,c].mean(), br[y,c].mean()))

def stat(b, n):
    p = g0[b[1]:b[3], b[0]:b[2]]
    l = p.mean(axis=2)
    print("%-14s %-22s lum %6.1f dark %5.3f B-R %+6.1f sat %5.1f ar %.4f" % (
        n, str(b), l.mean(), (l<95).mean(), (p[:,:,2]-p[:,:,0]).mean(),
        (p.max(axis=2)-p.min(axis=2)).mean(), (b[2]-b[0])/max(1,(b[3]-b[1]))))
print()
stat(MAPPED, "mapped")
for nm, a in (("g1", g1), ("g2", g2)):
    p = a[y0:y1, x0:x1]; l = p.mean(axis=2)
    print("%-14s lum %6.1f dark %5.3f B-R %+6.1f sat %5.1f" % (nm, l.mean(), (l<95).mean(),
          (p[:,:,2]-p[:,:,0]).mean(), (p.max(axis=2)-p.min(axis=2)).mean()))

z = av_scan.panel_zoom_ocr([a.astype(np.uint8) for a in rgbs], MAPPED)
print("\nOCR mapped:", z or "<none>")

im = Image.open(os.path.join(D, 'g0.jpg')).convert('RGB')
im.crop(MAPPED).save(os.path.join(D, 'r3_box.jpg'), quality=92)
ov = im.copy(); d = ImageDraw.Draw(ov)
d.rectangle(MAPPED, outline=(255,0,0), width=3); ov.save(os.path.join(D, 'r3_overlay.png'))
print("saved r3_box.jpg / r3_overlay.png")
