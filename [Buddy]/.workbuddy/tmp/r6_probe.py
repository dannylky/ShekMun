import numpy as np, json, os
from PIL import Image

D = r"C:\Work\Projects\ShekMun\[Buddy]\.workbuddy\tmp\live6b"
MAPPED = (457, 8, 772, 225)

def load(f):
    return np.asarray(Image.open(os.path.join(D, f)).convert('RGB'), dtype=np.float32)

g0, g1, g2 = load('g0.jpg'), load('g1.jpg'), load('g2.jpg')
H, W = g0.shape[:2]
print("frame", W, H)

x0, y0, x1, y1 = MAPPED
# --- edge finding: column / row profiles on the mapped box neighbourhood ---
lum = g0.mean(axis=2)
br = g0[:, :, 2] - g0[:, :, 0]

print("\n== column mean B-R (x 430..800) ==")
for x in range(430, 801, 10):
    col = br[max(0,y0-30):y1+30, x]
    print("  x=%3d  B-R %+7.1f   lum %6.1f" % (x, col.mean(), lum[max(0,y0-30):y1+30, x].mean()))

print("\n== row mean B-R (y 0..250) ==")
for y in range(0, 251, 8):
    row = br[y, x0:x1]
    print("  y=%3d  B-R %+7.1f   lum %6.1f" % (y, row.mean(), lum[y, x0:x1].mean()))

def stat(patch, name):
    bb = patch[:, :, 2] - patch[:, :, 0]
    sat = patch.max(axis=2) - patch.min(axis=2)
    l = patch.mean(axis=2)
    print("%-28s lum %6.1f  dark(<95) %5.3f  B-R %+7.1f  sat %6.1f" % (
        name, l.mean(), (l < 95).mean(), bb.mean(), sat.mean()))

stat(g0[y0:y1, x0:x1], "mapped box")
stat(g1[y0:y1, x0:x1], "mapped box g1")
stat(g2[y0:y1, x0:x1], "mapped box g2")

# wall reference right of the screen
stat(g0[y0:y1, max(0,x1+20):x1+60], "wall right")
stat(g0[max(0,y0-25):y0-5, x0:x1], "ceiling above")
