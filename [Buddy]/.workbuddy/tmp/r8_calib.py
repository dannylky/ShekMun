# -*- coding: utf-8 -*-
import sys, os, time, subprocess
import numpy as np
from PIL import Image
sys.path.insert(0, r"C:/Work/Projects/ShekMun/[Buddy]")
import av_scan

OUT = r"C:/Work/Projects/ShekMun/[Buddy]/.workbuddy/tmp/live8"; os.makedirs(OUT, exist_ok=True)
frames=[]
for i in range(3):
    p=os.path.join(OUT,"g%d.jpg"%i)
    subprocess.run(['curl','-s','--max-time','12','http://172.18.22.108/snapshot/snapshot','-o',p],check=False)
    frames.append(p); print("grabbed",p,Image.open(p).size); time.sleep(2.0)

MB=[(397,99,639,240),(1032,106,1271,252)]   # marked-image px  (1724x1033)
S =1280.0/1724.0
print("width scale=%.4f  scaled height=%.1f (frame 720)"%(S,1033*S))

rgb=np.asarray(Image.open(frames[0]).convert("RGB"))
def map_boxes(oy):
    return [[int(round(x0*S)),int(round((y0-oy)*S)),int(round(x1*S)),int(round((y1-oy)*S))]
            for (x0,y0,x1,y1) in MB]

print("\n=== oy sweep (frame0) ===")
for oy in (0,9,17,26,34,45):
    parts=[]
    for i,b in enumerate(map_boxes(oy)):
        p=rgb[b[1]:b[3],b[0]:b[2]]
        if p.size==0: parts.append("oob"); continue
        g=np.asarray(Image.fromarray(p).convert("L"),dtype=np.float32)
        st=av_scan.region_structure(g)
        parts.append("b%d lum=%.0f band=%.3f dark=%.3f"%(i,g.mean(),st['band'],st['darkshare']))
    print("oy=%2d %s | %s"%(oy,map_boxes(oy)," | ".join(parts)))

print("\n=== full-frame OCR ===")
items=av_scan.ocr_frame(rgb)
print("items:",len(items))
for t in items[:12]: print("   ",t['box'],repr(t['text'])[:60])

print("\n=== zoom OCR + controls ===")
for oy in (0,17,34):
    for i,b in enumerate(map_boxes(oy)):
        hits=av_scan.panel_zoom_ocr([rgb],b)
        print("oy=%2d b%d %s -> %s"%(oy,i,b,(" | ".join(hits))[:90] if hits else "(none)"))
