# -*- coding: utf-8 -*-
import sys, os, json
import numpy as np
from PIL import Image
sys.path.insert(0, r"C:/Work/Projects/ShekMun/[Buddy]")
import av_scan

cfg = json.load(open(av_scan.CONFIG, encoding='utf-8'))
regs = av_scan.display_regions(cfg, 'SM-11-07')
print("SM-11-07 regions:", regs)

OUT = r"C:/Work/Projects/ShekMun/[Buddy]/.workbuddy/tmp/live7"
files = [os.path.join(OUT,"g%d.jpg"%i) for i in range(3)]
frames = [av_scan.gray(f) for f in files]
rgbs   = [np.asarray(Image.open(f).convert('RGB')) for f in files]

scr = av_scan.screen_states(frames, rgbs[0], keep=2, regions=regs, rgbs=rgbs)
print("\n--- panels ---")
for s in scr:
    print("  %-22s box=%s monitored=%s\n      state=%s\n      text=%s" % (
        s.get('region_label') or '(unmarked)', s['box'], s.get('monitored', True),
        s['state'], (s.get('text') or '')[:110]))
print("\ndisplay_state:", av_scan.aggregate_screen_state(scr))
print("sync:", av_scan.sync_check(frames, scr, 2))
