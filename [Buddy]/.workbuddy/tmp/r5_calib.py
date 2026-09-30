# -*- coding: utf-8 -*-
import sys, os, time, subprocess
import numpy as np
from PIL import Image
sys.path.insert(0, r"C:/Work/Projects/ShekMun/[Buddy]")
import av_scan

OUT = r"C:/Work/Projects/ShekMun/[Buddy]/.workbuddy/tmp/live5"; os.makedirs(OUT, exist_ok=True)
frames=[]
for i in range(3):
    p=os.path.join(OUT,"g%d.jpg"%i)
    subprocess.run(['curl','-s','--max-time','12','http://172.18.22.105/snapshot/snapshot','-o',p],check=False)
    frames.append(p); print("grabbed",p,Image.open(p).size); time.sleep(2.0)

MB=[(59,47,567,323)]                # marked-image px (1727x962)
S =1280.0/1727.0
print("width scale=%.4f  scaled height=%.1f (frame 720)  extra=%.1f"%(S,962*S,962*S-720))

rgb=np.asarray(Image.open(frames[0]).convert("RGB"))
def map_boxes(oy):
    return [[int(round(x0*S)),int(round((y0-oy)*S)),int(round(x1*S)),int(round((y1-oy)*S))]
            for (x0,y0,x1,y1) in MB]

print("\n=== oy sweep (frame0) ===")
for oy in (0,6,12,18,24,30,35):
    parts=[]
    for i,b in enumerate(map_boxes(oy)):
        patch=rgb[max(0,b[1]):b[3],max(0,b[0]):b[2]]
        if patch.size==0: parts.append("oob"); continue
        g=np.asarray(Image.fromarray(patch).convert("L"),dtype=np.float32)
        st=av_scan.region_structure(g)
        parts.append("b%d box=%s lum=%.0f band=%.3f dark=%.3f"%(i,b,g.mean(),st['band'],st['darkshare']))
    print("oy=%2d | %s"%(oy," | ".join(parts)))

print("\n=== full-frame OCR ===")
items=av_scan.ocr_frame(rgb)
print("items:",len(items))
for t in items[:10]: print("   ",t['box'],repr(t['text'])[:60])
print("\n=== zoom OCR by oy ===")
for oy in (0,12,18,24,30):
    for i,b in enumerate(map_boxes(oy)):
        hits=av_scan.panel_zoom_ocr([rgb],b)
        print("oy=%2d b%d -> %s"%(oy,i,(" | ".join(hits))[:70] if hits else "(none)"))
