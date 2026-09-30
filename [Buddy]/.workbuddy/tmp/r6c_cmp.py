import numpy as np, os, sys
from PIL import Image
sys.path.insert(0, r"C:\Work\Projects\ShekMun\[Buddy]")
import av_scan

A = r"C:\Work\Projects\ShekMun\[Buddy]\.workbuddy\tmp\live6b"   # yest 16:03
B = r"C:\Work\Projects\ShekMun\[Buddy]\.workbuddy\tmp\live6c"   # today 09:07

def load(d):
    return [np.asarray(Image.open(os.path.join(d, f'g{i}.jpg')).convert('RGB'), dtype=np.float32) for i in range(3)]

ya, ta = load(A), load(B)

def stat(a, bx, n):
    p = a[bx[1]:bx[3], bx[0]:bx[2]]
    l = p.mean(axis=2)
    d1 = p[:,:,2]-p[:,:,1]; d2 = p[:,:,1]-p[:,:,0]
    print("   %-30s lum %6.1f b-g %+6.1f g-r %+6.1f B-R %+7.1f sat %6.1f lockshare %.3f dark %.3f" % (
        n, l.mean(), d1.mean(), d2.mean(), (p[:,:,2]-p[:,:,0]).mean(),
        (p.max(axis=2)-p.min(axis=2)).mean(), ((d1>35)&(d2>12)).mean(), (l<95).mean()))

CAND = {
    "marked  (474,12,765,196)": (474,12,765,196),
    "blue    (736,0,1104,200)": (736,0,1104,200),
    "old cfg (738,6,1063,199)": (738,6,1063,199),
    "blue2   (736,0,1104,160)": (736,0,1104,160),
}
print("=== YESTERDAY 16:03 (live6b) — box was showing AVoIP standby ===")
for n, bx in CAND.items(): stat(ya[0], bx, n)
print("\n=== TODAY 09:07 (live6c) ===")
for n, bx in CAND.items(): stat(ta[0], bx, n)

print("\n=== OCR: blue region today ===")
z = av_scan.panel_zoom_ocr([x.astype(np.uint8) for x in ta], (736,0,1104,200))
print("   ", z or "<none>")
print("=== OCR: blue region yesterday ===")
z = av_scan.panel_zoom_ocr([x.astype(np.uint8) for x in ya], (736,0,1104,200))
print("   ", z or "<none>")
print("=== OCR: marked box yesterday (known good) ===")
z = av_scan.panel_zoom_ocr([x.astype(np.uint8) for x in ya], (474,12,765,196))
print("   ", z or "<none>")

# full-frame OCR both days
for tag, fs in (("YEST 16:03", ya), ("TODAY 09:07", ta)):
    print("\n=== full-frame OCR %s ===" % tag)
    try:
        for it in av_scan.ocr_frame(np.asarray(fs[0], dtype=np.uint8))[:14]:
            bx = it.get('box') or []
            xs = [p[0] for p in bx] if bx else []
            print("   %-42s x=%s" % (it['text'][:42], (int(min(xs)), int(max(xs))) if xs else '?'))
    except Exception as e:
        print("  err", e)

# save side-by-side crops for Danny
for tag, fs in (("yest", ya), ("today", ta)):
    im = Image.open(os.path.join(A if tag=="yest" else B, 'g0.jpg')).convert('RGB')
    im.crop((474,12,765,196)).resize((582,368), Image.LANCZOS).save(
        os.path.join(B, 'cmpA_%s.png' % tag))
    im.crop((736,0,1104,200)).resize((736,400), Image.LANCZOS).save(
        os.path.join(B, 'cmpB_%s.png' % tag))
print("\nsaved cmpA_yest/today.png (marked box)  cmpB_yest/today.png (blue region)")
