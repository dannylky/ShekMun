import numpy as np, os, sys
from PIL import Image
sys.path.insert(0, r"C:\Work\Projects\ShekMun\[Buddy]")
import av_scan
D = r"C:\Work\Projects\ShekMun\[Buddy]\.workbuddy\tmp\live1"
try:
    fs = [np.asarray(Image.open(os.path.join(D, f'g{i}.jpg')).convert('RGB'), dtype=np.float32) for i in range(3)]
except Exception as e:
    print("no live1 frames:", e); fs = None

BOXES = [("left-wall 4K TV",(22,115,282,309)),
         ("centre-left",(450,88,558,202)),
         ("centre-right",(722,86,889,186)),
         ("right-wall TV",(1058,110,1272,232))]
if fs:
    print("yesterday frames live1:")
    for n, bx in BOXES:
        p = fs[0][bx[1]:bx[3], bx[0]:bx[2]]
        l = p.mean(axis=2); d1 = p[:,:,2]-p[:,:,1]; d2 = p[:,:,1]-p[:,:,0]
        print("  %-16s %-20s lum %6.1f b-g %+7.1f g-r %+7.1f lockshare %.3f B-R %+6.1f" % (
            n, str(bx), l.mean(), d1.mean(), d2.mean(), ((d1>35)&(d2>12)).mean(),
            (p[:,:,2]-p[:,:,0]).mean()))

# grab fresh room1 frames
import subprocess
D2 = r"C:\Work\Projects\ShekMun\[Buddy]\.workbuddy\tmp\live1b"
os.makedirs(D2, exist_ok=True)
for i in range(3):
    subprocess.run(["curl","-s","-m","25","-o",os.path.join(D2,f'g{i}.jpg'),
                    "http://172.18.22.101/snapshot/snapshot"], check=False)
fs2 = [np.asarray(Image.open(os.path.join(D2, f'g{i}.jpg')).convert('RGB'), dtype=np.float32) for i in range(3)]
print("\nNOW frames:")
for n, bx in BOXES:
    best = None
    for f in fs2:
        p = f[bx[1]:bx[3], bx[0]:bx[2]]
        l = p.mean(axis=2); d1 = p[:,:,2]-p[:,:,1]; d2 = p[:,:,1]-p[:,:,0]
        ok = av_scan.lock_screen_signature(p)
        print("  %-16s %-20s lum %6.1f b-g %+7.1f g-r %+7.1f lockshare %.3f B-R %+6.1f lock=%s" % (
            n, str(bx), l.mean(), d1.mean(), d2.mean(), ((d1>35)&(d2>12)).mean(),
            (p[:,:,2]-p[:,:,0]).mean(), ok))
        break
print("\nthresholds: LOCK_LUM %d-%d  LOCK_BG_DG %d  LOCK_BG_DR %d  share>=%.2f  MEAN_DG>=%d  MEAN_DR>=%d" % (
    av_scan.LOCK_LUM_MIN, av_scan.LOCK_LUM_MAX, av_scan.LOCK_BG_DG, av_scan.LOCK_BG_DR,
    av_scan.LOCK_BG_MIN_SHARE, av_scan.LOCK_MEAN_DG, av_scan.LOCK_MEAN_DR))
for n, bx in BOXES:
    z = av_scan.panel_zoom_ocr([f.astype(np.uint8) for f in fs2], bx)
    print("  OCR %-16s %s" % (n, z or '<none>'))
