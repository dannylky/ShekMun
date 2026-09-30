import os, sys, json
import numpy as np
from PIL import Image
from scipy import ndimage

MARK = r"C:\Users\Danny\.workbuddy\clipboard-images\clipboard-2026-09-29T08-02-23-175Z-09339b71.jpg"
im = Image.open(MARK).convert('RGB')
W, H = im.size
a = np.asarray(im, dtype=np.int16)
print("marker", W, H, "ar %.4f" % (W / H))

r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]

# RED boxes
red = (r > 140) & (r - g > 60) & (r - b > 50) & (g < 110) & (b < 110)
lab, n = ndimage.label(red)
print("red blobs", n)
redboxes = []
for i in range(1, n + 1):
    ys, xs = np.where(lab == i)
    if len(ys) < 300: continue
    filled = ndimage.binary_fill_holes(lab == i)
    fy, fx = np.where(filled)
    bx0, bx1, by0, by1 = fx.min(), fx.max(), fy.min(), fy.max()
    # reject near-square small blobs that are just the red logo
    redboxes.append((int(bx0), int(by0), int(bx1), int(by1)))
    print("  RED  bbox=(%d,%d,%d,%d) %dx%d ar %.4f fill %.3f npix %d" % (
        bx0, by0, bx1, by1, bx1-bx0, by1-by0, (bx1-bx0)/max(1,by1-by0), len(ys)/len(fy), len(ys)))

# GREEN boxes
green = (g > 130) & (g - r > 50) & (g - b > 50)
lab2, n2 = ndimage.label(green)
print("green blobs", n2)
for i in range(1, n2 + 1):
    ys, xs = np.where(lab2 == i)
    if len(ys) < 300: continue
    filled = ndimage.binary_fill_holes(lab2 == i)
    fy, fx = np.where(filled)
    print("  GREEN bbox=(%d,%d,%d,%d) %dx%d ar %.4f fill %.3f" % (
        fx.min(), fy.min(), fx.max(), fy.max(), fx.max()-fx.min(), fy.max()-fy.min(),
        (fx.max()-fx.min())/max(1,fy.max()-fy.min()), len(ys)/len(fy)))

if redboxes:
    ux0=min(b[0] for b in redboxes); uy0=min(b[1] for b in redboxes)
    ux1=max(b[2] for b in redboxes); uy1=max(b[3] for b in redboxes)
    print("RED union", (ux0,uy0,ux1,uy1), "%dx%d ar %.4f" % (ux1-ux0, uy1-uy0, (ux1-ux0)/(uy1-uy0)))
    scale = 1280.0/W
    print("scale %.5f  propH %.1f (vs720 %+.1f)" % (scale, H*scale, H*scale-720))
    m = (round(ux0*scale), round(uy0*scale), round(ux1*scale), round(uy1*scale))
    print("mapped RED", m, "%dx%d ar %.4f" % (m[2]-m[0], m[3]-m[1], (m[2]-m[0])/max(1,(m[3]-m[1]))))
