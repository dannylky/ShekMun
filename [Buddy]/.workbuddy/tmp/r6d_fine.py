import numpy as np, os, sys
from PIL import Image, ImageDraw
D = r"C:\Work\Projects\ShekMun\[Buddy]\.workbuddy\tmp\live6c"
a = np.asarray(Image.open(os.path.join(D,'g0.jpg')).convert('RGB'), dtype=np.float32)
lum = a.mean(axis=2); b = a[:,:,2]; g = a[:,:,1]; r = a[:,:,0]
dg = b - g
MAPPED = (732, 1, 1076, 204)

print("== fine column scan x 700..760 and 1040..1090 (rows y=20..190) ==")
for x in list(range(700, 762, 3)) + list(range(1040, 1092, 3)):
    c = slice(20, 190)
    print("  x=%4d lum %6.1f  b-g %+6.1f  bluish%% %5.1f" % (
        x, lum[c,x].mean(), dg[c,x].mean(), ((dg[c,x]>35)).mean()*100))

print("\n== fine row scan y 0..26 and 185..215 (cols x=760..1040) ==")
for y in list(range(0, 28, 2)) + list(range(184, 216, 2)):
    c = slice(760, 1040)
    print("  y=%4d lum %6.1f  b-g %+6.1f  bluish%% %5.1f" % (
        y, lum[y,c].mean(), dg[y,c].mean(), ((dg[y,c]>35)).mean()*100))

def stat(bx, n):
    p = a[bx[1]:bx[3], bx[0]:bx[2]]
    l = p.mean(axis=2)
    d1 = p[:,:,2]-p[:,:,1]; d2 = p[:,:,1]-p[:,:,0]
    print("%-20s %-24s lum %6.1f b-g %+6.1f g-r %+6.1f lockshare %.3f dark %.3f ar %.4f" % (
        n, str(bx), l.mean(), d1.mean(), d2.mean(), ((d1>35)&(d2>12)).mean(),
        (l<95).mean(), (bx[2]-bx[0])/max(1,(bx[3]-bx[1]))))

print()
stat(MAPPED, "mapped")
stat((738,6,1063,199), "old cfg")
for cand in [(740,10,1062,196),(738,8,1064,197),(736,8,1064,198),(738,6,1063,199)]:
    stat(cand, "cand")
