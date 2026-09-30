"""Rebuild every room's standby profile pool from LIVE frames (final).

Confirmation is deliberately wider than standby_banner(): that fuzzy test misses
SM-11-08, whose panel reads `AMOIR SYSTEASTATUS: DECOOCRSTANDBY` - ratio under the
0.65 floor, yet unmistakably the standby banner. So a panel counts as confirmed when
its normalised reading contains the banner word OR the word STAND.

Pools are replaced outright: every stored entry predates the v2.6.1 pool fix and was
exposed to the eviction bug, so none of them can be trusted.
"""
import os, sys, json
import numpy as np
from PIL import Image
sys.path.insert(0, '.')
import av_scan

CONFIG = 'av_monitor_config.json'
SRC = r'.workbuddy\tmp\config_backup_20260930.json'
json.dump(json.load(open(SRC, encoding='utf-8')),
          open(CONFIG, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
cfg = av_scan.load_config()
regions = cfg.get('display_regions') or {}
IP = {'SM-11-01': 101, 'SM-11-02': 102, 'SM-11-03': 103, 'SM-11-04': 104,
      'SM-11-05': 105, 'SM-11-06': 106, 'SM-11-07': 107, 'SM-11-08': 108}
OUT = r'.workbuddy\tmp\seed'


def confirmed(z):
    if not z:
        return False
    if av_scan.standby_banner(z)[0]:
        return True
    t = ' '.join(z).upper().replace(' ', '')
    return 'STAND' in t or 'STANDBY' in t


for room in sorted(regions):
    f = os.path.join(OUT, '%s.jpg' % room)
    if not os.path.exists(f) or os.path.getsize(f) < 5000:
        print('%-9s (no frame)' % room)
        continue
    im = Image.open(f).convert('RGB')
    arr = np.asarray(im, dtype=np.uint8)
    gray = np.asarray(im.convert('L')).astype(np.float32)

    info = []
    for reg in regions[room]:
        b = reg['box']
        try:
            z = av_scan.panel_zoom_ocr([arr], b) or []
        except Exception:
            z = []
        info.append((b, confirmed(z), not z, ' '.join(z)[:34]))

    nban = sum(1 for _, ok, _, _ in info if ok)
    seed = []
    for b, ok, silent, _t in info:
        if ok or (nban >= 2 and silent):
            seed.append(av_scan.standby_row_profile(gray[b[1]:b[3], b[0]:b[2]]))
    if seed:
        c = json.load(open(CONFIG, encoding='utf-8'))
        c.setdefault('standby_profiles', {})[room] = []
        json.dump(c, open(CONFIG, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
        av_scan.remember_standby_profiles(room, seed)
    cfg = av_scan.load_config()
    after = len((cfg.get('standby_profiles') or {}).get(room) or [])
    print('%-9s confirmed=%d/%d seeded=%d -> pool %d' % (room, nban, len(info), len(seed), after))
    for b, ok, silent, t in info:
        print('        %-22s %s %s' % (b, 'BANNER' if ok else ('silent' if silent else 'text'),
                                       t))
