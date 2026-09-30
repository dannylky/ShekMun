# -*- coding: utf-8 -*-
import sys, os, json
import numpy as np
from PIL import Image
sys.path.insert(0, r"C:/Work/Projects/ShekMun/[Buddy]")
import av_scan

OUT = r"C:/Work/Projects/ShekMun/[Buddy]/.workbuddy/tmp/live7"
frames = [av_scan.gray(os.path.join(OUT,"g%d.jpg"%i)) for i in range(3)]
rgb = np.asarray(Image.open(os.path.join(OUT,"g0.jpg")).convert("RGB"))
items = av_scan.ocr_frame(rgb)
print("full-frame OCR items:", len(items))
for t in items:
    print("   ", t['box'], repr(t['text'])[:70])

MB = [(242,82,545,265),(1086,77,1382,259)]
S = 1280.0/1734.0
def map_boxes(oy):
    return [[int(round(x0*S)), int(round((y0-oy)*S)), int(round(x1*S)), int(round((y1-oy)*S))]
            for (x0,y0,x1,y1) in MB]

print("\n=== grayscale band/dark by oy (frame0) ===")
for oy in (0,9,17,26,34,45):
    parts=[]
    for i,b in enumerate(map_boxes(oy)):
        p = frames[0][b[1]:b[3], b[0]:b[2]]
        if p.size==0: parts.append("oob"); continue
        st = av_scan.region_structure(p)
        parts.append("b%d lum=%.0f band=%.3f dark=%.3f nonflat=%.3f rowstd=%.1f"%(
            i,p.mean(),st['band'],st['darkshare'],st['nonflat'],st['rowstd']))
    print("oy=%2d | %s"%(oy," | ".join(parts)))

print("\n=== end-to-end screen_states(regions=...) ===")
for oy in (0,17,26,34):
    regs=[{"box":b,"label":"tv%d"%i} for i,b in enumerate(map_boxes(oy))]
    st = av_scan.screen_states(frames, rgb, keep=2, regions=regs)
    print("oy=%2d boxes=%s"%(oy,map_boxes(oy)))
    for s in st:
        print("   ", s.get('region_label','?'), s['box'], s['state'], "| text:", (s.get('text') or '')[:90])
