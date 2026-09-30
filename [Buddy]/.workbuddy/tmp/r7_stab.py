# -*- coding: utf-8 -*-
import sys, os
import numpy as np
from PIL import Image, ImageFilter, ImageOps
sys.path.insert(0, r"C:/Work/Projects/ShekMun/[Buddy]")
import av_scan
OUT = r"C:/Work/Projects/ShekMun/[Buddy]/.workbuddy/tmp/live7"
L=(179,61,402,196); R=(802,57,1020,191)

def hp(a, rad=12):
    im = Image.fromarray(a.astype(np.uint8))
    bl = np.asarray(im.filter(ImageFilter.GaussianBlur(rad)), dtype=np.float32)
    d = a - bl; d = d - d.min()
    return d/(d.max()+1e-6)*255.0
def rowprof(g, n=48):
    h = hp(g)
    ed = np.abs(np.diff(h, axis=1)).mean(axis=1)
    p = np.interp(np.linspace(0,len(ed)-1,n), np.arange(len(ed)), ed)
    return (p-p.mean())/(p.std()+1e-6)
def upocr(rgb, box, scale, auto):
    c = rgb.crop(box).convert('L')
    if auto: c = ImageOps.autocontrast(c, cutoff=2)
    c = c.resize((c.width*scale, c.height*scale), Image.LANCZOS)
    return [t['text'] for t in av_scan.ocr_frame(np.asarray(c.convert('RGB')))]

for i in range(3):
    p = os.path.join(OUT,"g%d.jpg"%i)
    rgb = Image.open(p).convert("RGB"); g = av_scan.gray(p)
    gl = g[L[1]:L[3], L[0]:L[2]]; gr = g[R[1]:R[3], R[0]:R[2]]
    ncc = float((rowprof(gl)*rowprof(gr)).mean())
    t2 = upocr(rgb, L, 2, True)
    hitL = any(k in ' '.join(t2).upper() for k in ('AVOIP','DECODER','STANDBY'))
    t2r = upocr(rgb, R, 2, True)
    hitR = any(k in ' '.join(t2r).upper() for k in ('AVOIP','DECODER','STANDBY'))
    print("g%d  NCC(L,R)=%.3f  L_hit=%s %s | R_hit=%s %s" %
          (i, ncc, hitL, (' '.join(t2))[:60], hitR, (' '.join(t2r))[:60]))
