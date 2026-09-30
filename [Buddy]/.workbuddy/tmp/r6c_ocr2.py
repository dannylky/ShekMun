import numpy as np, os, sys
from PIL import Image, ImageOps
sys.path.insert(0, r"C:\Work\Projects\ShekMun\[Buddy]")
import av_scan

D = r"C:\Work\Projects\ShekMun\[Buddy]\.workbuddy\tmp\live6c"
rgbs = [np.asarray(Image.open(os.path.join(D, f'g{i}.jpg')).convert('RGB'), dtype=np.uint8) for i in range(3)]

def ocr_crop(box, tag, scales=(2,3,4)):
    print("\n--- OCR %s %s ---" % (tag, box))
    x0,y0,x1,y1 = box
    for arr in rgbs[:2]:
        c = Image.fromarray(arr[y0:y1, x0:x1]).convert('L')
        for sc in scales:
            cc = ImageOps.autocontrast(c, cutoff=2).resize((c.width*sc, c.height*sc), Image.LANCZOS)
            try:
                for it in av_scan.ocr_frame(np.asarray(cc.convert('RGB'))):
                    t = it['text']
                    if len(t) >= 2:
                        print("    x%-2d %r" % (sc, t[:60]))
            except Exception as e:
                print("    err", e)
            break
        break

ocr_crop((474,12,765,196), "MARKED box")
ocr_crop((736,0,1104,200), "BLUE region")

# look for a clock glyph region: large bright digits
a = rgbs[0].astype(np.float32)
lum = a.mean(axis=2)
print("\n== brightest zones (possible clock digits) ==")
for tag, (x0,y0,x1,y1) in (("marked",(474,12,765,196)), ("blue",(736,0,1104,200))):
    p = lum[y0:y1, x0:x1]
    thr = np.percentile(p, 97)
    m = p > thr
    ys, xs = np.where(m)
    print("  %-7s p97=%.0f  bright-pixel bbox x=%d..%d y=%d..%d  count=%d" % (
        tag, thr, xs.min()+x0, xs.max()+x0, ys.min()+y0, ys.max()+y0, len(xs)))
