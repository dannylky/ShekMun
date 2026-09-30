import os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, '.')
import av_scan

D = r'.workbuddy\tmp\live2d'
cfg = av_scan.load_config()

arrs = []
for i in range(3):
    arrs.append(np.asarray(Image.open(os.path.join(D, 'g%d.jpg' % i)).convert('RGB'),
                           dtype=np.uint8))
a = arrs[0]

BOX = (861, 51, 1092, 185)     # room 2 right
BOX_L = (255, 52, 477, 189)    # room 2 left

print('=== OCR, room2 right, several zooms ===')
for sc in (2, 3, 4, 6):
    try:
        z = av_scan.panel_zoom_ocr([a], BOX, scales=(sc,))
        print('  scale %d -> %s' % (sc, z))
    except Exception as e:
        print('  scale %d ERR %s' % (sc, e))

print('\n=== OCR, room2 left ===')
print(' ', av_scan.panel_zoom_ocr([a], BOX_L, scales=(2, 3)))

print('\n=== learned profiles ===')
profs = cfg.get('standby_profiles') or {}
print('  rooms with profiles:', list(profs.keys()))
allp = []
for room, lst in profs.items():
    try:
        pr = av_scan.standby_profiles(cfg, room)
    except TypeError:
        pr = lst
    if isinstance(pr, list):
        allp.extend(pr)
print('  total profiles:', len(allp))

print('\n=== NCC of every marked panel vs learned profiles ===')
regions = cfg.get('display_regions') or {}
IP = {'SM-11-01': 101, 'SM-11-02': 102, 'SM-11-03': 103, 'SM-11-04': 104,
      'SM-11-05': 105, 'SM-11-06': 106, 'SM-11-07': 107, 'SM-11-08': 108}
OUT = r'.workbuddy\tmp\huescan'
for room in sorted(regions):
    f = os.path.join(OUT, '%s.jpg' % room)
    if not os.path.exists(f) or os.path.getsize(f) < 5000:
        continue
    im = Image.open(f).convert('RGB')
    arr = np.asarray(im, dtype=np.uint8)
    try:
        pr = av_scan.standby_profiles(cfg, room)
    except TypeError:
        pr = (profs.get(room) or [])
    if isinstance(pr, dict):
        pr = list(pr.values())
    for reg in regions[room]:
        b = reg['box']
        patch = np.asarray(Image.fromarray(arr).convert("L"), dtype=np.float32)[b[1]:b[3], b[0]:b[2]]
        prof = av_scan.standby_row_profile(patch)
        nccs = [av_scan.profile_ncc(prof, r) for r in (pr or [])]
        best = max(nccs) if nccs else float('nan')
        hue = av_scan.standby_hue(patch)
        hm = av_scan.standby_hue_match(patch, None)
        mp = av_scan.measure_panel([arr], [], b) or {}
        stc = mp.get('struct') or {}
        print('  %-9s %-18s NCC=%s  hue=%s match=%-5s dark=%.3f nonflat=%.3f rowstd=%.1f' % (
            room, reg.get('label', '')[:18],
            ('%.3f' % best) if nccs else 'n/a',
            ('(%.1f,%.1f)' % hue) if hue else 'None', hm,
            stc.get('darkshare', -1), stc.get('nonflat', -1), stc.get('rowstd', -1)))
