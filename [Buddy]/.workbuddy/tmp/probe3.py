"""Probe 3 - how flat is the grey wall inside a TV vs the wall around it?

A dark-bezel TV shows its picture against a fairly uniform grey wall. If the panel is
"lit at all" it has to stand out from that wall locally, no matter how dim the room
overall. A wall clock / whiteboard / desk strip behave differently.
"""
import os
import sys
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
TMP = os.path.join('.workbuddy', 'tmp')
PASS = ('s1', 's2', 's3')
TRUTH = {
    '101': [(110, 375, 455, 635), (730, 90, 905, 215),
            (735, 365, 835, 505), (1050, 85, 1270, 225)],
    '102': [(255, 57, 478, 207), (871, 53, 1100, 208)],
}


def gray(p):
    return np.asarray(Image.open(p).convert('L'), dtype=np.float32)


def local_contrast(a, box, band=22):
    """Panel vs the *tight ring* immediately around it, per edge, in a wall band."""
    x0, y0, x1, y1 = (int(v) for v in box)
    panel = a[y0:y1, x0:x1]
    ring = np.concatenate([
        a[max(0, y0 - band):y0, x0:x1].ravel(),
        a[y1:min(a.shape[0], y1 + band), x0:x1].ravel(),
        a[y0:y1, max(0, x0 - band):x0].ravel(),
        a[y0:y1, x1:min(a.shape[1], x1 + band)].ravel()])
    return float(panel.mean()), float(ring.mean()), float(panel.mean() - ring.mean())


def block_scores(a, gh=45, gw=80, pct=93, floor=100):
    h, w = a.shape
    bh, bw = h // gh, w // gw
    blocks = a[:gh * bh, :gw * bw].reshape(gh, bh, gw, bw).mean(axis=(1, 3))
    thr = max(floor, float(np.percentile(blocks, pct)))
    return blocks, thr, bh, bw


if __name__ == '__main__':
    for ip, truth in TRUTH.items():
        fr = [gray(os.path.join(TMP, d, f'{ip}.jpg')) for d in PASS]
        a = fr[0]
        print('====', ip)
        for t in truth:
            p, r, d = local_contrast(a, t)
            print('  truth %-24s panel=%3.0f ring=%3.0f  contrast=%+.0f' % (t, p, r, d))
        for extra, tag in ((('1056', 'clock') if False else ((1120, 30, 1180, 90), 'wall clock 101')),
                           ((520, 560, 900, 620), 'bright desk strip 101'),
                           ((112, 448, 400, 624), 'old blob #1 101'),
                           ((1056, 160, 1248, 224), 'old blob #2 101'),
                           ((800, 448, 1280, 528), 'desk band 102'),
                           ((704, 112, 832, 208), 'blob TV2 102')):
            if (ip == '101') != (tag.endswith('101')):
                continue
            p, r, d = local_contrast(a, extra)
            print('  %-22s panel=%3.0f ring=%3.0f  contrast=%+.0f' % (tag, p, r, d))
        blocks, thr, bh, bw = block_scores(a)
        print('  block threshold=%.0f  max block=%.0f' % (thr, blocks.max()))
        # how do the truth panels score as blocks?
        for t in truth:
            x0, y0, x1, y1 = t
            sub = blocks[y0 // bh:(y1 // bh) + 1, x0 // bw:(x1 // bw) + 1]
            print('    truth %s block mean=%.0f max=%.0f' % (t, sub.mean(), sub.max()))
