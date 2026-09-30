import os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, '.')
import av_scan

os.makedirs(r'.workbuddy\tmp\now', exist_ok=True)
cfg = av_scan.load_config()
regions = cfg.get('display_regions') or {}
IP = {'SM-11-01': 101, 'SM-11-02': 102, 'SM-11-03': 103, 'SM-11-04': 104,
      'SM-11-05': 105, 'SM-11-06': 106, 'SM-11-07': 107, 'SM-11-08': 108}

for room in sorted(regions):
    f = r'.workbuddy\tmp\now\%s.jpg' % room
    os.system('curl -s -m 25 -o "%s" "http://172.18.22.%d/snapshot/snapshot"' % (f, IP[room]))
    if not os.path.exists(f) or os.path.getsize(f) < 5000:
        print('%-9s (no frame)' % room)
        continue
    im = Image.open(f).convert('RGB')
    arr = np.asarray(im, dtype=np.uint8)
    gray = np.asarray(im.convert('L')).astype(np.float32)
    pr = av_scan.standby_profiles(cfg, room)
    print('== %-9s pool=%d' % (room, len(pr)))
    for reg in regions[room]:
        b = reg['box']
        rgb = arr[b[1]:b[3], b[0]:b[2]]
        g = gray[b[1]:b[3], b[0]:b[2]]
        h = av_scan.standby_hue(rgb)
        hm = av_scan.standby_hue_match(rgb, None)
        ncc = max([av_scan.profile_ncc(av_scan.standby_row_profile(g), p) for p in pr],
                  default=float('nan'))
        try:
            z = av_scan.panel_zoom_ocr([arr], b) or []
        except Exception:
            z = []
        txt = ' '.join(z)[:44]
        v = ('Idle-standby' if (ncc >= av_scan.STANDBY_NCC_MIN or (hm and np.isnan(ncc)))
             else 'content/other')
        print('   %-22s lum=%6.1f B-R=%6.1f sat=%6.1f hue=%-5s NCC=%6.3f  %-13s %s' % (
            str(b), g.mean(), h[0], h[1], hm, ncc, v, txt))
