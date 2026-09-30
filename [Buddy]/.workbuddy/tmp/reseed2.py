"""Seed the standby profile pool from LIVE frames, using the production banner test.

Rule (conservative): a panel's row profile is stored only when
  (a) its own OCR reading matches the AVoIP standby banner (fuzzy), or
  (b) the room has >= 2 banner-confirmed panels AND this panel has no OCR text at
      all - i.e. there is no evidence it is showing content.
(b) exists for SM-11-01 centre-left: an angled TV whose row profile matches neither
its siblings (0.38-0.41) nor the pool, too dark for standby_fingerprint (dark 0.975),
and too neutral in colour for the hue gate (B-R 5.6). It is genuine standby - three
siblings in the same room read the banner - but without its own reference it falls
through every test and turns the room into a phantom OUT OF SYNC.
"""
import os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, '.')
import av_scan

cfg = av_scan.load_config()
regions = cfg.get('display_regions') or {}
IP = {'SM-11-01': 101, 'SM-11-02': 102, 'SM-11-03': 103, 'SM-11-04': 104,
      'SM-11-05': 105, 'SM-11-06': 106, 'SM-11-07': 107, 'SM-11-08': 108}
OUT = r'.workbuddy\tmp\seed'
os.makedirs(OUT, exist_ok=True)

for room in sorted(regions):
    ip = IP.get(room)
    if not ip:
        continue
    f = os.path.join(OUT, '%s.jpg' % room)
    os.system('curl -s -m 25 -o "%s" "http://172.18.22.%d/snapshot/snapshot"' % (f, ip))
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
            z = av_scan.panel_zoom_ocr([arr], b)
        except Exception:
            z = []
        z = z or []
        banner = av_scan.standby_banner(z)
        info.append((b, banner, not z))

    nban = sum(1 for _, bn, _ in info if bn)
    seed = []
    for b, banner, silent in info:
        if banner or (nban >= 2 and silent):
            seed.append(av_scan.standby_row_profile(gray[b[1]:b[3], b[0]:b[2]]))
    before = len((cfg.get('standby_profiles') or {}).get(room) or [])
    if seed:
        av_scan.remember_standby_profiles(room, seed)
    cfg = av_scan.load_config()
    after = len((cfg.get('standby_profiles') or {}).get(room) or [])
    print('%-9s banners=%d/%d  seeded=%d  pool %d -> %d' % (
        room, nban, len(info), len(seed), before, after))
