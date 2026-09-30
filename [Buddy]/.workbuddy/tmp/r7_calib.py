# -*- coding: utf-8 -*-
import sys, time, os, subprocess
import numpy as np
from PIL import Image

sys.path.insert(0, r"C:/Work/Projects/ShekMun/[Buddy]")
import av_scan

OUT = r"C:/Work/Projects/ShekMun/[Buddy]/.workbuddy/tmp/live7"
os.makedirs(OUT, exist_ok=True)

frames = []
for i in range(3):
    p = os.path.join(OUT, "g%d.jpg" % i)
    subprocess.run(['curl','-s','--max-time','12',
                    'http://172.18.22.107/snapshot/snapshot','-o',p], check=False)
    frames.append(p)
    print("grabbed", p, Image.open(p).size)
    time.sleep(2.0)

MB = [(242, 82, 545, 265), (1086, 77, 1382, 259)]
S  = 1280.0 / 1734.0

rgb = np.asarray(Image.open(frames[0]).convert("RGB"))
print("frame", rgb.shape)

def map_boxes(oy):
    out = []
    for (x0,y0,x1,y1) in MB:
        out.append((int(round(x0*S)), int(round((y0-oy)*S)),
                    int(round(x1*S)), int(round((y1-oy)*S))))
    return out

print("\n=== offset calibration (frame0) ===")
for oy in (0, 9, 17, 26, 34):
    parts = []
    for i, b in enumerate(map_boxes(oy)):
        patch = rgb[b[1]:b[3], b[0]:b[2]]
        if patch.size == 0:
            parts.append("oob"); continue
        st = av_scan.region_structure(patch)
        parts.append("b%d lum=%.0f band=%.3f dark=%.3f" % (i, patch.mean(), st['band'], st['darkshare']))
    print("oy=%2d boxes=%s | %s" % (oy, map_boxes(oy), " | ".join(parts)))

print("\n=== OCR per crop (oy sweep) ===")
for oy in (0, 9, 17, 26):
    for i, b in enumerate(map_boxes(oy)):
        crop = rgb[b[1]:b[3], b[0]:b[2]]
        cp = os.path.join(OUT, "oy%d_b%d.png" % (oy, i))
        Image.fromarray(crop).save(cp)
        txts = [t['text'] for t in av_scan.ocr_frame(np.asarray(Image.open(cp).convert("RGB")))]
        print("oy=%2d b%d %s -> %s" % (oy, i, b, (" | ".join(txts))[:180] if txts else "(none)"))
