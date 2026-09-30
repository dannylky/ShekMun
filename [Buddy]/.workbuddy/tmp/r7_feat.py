# -*- coding: utf-8 -*-
import sys, os, subprocess, time
import numpy as np
from PIL import Image, ImageFilter, ImageOps
sys.path.insert(0, r"C:/Work/Projects/ShekMun/[Buddy]")
import av_scan

TMP = r"C:/Work/Projects/ShekMun/[Buddy]/.workbuddy/tmp/feat"; os.makedirs(TMP, exist_ok=True)
def grab(ip):
    p = os.path.join(TMP, "%s.jpg" % ip)
    subprocess.run(['curl','-s','--max-time','12',
                    'http://172.18.22.%s/snapshot/snapshot'%ip,'-o',p], check=False)
    return p

def hp(a, rad=12):
    im = Image.fromarray(a.astype(np.uint8))
    bl = np.asarray(im.filter(ImageFilter.GaussianBlur(rad)), dtype=np.float32)
    d = a - bl
    d = d - d.min()
    return d / (d.max()+1e-6) * 255.0

def feats(g):
    st = av_scan.region_structure(g)
    h  = hp(g)
    edh = np.abs(np.diff(h, axis=1))
    top = edh[:max(8,int(h.shape[0]*0.30)), :]
    band_hp = float((top.mean(axis=1) > 9).mean())
    return dict(lum=float(g.mean()), band=st['band'], dark=st['darkshare'],
                band_hp=band_hp, std_hp=float(h.std()))

def rowprof(g, n=48):
    h = hp(g)
    ed = np.abs(np.diff(h, axis=1)).mean(axis=1)
    p = np.interp(np.linspace(0,len(ed)-1,n), np.arange(len(ed)), ed)
    return (p - p.mean())/(p.std()+1e-6)

def ncc(a,b): return float((a*b).mean())

CASES = [
 # (label, camera_ip, box, truth)
 ('R7-left  standby?', '107', (179,61,402,196),   'standby'),
 ('R7-right standby?', '107', (802,57,1020,191),  'standby'),
 ('R7-lower bright',   '107', (1004,334,1280,441),'other'),
 ('R2-left  standby',  '102', (255,52,477,189),   'standby'),
 ('R2-right standby',  '102', (861,51,1092,185),  'standby'),
 ('R1-tv1  content',   '101', (2,128,286,352),    'other'),
 ('R1-tv2  content',   '101', (703,116,845,203),  'other'),
 ('R1-tv3  content',   '101', (1014,116,1222,242),'other'),
 ('R1-tv4  content',   '101', (1035,120,1268,250),'other'),
]
cache={}
res={}
for label, ip, box, truth in CASES:
    if ip not in cache: cache[ip] = av_scan.gray(grab(ip))
    g = cache[ip][box[1]:box[3], box[0]:box[2]]
    f = feats(g); f['truth']=truth; f['prof']=rowprof(g)
    res[label]=f
    print("%-20s truth=%-8s lum=%5.1f band=%.3f dark=%.3f | band_hp=%.3f std_hp=%5.1f" %
          (label, truth, f['lum'], f['band'], f['dark'], f['band_hp'], f['std_hp']))

print("\nrow-profile NCC vs R7-left (the OCR-confirmed standby panel):")
ref = res['R7-left  standby?']['prof']
for k,f in res.items():
    print("   %-20s truth=%-8s ncc=%.3f" % (k, f['truth'], ncc(ref, f['prof'])))
print("\nrow-profile NCC vs R2-left (Room2 confirmed standby):")
ref2 = res['R2-left  standby']['prof']
for k,f in res.items():
    print("   %-20s truth=%-8s ncc=%.3f" % (k, f['truth'], ncc(ref2, f['prof'])))
