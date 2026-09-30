"""Sweep candidate display detectors against the rooms whose wall TVs are known.

Ground truth = the regions Danny marked with red boxes (2026-09-28):
  SM-11-01  four wall TVs: (110,375,455,635) (730,90,905,215) (735,365,835,505) (1050,85,1270,225)
  SM-11-02  two wall TVs:  (255,57,478,207) (871,53,1100,208)
Everything else in those frames (desks, bright wall, whiteboard, clock) must NOT be
picked up. Run: python probe_filters.py
"""
import os
import sys
import numpy as np
from PIL import Image
from scipy import ndimage

sys.stdout.reconfigure(encoding='utf-8')
TMP = os.path.join('.workbuddy', 'tmp')
PASS = ('s1', 's2', 's3')


def gray(p):
    return np.asarray(Image.open(p).convert('L'), dtype=np.float32)


def known():
    return {
        '101': [(110, 375, 455, 635), (730, 90, 905, 215),
                (735, 365, 835, 505), (1050, 85, 1270, 225)],
        '102': [(255, 57, 478, 207), (871, 53, 1100, 208)],
    }


def iou(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    if not inter:
        return 0.0
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / float(ua)


def edge_columns(a, box, thresh=14, span=6):
    """Column positions inside `box` where the vertical edge energy peaks."""
    x0, y0, x1, y1 = (int(v) for v in box)
    reg = a[y0:y1, x0:x1]
    if reg.shape[1] < 20 or reg.shape[0] < 10:
        return []
    prof = np.abs(np.diff(reg, axis=1)).mean(axis=0)
    prof = np.convolve(prof, np.ones(span) / span, mode='same')
    lim = max(float(prof.mean()) * 2.0, 8.0)
    peaks = []
    for i in range(1, len(prof) - 1):
        if prof[i] >= lim and prof[i] >= prof[i - 1] and prof[i] >= prof[i + 1]:
            if not peaks or i - peaks[-1] > span:
                peaks.append(i)
    return [x0 + p for p in peaks]


def edge_rows(a, box, thresh=14, span=6):
    x0, y0, x1, y1 = (int(v) for v in box)
    reg = a[y0:y1, x0:x1]
    if reg.shape[0] < 20 or reg.shape[1] < 10:
        return []
    prof = np.abs(np.diff(reg, axis=0)).mean(axis=1)
    prof = np.convolve(prof, np.ones(span) / span, mode='same')
    lim = max(float(prof.mean()) * 2.0, 8.0)
    peaks = []
    for i in range(1, len(prof) - 1):
        if prof[i] >= lim and prof[i] >= prof[i - 1] and prof[i] >= prof[i + 1]:
            if not peaks or i - peaks[-1] > span:
                peaks.append(i)
    return [y0 + p for p in peaks]


def candidate_windows(a, fname, thr_floor=100, percentile=99, win=(0.115, 0.265), stride=(0.01, 0.02)):
    """Slide a TV-shaped window around; score = mean brightness minus surroundings."""
    h, w = a.shape
    rw, rh = win
    results = []
    for cx in np.arange(0.08, 0.95, stride[0]):
        for cy in np.arange(0.05, 0.62, stride[1]):
            x0, y0 = int((cx - rw / 2) * w), int((cy - rh / 2) * h)
            x1, y1 = int((cx + rw / 2) * w), int((cy + rh / 2) * h)
            if x0 < 0 or y0 < 0 or x1 > w or y1 > h:
                continue
            win_mean = float(a[y0:y1, x0:x1].mean())
            if win_mean < thr_floor:
                continue
            pad = int(0.25 * (y1 - y0))
            oy0, oy1 = max(0, y0 - pad), min(h, y1 + pad)
            ox0, ox1 = max(0, x0 - pad), min(w, x1 + pad)
            outer = np.concatenate([a[oy0:y0, ox0:ox1].ravel(),
                                    a[y1:oy1, ox0:ox1].ravel()])
            ring = float(outer.mean()) if outer.size else 0.0
            results.append(((win_mean - ring), win_mean, ring, (x0, y0, x1, y1)))
    results.sort(key=lambda r: -r[0])
    return results


if __name__ == '__main__':
    for ip, truth in known().items():
        fr = [gray(os.path.join(TMP, d, f'{ip}.jpg')) for d in PASS]
        a = fr[0]
        print('====', ip, 'ground truth', len(truth), 'displays')
        for t in truth:
            print('    truth %s  mean=%.0f' % (t, a[t[1]:t[3], t[0]:t[2]].mean()))
        top = candidate_windows(a, ip)[:6]
        print('  top sliding-window candidates:')
        for score, wm, ring, box in top:
            best = max(iou(box, t) for t in truth)
            print('    %s  win=%.0f ring=%.0f contrast=+%.0f  IoU(best truth)=%.2f'
                  % (box, wm, ring, score, best))
        print('  vertical edge peaks on truth boxes:')
        for t in truth:
            print('    %s cols=%s rows=%s' % (t, edge_columns(a, t), edge_rows(a, t)))
