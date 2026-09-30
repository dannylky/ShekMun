import numpy as np, os
from PIL import Image

D = r"C:\Work\Projects\ShekMun\[Buddy]\.workbuddy\tmp\live6b"
g0 = np.asarray(Image.open(os.path.join(D, 'g0.jpg')).convert('RGB'), dtype=np.float32)
lum = g0.mean(axis=2); br = g0[:,:,2]-g0[:,:,0]
sat = g0.max(axis=2)-g0.min(axis=2)

print("== fine x scan (470..490 and 755..780), rows y=20..190 ==")
for x in list(range(468, 492, 2)) + list(range(755, 782, 2)):
    c = slice(20,190)
    print("  x=%3d lum %6.1f  B-R %+7.1f  sat %5.1f" % (x, lum[c,x].mean(), br[c,x].mean(), sat[c,x].mean()))

print("\n== fine y scan (4..24 and 188..212), cols x=480..760 ==")
for y in list(range(4, 26, 2)) + list(range(186, 214, 2)):
    c = slice(480,760)
    print("  y=%3d lum %6.1f  B-R %+7.1f  sat %5.1f" % (y, lum[y,c].mean(), br[y,c].mean(), sat[y,c].mean()))

def stat(b, n):
    p = g0[b[1]:b[3], b[0]:b[2]]
    l = p.mean(axis=2)
    print("%-24s box=%-20s lum %6.1f dark %5.3f B-R %+6.1f sat %5.1f ar %.4f" % (
        n, str(b), l.mean(), (l<95).mean(), (p[:,:,2]-p[:,:,0]).mean(),
        (p.max(axis=2)-p.min(axis=2)).mean(), (b[2]-b[0])/max(1,(b[3]-b[1]))))

stat((457,8,772,225), "mapped")
stat((474,12,765,196), "measured")
stat((474,12,765,198), "measured y196-198 hmm")
