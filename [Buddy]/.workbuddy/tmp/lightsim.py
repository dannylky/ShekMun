"""Does the row-profile NCC survive a change of illumination?
Simulate sunlight two ways on OCR-confirmed standby panels:
  additive   (white ambient / glare veiling)  p -> p + k
  multiplicative (brighter room light)        p -> p * k
and also warm sunlight (adds more to R than B).
If NCC holds above the 0.65 gate, requiring hue AND NCC is safe.
"""
import os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, '.')
import av_scan

OUT = r'.workbuddy\tmp\huescan'
cfg = av_scan.load_config()
regions = cfg.get('display_regions') or {}

# OCR-confirmed standby panels to test
TEST = [('SM-11-06', 0), ('SM-11-03', 0), ('SM-11-07', 0), ('SM-11-07', 1),
        ('SM-11-01', 0), ('SM-11-01', 2), ('SM-11-01', 3), ('SM-11-08', 0)]

print('%-11s %7s | %s' % ('panel', 'lum', '  '.join('%-7s' % s for s in
      ('orig', '+40', '+80', '+120', 'x1.5', 'x2.0', 'warm+80'))))
print('-' * 95)

for room, idx in TEST:
    f = os.path.join(OUT, '%s.jpg' % room)
    if not os.path.exists(f) or os.path.getsize(f) < 5000:
        continue
    im = Image.open(f).convert('RGB')
    arr = np.asarray(im, dtype=np.uint8)
    gray = np.asarray(im.convert('L'), dtype=np.float32)
    try:
        pr = av_scan.standby_profiles(cfg, room)
    except TypeError:
        pr = (cfg.get('standby_profiles') or {}).get(room) or []
    if isinstance(pr, dict):
        pr = list(pr.values())
    if not pr:
        continue
    b = regions[room][idx]['box']
    base = gray[b[1]:b[3], b[0]:b[2]]
    rgb = arr[b[1]:b[3], b[0]:b[2]].astype(np.float32)

    def score(g):
        prof = av_scan.standby_row_profile(g)
        return max(av_scan.profile_ncc(prof, r) for r in pr)

    warm = rgb.copy()
    warm[:, :, 0] += 90      # sunlight adds most to red
    warm[:, :, 1] += 70
    warm[:, :, 2] += 55
    warm_g = 0.299 * warm[:, :, 0] + 0.587 * warm[:, :, 1] + 0.114 * warm[:, :, 2]

    vals = [score(base),
            score(base + 40), score(base + 80), score(base + 120),
            score(base * 1.5), score(base * 2.0),
            score(np.clip(warm_g, 0, 255))]
    print('%-11s %7.1f | %s' % (
        '%s#%d' % (room, idx), base.mean(),
        '  '.join('%7.3f' % v for v in vals)))
