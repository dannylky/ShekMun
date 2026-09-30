"""Fleet-wide sample of the standby hue gate.
For every marked display region in every room, measure B-R / sat plus the
other standby cues, and OCR the patch, so we can see where the real
separation between 'AVoIP standby' and 'content slide' actually lies.
"""
import os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, '.')
import av_scan

OUT = r'.workbuddy\tmp\huescan'
os.makedirs(OUT, exist_ok=True)

cfg = av_scan.load_config()
regions = cfg.get('display_regions') or {}

IP = {'SM-11-01': 101, 'SM-11-02': 102, 'SM-11-03': 103, 'SM-11-04': 104,
      'SM-11-05': 105, 'SM-11-06': 106, 'SM-11-07': 107, 'SM-11-08': 108}

rows = []
print('%-9s %-20s %6s %6s %6s %6s %6s %6s %6s  %s' % (
    'room', 'region', 'lum', 'B-R', 'sat', 'sat/l', 'BR/l', 'band', 'dark', 'ocr'))
print('-' * 128)

for room in sorted(regions):
    ip = IP.get(room)
    if not ip:
        continue
    f = os.path.join(OUT, '%s.jpg' % room)
    if not os.path.exists(f) or os.path.getsize(f) < 5000:
        os.system('curl -s -m 25 -o "%s" "http://172.18.22.%d/snapshot/snapshot"' % (f, ip))
    if not os.path.exists(f) or os.path.getsize(f) < 5000:
        print('%-9s (no frame)' % room)
        continue
    im = Image.open(f).convert('RGB')
    arr = np.asarray(im, dtype=np.uint8)
    lum = np.asarray(im.convert('L'), dtype=np.float32)
    for reg in regions[room]:
        x0, y0, x1, y1 = reg['box']
        p = arr[y0:y1, x0:x1]
        l = lum[y0:y1, x0:x1]
        br = float((p[:, :, 2].astype(np.float32) - p[:, :, 0]).mean())
        sat = float((p.max(axis=2).astype(np.float32) - p.min(axis=2)).mean())
        L = float(l.mean())
        mp = av_scan.measure_panel([arr], [], reg['box']) or {}
        stc = mp.get('struct') or {}
        band = stc.get('band', -1)
        dark = stc.get('darkshare', -1)
        try:
            z = av_scan.panel_zoom_ocr([arr], reg['box'])
            txt = ' | '.join(z)[:40] if z else ''
        except Exception as e:
            txt = 'ERR'
        rows.append((room, reg.get('label', '')[:20], L, br, sat, band, dark, txt,
                     mp.get('state')))
        print('%-9s %-20s %6.1f %6.1f %6.1f %6.3f %6.3f %6.3f %6.3f  %s' % (
            room, reg.get('label', '')[:20], L, br, sat, sat / max(L, 1), br / max(L, 1),
            band, dark, txt))

print()
print('=== sorted by sat/lum ===')
for r in sorted(rows, key=lambda x: x[4] / max(x[2], 1)):
    print('  sat/l %5.3f  BR/l %6.3f  B-R %6.1f sat %5.1f lum %6.1f  %-9s %-18s %s' % (
        r[4] / max(r[2], 1), r[3] / max(r[2], 1), r[3], r[4], r[2], r[0], r[1], r[7][:38]))
