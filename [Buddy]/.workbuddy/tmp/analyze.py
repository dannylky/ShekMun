import os
import numpy as np
from PIL import Image

NAMES = {
    '101': 'SM01 (11-01)', '102': 'SM02 (11-02)', '103': 'SM03 (11-03)',
    '104': 'SM04 (11-04)', '105': 'SM05 (11-05)', '106': 'SM06 (11-06)',
    '107': 'SM07 (11-07)', '108': 'SM08 (11-08)', '109': 'Common Area',
}

def lum(path):
    im = Image.open(path).convert('L')
    return np.asarray(im, dtype=np.float32), im.size

print(f"{'Room':16s} {'Res':10s} {'Mean':>6s} {'Dark%':>6s} {'Bright%':>7s} {'Motion%':>8s} {'HotSpots':>8s}")
print('-' * 70)
rows = []
for ip in ['101', '102', '103', '104', '105', '106', '107', '108', '109']:
    p1 = f'm1/{ip}.jpg'
    if not os.path.exists(p1):
        print(f"{NAMES[ip]:16s}  UNREACHABLE (502 upstream connect failed)")
        rows.append((ip, None))
        continue
    a, size = lum(p1)
    dark = (a < 40).mean() * 100
    bright = (a > 180).mean() * 100

    motion = float('nan')
    p2 = f'm2/{ip}.jpg'
    if os.path.exists(p2):
        b, _ = lum(p2)
        if a.shape == b.shape:
            motion = (np.abs(a - b) > 18).mean() * 100

    # 16x9 block map -> count blocks that are clearly bright (candidate lit displays)
    h, w = a.shape
    bh, bw = h // 9, w // 16
    blocks = a[:bh * 9, :bw * 16].reshape(9, bh, 16, bw).mean(axis=(1, 3))
    hotspots = int((blocks > 150).sum())

    rows.append((ip, (size, a.mean(), dark, bright, motion, hotspots)))
    print(f"{NAMES[ip]:16s} {str(size):10s} {a.mean():6.1f} {dark:6.1f} {bright:7.2f} {motion:8.2f} {hotspots:8d}")

# brightest blocks location for context
print()
for ip, r in rows:
    if not r:
        continue
    a, _ = lum(f'm1/{ip}.jpg')
    h, w = a.shape
    bh, bw = h // 9, w // 16
    blocks = a[:bh * 9, :bw * 16].reshape(9, bh, 16, bw).mean(axis=(1, 3))
    top = np.dstack(np.unravel_index(np.argsort(-blocks.ravel())[:3], blocks.shape))[0]
    pos = ', '.join(f"r{int(y)}/c{int(x)}({blocks[y, x]:.0f})" for y, x in top)
    print(f"{NAMES[ip]:16s} brightest blocks -> {pos}")
