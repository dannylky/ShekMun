import numpy as np, os, sys
from PIL import Image, ImageDraw
sys.path.insert(0, r"C:\Work\Projects\ShekMun\[Buddy]")
import av_scan

D = r"C:\Work\Projects\ShekMun\[Buddy]\.workbuddy\tmp\live6c"
BOX = (474, 12, 765, 196)
OTHER = (736, 0, 1104, 96)

rgbs = [np.asarray(Image.open(os.path.join(D, f'g{i}.jpg')).convert('RGB'), dtype=np.float32) for i in range(3)]

def probe(a, b, n):
    p = a[b[1]:b[3], b[0]:b[2]]
    r, g, bl = p[:,:,0], p[:,:,1], p[:,:,2]
    lum = p.mean(axis=2)
    dg = bl - g; dr = g - r
    share = float(((dg > av_scan.LOCK_BG_DG) & (dr > av_scan.LOCK_BG_DR)).mean())
    br = bl - r
    sat = p.max(axis=2) - p.min(axis=2)
    print("%-22s lum %6.1f | b-g %+6.1f g-r %+6.1f B-R %+6.1f sat %5.1f | lockshare %.3f | dark %.3f" % (
        n, lum.mean(), dg.mean(), dr.mean(), br.mean(), sat.mean(), share, (lum < 95).mean()))
    ok = av_scan.lock_screen_signature(p)
    print("      lock_screen_signature ->", ok,
          " (need share>=%.2f, b-g>=%d, g-r>=%d, lum %d-%d)" % (
              av_scan.LOCK_BG_MIN_SHARE, av_scan.LOCK_MEAN_DG, av_scan.LOCK_MEAN_DR,
              av_scan.LOCK_LUM_MIN, av_scan.LOCK_LUM_MAX))
    return ok

for i, a in enumerate(rgbs):
    print("-- frame g%d --" % i)
    probe(a, BOX, "marked LED wall")
    probe(a, OTHER, "blob 736,0,1104,96")
    print()

# top-of-frame row scan to see where content is
a = rgbs[0]
print("== row profile of full width (lum / b-g) ==")
for y in range(0, 260, 10):
    row = a[y]
    l = row.mean(axis=1)
    dg = (row[:,2]-row[:,1]).mean()
    print("  y=%3d lum %6.1f  b-g %+6.1f" % (y, l.mean(), dg))

print("\n== OCR on marked box ==")
z = av_scan.panel_zoom_ocr([x.astype(np.uint8) for x in rgbs], BOX)
print("   ", z or "<none>")
print("== full-frame OCR texts ==")
try:
    for it in av_scan.ocr_frame(np.asarray(rgbs[0], dtype=np.uint8))[:25]:
        print("   %-40s @ %s" % (it['text'][:40], (it.get('box') or '')[:1]))
except Exception as e:
    print("  err", e)

im = Image.open(os.path.join(D, 'g0.jpg')).convert('RGB')
ov = im.copy(); d = ImageDraw.Draw(ov)
d.rectangle(BOX, outline=(255,0,0), width=3)
d.rectangle(OTHER, outline=(0,128,255), width=3)
ov.save(os.path.join(D, 'r6c_overlay.png'))
im.crop(BOX).resize((291*2,184*2), Image.LANCZOS).save(os.path.join(D, 'r6c_box.png'))
print("\nsaved r6c_overlay.png (red=marked, blue=clock-blob) / r6c_box.png")
