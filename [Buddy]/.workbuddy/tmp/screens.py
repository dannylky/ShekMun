import os
import numpy as np
from PIL import Image
from scipy import ndimage

IPS = ['101', '102', '103', '104', '105', '106', '107', '108']
ROOM = {
    '101': 'SM-11-01', '102': 'SM-11-02', '103': 'SM-11-03', '104': 'SM-11-04',
    '105': 'SM-11-05', '106': 'SM-11-06', '107': 'SM-11-07', '108': 'SM-11-08',
}
GH, GW = 36, 64          # coarse grid


def gray(p):
    return np.asarray(Image.open(p).convert('L'), dtype=np.float32)


def grid(a):
    h, w = a.shape
    bh, bw = h // GH, w // GW
    return a[:GH * bh, :GW * bw].reshape(GH, bh, GW, bw).mean(axis=(1, 3))


grids = {}
for ip in IPS:
    grids[ip] = grid(gray(f's1/{ip}.jpg'))

# consensus: blocks that are bright in most rooms => fixed bright fixtures (displays / lights)
stack = np.stack([grids[ip] for ip in IPS])
consensus = (stack > 140).sum(axis=0)          # how many rooms are bright here
common = consensus >= 6                        # present in >=6 of 8 rooms
lab, n = ndimage.label(common)
print('consensus bright regions (present in >=6/8 rooms):')
regions = []
for i in range(1, n + 1):
    ys, xs = np.where(lab == i)
    if len(ys) < 6:
        continue
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    regions.append((y0, y1, x0, x1))
    print(f'  grid r{y0}-{y1} c{x0}-{x1}  ({len(ys)} blocks)')

print()
print('per-room brightness inside each consensus region:')
print(f"{'room':10s} " + ' '.join(f'R{k+1}' for k in range(len(regions))))
for ip in IPS:
    vals = [f'{grids[ip][y0:y1+1, x0:x1+1].mean():5.0f}' for y0, y1, x0, x1 in regions]
    print(f'{ROOM[ip]:10s} ' + ' '.join(vals))

# within-room sync: compare the full frame halves? instead compare bright patches found per room
print()
print('within-room: compare all per-room bright patches (16x9 grid blobs):')


def patches(ip, min_blocks=10):
    g = grids[ip]
    h, w = gray(f's1/{ip}.jpg').shape
    bh, bw = h // GH, w // GW
    thr = max(130, np.percentile(g, 94))
    lab, n = ndimage.label(g > thr)
    out = []
    for i in range(1, n + 1):
        ys, xs = np.where(lab == i)
        if len(ys) < min_blocks:
            continue
        y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
        if (y1 - y0) < 2 or (x1 - x0) < 3:
            continue
        p = gray(f's1/{ip}.jpg')[y0 * bh:(y1 + 1) * bh, x0 * bw:(x1 + 1) * bw]
        out.append(((x0, y0, x1, y1), p))
    return out[:5]


def sig(p, n=32):
    im = Image.fromarray(p.astype(np.uint8)).resize((n, n))
    v = np.asarray(im, dtype=np.float32)
    return (v - v.mean()) / (v.std() + 1e-6)


for ip in IPS:
    ps = patches(ip)
    print(f'  {ROOM[ip]}: {len(ps)} patch(es)', end='')
    if len(ps) > 1:
        ds = []
        for i in range(len(ps)):
            for j in range(i + 1, len(ps)):
                ds.append(np.abs(sig(ps[i][1]) - sig(ps[j][1])).mean())
        print('  diffs=' + ', '.join(f'{d:.2f}' for d in ds))
    else:
        print()
