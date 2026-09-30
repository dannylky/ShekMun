"""Re-seed the standby profile pool from panels whose banner OCR confirms standby.
Run once after the v2.6.1 pool fix, to put a good reference back into SM-11-01
(the rooms whose pool had been wrecked by the old limit=2 eviction).
"""
import os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, '.')
import av_scan

OUT = r'.workbuddy\tmp\huescan'
cfg = av_scan.load_config()
regions = cfg.get('display_regions') or {}

for room in sorted(regions):
    f = os.path.join(OUT, '%s.jpg' % room)
    if not os.path.exists(f) or os.path.getsize(f) < 5000:
        print('%-9s (no frame)' % room)
        continue
    im = Image.open(f).convert('RGB')
    arr = np.asarray(im, dtype=np.uint8)
    gray = np.asarray(im.convert('L')).astype(np.float32)
    learned = []
    for reg in regions[room]:
        b = reg['box']
        try:
            z = av_scan.panel_zoom_ocr([arr], b)
            txt = ' '.join(z)
        except Exception:
            txt = ''
        if 'AVOIP' not in txt.upper().replace(' ', ''):
            continue
        learned.append(av_scan.standby_row_profile(gray[b[1]:b[3], b[0]:b[2]]))
    n_before = len((cfg.get('standby_profiles') or {}).get(room) or [])
    if learned:
        av_scan.remember_standby_profiles(room, learned)
    cfg = av_scan.load_config()
    n_after = len((cfg.get('standby_profiles') or {}).get(room) or [])
    print('%-9s seeded %d  pool %d -> %d' % (room, len(learned), n_before, n_after))
