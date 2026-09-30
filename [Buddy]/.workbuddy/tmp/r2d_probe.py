import os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, '.')
import av_scan

D = r'.workbuddy\tmp\live2d'
frames = []
for i in range(3):
    im = Image.open(os.path.join(D, 'g%d.jpg' % i)).convert('RGB')
    frames.append(np.asarray(im, dtype=np.uint8))
print('frame', frames[0].shape)

BOXES = {
    'LEFT  (255,52,477,189)':  (255, 52, 477, 189),
    'RIGHT (861,51,1092,185)': (861, 51, 1092, 185),
}

for name, (x0, y0, x1, y1) in BOXES.items():
    print('\n===', name, '===')
    for i, f in enumerate(frames):
        p = f[y0:y1, x0:x1]
        l = np.asarray(Image.fromarray(f).convert('L'), dtype=np.float32)[y0:y1, x0:x1]
        br = float((p[:, :, 2].astype(np.float32) - p[:, :, 0]).mean())
        sat = float((p.max(axis=2).astype(np.float32) - p.min(axis=2)).mean())
        print('  g%d  lum=%6.1f  B-R=%7.2f  sat=%6.2f  meanRGB=(%.0f,%.0f,%.0f)' % (
            i, l.mean(), br, sat, p[:, :, 0].mean(), p[:, :, 1].mean(), p[:, :, 2].mean()))

# what does the hue gate say right now?
cfg = av_scan.load_config()
print('\n--- gate constants ---')
for c in ('STANDBY_HUE_BR_MIN', 'STANDBY_HUE_BR_MAX', 'STANDBY_HUE_SAT_MAX',
          'STANDBY_NCC_MIN', 'STANDBY_BAND_MIN'):
    print('  %-22s %s' % (c, getattr(av_scan, c, '?')))

print('\n--- hue_match verdict per frame ---')
for name, (x0, y0, x1, y1) in BOXES.items():
    for i, f in enumerate(frames):
        p = f[y0:y1, x0:x1]
        h = av_scan.standby_hue(p)
        m = av_scan.standby_hue_match(p, None)
        print('  %-24s g%d  hue=%s  match=%s' % (name, i, h, m))
