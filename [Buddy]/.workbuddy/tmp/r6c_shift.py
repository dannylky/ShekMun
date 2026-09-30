import numpy as np, os
from PIL import Image

A = r"C:\Work\Projects\ShekMun\[Buddy]\.workbuddy\tmp\live6b"   # yest 16:03
B = r"C:\Work\Projects\ShekMun\[Buddy]\.workbuddy\tmp\live6c"   # today 09:07
ya = np.asarray(Image.open(os.path.join(A,'g0.jpg')).convert('L'), dtype=np.float32)
tb = np.asarray(Image.open(os.path.join(B,'g0.jpg')).convert('L'), dtype=np.float32)
H, W = ya.shape

def ncc(a, b):
    a = a - a.mean(); b = b - b.mean()
    d = (np.sqrt((a*a).sum()) * np.sqrt((b*b).sum()))
    return float((a*b).sum()/d) if d else 0.0

best = []
for dy in range(-40, 41, 4):
    for dx in range(-320, 321, 8):
        y0, y1 = max(0, dy), min(H, H+dy)
        yb0, yb1 = max(0, -dy), min(H, H-dy)
        x0, x1 = max(0, dx), min(W, W+dx)
        xb0, xb1 = max(0, -dx), min(W, W-dx)
        if (y1-y0) < 200 or (x1-x0) < 400: continue
        v = ncc(ya[yb0:yb1, xb0:xb1], tb[y0:y1, x0:x1])
        best.append((v, dx, dy))
best.sort(reverse=True)
print("best global shifts (NCC, dx, dy):")
for v, dx, dy in best[:8]:
    print("   %.4f  dx=%+4d dy=%+3d" % (v, dx, dy))
print("\nzero-shift NCC:", "%.4f" % ncc(ya, tb))

# if camera moved, does yesterday's marked box land on today's blue region?
v, dx, dy = best[0]
print("\nif shift (dx=%d,dy=%d): marked box (474,12,765,196) -> (%d,%d,%d,%d)" % (
    dx, dy, 474+dx, 12+dy, 765+dx, 196+dy))
