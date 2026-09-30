"""Rebuild the standby profile pool from LIVE frames - corrected.

The first attempt was wrong: standby_banner() returns a (ok, ratio, text) tuple and a
non-empty tuple is truthy even when ok is False, so every panel counted as
"banner confirmed" and room 2's slide was stored as a standby reference.

Rule: store a panel's row profile only when
  (a) standby_banner()[0] is True - its own reading is the AVoIP banner, or
  (b) the room has >= 2 banner-confirmed panels AND this panel produced no OCR text
      at all - no evidence of content.
(b) covers SM-11-01 centre-left: an angled TV that matches neither its siblings
(NCC 0.38-0.41) nor the pool, is too dark for standby_fingerprint (dark 0.975) and too
neutral for the hue gate (B-R 5.6), yet is genuine standby - three siblings in the same
room read the banner. Without its own reference it fails every test and turns the room
into a phantom OUT OF SYNC.

For rooms where we recover >= 2 confirmed references the old pool is REPLACED, because
the old entries are the ones wrecked by the v2.6.0 eviction bug.
"""
import os, sys, json
import numpy as np
from PIL import Image
sys.path.insert(0, '.')
import av_scan

SRC = r'.workbuddy\tmp\config_backup_20260930.json'
CONFIG = 'av_monitor_config.json'

# start from the pristine backup (taken before any seeding)
cfg = json.load(open(SRC, encoding='utf-8'))
json.dump(cfg, open(CONFIG, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
cfg = av_scan.load_config()
print('restored from backup; pools:',
      {k: len(v) for k, v in (cfg.get('standby_profiles') or {}).items()})

regions = cfg.get('display_regions') or {}
IP = {'SM-11-01': 101, 'SM-11-02': 102, 'SM-11-03': 103, 'SM-11-04': 104,
      'SM-11-05': 105, 'SM-11-06': 106, 'SM-11-07': 107, 'SM-11-08': 108}
OUT = r'.workbuddy\tmp\seed'
os.makedirs(OUT, exist_ok=True)

print()
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
            z = av_scan.panel_zoom_ocr([arr], b) or []
        except Exception:
            z = []
        ok = av_scan.standby_banner(z)[0] if z else False
        info.append((b, ok, not z))

    nban = sum(1 for _, ok, _ in info if ok)
    seed = []
    for b, ok, silent in info:
        if ok or (nban >= 2 and silent):
            seed.append(av_scan.standby_row_profile(gray[b[1]:b[3], b[0]:b[2]]))

    before = len((cfg.get('standby_profiles') or {}).get(room) or [])
    if seed:
        if nban >= 2:                      # replace the wrecked pool outright
            c = json.load(open(CONFIG, encoding='utf-8'))
            c.setdefault('standby_profiles', {})[room] = []
            json.dump(c, open(CONFIG, 'w', encoding='utf-8'), indent=2,
                      ensure_ascii=False)
        av_scan.remember_standby_profiles(room, seed)
    cfg = av_scan.load_config()
    after = len((cfg.get('standby_profiles') or {}).get(room) or [])
    print('%-9s banners=%d/%d seeded=%d  pool %d -> %d  %s' % (
        room, nban, len(info), len(seed), before, after,
        '(replaced)' if (seed and nban >= 2) else ''))
