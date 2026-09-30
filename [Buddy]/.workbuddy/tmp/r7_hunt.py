# -*- coding: utf-8 -*-
import sys, os
import numpy as np
from PIL import Image
sys.path.insert(0, r"C:/Work/Projects/ShekMun/[Buddy]")
import av_scan

OUT = r"C:/Work/Projects/ShekMun/[Buddy]/.workbuddy/tmp/live7"
g0 = av_scan.gray(os.path.join(OUT,"g0.jpg"))
rgb0 = Image.open(os.path.join(OUT,"g0.jpg")).convert("RGB")

def up_ocr(box, scale=3):
    c = rgb0.crop(box)
    c = c.resize((c.width*scale, c.height*scale), Image.LANCZOS)
    txts=[t['text'] for t in av_scan.ocr_frame(np.asarray(c))]
    g = g0[box[1]:box[3], box[0]:box[2]]
    st = av_scan.region_structure(g)
    return txts, float(g.mean()), st['band'], st['darkshare']

cands = {
 "blob_L   [228,79,370,184]": (228,79,370,184),
 "marked_L [179,61,402,196]": (179,61,402,196),
 "mirrorR  [840,79,982,184]": (840,79,982,184),
 "marked_R [802,57,1020,191]": (802,57,1020,191),
}
for k,b in cands.items():
    t,l,bd,dk = up_ocr(b)
    print("%s lum=%.0f band=%.3f dark=%.3f | %s" % (k,l,bd,dk, (" | ".join(t))[:120] if t else "(none)"))

print("\n=== horizontal scan: 142x105 window at y79-184, step 20 ===")
best=[]
for x0 in range(140, 1120, 20):
    b=(x0,79,x0+142,184)
    g=g0[79:184, x0:x0+142]
    st=av_scan.region_structure(g)
    best.append((st['band'], st['darkshare'], float(g.mean()), x0))
for bd,dk,l,x0 in best:
    if bd>0.15 or dk>0.35:
        print("  x0=%4d band=%.3f dark=%.3f lum=%.0f" % (x0,bd,dk,l))
