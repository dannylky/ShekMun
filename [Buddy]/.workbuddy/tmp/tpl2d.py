"""Test: 2D high-pass normalised cross-correlation against a confirmed standby panel.

Colour cannot separate a slide from the standby screen (room 2's slide measures
B-R 15.0 / sat 28.8, inside the standby band). Layout can - so compare the actual
2-D structure, high-pass filtered to kill sun glare, resized to a common grid.
"""
import os, sys
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, zoom
sys.path.insert(0, '.')
import av_scan

OUT = r'.workbuddy\tmp\huescan'
cfg = av_scan.load_config()
regions = cfg.get('display_regions') or {}
GW, GH = 64, 36


def hp(img, sigma=12):
    """high-pass: subtract a heavy blur -> immune to sun-glare gradients."""
    f = img.astype(np.float32)
    return f - gaussian_filter(f, sigma)


def norm(img):
    f = img.astype(np.float32)
    f = zoom(f, (GH / f.shape[0], GW / f.shape[1]), order=1)
    f = f - f.mean()
    s = f.std()
    return f / s if s > 1e-6 else f


def sig(gray_patch):
    return norm(hp(gray_patch))


def ncc(a, b):
    return float((a * b).mean())


# build signatures
sigs = {}
for room in sorted(regions):
    f = os.path.join(OUT, '%s.jpg' % room)
    if not os.path.exists(f) or os.path.getsize(f) < 5000:
        continue
    im = Image.open(f).convert('RGB')
    arr = np.asarray(im, dtype=np.uint8)
    gray = np.asarray(im.convert('L'), dtype=np.float32)
    for i, reg in enumerate(regions[room]):
        b = reg['box']
        g = gray[b[1]:b[3], b[0]:b[2]]
        try:
            z = av_scan.panel_zoom_ocr([arr], b)
            txt = ' | '.join(z)[:30]
        except Exception:
            txt = ''
        sigs['%s#%d' % (room, i)] = (sig(g), reg.get('label', '')[:16], txt,
                                     room, b)

# reference = SM-11-06 (clean OCR'd standby)
ref_key = None
for k, v in sigs.items():
    if v[3] == 'SM-11-06':
        ref_key = k
        break
print('reference panel:', ref_key, sigs[ref_key][1], '|', sigs[ref_key][2])
ref = sigs[ref_key][0]

print('\n%-11s %-18s %7s  %s' % ('panel', 'label', '2D-NCC', 'ocr (ground truth)'))
print('-' * 100)
rows = []
for k in sorted(sigs):
    s, lab, txt, room, b = sigs[k]
    v = ncc(ref, s)
    banner = 'AVOIP' in txt.upper().replace(' ', '') or 'STAND' in txt.upper()
    rows.append((v, k, lab, txt, banner))
for v, k, lab, txt, banner in sorted(rows, reverse=True):
    mark = 'STANDBY' if banner else 'content'
    print('%-11s %-18s %7.3f  %-30s %s' % (k, lab, v, txt[:30], mark))

st = [r[0] for r in rows if r[4]]
ct = [r[0] for r in rows if not r[4]]
print('\nOCR-confirmed standby : n=%d  min %.3f  max %.3f' % (len(st), min(st), max(st)))
print('content (no banner)   : n=%d  min %.3f  max %.3f' % (len(ct), min(ct), max(ct)))
