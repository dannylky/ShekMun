import os, sys, json
import numpy as np
from PIL import Image
from scipy import ndimage

MARK = r"C:\Users\Danny\.workbuddy\clipboard-images\clipboard-2026-09-29T04-50-07-901Z-2badeba6.jpg"
OUT = r"C:\Work\Projects\ShekMun\[Buddy]\.workbuddy\tmp\live3"
os.makedirs(OUT, exist_ok=True)

im = Image.open(MARK).convert('RGB')
W, H = im.size
a = np.asarray(im, dtype=np.int16)
print("marker", W, H, "ar %.4f" % (W / H))

r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
mask = (r > 150) & (g < 90) & (b < 90) & (r - g > 70) & (r - b > 60)
lab, n = ndimage.label(mask)
print("blobs", n)
boxes = []
for i in range(1, n + 1):
    ys, xs = np.where(lab == i)
    if len(ys) < 200:
        continue
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    filled = ndimage.binary_fill_holes(lab == i)
    fy, fx = np.where(filled)
    if len(fy) == 0:
        continue
    bx0, bx1, by0, by1 = fx.min(), fx.max(), fy.min(), fy.max()
    boxes.append((bx0, by0, bx1, by1))
    print("  blob %d  bbox=(%d,%d,%d,%d) %dx%d ar %.4f  fillfrac %.3f" % (
        i, bx0, by0, bx1, by1, bx1 - bx0, by1 - by0,
        (bx1 - bx0) / max(1, by1 - by0), len(ys) / len(fy)))

# union of all frames
if boxes:
    ux0 = min(b[0] for b in boxes); uy0 = min(b[1] for b in boxes)
    ux1 = max(b[2] for b in boxes); uy1 = max(b[3] for b in boxes)
    print("union", (ux0, uy0, ux1, uy1), "%dx%d ar %.4f" % (ux1-ux0, uy1-uy0, (ux1-ux0)/(uy1-uy0)))

scale = 1280.0 / W
print("width scale %.5f   prop height %.1f  (vs 720 -> %+.1f)" % (scale, H * scale, H * scale - 720))
for b in boxes:
    m = (int(round(b[0]*scale)), int(round(b[1]*scale)), int(round(b[2]*scale)), int(round(b[3]*scale)))
    print("  mapped", b, "->", m, "%dx%d ar %.4f" % (m[2]-m[0], m[3]-m[1], (m[2]-m[0])/max(1,(m[3]-m[1]))))
