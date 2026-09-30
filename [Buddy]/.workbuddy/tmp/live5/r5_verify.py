import sys, os, json, numpy as np
sys.path.insert(0, r'C:\Work\Projects\ShekMun\[Buddy]')
from PIL import Image
import av_scan as A

base = r'C:\Work\Projects\ShekMun\[Buddy]\.workbuddy\tmp\live5'
files = [os.path.join(base, f'g{i}.jpg') for i in range(3)]
cfg = A.load_config()
label = 'SM-11-05'

rg = [np.asarray(Image.open(f).convert('RGB')) for f in files]
fr = [A.gray(f) for f in files]

regions = A.display_regions(cfg, label)
print('regions:', regions)
print('standby_refs:', len(A.standby_profiles(cfg, label)))

ocr = A.ocr_frame(rg[0])
print('full-frame OCR items:', len(ocr))
for it in ocr[:12]:
    print('   ', it)

for box, lbl in [(r['box'], r['label']) for r in regions]:
    m = A.measure_panel(fr, ocr, tuple(box), rgb=rg[0])
    print('---', lbl, box)
    for k in ('state', 'text', 'mean_lum', 'dark_share', 'struct'):
        print('   ', k, '=', m.get(k))
    z = A.panel_zoom_ocr(rg, tuple(box))
    print('    zoom ocr:', z)
    print('    lock sig:', A.lock_screen_signature(rg[0][box[1]:box[3], box[0]:box[2]]))
    prof = A.standby_row_profile(fr[0][box[1]:box[3], box[0]:box[2]])
    for ref in A.standby_profiles(cfg, label):
        print('    ncc vs stored:', round(float(A.profile_ncc(prof, np.asarray(ref, dtype=np.float32))), 3))

scr = A.screen_states(fr, rg[0], keep=1,
                      filt=A.display_filter(cfg, label),
                      regions=regions,
                      rgbs=rg,
                      standby_refs=A.standby_profiles(cfg, label))
print('=== screen_states ===')
for s in scr:
    print(s)
sync = A.sync_check(fr, scr, 1)
print('sync:', sync)
