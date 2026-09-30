"""One table: every marked panel, its OCR ground truth, hue, NCC, dark share.
Used to pick thresholds that separate AVoIP-standby from content.
"""
import os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, '.')
import av_scan

cfg = av_scan.load_config()
regions = cfg.get('display_regions') or {}
OUT = r'.workbuddy\tmp\huescan'

rows = []
for room in sorted(regions):
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
    for reg in regions[room]:
        b = reg['box']
        rgb = arr[b[1]:b[3], b[0]:b[2]]
        g = gray[b[1]:b[3], b[0]:b[2]]
        hue = av_scan.standby_hue(rgb)
        prof = av_scan.standby_row_profile(g)
        nccs = [av_scan.profile_ncc(prof, r) for r in (pr or [])]
        ncc = max(nccs) if nccs else float('nan')
        mp = av_scan.measure_panel([arr], [], b) or {}
        stc = mp.get('struct') or {}
        try:
            z = av_scan.panel_zoom_ocr([arr], b)
            txt = ' | '.join(z)[:34]
        except Exception:
            txt = ''
        banner = 'AVOIP' in txt.upper().replace(' ', '') or 'STAND' in txt.upper()
        rows.append(dict(room=room, label=reg.get('label', '')[:17], box=b,
                         lum=float(g.mean()), br=hue[0] if hue else None,
                         sat=hue[1] if hue else None, ncc=ncc,
                         dark=stc.get('darkshare', -1), banner=banner, txt=txt))

print('%-9s %-17s %6s %6s %6s %6s %6s %5s  %s' % (
    'room', 'label', 'lum', 'B-R', 'sat', 'NCC', 'dark', 'BANN', 'ocr'))
print('-' * 130)
for r in rows:
    print('%-9s %-17s %6.1f %6.1f %6.1f %6.3f %6.3f %5s  %s' % (
        r['room'], r['label'], r['lum'], r['br'], r['sat'], r['ncc'], r['dark'],
        'YES' if r['banner'] else '.', r['txt']))

st = [r for r in rows if r['banner']]
ct = [r for r in rows if not r['banner']]
print('\n--- OCR-confirmed STANDBY  (n=%d) ---' % len(st))
for k in ('br', 'sat', 'ncc', 'dark'):
    v = [r[k] for r in st if r[k] is not None]
    print('  %-4s min %7.2f  max %7.2f   %s' % (k, min(v), max(v),
          ' '.join('%.2f' % x for x in sorted(v))))
print('--- NOT standby (n=%d) ---' % len(ct))
for k in ('br', 'sat', 'ncc', 'dark'):
    v = [r[k] for r in ct if r[k] is not None]
    print('  %-4s min %7.2f  max %7.2f   %s' % (k, min(v), max(v),
          ' '.join('%.2f' % x for x in sorted(v))))
