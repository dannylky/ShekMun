import numpy as np, os
from PIL import Image

D = r"C:\Work\Projects\ShekMun\[Buddy]\.workbuddy\tmp\live6c"
a = np.asarray(Image.open(os.path.join(D, 'g0.jpg')).convert('RGB'), dtype=np.float32)
H, W = a.shape[:2]
r, g, b = a[:,:,0], a[:,:,1], a[:,:,2]
dg = b - g; dr = g - r
blue = (dg > 35) & (dr > 12)

print("== blue-lock pixel coverage: column scan (whole height) ==")
for x in range(0, W, 20):
    print("  x=%4d  blue%% %5.1f  b-g %+6.1f  lum %6.1f" % (
        x, blue[:, x:x+20].mean()*100, dg[:, x:x+20].mean(), a[:, x:x+20].mean()))

print("\n== blue-lock pixel coverage: row scan (whole width) ==")
for y in range(0, 300, 8):
    print("  y=%4d  blue%% %5.1f  b-g %+6.1f  lum %6.1f" % (
        y, blue[y:y+8, :].mean()*100, dg[y:y+8, :].mean(), a[y:y+8, :].mean()))

# bounding box of the dense blue area
rows = blue.mean(axis=1); cols = blue.mean(axis=0)
ys = np.where(rows > 0.35)[0]; xs = np.where(cols > 0.35)[0]
print("\ndense-blue rows:", (ys.min(), ys.max()) if len(ys) else None)
print("dense-blue cols:", (xs.min(), xs.max()) if len(xs) else None)

def stat(bx, n):
    p = a[bx[1]:bx[3], bx[0]:bx[2]]
    l = p.mean(axis=2)
    d1 = p[:,:,2]-p[:,:,1]; d2 = p[:,:,1]-p[:,:,0]
    print("%-26s lum %6.1f b-g %+6.1f g-r %+6.1f B-R %+7.1f sat %6.1f lockshare %.3f ar %.3f" % (
        n, l.mean(), d1.mean(), d2.mean(), (p[:,:,2]-p[:,:,0]).mean(),
        (p.max(axis=2)-p.min(axis=2)).mean(),
        ((d1>35)&(d2>12)).mean(), (bx[2]-bx[0])/max(1,(bx[3]-bx[1]))))

print()
stat((474,12,765,196), "marked (yesterday)")
if len(xs) and len(ys):
    stat((int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())), "dense blue bbox")
stat((736,0,1104,320), "736-1104 x 0-320")
stat((736,0,1104,96), "736,0,1104,96 (blob)")
