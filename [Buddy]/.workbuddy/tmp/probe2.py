"""Probe 2 - test 'screen = rectangle framed by dark edges' vs the truth boxes."""
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


def border_profile(a, box, t=45, pad=26):
    """Mean brightness of a 1-D strip t px outside and inside each edge."""
    x0, y0, x1, y1 = (int(v) for v in box)
    out = {}
    for name, o0, i0 in (
            ('L', (slice(y0, y1), slice(x0 - pad - t, x0 - pad)),
             (slice(y0, y1), slice(x0 + 2, x0 + 2 + t))),
            ('R', (slice(y0, y1), slice(x1 + pad, x1 + pad + t)),
             (slice(y0, y1), slice(x1 - 2 - t, x1 - 2))),
            ('T', (slice(y0 - pad - t, y0 - pad), slice(x0, x1)),
             (slice(y0 + 2, y0 + 2 + t), slice(x0, x1))),
            ('B', (slice(y1 + pad, y1 + pad + t), slice(x0, x1)),
             (slice(y1 - 2 - t, y1 - 2), slice(x0, x1)))):
        o = a[o0]
        i = a[i0]
        out[name] = (float(i.mean()) - float(o.mean())) if o.size and i.size else None
    return out


if __name__ == '__main__':
    for ip, truth in TRUTH.items():
        fr = [gray(os.path.join(TMP, d, f'{ip}.jpg')) for d in PASS]
        a = fr[0]
        print('====', ip)
        for t in truth:
            print('  truth %s' % (t,))
            print('     step-out-in contrast:', border_profile(a, t))
        # a deliberate non-display: bright desk strip and the whiteboard
        if ip == '101':
            for extra, tag in (((520, 560, 900, 620), 'bright desk strip'),
                               ((600, 80, 780, 175), 'whiteboard-ish'),
                               ((112, 448, 400, 624), 'old blob #1'),
                               ((1056, 160, 1248, 224), 'old blob #2')):
                print('  %-18s %s' % (tag, extra))
                print('     step-out-in contrast:', border_profile(a, extra))
