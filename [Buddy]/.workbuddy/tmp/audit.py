import os
import numpy as np
from PIL import Image
from scipy import ndimage

ROOMS = [
    ('101', 'SM-11-01'), ('102', 'SM-11-02'), ('103', 'SM-11-03'),
    ('104', 'SM-11-04'), ('105', 'SM-11-05'), ('106', 'SM-11-06'),
    ('107', 'SM-11-07'), ('108', 'SM-11-08'), ('109', 'Common Area'),
]
PASSES = ['s1', 's2', 's3']


def gray(path):
    return np.asarray(Image.open(path).convert('L'), dtype=np.float32)


def find_screens(a):
    """Locate bright wall-mounted display regions on a coarse block grid."""
    h, w = a.shape
    gh, gw = 45, 80                      # block grid
    bh, bw = h // gh, w // gw
    blocks = a[:gh * bh, :gw * bw].reshape(gh, bh, gw, bw).mean(axis=(1, 3))

    thr = max(120, np.percentile(blocks, 93))
    mask = blocks > thr
    lab, n = ndimage.label(mask)
    out = []
    for i in range(1, n + 1):
        ys, xs = np.where(lab == i)
        if len(ys) < 8:                  # ignore tiny specks (<0.25% of frame)
            continue
        y0, y1 = ys.min(), ys.max()
        x0, x1 = xs.min(), xs.max()
        bhpx, bwpx = (y1 - y0 + 1) * bh, (x1 - x0 + 1) * bw
        if bhpx < 60 or bwpx < 100:      # too small to be a display
            continue
        patch = a[y0 * bh:(y1 + 1) * bh, x0 * bw:(x1 + 1) * bw]
        out.append({
            'box': (x0 * bw, y0 * bh, (x1 + 1) * bw, (y1 + 1) * bh),
            'mean': float(patch.mean()),
            'std': float(patch.std()),
            'area': float((y1 - y0 + 1) * (x1 - x0 + 1)) / (gh * gw) * 100,
            'patch': patch,
            'pos': (float((x0 + x1) / 2) / gw, float((y0 + y1) / 2) / gh),
        })
    out.sort(key=lambda d: -d['area'])
    return out[:6], blocks


def classify(s):
    """Rough on/off call from brightness + internal contrast."""
    if s['mean'] >= 150 and s['std'] < 25:
        return 'ON (near-white / standby splash)'
    if s['mean'] >= 90 and s['std'] >= 25:
        return 'ON (live content)'
    if s['mean'] >= 90:
        return 'ON (bright, low detail)'
    if s['mean'] >= 45:
        return 'DIM / standby'
    return 'OFF / black'


def sig(patch, n=32):
    im = Image.fromarray(patch.astype(np.uint8)).resize((n, n))
    v = np.asarray(im, dtype=np.float32)
    return (v - v.mean()) / (v.std() + 1e-6)


def compare(a, b):
    return float(np.abs(sig(a) - sig(b)).mean())


def motion_blobs(frames):
    """Connected regions that changed between passes -> moving objects."""
    stack = np.stack(frames)
    rng = stack.max(axis=0) - stack.min(axis=0)
    m = rng > 22
    m = ndimage.binary_opening(m, np.ones((3, 3)))
    lab, n = ndimage.label(m)
    blobs = []
    for i in range(1, n + 1):
        ys, xs = np.where(lab == i)
        if len(ys) < 400:
            continue
        h = ys.max() - ys.min()
        w = xs.max() - xs.min()
        blobs.append((len(ys), h, w, float(xs.mean()), float(ys.mean())))
    return blobs, float(m.mean() * 100)


report = []
for ip, name in ROOMS:
    files = [f'{p}/{ip}.jpg' for p in PASSES]
    if not all(os.path.exists(f) and os.path.getsize(f) > 5000 for f in files):
        report.append((name, ip, None))
        continue

    frames = [gray(f) for f in files]
    a = frames[0]
    screens, blocks = find_screens(a)
    blobs, mfrac = motion_blobs(frames)

    # person-ish blobs: tall-ish, moderate size, in lower 2/3 of frame
    persons = []
    for area, h, w, cx, cy in blobs:
        if 60 <= h <= 400 and 25 <= w <= 260 and cy > a.shape[0] * 0.35:
            persons.append((area, h, w, cx, cy))

    report.append((name, ip, {
        'mean': float(a.mean()),
        'dark': float((a < 40).mean() * 100),
        'bright': float((a > 180).mean() * 100),
        'motion': mfrac,
        'persons': persons,
        'screens': screens,
    }))

for name, ip, r in report:
    print('=' * 78)
    print(f'{name}   (172.18.22.{ip})')
    if r is None:
        print('  CAMERA UNREACHABLE - 502 upstream connect failed')
        continue
    print(f"  [1] Lighting : mean luminance {r['mean']:.1f} | dark pixels {r['dark']:.1f}% "
          f"| bright {r['bright']:.2f}%")
    print(f"      -> {'LIGHTS ON' if r['mean'] > 90 and r['dark'] < 20 else 'LIGHTS OFF / PARTIAL'}")
    print(f"  [2] Activity : motion pixels over 12s = {r['motion']:.2f}% | "
          f"candidate moving blobs = {len(r['persons'])}")
    for area, h, w, cx, cy in sorted(r['persons'], key=lambda t: -t[0])[:5]:
        print(f"      blob {w}x{h}px at ({cx:.0f},{cy:.0f})  [NOT a confirmed person count]")
    print(f"  [3] Displays : {len(r['screens'])} candidate bright region(s)")
    for i, s in enumerate(r['screens'], 1):
        x0, y0, x1, y1 = s['box']
        print(f"      #{i} {x1-x0}x{y1-y0}px at ({x0},{y0})  mean={s['mean']:.0f} "
              f"std={s['std']:.0f}  -> {classify(s)}")
    if len(r['screens']) > 1:
        print('      sync (lower = more identical):')
        for i in range(len(r['screens'])):
            for j in range(i + 1, len(r['screens'])):
                d = compare(r['screens'][i]['patch'], r['screens'][j]['patch'])
                verdict = 'SAME CONTENT (synced)' if d < 0.55 else (
                    'similar' if d < 0.85 else 'DIFFERENT CONTENT (out of sync)')
                print(f"        #{i+1} vs #{j+1}: diff={d:.2f} -> {verdict}")
