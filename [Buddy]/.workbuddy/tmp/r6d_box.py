import numpy as np
from PIL import Image
from scipy import ndimage

MARK = r"C:\Users\Danny\.workbuddy\clipboard-images\clipboard-2026-09-30T01-15-23-074Z-43ac3b08.jpg"
im = Image.open(MARK).convert('RGB')
W, H = im.size
a = np.asarray(im, dtype=np.int16)
print("mark", W, H, "ar %.4f" % (W/H))
r, g, b = a[:,:,0], a[:,:,1], a[:,:,2]

red = (r > 140) & (r - g > 60) & (r - b > 50)
lab, n = ndimage.label(red)
print("red blobs", n)
boxes = []
for i in range(1, n+1):
    m = (lab == i)
    if m.sum() < 300: continue
    filled = ndimage.binary_fill_holes(m)
    fy, fx = np.where(filled)
    bx = (int(fx.min()), int(fy.min()), int(fx.max()), int(fy.max()))
    boxes.append(bx)
    print("  RED bbox=(%d,%d,%d,%d) %dx%d ar %.4f fill %.3f npix %d" % (
        bx[0],bx[1],bx[2],bx[3], bx[2]-bx[0], bx[3]-bx[1],
        (bx[2]-bx[0])/max(1,bx[3]-bx[1]), m.sum()/filled.sum(), m.sum()))

green = (g > 130) & (g - r > 50) & (g - b > 50)
l2, n2 = ndimage.label(green)
for i in range(1, n2+1):
    m = (l2 == i)
    if m.sum() < 300: continue
    filled = ndimage.binary_fill_holes(m)
    fy, fx = np.where(filled)
    print("  GREEN bbox=(%d,%d,%d,%d) %dx%d ar %.4f" % (
        fx.min(),fy.min(),fx.max(),fy.max(), fx.max()-fx.min(), fy.max()-fy.min(),
        (fx.max()-fx.min())/max(1,fy.max()-fy.min())))
print("green blobs(>=300px):", sum(1 for i in range(1,n2+1) if (l2==i).sum()>=300))

if boxes:
    ux0=min(b[0] for b in boxes); uy0=min(b[1] for b in boxes)
    ux1=max(b[2] for b in boxes); uy1=max(b[3] for b in boxes)
    print("\nunion", (ux0,uy0,ux1,uy1), "%dx%d ar %.4f" % (ux1-ux0, uy1-uy0, (ux1-ux0)/(uy1-uy0)))
    sx = 1280.0/W; sy = 720.0/H
    print("scale x %.5f  y %.5f   (ar match: %s)" % (
        sx, sy, "uniform" if abs(sx-sy)/sx < 0.01 else "NON-uniform!"))
    for sy_use, tag in ((sx,"uniform-x"), (sy,"uniform-y")):
        m = (round(ux0*sx), round(uy0*sy_use), round(ux1*sx), round(uy1*sy_use))
        print("  mapped[%s] %s %dx%d ar %.4f" % (tag, m, m[2]-m[0], m[3]-m[1], (m[2]-m[0])/max(1,m[3]-m[1])))
