#!/usr/bin/env python
# Shek Mun AV room scan -> HTML report with inline camera snapshots.
import os
import re
import json
import time
import base64
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageOps, ImageFilter
from scipy import ndimage

OUT = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(OUT, '.workbuddy', 'tmp')
SNAP_URL = 'http://10.107.147.121:8080/snapshot.json'
CONFIG = os.path.join(OUT, 'av_monitor_config.json')
CHANGELOG = os.path.join(OUT, 'changelog.md')

# Report engine version. Keep in step with the top entry of changelog.md; it is stamped
# into the HTML report, the email body and the email subject footer so Danny always
# knows which rule set produced a given report.
VERSION = '2.6.1'
# an OUT OF SYNC verdict must repeat on a consecutive run inside this window before it
# is allowed to raise an Abnormal (Danny: avoid one-off false alarms)
SYNC_CONFIRM_WINDOW_S = 3 * 3600

# KDS temperature alarm threshold (deg C) - only at/above this is a room "Abnormal".
# Danny raised it from 45 to 49 on 2026-09-21; the value in av_monitor_config.json wins.
KDS_ALARM = 49
# rooms with at least this many monitored displays must show one common picture
SYNC_MIN_DECODERS = 2
# a disagreeing region must cover at least this share of the largest display's area
# before the room is called OUT OF SYNC (Danny: only flag a *highly* unmatched room)
SYNC_MIN_AREA_RATIO = 0.30
# text that identifies the AVoIP "decoder standby" screen
AVOIP_IDLE_KEYS = ('AVOIP', 'DECODER', 'STANDBY', 'VIDEO SOURCE', 'DISCONNECTED',
                   'SWITCHED OFF', 'SLEEP MODE', 'TO WAKE')
# Narrower evidence that a bright region really IS a TV: an AVoIP decoder standby
# screen can only come from a display, never from a whiteboard / noticeboard.
DISPLAY_TEXT_KEYS = ('AVOIP', 'DECODER', 'STANDBY', 'VIDEO SOURCE', 'DISCONNECTED')

ROOMS = [
    ('101', 'SM-11-01', 'SM-11-01'), ('102', 'SM-11-02', 'SM-11-02'),
    ('103', 'SM-11-03', 'SM-11-03'), ('104', 'SM-11-04', 'SM-11-04'),
    ('105', 'SM-11-05', 'SM-11-05'), ('106', 'SM-11-06', 'SM-11-06'),
    ('107', 'SM-11-07', 'SM-11-07'), ('108', 'SM-11-08', 'SM-11-08'),
    ('109', 'Common Rm', 'Common Area'),
]
# snapshot.json room key -> camera ip suffix
PASS_DIRS = ['s1', 's2', 's3']


def load_config():
    if os.path.exists(CONFIG):
        with open(CONFIG, encoding='utf-8') as f:
            return json.load(f)
    return {'scheduled_down': ['Common Area'],
            'note': 'Rooms listed here are intentionally offline. '
                    'They are still scanned every run, but reported as SCHEDULED DOWN, not as a fault.'}


def kds_alarm(cfg):
    """Alarm threshold from the config file (falls back to the built-in constant)."""
    v = (cfg.get('scan') or {}).get('temp_alarm_c')
    try:
        return int(v)
    except (TypeError, ValueError):
        return KDS_ALARM


def display_spec(cfg, label, fallback):
    """Declared display inventory for a room: (count, type).

    Danny confirmed: SM-11-02 = 2 LED TV, SM-11-03..06 = 1 LED wall, SM-11-07 = 2 LED TV.
    Any smaller bright region in the frame is a traditional whiteboard and is ignored.
    """
    d = (cfg.get('displays') or {}).get(label) or {}
    try:
        n = int(d.get('count') or fallback)
    except (TypeError, ValueError):
        n = int(fallback)
    typ = d.get('type') or ('LED TV' if n > 1 else 'LED wall')
    return max(1, n), typ


def display_filter(cfg, label):
    """Wall-display filter for a room, or None.

    Danny (2026-09-23): in SM-11-02 / 07 / 08 only the two large LED TVs **on the
    wall** count for the idle and picture-sync verdicts — the small computer monitors
    on the desks must be ignored. Configured per room under
    `av_monitor_config.json → display_filter`.
    """
    f = (cfg.get('display_filter') or {}).get(label)
    return dict(f) if isinstance(f, dict) and f else None


def display_regions(cfg, label):
    """Fixed display boxes (in 1280x720 frame pixels) for a room, or None.

    Danny (2026-09-28): he marks the displays he wants watched with a red rectangle
    on the camera image, and those boxes are now authoritative for the rooms where
    the bright-blob detector cannot find the panels at all.

    Why this is needed for SM-11-02: both wall TVs currently show the Windows lock
    screen, whose blue wallpaper makes the panel *darker* than the wall around it
    (panel mean 98 / 99 vs wall 129 / 171). The detector looks for bright blobs
    (`blocks > max(120, 93rd pct)`), so it finds only the bright desk band and the
    small desk monitors - never these two TVs. Measured on the live frame: the best
    sliding-window candidate scored IoU 0.00 against Danny's boxes.

    A region entry therefore bypasses bright-blob detection entirely: the engine
    measures the box directly. Each region is `{"box": [x0,y0,x1,y1], "label": "..."}`.
    Boxes may be given in the camera frame's own pixels; `frame` (optional) names the
    frame size they were measured in, and they are rescaled when it differs.
    """
    r = (cfg.get('display_regions') or {}).get(label)
    if not isinstance(r, (list, tuple)) or not r:
        return None
    out = []
    for item in r:
        if not isinstance(item, dict):
            continue
        b = item.get('box')
        if not (isinstance(b, (list, tuple)) and len(b) == 4):
            continue
        try:
            box = [float(v) for v in b]
        except (TypeError, ValueError):
            continue
        fw, fh = item.get('frame') or (1280, 720)
        try:
            fw, fh = float(fw), float(fh)
        except (TypeError, ValueError):
            fw, fh = 1280.0, 720.0
        if fw > 0 and fh > 0 and (fw != 1280 or fh != 720):
            box = [box[0] * 1280 / fw, box[1] * 720 / fh,
                   box[2] * 1280 / fw, box[3] * 720 / fh]
        out.append({'box': [int(round(v)) for v in box],
                    'label': item.get('label') or ''})
    return out or None


def poller_state(snap):
    """Detect a monitoring-poller restart.

    Right after the poller restarts, snapshot.json is republished with every device
    still un-polled: `status: "unknown"`, empty `checkedAt` and `rttMs: -1`. That used to
    be read as "device unreachable" and produced a whole-floor false Abnormal
    (2026-09-22 08:02). `unknown` now means "not measured yet", never "fault".
    """
    rooms = (snap or {}).get('rooms') or {}
    total = unknown = fail = 0
    for devs in rooms.values():
        for d in devs or []:
            total += 1
            st = d.get('status')
            if st == 'unknown' or (not d.get('checkedAt') and d.get('rttMs', 0) < 0):
                unknown += 1
            elif st == 'fail':
                fail += 1
    ratio = unknown / total if total else 0.0
    return {'total': total, 'unknown': unknown, 'fail': fail, 'unknown_ratio': round(ratio, 3),
            'stale': bool(total) and ratio >= 0.5,
            'generated_at': (snap or {}).get('generatedAt', ''),
            'updated_at': (snap or {}).get('updatedAt', '')}


def is_fault(d):
    """Only an explicit `fail` is a fault. `unknown` = not polled yet (see poller_state)."""
    return d.get('status') == 'fail'


def sync_history_path():
    return os.path.join(TMP, 'sync_history.json')


def load_sync_history():
    try:
        with open(sync_history_path(), encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def apply_sync_persistence(label, sync):
    """Require two consecutive runs before OUT OF SYNC is allowed to raise Abnormal.

    The *raw* verdict is always stored, so the next run can confirm or clear it. A
    first-time out-of-sync is downgraded to `check` and only asks for a visual check.
    """
    if not sync.get('applicable') or sync.get('verdict') != 'out-of-sync':
        return sync
    hist = load_sync_history()
    now = time.time()
    prev = hist.get(label) or {}
    sync['raw_verdict'] = 'out-of-sync'
    confirmed = (prev.get('verdict') == 'out-of-sync'
                 and (now - float(prev.get('ts', 0))) <= SYNC_CONFIRM_WINDOW_S)
    hist[label] = {'verdict': 'out-of-sync', 'ts': now}
    try:
        os.makedirs(TMP, exist_ok=True)
        with open(sync_history_path(), 'w', encoding='utf-8') as f:
            json.dump(hist, f, indent=1)
    except Exception:
        pass
    if confirmed:
        sync['detail'].append('Confirmed on <b>two consecutive runs</b> '
                              f'(within {SYNC_CONFIRM_WINDOW_S // 3600} h) &mdash; reported as '
                              'an Abnormal condition.')
        return sync
    sync['verdict'] = 'check'
    sync['pill'] = 'p-idle'
    sync['label'] = 'OUT OF SYNC (1ST RUN)'
    sync['detail'].append('First run that reports this mismatch &mdash; <b>not</b> counted as '
                          'abnormal yet. It is raised only if the next run (within '
                          f'{SYNC_CONFIRM_WINDOW_S // 3600} h) agrees. Worth a visual check now.')
    return sync


def fetch_snapshot():
    p = os.path.join(TMP, 'snapshot_live.json')
    subprocess.run(['curl', '-s', '--max-time', '20', SNAP_URL, '-o', p], check=False)
    try:
        with open(p, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def grab():
    for d in PASS_DIRS:
        os.makedirs(os.path.join(TMP, d), exist_ok=True)
    for i, d in enumerate(PASS_DIRS):
        procs = []
        for ip, _, _ in ROOMS:
            out = os.path.join(TMP, d, f'{ip}.jpg')
            procs.append(subprocess.Popen(
                ['curl', '-s', '--max-time', '12',
                 f'http://172.18.22.{ip}/snapshot/snapshot', '-o', out]))
        for p in procs:
            p.wait()
        if i < len(PASS_DIRS) - 1:
            time.sleep(6)


def gray(path):
    return np.asarray(Image.open(path).convert('L'), dtype=np.float32)


def refine_box(a, box, pad=30, edge_frac=0.55, streak=0.70, max_grow=0.65):
    """Tighten a blob-detected display box onto the actual lit panel.

    Danny (2026-09-28): the blob detector works on 45x80 blocks, so it merges a
    display with the bright wall / ceiling around it and reports a rectangle that is
    much bigger than the real screen. Run 2026-09-28 14:16 is the proof: SM-11-01
    reported three regions of 288x176 / 192x64 / 112x96, i.e. absurd aspect ratios
    for 16:9 TVs (1.64 / 3.00 / 1.17) - those rectangles are not screens, they are
    "bright block clusters". RapidOCR also joined the speech text on TV2 + TV3 into
    one reading at x=170-830, which spans the dark wall between them, because the
    attribution test asked "is the centre inside the box?" and the wrongly-huge box
    swallowed both TVs.

    This routine walks outwards from the blob until a real edge shows up - a row
    (or column) whose edge density falls below `streak` of the in-blob mean, measured
    at `edge_frac` of the blob's own brightness so it works on a dim standby screen
    as well as on a bright one. `max_grow` caps the search so a blob that sits on a
    wall with no edge nearby cannot run away across the frame.

    Returns a new box, or the original one when no sensible edge is found.
    """
    h, w = a.shape
    x0, y0, x1, y1 = (int(v) for v in box)
    bw, bh = max(1, x1 - x0), max(1, y1 - y0)
    gx, gy = int(round(bw * max_grow)), int(round(bh * max_grow))
    px0, py0 = max(0, x0 - pad - gx), max(0, y0 - pad - gy)
    px1, py1 = min(w, x1 + pad + gx), min(h, y1 + pad + gy)
    patch = a[py0:py1, px0:px1]
    if patch.size == 0 or patch.shape[0] < 12 or patch.shape[1] < 12:
        return (x0, y0, x1, y1)
    ed = np.abs(np.diff(patch, axis=1))
    e_row = ed.mean(axis=1)                     # per-row edge density
    e_col = np.abs(np.diff(patch, axis=0)).mean(axis=0)
    level = float(np.median(patch)) * edge_frac
    lit_row, lit_col = patch.mean(axis=1) > level, patch.mean(axis=0) > level

    y_lo, y_hi = y0 - py0, y1 - py0 - 1
    if e_row[y_lo:y_hi + 1].size < 4:
        return (x0, y0, x1, y1)
    thr = max(4.0, float(e_row[y_lo:y_hi + 1].mean()) * streak)
    lim = int(max(bw, bh) * max_grow)

    def walk(mask, dens, thr_, start, stop, limit):
        frm, to = min(start, stop), max(start, stop)
        i = to
        while i + 1 < len(dens) and i - to < limit and dens[i + 1] >= thr_ and mask[i + 1]:
            i += 1
        j = frm
        while j - 1 >= 0 and frm - j < limit and dens[j - 1] >= thr_ and mask[j - 1]:
            j -= 1
        return j, i

    ny0, ny1 = walk(lit_row, e_row, thr, y_lo, y_hi, lim)
    cx_lo, cx_hi = x0 - px0, x1 - px0 - 1
    thrx = max(4.0, float(e_col[cx_lo:cx_hi + 1].mean()) * streak)
    nx0, nx1 = walk(lit_col, e_col, thrx, cx_lo, cx_hi, lim)
    nb = (px0 + nx0, py0 + ny0, px0 + nx1 + 1, py0 + ny1 + 1)
    if (nb[2] - nb[0]) < 40 or (nb[3] - nb[1]) < 30:
        return (x0, y0, x1, y1)
    return nb


def refine_box_frames(frames, box, **kw):
    """Run `refine_box` on every pass and keep the intersection (stable geometry)."""
    boxes = [refine_box(f, box, **kw) for f in frames]
    return (max(b[0] for b in boxes), max(b[1] for b in boxes),
            min(b[2] for b in boxes), min(b[3] for b in boxes))


def iou(a, b):
    """Intersection over union of two (x0,y0,x1,y1) boxes."""
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    if not inter:
        return 0.0
    ua = ((a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter)
    return inter / ua if ua else 0.0


# tuned on the live SM-11-01 frame (2026-09-28): a 288x176 wall-band blob shrinks to
# 312x180 around the TV panel, a 192x64 blob to 193x65 (spectator band removed), while
# the big 4K TV is kept at 142x170 instead of the 112x96 that cut it in half.
REFINE_TUNE = {'pad': 30, 'edge_frac': 0.85, 'streak': 0.75, 'max_grow': 0.35}


def screens(a):
    gh, gw = 45, 80
    h, w = a.shape
    bh, bw = h // gh, w // gw
    blocks = a[:gh * bh, :gw * bw].reshape(gh, bh, gw, bw).mean(axis=(1, 3))
    thr = max(120, np.percentile(blocks, 93))
    lab, n = ndimage.label(blocks > thr)
    out = []
    for i in range(1, n + 1):
        ys, xs = np.where(lab == i)
        if len(ys) < 8:
            continue
        y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
        if (y1 - y0 + 1) * bh < 60 or (x1 - x0 + 1) * bw < 100:
            continue
        patch = a[y0 * bh:(y1 + 1) * bh, x0 * bw:(x1 + 1) * bw]
        out.append({'box': (x0 * bw, y0 * bh, (x1 + 1) * bw, (y1 + 1) * bh),
                    'mean': float(patch.mean()), 'std': float(patch.std()),
                    'patch': patch})
    # Merge blobs that are actually one display: a dark-bezel TV splits the wall band
    # it sits in into left / right fragments (SM-11-02, SM-11-04), and treating those
    # as two separate "displays" is what makes the idle / sync verdict nonsense. Two
    # blobs merge when they overlap vertically (>=40% of the shorter one) and their
    # gap is small relative to their height, so separate TVs side by side stay apart.
    merged = True
    while merged and len(out) > 1:
        merged = False
        for i in range(len(out)):
            for j in range(i + 1, len(out)):
                a_, b_ = out[i]['box'], out[j]['box']
                ov = min(a_[3], b_[3]) - max(a_[1], b_[1])
                gap = max(a_[0], b_[0]) - min(a_[2], b_[2])
                if ov > 0.4 * min(a_[3] - a_[1], b_[3] - b_[1]) and gap < 0.9 * ov:
                    box = (min(a_[0], b_[0]), min(a_[1], b_[1]),
                           max(a_[2], b_[2]), max(a_[3], b_[3]))
                    patch = a[int(box[1]):int(box[3]), int(box[0]):int(box[2])]
                    out[i] = {'box': box, 'mean': float(patch.mean()),
                              'std': float(patch.std()), 'patch': patch}
                    del out[j]
                    merged = True
                    break
            if merged:
                break
    out.sort(key=lambda d: -(d['box'][2] - d['box'][0]) * (d['box'][3] - d['box'][1]))
    return out[:6]


_OCR = None


def get_ocr():
    global _OCR
    if _OCR is None:
        try:
            from rapidocr_onnxruntime import RapidOCR
            _OCR = RapidOCR()
        except Exception:
            _OCR = False          # OCR unavailable -> screen state falls back to heuristics
    return _OCR or None


def ocr_frame(rgb):
    """OCR the whole 1280x720 frame once; return [{text, box}]."""
    eng = get_ocr()
    if eng is None:
        return []
    try:
        res, _ = eng(rgb)
    except Exception:
        return []
    out = []
    for t in (res or []):
        if not t or not t[1]:
            continue
        pts = t[0]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        out.append({'text': str(t[1]),
                    'box': (float(min(xs)), float(min(ys)), float(max(xs)), float(max(ys)))})
    return out


# v2.6.0 - the lock-screen clock, tolerant of OCR garble on the separator.
# The old pattern was `^\d{1,2}[:.]\d{2}$`, i.e. it demanded a colon or a full stop.
# Danny (2026-09-30, SM-11-06 follow-up): all four SM-11-01 panels were showing the
# SAME Windows lock screen, yet the room reported "2 idle / 2 not idle -> OUT OF SYNC".
# The two "active" panels had simply had their colon eaten by OCR - one read `917`
# and the other `9-17` - so the clock was not recognised, the panel fell through to
# "readable text => content", and the room raised a false Abnormal. On a 220x135 px
# wall TV the colon is a couple of pixels; losing it is routine, not exceptional.
CLOCK_RE = re.compile(r'^\s*(\d{1,2})\s*[:.\-\u2013\u2014 ]\s*(\d{2})\s*$')   # 9:17 9.17 9-17 9 17
CLOCK_BARE_RE = re.compile(r'^\s*(\d{1,2})(\d{2})\s*$')                      # 917 0917


def is_clock(t):
    """True when a reading is a wall-clock time, allowing for a lost separator.

    Accepts `9:17`, `9.17`, `9-17`, `9 17`, `0917` and bare `917`. The hour must land
    in 0-23 and the minute in 00-59, which is what keeps a bare three- or four-digit
    reading from being accepted blindly. `classify_texts()` adds the second guard: a
    panel is only called a lock screen when the clocks *dominate* its readings
    (`clocks and len(texts) <= len(clocks) + 2`), so a slide that happens to carry a
    number does not qualify.
    """
    t = (t or '').strip()
    m = CLOCK_RE.match(t) or CLOCK_BARE_RE.match(t)
    if not m:
        return False
    h, mi = int(m.group(1)), int(m.group(2))
    return 0 <= h <= 23 and 0 <= mi <= 59


def region_structure(patch):
    """Shape cues that separate a live Windows/application image from a blank screen."""
    ed = np.abs(np.diff(patch, axis=0))
    return {'rowstd': float(patch.std(axis=1).mean()),
            'hline': float(((ed > 18).mean(axis=1) > 0.55).mean()),
            'std': float(patch.std()),
            'nonflat': float((np.abs(patch - np.median(patch)) > 12).mean()),
            'darkshare': float((patch < 95).mean()),
            'band': text_band(patch)}


# ---------------------------------------------------------------------------
# AVoIP decoder standby - learned visual fingerprint (Danny, 2026-09-28)
# ---------------------------------------------------------------------------
# Danny sent a reference picture of the AVoIP standby screen and asked the audit to
# "learn the pattern", because OCR alone cannot be trusted on it: on SM-11-02 the
# RIGHT panel reads "AVOIP SYSTEM STATUS: DECODER STANDBY" but the LEFT panel - same
# picture, dimmer and softer - returns *nothing*. The left panel then fell through to
# "content not readable" (unknown) while the right was idle, and the mismatched state
# classes made the room report OUT OF SYNC even though both panels were idle.
#
# The screen's signature is a dense block of headline text across the top of the
# panel over a DARK grey background, with a laptop graphic and a two-panel button
# layout below. Measured across live frames:
#
#   panel                        top-band text   dark share (<95)
#   SM-11-02 left  (true)            0.585           0.806
#   SM-11-02 right (true)            0.475           0.670
#   SM-11-08 wall cladding (FALSE)   0.739           0.055
#   Room 1 content slides (FALSE)    0.000           0.24 - 0.29
#
# `band` alone is NOT enough: the patterned wall cladding in SM-11-08 produces just
# as much top-band edge energy as a real headline, and a standby panel seen at a
# steep angle through glass glares up to lum 160-174 and loses its dark background.
# The dark share is what actually identifies the screen - the banner is white text on
# a near-black panel. Both gates must pass.
STANDBY_BAND_MIN = 0.35      # headline rows in the top band for a standby screen
STANDBY_DARK_MIN = 0.55      # the banner sits on a dark panel, not a bright wall
# (was 0.45; raised 2026-09-28 after a dark slide with a top title band on SM-11-01
#  tv3 reached 0.45-0.55 and was wrongly called standby. True AVoIP standby panels
#  measure 0.71-0.81, so 0.55 keeps them with margin.)
STANDBY_LUM_MIN, STANDBY_LUM_MAX = 60, 175
# v2.5.0 - pattern matching for a panel that glare makes unreadable. A panel with no
# text of its own is called standby when its row layout matches a standby panel that
# WAS confirmed in the same room. Measured 2026-09-28: twin standby panels 0.88,
# a content panel in the same test set 0.28 at most -> 0.45 was chosen then.
# v2.5.7 - raised to 0.75. Danny (2026-09-29) saw SM-11-01 sit on CHECK REGION while
# it was really IN SYNC: the centre-right TV is a bright slide (lum 143, dark 0.127)
# yet scored NCC 0.590 against the stored profile, clearing 0.45 and being re-labelled
# Idle - which then disagreed with the right-wall TV and produced a phantom out-of-sync
# alert. Re-measured across every marked panel in the fleet (12 samples): real standby
# panels score 0.99-1.00, real content 0.28-0.59. 0.75 sits in that gap with margin on
# both sides and separates all 12 correctly, where a dark-share gate would have broken
# SM-11-02's left TV (genuine standby at dark 0.079 through window glare).
# v2.6.1 - 0.75 was too strict, and the whole reason it had been raised was misdiagnosed.
# Re-measured across every marked panel in the fleet on 2026-09-30, ground truth from the
# OCR banner, three separate times of day as the light changed:
#   OCR-confirmed standby  0.558 - 1.000   (the 0.558 is SM-11-01 under blue skylight,
#                                           which lifts B-R to 43-58 and washes the panel)
#   content / slide / lock 0.064 - 0.449   (SM-11-02's slide, the one Danny reported,
#                                           tops out at 0.449)
# 0.50 sits in that gap with roughly 0.05 of margin on each side. It also still rejects
# the 0.590 bright slide that made v2.5.7 raise the gate.
STANDBY_NCC_MIN = 0.50
# v2.6.1 - how many row-profile signatures are kept per room. This was 2, and that was
# the real reason the NCC test kept failing: remember_standby_profiles() appends the new
# signature and then stores cur[-limit:], so every learning run EVICTED the oldest one.
# A single bad learning pass therefore destroyed the good reference permanently, and the
# next run's genuine standby panel scored 0.36 against the wreckage - which looked exactly
# like "sunlight broke the matcher" and sent v2.5.7 off to build a colour test instead.
# It was not sunlight: simulating glare on a confirmed standby panel (additive +120,
# multiplicative x2.0, warm-tinted +80) moves its NCC by less than 0.02, because the row
# profile is high-passed and z-normalised before comparison. The reference was simply bad.
# Keeping a pool of 8 and scoring against the best of them (see standby_profiles()) means
# one bad sample can no longer erase a good one.
STANDBY_PROFILE_POOL = 8
# v2.6.1 - the hue test is a COLD-START fallback only: it runs when a room has no learned
# reference at all. It is deliberately not allowed to rescue a panel the layout test
# rejects. SM-11-02's slide measured B-R 9.1 / saturation 22.2 against 17.4 / 20.9 for a
# real standby panel on SM-11-08 - colour cannot separate them - and that slide still
# scores 0.37-0.45 on layout. Letting colour override layout is precisely what produced
# the false "idle" verdict Danny reported on 2026-09-30.
# v2.5.7 - colour signature of the AVoIP standby screen (see standby_hue()). Sunlight
# lifts a standby panel's brightness from ~83 to ~143-169 without changing its colour,
# so absolute brightness / dark-share tests fail on it. Measured across the fleet the
# standby screen is the only surface that is both faintly blue and nearly desaturated:
# B-R 13.6-18.1 with saturation 17.0-21.7, against 101/102 (Win11 wallpaper), 151/152
# (lock screen) and -1.5/3.3 (white slide). Ratios, so exposure-independent.
# v2.6.1 - the v2.5.7 window was far too generous and let real slides through. Danny
# (2026-09-30) reported SM-11-02 "both are in use but not idle": both panels were slides
# measuring B-R 26.8 / 25.1 with saturation 36.6 / 38.9, comfortably inside 8-40 / <=45.
# Fleet-wide re-measure (2026-09-30, 9 OCR-confirmed standby panels vs 4 content panels):
#   saturation : standby  5.4 - 31.7   |   content 36.6 - 169.8
#   B-R        : standby -0.4 - 24.8   |   content 25.1 - 169.7
# Saturation is the sharper of the two, so it carries the decision; B-R is a backstop for
# a saturated-but-dim slide. BR_MIN stays at 8.0 deliberately - a white slide measures
# B-R -1.5 / saturation 3.3 and must keep failing, even though the dimmest real standby
# panel (SM-11-01 left, B-R -0.4) then falls through to the NCC test instead.
STANDBY_HUE_BR_MIN, STANDBY_HUE_BR_MAX = 8.0, 28.0
STANDBY_HUE_SAT_MAX = 34.0
STANDBY_ZOOM_SCALES = (2, 3)
# v2.5.2 - whole-headline matching for a garbled banner (see standby_banner())
STANDBY_BANNER_REF = ('AVOIPSYSTEMSTATUSDECODERSTANDBY',
                      'AVOIPSYSTEMSTATUSDECODERSTANDBYTHEVIDEOSOURCEDEVICE')
STANDBY_BANNER_MIN_RATIO = 0.65
STANDBY_BANNER_MIN_LEN = 18
# v2.5.1 - Windows lock-screen wallpaper signature (see lock_screen_signature()).
# SM-11-08 measured b-g ~90 / g-r ~45 / lum 74-87 on an idle lock screen.
LOCK_BG_DG = 35         # b - g: the pixel is strongly blue
LOCK_BG_DR = 12         # g - r: and the blue comes from the blue channel, not grey
LOCK_BG_MIN_SHARE = 0.45  # share of the panel that must carry that blue
LOCK_MEAN_DG = 60       # panel-level mean b - g (lock 109-111 vs content <= 22)
LOCK_MEAN_DR = 12       # panel-level mean g - r (lock 23-27 vs content <= 6)
LOCK_LUM_MIN, LOCK_LUM_MAX = 45, 135


def text_band(patch, frac=0.30, thr=9):
    """Share of rows in the panel's top band that carry a text line.

    A standby banner sets its headline across the top of the screen, which produces
    dense horizontal edges there. A slide, a desktop or a lock screen puts its hero
    content in the middle, so its top band is flat.
    """
    h = patch.shape[0]
    top = patch[:max(8, int(h * frac)), :]
    if top.shape[1] < 12:
        return 0.0
    ed = np.abs(np.diff(top, axis=1))
    return float((ed.mean(axis=1) > thr).mean())


def standby_fingerprint(struct, mean_lum, dark_share=None):
    """True when the measured panel matches the AVoIP decoder standby screen.

    Used only as a fallback when OCR returned nothing for the panel, so an unreadable
    but visually identical standby panel is still reported as Idle. A panel that OCR
    *can* read is always classified from its text, and a slide has an empty top band,
    so this cannot flip a genuine content reading.

    Both gates are needed: the headline band AND the dark panel behind it. The dark
    share alone keeps the SM-11-08 wall cladding (bright, textured) out, which the
    band test on its own would wrongly accept.
    """
    if not struct:
        return False
    if not (STANDBY_LUM_MIN <= mean_lum <= STANDBY_LUM_MAX):
        return False
    if struct.get('band', 0.0) < STANDBY_BAND_MIN:
        return False
    return struct.get('darkshare', 0.0) >= STANDBY_DARK_MIN


def standby_hue(rgb_patch):
    """Colour signature of the AVoIP decoder standby screen.

    Danny (2026-09-29, SM-11-01): sunlight falling on two of the four wall TVs lifts
    their measured brightness from ~83 to ~143-169, which made every luminance- and
    darkness-based test classify them as *content* and produced a phantom
    out-of-sync / CHECK REGION on a room that was in fact fully idle. The picture
    underneath never changes: all four panels measure the same low-saturation,
    slightly-blue cast, only the exposure differs.

    Measured across the fleet (mean B-R / mean saturation of the panel):

    | panel                          | B-R   | sat   | truth     |
    |--------------------------------|-------|-------|-----------|
    | SM-11-01 TV1 (dark)            | 16.8  | 20.0  | standby   |
    | SM-11-01 TV2 (dark)            | 18.1  | 21.4  | standby   |
    | SM-11-01 TV3 (sunlit)          | 15.1  | 21.7  | standby   |
    | SM-11-01 TV4 (sunlit)          | 13.6  | 17.0  | standby   |
    | SM-11-04 Win11 blue wallpaper  | 101.2 | 102.3 | content   |
    | SM-11-06 Windows lock screen   | 150.8 | 152.3 | lock      |
    | SM-11-05 white slide           | -1.5  | 3.3   | content   |

    So the standby screen is the ONLY thing in this fleet that is simultaneously
    *faintly blue* and *nearly desaturated*. A saturated screen (real content, a
    lock screen) fails the saturation ceiling; a neutral screen (a white slide, a
    grey wall) fails the blue floor. Crucially this is a RATIO test, so it is
    immune to the exposure change that sunlight causes.

    Returns (mean_b_minus_r, mean_saturation) or None if the patch is unusable.
    """
    p = np.asarray(rgb_patch, dtype=np.float32)
    if p.ndim != 3 or p.shape[2] < 3 or p.shape[0] < 4 or p.shape[1] < 4:
        return None
    b_minus_r = float((p[:, :, 2] - p[:, :, 0]).mean())
    sat = float((p.max(axis=2) - p.min(axis=2)).mean())
    return b_minus_r, sat


def standby_hue_match(rgb_patch, struct=None, mean_lum=None, require_band=True):
    """True when the panel's COLOUR matches AVoIP standby, whatever its brightness.

    Used after the luminance fingerprints fail, which is exactly the sunlit case.
    Still requires the structure gate (a headline band) so a flat wall cannot pass,
    but deliberately does NOT test absolute brightness or dark share.

    `require_band=False` is for a marked room where another panel has ALREADY been
    confirmed as standby this run: the room is known to be showing the standby
    picture, so the colour alone is enough for a twin whose box happens to clip the
    headline (SM-11-01's right-wall TV measures band 0.000 but B-R 13.6 / sat 17.0,
    i.e. unmistakably the same screen).
    """
    hue = standby_hue(rgb_patch)
    if hue is None:
        return False
    b_minus_r, sat = hue
    if not (STANDBY_HUE_BR_MIN <= b_minus_r <= STANDBY_HUE_BR_MAX):
        return False
    if sat > STANDBY_HUE_SAT_MAX:
        return False
    if require_band and struct is not None and struct.get('band', 0.0) < STANDBY_BAND_MIN:
        return False
    return True


def standby_row_profile(patch):
    """Glare-proof 1-D signature of a panel: edge density per row, high-passed.

    Danny (2026-09-28, SM-11-07): the two wall TVs are watched through window glare,
    so their brightness (128 / 146) and dark share (0.23 / 0.18) look nothing like the
    dark standby panels in SM-11-02 (0.81 / 0.71) - every absolute threshold fails on
    them. Subtracting a heavy blur removes the slow glare gradient and leaves the text
    layout, which is what actually makes the standby screen recognisable.

    A row profile is used instead of a 2-D template match because the two panels are
    seen from different angles: perspective squashes columns but leaves row order
    alone. Measured on SM-11-07 the twin panels score 0.88 against each other, while
    content panels in SM-11-01 score 0.28 at most and mostly go negative.
    """
    im = Image.fromarray(patch.astype(np.uint8))
    blur = np.asarray(im.filter(ImageFilter.GaussianBlur(12)), dtype=np.float32)
    d = patch.astype(np.float32) - blur
    d = d - d.min()
    if d.max() > 0:
        d = d / d.max() * 255.0
    ed = np.abs(np.diff(d, axis=1)).mean(axis=1)
    if len(ed) < 4:
        return np.zeros(48, dtype=np.float32)
    n = 48
    p = np.interp(np.linspace(0, len(ed) - 1, n), np.arange(len(ed)), ed)
    p = (p - p.mean()) / (p.std() + 1e-6)
    return p.astype(np.float32)


def profile_ncc(a, b):
    """Normalised cross-correlation of two row profiles (-1..1)."""
    a = np.asarray(a, dtype=np.float32).ravel()
    b = np.asarray(b, dtype=np.float32).ravel()
    if a.size != b.size or a.size == 0:
        return 0.0
    return float((a * b).mean())


def lock_screen_signature(rgb_patch, struct=None):
    """True when the panel carries the Windows lock-screen wallpaper.

    Danny (2026-09-28, SM-11-08): both wall TVs show the Windows lock screen, but the
    clock never reaches us as OCR text - the panels sit at 74-87 mean luminance and the
    digits are small, so `is_clock()` has nothing to latch onto and the room used to
    report "Active - content on screen" for an idle room.

    The fallback is the wallpaper itself. Measured on SM-11-08 the lock screen is a
    saturated deep blue: `b - g` around 90 with the red channel far below green
    (`g - r` around 45), on a panel whose luminance is moderate. Content panels in this
    fleet sit far away from that corner, so the window is deliberately wide but still
    anchored to all three conditions - a blue cast alone must not be enough, or a
    projector slide with a blue theme would qualify.
    """
    try:
        a = np.asarray(rgb_patch, dtype=np.float32)
    except Exception:
        return False
    if a.ndim != 3 or a.shape[2] < 3:
        return False
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    dg, dr = b - g, g - r
    share = float(((dg > LOCK_BG_DG) & (dr > LOCK_BG_DR)).mean())
    lum = float(a.mean())
    # Both a panel-level mean and a per-pixel share are required. Measured 2026-09-28:
    # SM-11-08 lock screens score b-g 109/111 with mean share 0.58/0.52, while every
    # other panel in the fleet - AVoIP standby in SM-11-02/07 and live slides in
    # SM-11-01 - sits at b-g <= 22 and share 0.000. The gap is two orders of magnitude,
    # so the test is nowhere near a borderline.
    return (share >= LOCK_BG_MIN_SHARE
            and float(dg.mean()) >= LOCK_MEAN_DG
            and float(dr.mean()) >= LOCK_MEAN_DR
            and LOCK_LUM_MIN <= lum <= LOCK_LUM_MAX)


def standby_banner(texts, ref_ratio=STANDBY_BANNER_MIN_RATIO):
    """True when a reading is the AVoIP standby banner, allowing for OCR garble.

    Danny (2026-09-28, SM-11-07): on a glared panel the banner reads back as
    `AVOIPSVSTEASTATUE...`, `AMOIPSYSTEASTATUE...` or even `AMCIP SYSTEASTATUE...` - the
    brand word flips between AVOIP / AMOIP / AMCIP from frame to frame on a picture that
    has not changed at all (two frames 1.1 grey levels apart read "AVOIP..." and
    "AMCIP..."). Keying on the exact word `AVOIP` is therefore a coin toss.

    Match the *whole* headline instead, letter-normalised, against the known banner
    wording. Measured 2026-09-28 on this fleet:

    | panel | best ratio | truth |
    |---|---|---|
    | SM-11-02 left / right | 1.000 | standby |
    | SM-11-07 left / right | 0.806 / 0.793 | standby |
    | SM-11-01 tv1…tv4, SM-11-08 | 0.000 | not standby |

    `STANDBY_BANNER_MIN_LEN` keeps short junk from scoring against the long reference.
    """
    import difflib
    best, best_txt = 0.0, ''
    for t in (texts or []):
        n = re.sub(r'[^A-Z]', '', str(t).upper())
        if len(n) < STANDBY_BANNER_MIN_LEN:
            continue
        for ref in STANDBY_BANNER_REF:
            r = difflib.SequenceMatcher(None, n, ref).ratio()
            if r > best:
                best, best_txt = r, n
    return (best >= ref_ratio), best, best_txt


def panel_zoom_ocr(rgbs, box, scales=STANDBY_ZOOM_SCALES):
    """Re-read one marked panel at higher resolution, looking only for the AVoIP banner.

    Danny (2026-09-28, SM-11-07): a wall TV only fills about 220x135 px of a
    1280x720 frame, so its standby banner is far too small for the whole-frame OCR
    pass - that pass returned *zero* readings for the entire room. Upscaling just the
    panel 2-3x and stretching its contrast makes the banner legible
    ("AVOIP SYSTEM STATUS ... DECODER STANDBY", garbled but with the keywords intact).

    The standby picture is static, so every grabbed frame is tried and one hit is
    enough. Only readings carrying an AVoIP keyword are returned: this pass is a
    standby detector and must never be used to call a panel "content".
    """
    hits, seen = [], set()
    for arr in (rgbs or [])[:3]:
        x0, y0, x1, y1 = (int(v) for v in box)
        x0, y0 = max(0, x0), max(0, y0)
        x1, y1 = min(arr.shape[1], x1), min(arr.shape[0], y1)
        if x1 - x0 < 20 or y1 - y0 < 15:
            continue
        try:
            crop = Image.fromarray(arr[y0:y1, x0:x1]).convert('L')
        except Exception:
            continue
        for sc in scales:
            try:
                c = ImageOps.autocontrast(crop, cutoff=2)
                c = c.resize((c.width * sc, c.height * sc), Image.LANCZOS)
                for it in ocr_frame(np.asarray(c.convert('RGB'))):
                    txt = it['text']
                    ok = any(k in txt.upper() for k in DISPLAY_TEXT_KEYS)
                    if not ok:                      # v2.5.2: garbled headline match
                        ok = standby_banner([txt])[0]
                    if ok and txt not in seen:
                        seen.add(txt)
                        hits.append(txt)
            except Exception:
                pass
        if hits:
            break
    return hits


# Danny (2026-09-21): Idle means ONLY (a) Windows lock screen, (b) AVoIP decoder
# standby banner, (c) an all-blank screen. A Windows desktop or an application that
# sits static for a long time is still "content on screen" -> In use, not Idle.
# A blank screen is featureless: almost no pixel deviates from the median and the
# row-to-row variation is tiny.
BLANK_NONFLAT_MAX = 0.10
BLANK_ROWSTD_MAX = 12.0


def classify_texts(texts, static_ratio, mean_lum, struct=None):
    """Map the readable text belonging to one display onto an idle / active state.

    Idle is deliberately narrow: Windows lock screen, AVoIP decoder standby, or an
    all-blank screen. Everything else that is lit counts as content on screen.
    """
    if mean_lum < 55:
        return 'Off / dark'
    joined = ' '.join(texts).upper()
    if any(k in joined for k in AVOIP_IDLE_KEYS):
        return 'Idle &ndash; AVoIP decoder standby'
    # v2.5.2: the banner arrived garbled - "AMCIP SYSTEASTATUE: DECODEISTAESY" carries no
    # intact keyword, yet it *is* the standby headline (whole-string match 0.79-0.81).
    # Check that before the generic "readable text => content" rule below, otherwise a
    # glared standby panel is called content and disagrees with its twin.
    if standby_banner(texts)[0]:
        return 'Idle &ndash; AVoIP decoder standby'
    if texts:
        clocks = [t for t in texts if is_clock(t)]
        if clocks and len(texts) <= len(clocks) + 2:
            return 'Idle &ndash; Windows lock screen'
        return 'Active &ndash; content on screen'
    struct = struct or {}
    # OCR returned nothing for this panel. Danny (2026-09-28): both SM-11-02 panels
    # show the same AVoIP standby picture, but only the right one is readable - the
    # left is dimmer and softer. Match it against the learned standby fingerprint so
    # a visually identical standby panel is not called "unreadable" (= unknown), which
    # used to make the twin panels disagree and report a false OUT OF SYNC.
    if standby_fingerprint(struct, mean_lum, struct.get('darkshare')):
        return 'Idle &ndash; AVoIP decoder standby'
    if not struct:                      # no structural evidence at all -> do not guess
        return 'On &ndash; content not readable'
    if (struct.get('nonflat', 1) < BLANK_NONFLAT_MAX
            and struct.get('rowstd', 99) < BLANK_ROWSTD_MAX):
        return 'Idle &ndash; blank screen (no content)'
    return 'Active &ndash; content on screen'


def display_pill(state):
    """Compact Idle / In-use verdict used in the summary tables."""
    if state.startswith('Idle'):
        return 'p-idle', 'IDLE', state.split('&ndash;')[1].strip() if '&ndash;' in state else ''
    if state.startswith('Active'):
        return 'p-act', 'IN USE', 'content on screen'
    if state.startswith('Off'):
        return 'p-off', 'OFF', 'display dark'
    if state.startswith('On '):
        return 'p-idle', 'UNCONFIRMED', 'content not readable'
    return 'p-idle', 'UNKNOWN', ''


def aggregate_screen_state(scr):
    """Room level verdict built from the per-display readings (ignored boards excluded)."""
    scr = [s for s in (scr or []) if s.get('monitored', True)]
    if not scr:
        return 'Unknown &ndash; no display detected in frame'
    def bucket(s):
        if s.startswith('Idle'):
            return 'idle'
        if s.startswith('Active'):
            return 'active'
        if s.startswith('Off'):
            return 'off'
        return 'unconfirmed'

    st = [s['state'] for s in scr]
    n_idle = sum(1 for s in st if bucket(s) == 'idle')
    n_act = sum(1 for s in st if bucket(s) == 'active')
    n_off = sum(1 for s in st if bucket(s) == 'off')
    n_unc = sum(1 for s in st if bucket(s) == 'unconfirmed')
    # idle readings proved by a standby / lock banner that no bright region could hold
    n_banner = sum(1 for s in scr if bucket(s['state']) == 'idle' and s.get('box') is None)
    if n_idle:
        reasons = sorted({s.split('&ndash;')[1].strip() for s in st if bucket(s) == 'idle'})
        base = 'Idle &ndash; ' + '; '.join(reasons)
        if n_banner and (n_act or n_off):
            # the banner is the strongest evidence in the room (all displays share one
            # source); the remaining bright regions could not be matched to a screen
            return (base + f' (standby banner read in frame; {n_act + n_off} detected region(s) '
                    'not attributable &mdash; possibly whiteboard / window)')
        if n_act or n_off:
            return base + f' ({n_idle} idle / {n_act + n_off} not idle)'
        if n_unc:
            return base + f' ({n_unc} display(s) unconfirmed)'
        return base
    if n_act:
        return 'Active &ndash; content on screen'
    if n_off:
        return 'Off / dark'
    if n_unc:
        return 'On &ndash; state unconfirmed'
    return 'Unknown'


def measure_panel(frames, items, box, used=None, rgb=None):
    """Measure one display panel at a known box and classify what it shows.

    Split out of `screen_states()` so the same measurement is used whether the box
    came from the bright-blob detector or from a fixed `display_regions` entry
    (Danny's red rectangles). `used` is the shared set of OCR readings already
    attributed to a panel, so a reading is never counted twice.
    """
    x0, y0, x1, y1 = (int(v) for v in box)
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(frames[0].shape[1], x1), min(frames[0].shape[0], y1)
    if x1 - x0 < 20 or y1 - y0 < 15:
        return None
    sub = np.stack([f[y0:y1, x0:x1] for f in frames])
    moved = (sub.max(axis=0) - sub.min(axis=0)) > 22
    static_ratio = float(1 - moved.mean())
    mine = []
    for i, it in enumerate(items):
        itb = it['box']
        # A reading counts when it lies *wholly* inside the panel - a text box that
        # overhangs the edge is hallucinated OCR, not content. Danny 2026-09-28:
        # the classifier only keys on the wording at the top of the standby banner
        # ("AVOIP SYSTEM ..."), so when something crosses the panel edge the words
        # below it are still allowed through - that is how a half-cut banner is
        # still recognised, while junk text sitting on the furniture is not.
        if itb[0] >= x0 and itb[1] >= y0 and itb[2] <= x1 and itb[3] <= y1:
            mine.append(it['text'])
            if used is not None:
                used.add(i)
        elif itb[2] > x0 and itb[0] < x1 and itb[3] > y0 and itb[1] < y1:
            if 'AVOIP' in it['text'].upper() or 'STANDBY' in it['text'].upper():
                mine.append(it['text'])
                if used is not None:
                    used.add(i)
    struct = region_structure(sub[0])
    lum = float(sub[0].mean())
    state = classify_texts(mine, static_ratio, lum, struct)
    # v2.5.1: a lock screen whose clock OCR never read. Only a panel that would
    # otherwise be called live content is eligible - never a blank / dark / standby one.
    # This runs even when the panel did yield text: on SM-11-08 the whole-frame pass
    # reads the clock ("4:38") off the left wall TV but not off the right one, and if
    # only the unread panel were tested the twin panels would disagree and the room
    # would be called OUT OF SYNC for showing two identical lock screens.
    if (not state.startswith('Idle') and not state.startswith('Off')
            and rgb is not None and lock_screen_signature(rgb[y0:y1, x0:x1], struct)):
        state = 'Idle &ndash; Windows lock screen'
        if not mine:
            mine = ['lock-screen wallpaper (clock below OCR range)']
    return {'box': [x0, y0, x1, y1], 'mean': lum, 'static': static_ratio,
            'struct': struct, 'state': state, 'text': ' | '.join(mine[:6])}


def standby_profiles(cfg, label, limit=STANDBY_PROFILE_POOL):
    """Remembered standby row-profile signatures for one room (see v2.5.2).

    A glared panel is unreadable on many runs, so the pattern learned on a run where the
    banner *was* legible is kept and reused later. Measured 2026-09-28 on SM-11-07: the
    same panel scores NCC 0.91-0.999 against itself across runs 20 minutes apart, even
    though its mean luminance moved from 128 to 149 as the glare grew - which is why the
    high-passed row profile is stored rather than anything brightness-based.
    """
    out = []
    for p in ((cfg.get('standby_profiles') or {}).get(label) or [])[:limit]:
        a = np.asarray(p, dtype=np.float32).ravel()
        if a.size == 48:
            out.append(a)
    return out


def remember_standby_profiles(label, profiles, limit=STANDBY_PROFILE_POOL):
    """Persist newly confirmed standby signatures into av_monitor_config.json."""
    if not profiles:
        return False
    try:
        with open(CONFIG, encoding='utf-8') as f:
            cfg = json.load(f)
    except Exception:
        return False
    store = cfg.setdefault('standby_profiles', {})
    cur = [np.asarray(p, dtype=np.float32).ravel() for p in (store.get(label) or [])
           if np.asarray(p).size == 48]
    for pr in profiles:
        a = np.asarray(pr, dtype=np.float32).ravel()
        if a.size != 48:
            continue
        if cur and max(profile_ncc(a, c) for c in cur) >= 0.97:
            continue                      # already remembered
        cur.append(a)
    if not cur:
        return False
    store[label] = [[round(float(v), 4) for v in c] for c in cur[-limit:]]
    try:
        with open(CONFIG, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def screen_states(frames, rgb, keep=None, filt=None, regions=None, rgbs=None,
                  standby_refs=None):
    """Locate screen-shaped bright regions, attribute OCR text to each, classify.

    `keep` = number of displays actually installed in the room. Only the `keep`
    largest bright regions are monitored; every smaller bright region is treated as
    a traditional whiteboard / noticeboard and is ignored (Danny: those boards are
    not to be monitored).

    `filt` = optional wall-display filter (see `display_filter()`), e.g.
    `{'max_center_y_frac': 0.35}`. Danny (2026-09-23): in SM-11-02 / 07 / 08 only
    the two large LED TVs on the wall count for the idle and sync verdicts — the
    small computer monitors sitting on the desks are ignored. Desk-level regions are
    dropped from the candidate list and reported with a reason.

    `regions` = fixed display boxes from `display_regions()`. Danny (2026-09-28):
    when he has marked the displays he wants watched, those boxes are authoritative
    and the bright-blob detector is skipped for that room entirely. This is the only
    way to watch a panel that is *darker* than the wall around it (a Windows lock
    screen on SM-11-02), which no bright-blob rule can ever find.
    """
    items = ocr_frame(rgb)
    used = set()
    out = []
    frame_h, frame_w = frames[0].shape[:2]

    if regions:
        # ---- fixed-region path: measure Danny's boxes directly ----------------
        marked = []
        for r in regions:
            m = measure_panel(frames, items, r['box'], used, rgb=rgbs[0] if rgbs else rgb)
            if m is None:
                continue
            m['fixed_region'] = True
            m['region_label'] = r.get('label') or ''
            m['monitored'] = True
            # v2.5.0: the whole-frame OCR pass cannot read a banner that is only
            # ~135 px tall, so re-read the panel itself before calling it unreadable.
            if not m['text']:
                zoom = panel_zoom_ocr(rgbs or [rgb], r['box'])
                if zoom:
                    m['text'] = ' | '.join(zoom[:4])
                    m['state'] = classify_texts(zoom, m['static'], m['mean'], m['struct'])
                    m['zoom_ocr'] = True
            marked.append(m)
            out.append(m)
        # v2.5.0: propagate a confirmed standby picture to a twin panel that glare
        # makes unreadable. Only a panel with NO text of its own is eligible, and the
        # reference must be a marked panel in the same room whose banner was actually
        # read - so this can never override a real content reading.
        refs = []
        for m in marked:
            if 'AVoIP' in (m.get('state') or ''):
                b = m['box']
                refs.append(standby_row_profile(frames[0][b[1]:b[3], b[0]:b[2]]))
        # v2.5.2: a run where the banner could not be read at all still has the pattern
        # learned on an earlier run to fall back on.
        for p in (standby_refs or []):
            a = np.asarray(p, dtype=np.float32).ravel()
            if a.size == 48:
                refs.append(a)
        for m in marked:
            if m.get('text') or 'AVoIP' in (m.get('state') or ''):
                continue
            b = m['box']
            patch = frames[0][b[1]:b[3], b[0]:b[2]]
            rgb_patch = None
            if rgbs:
                rgb_patch = np.asarray(rgbs[0], dtype=np.uint8)[b[1]:b[3], b[0]:b[2]]
            room_confirmed = any('AVoIP' in (x.get('state') or '') for x in marked)
            hue_ok = (rgb_patch is not None and standby_hue_match(
                rgb_patch, m.get('struct'), require_band=not room_confirmed))
            # v2.6.1: layout first, colour second - the order v2.5.7 had back to front.
            # Danny (2026-09-30): SM-11-02 reported idle while both TVs were in use. The
            # hue gate alone had accepted them: the slide measured B-R 9.1 / saturation
            # 22.2, which is indistinguishable from a real standby panel on SM-11-08
            # (B-R 17.4 / 20.9) - colour simply cannot separate the two. Row layout can,
            # and it does not care about the light: simulating glare on a confirmed
            # standby panel (additive +120, multiplicative x2.0, warm-tinted +80) moves
            # its NCC by less than 0.02, because the profile is high-passed and
            # z-normalised before it is compared.
            # The NCC test only looks weak because the stored reference kept being
            # destroyed - see STANDBY_PROFILE_POOL.
            best = None
            if refs:
                prof = standby_row_profile(patch)
                best = max(profile_ncc(prof, r) for r in refs)
            if best is not None and best >= STANDBY_NCC_MIN:
                m['state'] = 'Idle &ndash; AVoIP decoder standby'
                m['text'] = ('matches the learned AVoIP standby pattern '
                             '(row-layout match %.2f)' % best)
                m['matched'] = round(best, 3)
                continue
            # Cold start only: a room with no learned reference at all has nothing to
            # compare the layout against, so colour is all that is left.
            if hue_ok and best is None:
                br, sat = standby_hue(rgb_patch)
                m['state'] = 'Idle &ndash; AVoIP decoder standby'
                m['text'] = ('matches the AVoIP standby colour signature '
                             '(B-R %.1f, saturation %.1f)' % (br, sat))
                m['hue_match'] = round(br, 1)
        # Anything the blob detector WOULD also have found is reported for information
        # only, so the room card still shows what else is bright in the frame.
        for s in screens(frames[0]):
            box = refine_box_frames(frames, s['box'], **REFINE_TUNE)
            if any(iou(box, r['box']) > 0.5 for r in regions):
                continue
            m = measure_panel(frames, items, box, used, rgb=rgbs[0] if rgbs else rgb)
            if m is None:
                continue
            m['blob'] = [int(v) for v in s['box']]
            m['monitored'] = False
            m['skip_reason'] = ('bright region outside the marked display areas '
                                '&mdash; not counted towards the Idle / picture-sync '
                                'verdict')
            out.append(m)
        stray = [items[i]['text'] for i in range(len(items)) if i not in used]
        if stray:
            st = classify_texts(stray, 1.0, float(rgb.mean()))
            if st.startswith('Idle') and 'blank' not in st:
                out.append({'box': None, 'mean': float(rgb.mean()), 'std': 0.0, 'static': 1.0,
                            'state': st, 'text': ' | '.join(stray[:6])})
        # in a marked room a stray reading is only kept when it is a standby banner
        standby_ids = {id(s) for s in out if s.get('box') is None and 'AVoIP' in s['state']}
        for s in out:
            if s.get('box') is None:
                s['monitored'] = id(s) in standby_ids
                if not s['monitored']:
                    s['skip_reason'] = ('text read in frame but not attributable to a marked '
                                        'display (desk monitor / wall clock) &mdash; ignored')
        return out

    regs = screens(frames[0])
    for s in regs:
        # Tighten the blob to the real lit panel before using it for anything: OCR
        # attribution (below), the desk-level test, and what the report draws.
        box = refine_box_frames(frames, s['box'], **REFINE_TUNE)
        m = measure_panel(frames, items, box, used, rgb=rgbs[0] if rgbs else rgb)
        if m is None:
            continue
        m['blob'] = [int(v) for v in s['box']]
        m['std'] = s['std']
        out.append(m)
    # text that belongs to a display the blob detector missed. Only OCR-proven idle
    # banners count here (a stray clock could be a wall clock, and a textless stray
    # would otherwise be labelled "blank" without any structural evidence).
    stray = [items[i]['text'] for i in range(len(items)) if i not in used]
    if stray:
        st = classify_texts(stray, 1.0, float(rgb.mean()))
        if st.startswith('Idle') and 'blank' not in st:
            out.append({'box': None, 'mean': float(rgb.mean()), 'std': 0.0, 'static': 1.0,
                        'state': st, 'text': ' | '.join(stray[:6])})
    # keep only the installed displays; smaller bright regions are whiteboards.
    # A phantom (OCR-only) display is a real screen the blob detector missed, so it
    # takes a slot from the declared inventory first - otherwise a 4-TV room could end
    # up with 4 detected regions + 1 phantom = 5 "monitored" displays.
    # EXCEPT in a wall-only room: there Danny wants *only* the two wall TVs to count,
    # and a stray OCR reading has no position we can prove is on the wall.
    wall_only = bool(filt)
    phantom = [s for s in out if s.get('box') is None]
    # Danny (2026-09-23): an AVoIP standby banner read anywhere in the frame proves one
    # of the room's displays is dark / on standby, so it counts as Idle in EVERY room -
    # including the wall-only rooms (SM-11-02 / 07 / 08), where every other stray
    # reading is dropped because it cannot be tied to a wall display.
    standby_ids = {id(s) for s in phantom if 'AVoIP' in s['state']}
    for s in phantom:
        if (not wall_only) or (id(s) in standby_ids):
            s['monitored'] = True
        else:
            s['monitored'] = False
            s['skip_reason'] = ('text read in frame but not attributable to a wall '
                                'display (desk monitor / wall clock) &mdash; ignored')
    boxed = sorted((s for s in out if s.get('box') is not None),
                   key=lambda s: -((s['box'][2] - s['box'][0]) * (s['box'][3] - s['box'][1])))

    # ---- wall-display filter: drop desk-level regions -------------------
    if wall_only:
        max_cy = filt.get('max_center_y_frac')
        min_area = filt.get('min_area_px') or 0
        for s in boxed:
            x0, y0, x1, y1 = s['box']
            cy = ((y0 + y1) / 2) / frame_h
            area = (x1 - x0) * (y1 - y0)
            if max_cy is not None and cy > max_cy:
                s['skip_reason'] = (f'desk level &mdash; centre at {cy:.0%} of frame height, '
                                    f'below the {max_cy:.0%} wall line (desk computer monitor '
                                    'or tabletop), not one of the wall displays')
            elif min_area and area < min_area:
                s['skip_reason'] = (f'too small for a wall display ({area:,} px &lt; '
                                    f'{min_area:,} px)')

    eligible = [s for s in boxed if not s.get('skip_reason')]
    standby_ph = [s for s in phantom if s.get('monitored')]
    if wall_only and standby_ph:
        # Only spend a declared slot on the banner when the detector really missed a
        # screen (a standby display goes dark, so it never forms a bright blob). If
        # every declared wall display is already accounted for by a real region, the
        # banner is shown as a note instead - the monitored count never exceeds the
        # declared inventory.
        free = max(0, (keep or 0) - len(eligible))
        for i, s in enumerate(standby_ph):
            if i >= free:
                s['monitored'] = False
                s['skip_reason'] = ('AVoIP standby text read, but every declared wall '
                                    'display is already accounted for by a detected '
                                    'region &mdash; shown for information only')
    n_phantom_slot = sum(1 for s in phantom if s.get('monitored'))
    limit = (keep - n_phantom_slot) if keep else len(boxed)
    limit = max(0, limit)
    for rank, s in enumerate(eligible):
        # Danny: an AVoIP decoder standby screen IS one of the room's TVs, even if
        # the blob is not among the N largest bright regions -> always monitored.
        evidence = any(k in (s.get('text') or '').upper() for k in DISPLAY_TEXT_KEYS)
        s['monitored'] = bool(rank < limit or evidence)
        if evidence and rank >= limit:
            s['promoted'] = True
    for s in boxed:
        if s.get('skip_reason'):
            s['monitored'] = False
    # NOTE: no "one idle display makes the siblings idle" propagation any more.
    # Danny (2026-09-21): a Windows desktop / application that sits static for a long
    # time is content on screen, so inheriting an idle verdict from a neighbour would
    # be wrong. Every display is judged on its own OCR + structure evidence.
    return out


def sync_class(state):
    """Collapse a per-display reading into a class that can be compared across displays."""
    if state.startswith('Active'):
        return 'active'
    if state.startswith('Idle'):
        return 'idle'
    if state.startswith('Off'):
        return 'off'
    return 'unknown'


def sync_confidence(s):
    """How much one display reading can be trusted for a *sync* verdict.

    Danny (2026-09-21): only flag OUT OF SYNC when the displays are *highly* unmatched.
    A verdict therefore needs OCR / luminance evidence on both sides. Readings that come
    from structure heuristics alone (blank-vs-desktop guess, unreadable text) are "low"
    and can never create an out-of-sync verdict on their own.
    """
    st = s['state']
    if st.startswith('Off'):
        return 'high'                       # measured luminance - solid evidence
    if st.startswith('Idle'):
        return 'high' if ('AVoIP' in st or 'lock' in st) else 'medium'
    if st.startswith('Active'):
        return 'high' if (s.get('text') or '').strip() else 'medium'
    return 'low'          # 'On - content not readable': no evidence either way


def idle_subtype(state):
    if 'AVoIP' in state:
        return 'AVoIP decoder standby'
    if 'lock' in state:
        return 'Windows lock screen'
    if 'blank' in state:
        return 'blank screen (no content)'
    return state.replace('Idle &ndash; ', '')


def coarse_grid(patch, g=8):
    """Perspective-tolerant 8x8 luminance fingerprint of a display region."""
    h, w = patch.shape
    bh, bw = h // g, w // g
    if bh < 1 or bw < 1:
        return None
    b = patch[:g * bh, :g * bw].reshape(g, bh, g, bw).mean(axis=(1, 3))
    return (b - b.mean()) / (b.std() + 1e-6)


def sync_check(frames, scr, n_dec):
    """Judge whether the displays inside one room are showing the same picture.

    Dual / quad rooms are fed from a single AVoIP source, so every display must
    show the same image. Pixel-level correlation between displays is unreliable
    here (very different viewing angles and sizes), so the verdict is taken from
    the per-display *state class*.

    Danny (2026-09-21): only call OUT OF SYNC when the room is *highly* unmatched.
    Three gates must all pass, otherwise the room is downgraded to CHECK REGION /
    NOT VERIFIED (never Abnormal):
      1. evidence - the disagreeing readings must be OCR / luminance proven, not
         structure-only guesses (`sync_confidence()`)
      2. hard mismatch - one side standby / lock / off vs the other side real content
      3. dominance - the disagreeing area is >= SYNC_MIN_AREA_RATIO (30%) of the
         largest display, and with 3+ evidenced displays at least two must disagree
    """
    regions = [(i, s) for i, s in enumerate(scr)
               if s.get('box') and s.get('monitored', True)]
    res = {'applicable': n_dec >= SYNC_MIN_DECODERS, 'verdict': 'n/a', 'n': len(regions),
           'n_displays': n_dec, 'n_decoders': n_dec, 'pairs': [], 'detail': [],
           'pill': 'p-idle', 'label': 'N/A'}
    if not res['applicable']:
        res['detail'].append(f'Single-display room ({n_dec} monitored display) &ndash; '
                             'sync check not applicable.')
        return res

    grids = []
    for i, s in regions:
        x0, y0, x1, y1 = s['box']
        grids.append(coarse_grid(frames[0][y0:y1, x0:x1]))
    for a in range(len(regions)):
        for b in range(a + 1, len(regions)):
            corr = None
            if grids[a] is not None and grids[b] is not None:
                try:
                    v = float(np.corrcoef(grids[a].ravel(), grids[b].ravel())[0, 1])
                    corr = round(v, 2) if np.isfinite(v) else None
                except Exception:
                    corr = None
            res['pairs'].append({'a': regions[a][0] + 1, 'b': regions[b][0] + 1,
                                 'corr': corr})

    if len(regions) < 2:
        res['verdict'] = 'unverified'
        res['label'] = 'NOT VERIFIED'
        res['detail'].append(f'Only {len(regions)} display region could be isolated in the '
                             f'frame ({n_dec} displays declared) &ndash; compare by eye against '
                             'the snapshot below.')
        return res

    by_idx = dict(regions)
    cls = {i: sync_class(s['state']) for i, s in regions}
    firm = {i: c for i, c in cls.items() if c != 'unknown'}

    def area(i):
        x0, y0, x1, y1 = by_idx[i]['box']
        return float((x1 - x0) * (y1 - y0))

    # --- Danny: OUT OF SYNC only on a *high-confidence*, *dominant* mismatch -------
    conf = {i: sync_confidence(by_idx[i]) for i in firm}
    weak = [i for i in firm if conf[i] == 'low']
    if weak:
        res['detail'].append(
            'Unreadable display(s) '
            + ', '.join('#%d' % (i + 1) for i in weak)
            + ' carry no usable evidence and are excluded from the sync verdict.')
    evidential = {i: c for i, c in firm.items() if conf[i] != 'low'}
    if len(evidential) < 2:
        res['verdict'] = 'unverified'
        res['label'] = 'NOT VERIFIED'
        res['detail'].append('Fewer than two displays could be read from this frame, so an '
                             'out-of-sync verdict would be a guess. Compare by eye against '
                             'the snapshot below.')
        return res
    firm = evidential
    strong = [i for i in firm if conf[i] == 'high']

    groups = {}
    for i, c in firm.items():
        groups.setdefault(c, []).append(i)
    if len(groups) > 1:
        maj = max(groups, key=lambda k: len(groups[k]))
        for c, idxs in sorted(groups.items(), key=lambda kv: -len(kv[1])):
            role = 'majority' if c == maj else 'minority'
            shown = sorted({by_idx[i]['state'] for i in idxs})[0]
            res['detail'].append(
                f"{role}: {' + '.join('#%d' % (i + 1) for i in idxs)} &rarr; "
                f"<b>{c}</b> ({shown})")

        biggest = max(area(i) for i in firm)
        odd = [i for c, idxs in groups.items() if c != maj for i in idxs]
        odd_area = sum(area(i) for i in odd)
        area_ratio = odd_area / biggest if biggest else 0.0
        # share of the room's picture area that disagrees -> how "unmatched" the room is
        severity = len(odd) / max(1, len(firm))
        res['area_ratio'] = round(area_ratio, 2)
        res['severity'] = round(severity, 2)

        # Hard mismatch only: one side is showing nothing (standby / lock / off) while
        # the other side is showing real content. Two different *content* readings are
        # not enough - the OCR is too angle-dependent for that.
        sides = set(groups)
        hard = ({'idle', 'off'} & sides) and ('active' in sides)
        if not hard:
            res['verdict'] = 'check'
            res['label'] = 'CHECK REGION'
            res['detail'].append('The readings differ, but not in a stand-by-vs-content way, so '
                                 'this is <b>not</b> treated as an out-of-sync condition. Flagged '
                                 'for a visual check only.')
            return res
        if not strong:
            # both sides are structure-only guesses (e.g. blank vs desktop) - too weak
            res['verdict'] = 'check'
            res['label'] = 'CHECK REGION'
            res['detail'].append('Both sides are structural readings without OCR / luminance '
                                 'evidence, so this is <b>not</b> called out-of-sync. Flagged '
                                 'for a visual check only.')
            return res
        if area_ratio < SYNC_MIN_AREA_RATIO:
            # disagreeing patch is small next to the main displays - likely a reflection
            res['verdict'] = 'check'
            res['label'] = 'CHECK REGION'
            res['detail'].append(
                f'The disagreeing region covers only {area_ratio * 100:.0f}% of the largest '
                f'display (needs {SYNC_MIN_AREA_RATIO * 100:.0f}%), so it may be a reflection. '
                'Flagged for a visual check, <b>not</b> counted as abnormal.')
            return res
        if len(firm) >= 3 and len(odd) == 1 and conf[odd[0]] != 'high':
            # a lone dissenter out of three or more, backed only by a structural guess
            res['verdict'] = 'check'
            res['label'] = 'CHECK REGION'
            res['detail'].append('Only one of '
                                 f'{len(firm)} evidenced displays disagrees and its reading has no '
                                 'OCR / luminance evidence, so this is <b>not</b> called '
                                 'out-of-sync. Flagged for a visual check.')
            return res
        res['verdict'] = 'out-of-sync'
        res['pill'] = 'p-off'
        res['label'] = 'OUT OF SYNC'
        res['detail'].append(
            'All displays in this room share one source, so they should show the same picture. '
            f'Here {len(odd)} of {len(firm)} evidenced displays disagree'
            + (f' ({area_ratio * 100:.0f}% of the main display area)' if odd else '')
            + ' with a standby-vs-content mismatch &mdash; a <b>highly unmatched</b> condition. '
            'Confirm against the snapshot.')
        return res

    only = next(iter(groups))
    if only == 'idle':
        subs = sorted({idle_subtype(by_idx[i]['state']) for i in firm})
        if len(subs) > 1:
            res['verdict'] = 'check'
            res['label'] = 'MIXED STANDBY'
            res['detail'].append('Every display is idle, but with different standby banners: '
                                 + '; '.join(subs) + '. Verify by eye &ndash; flagged as a note, '
                                 'not as an Abnormal condition.')
            return res
    res['verdict'] = 'in-sync'
    res['pill'] = 'p-on'
    res['label'] = 'IN SYNC'
    res['detail'].append(f'All {len(firm)} evidenced displays report the same state '
                         f'class (<b>{only}</b>).')
    return res


def motion(frames):
    st = np.stack(frames)
    m = (st.max(axis=0) - st.min(axis=0)) > 22
    m = ndimage.binary_opening(m, np.ones((3, 3)))
    lab, n = ndimage.label(m)
    blobs = []
    for i in range(1, n + 1):
        ys, xs = np.where(lab == i)
        if len(ys) < 400:
            continue
        blobs.append((len(ys), ys.max() - ys.min(), xs.max() - xs.min(),
                      float(xs.mean()), float(ys.mean())))
    return blobs, float(m.mean() * 100)


def placeholder(text):
    im = Image.new('RGB', (640, 360), (238, 240, 245))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 639, 359], outline=(190, 195, 205), width=3)
    d.text((40, 165), text, fill=(90, 95, 105))
    return im


def embed(im, width=560, q=72):
    w, h = im.size
    im = im.resize((width, int(h * width / w)))
    import io
    buf = io.BytesIO()
    im.save(buf, 'JPEG', quality=q, optimize=True)
    return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()


def analyse(snap, cfg=None):
    cfg = cfg or {}
    rows = []
    for ip, skey, label in ROOMS:
        files = [os.path.join(TMP, d, f'{ip}.jpg') for d in PASS_DIRS]
        alive = all(os.path.exists(f) and os.path.getsize(f) > 5000 for f in files)
        rec = {'ip': ip, 'key': skey, 'label': label, 'online': alive}

        devs = (snap or {}).get('rooms', {}).get(skey, [])
        dec = sorted([d for d in devs if d.get('role') == 'display'
                      and not d['name'].startswith('TV-Res')], key=lambda x: x['name'])
        res = sorted([d for d in devs if d.get('role') == 'display'
                      and d['name'].startswith('TV-Res')], key=lambda x: x['name'])
        avoip = sorted([d for d in devs if d.get('role') == 'avoip'], key=lambda x: x['name'])
        rec['decoders'], rec['reserve'], rec['avoip'] = dec, res, avoip
        # declared inventory wins over the monitoring count (Danny's confirmed list)
        n_disp, disp_type = display_spec(cfg, label, len(dec))
        rec['display_count'], rec['display_type'] = n_disp, disp_type

        if alive:
            im0 = Image.open(files[0]).convert('RGB')
            rgb = np.asarray(im0)
            frames = [gray(f) for f in files]
            rgbs = [np.asarray(Image.open(f).convert('RGB')) for f in files[:3]]
            a = frames[0]
            blobs, mfrac = motion(frames)
            persons = [b for b in blobs if 60 <= b[1] <= 400 and 25 <= b[2] <= 260
                       and b[4] > a.shape[0] * 0.35]
            scr = screen_states(frames, rgb, keep=n_disp,
                                filt=display_filter(cfg, label),
                                regions=display_regions(cfg, label),
                                rgbs=rgbs,
                                standby_refs=standby_profiles(cfg, label))
            sync = sync_check(frames, scr, n_disp)
            # v2.5.2: remember a standby pattern that was proven this run, so a later
            # run that cannot read the banner at all can still recognise it.
            # v2.5.7: only learn from a panel whose OWN evidence is physical - OCR read
            # the banner, or it matches the standby fingerprint (dark panel + top band).
            # Never learn from a panel that was only accepted by the NCC fallback, or a
            # bad profile could be re-learned and get progressively worse.
            try:
                learned = []
                for _s in scr:
                    if not (_s.get('monitored', True) and 'AVoIP' in (_s.get('state') or '')
                            and _s.get('box') and not _s.get('matched')):
                        continue
                    _st = _s.get('struct') or {}
                    _banner = any(k in (_s.get('text') or '')
                                  for k in ('AVOIP', 'AVoIP'))
                    _finger = standby_fingerprint(_st, _s.get('mean') or 0.0)
                    if not (_banner or _finger):
                        continue
                    _b = _s['box']
                    learned.append(standby_row_profile(
                        frames[0][_b[1]:_b[3], _b[0]:_b[2]]))
                if learned:
                    remember_standby_profiles(label, learned)
            except Exception:
                pass
            rec.update({'mean': float(a.mean()), 'dark': float((a < 40).mean() * 100),
                        'bright': float((a > 180).mean() * 100),
                        'motion': mfrac, 'blobs': len(persons),
                        'screens': scr, 'display_state': aggregate_screen_state(scr),
                        'sync': apply_sync_persistence(label, sync)})
            rec['shot'] = embed(im0)
            rec['rects'] = [s['box'] for s in scr
                            if s.get('box') and s.get('monitored')]
        else:
            rec['screens'] = []
            rec['display_state'] = 'Unknown &ndash; camera offline'
            rec['sync'] = {'applicable': n_disp >= SYNC_MIN_DECODERS, 'verdict': 'unverified',
                           'n': 0, 'n_displays': n_disp, 'n_decoders': len(dec), 'pairs': [],
                           'pill': 'p-idle',
                           'label': 'NOT VERIFIED',
                           'detail': ['Camera offline &ndash; display sync cannot be measured.']}
            rec['shot'] = embed(placeholder(f'{label} - camera unreachable (HTTP 502)'))
        rows.append(rec)
    return rows


CSS = """
body{font-family:'Segoe UI',Arial,'Microsoft JhengHei',sans-serif;background:#f5f6f8;
color:#1f2430;margin:0;padding:24px;}
.wrap{max-width:1000px;margin:0 auto;}
h1{font-size:22px;margin:0 0 4px;}
.sub{color:#6b7280;font-size:13px;margin-bottom:18px;}
table.summary{border-collapse:collapse;width:100%;background:#fff;font-size:13px;
box-shadow:0 1px 3px rgba(0,0,0,.08);margin-bottom:24px;}
table.summary th{background:#eef2f7;text-align:left;padding:8px 10px;border:1px solid #dfe3ea;}
table.summary td{padding:8px 10px;border:1px solid #dfe3ea;vertical-align:middle;}
.room{background:#fff;border:1px solid #dfe3ea;border-radius:8px;padding:16px 18px;
margin-bottom:18px;box-shadow:0 1px 3px rgba(0,0,0,.06);}
.room h2{font-size:17px;margin:0 0 10px;padding-bottom:8px;border-bottom:2px solid #eef2f7;}
.room h3{font-size:13px;color:#4b5563;margin:14px 0 6px;text-transform:uppercase;letter-spacing:.4px;}
.pill{display:inline-block;font-size:11px;font-weight:bold;padding:3px 9px;border-radius:10px;
margin-left:8px;vertical-align:middle;}
.p-on{background:#e6f4ea;color:#186a3b;}
.p-off{background:#fce8e6;color:#a52714;}
.p-idle{background:#eef2f7;color:#4b5563;}
.p-sched{background:#fef7e0;color:#8a6100;}
.p-act{background:#e8f0fe;color:#174ea6;}
table.tv{border-collapse:collapse;width:100%;font-size:12.5px;margin-top:6px;}
table.tv th{background:#f3f5f8;text-align:left;padding:6px 8px;border:1px solid #dfe3ea;}
table.tv td{padding:6px 8px;border:1px solid #dfe3ea;vertical-align:top;}
td.shot{width:300px;text-align:center;background:#fafbfc;}
td.shot img{width:280px;border:1px solid #dfe3ea;border-radius:5px;display:block;margin:0 auto 6px;}
td.shot .cap{font-size:11px;color:#6b7280;}
.shotwrap{position:relative;display:inline-block;width:280px;line-height:0;}
.shotwrap img{margin:0 auto;}
.shotwrap .op{position:absolute;border:2px solid #e11d48;background:rgba(225,29,72,.07);}
.shotwrap .op span{position:absolute;top:-13px;left:-2px;background:#e11d48;color:#fff;
font-size:9px;font-weight:bold;padding:1px 4px;border-radius:3px;line-height:1.2;}
.shotwrap .op.stby{border-color:#7c3aed;background:rgba(124,58,237,.07);}
.shotwrap .op.stby span{background:#7c3aed;}
.legend{font-size:11px;color:#6b7280;margin:6px 0 0;}
.legend i{display:inline-block;width:10px;height:10px;border:2px solid #e11d48;vertical-align:-1px;
margin:0 3px 0 8px;}
.legend i.s{border-color:#7c3aed;}
ul{margin:4px 0 0 18px;padding:0;font-size:13px;}
li{padding:2px 0;}
.warn{background:#fff8e1;border-left:4px solid #f9a825;padding:8px 12px;font-size:13px;margin-top:8px;}
.note{background:#eef2f7;border-left:4px solid #607d8b;padding:8px 12px;font-size:12px;
color:#455a64;margin-bottom:18px;}
.ok{color:#186a3b;font-weight:bold;} .bad{color:#a52714;font-weight:bold;}
.muted{color:#4b5563;font-weight:bold;}
.foot{color:#6b7280;font-size:12px;margin-top:20px;border-top:1px solid #dfe3ea;padding-top:10px;}
"""


def overlay_html(shot, screens, w=280, frame_w=1280, frame_h=720):
    """Wrap the embedded frame in a box that outlines every monitored display.

    Danny (2026-09-28): he marks the displays he wants watched with a red rectangle
    on the camera image, so the report now draws the same rectangle back onto the
    snapshot. Red = the panel the scan actually measured (used for the Idle verdict
    and for picture sync); purple = a dark AVoIP standby panel that no bright blob
    could hold, so it could not be drawn.
    """
    scr = [s for s in (screens or []) if s.get('monitored')]
    if not scr:
        return f'<img src="{shot}" alt="room frame">'
    sx, sy = w / float(frame_w), w / float(frame_w) * (frame_h / float(frame_h))
    sy = w / float(frame_w)
    out = [f'<div class="shotwrap" style="width:{w}px"><img src="{shot}" alt="room frame">']
    for s in scr:
        b = s.get('box')
        if not b:
            cls = 'op stby'
            out.append(f'<div class="{cls}" style="left:-10000px"><span>STANDBY</span></div>')
            continue
        x0, y0, x1, y1 = b
        cls = 'op stby' if s['state'].startswith('Idle') and 'AVoIP' in s['state'] else 'op'
        out.append(f'<div class="{cls}" style="left:{x0 * sx:.0f}px;top:{y0 * sx:.0f}px;'
                   f'width:{(x1 - x0) * sx:.0f}px;height:{(y1 - y0) * sx:.0f}px"></div>')
    out.append('</div>')
    return ''.join(out)


def build_html(rows, cfg, snap):
    sched = cfg.get('scheduled_down', [])
    alarm = kds_alarm(cfg)
    try:
        warn = int((cfg.get('scan') or {}).get('temp_warn_c', alarm - 3))
    except (TypeError, ValueError):
        warn = alarm - 3
    ts = time.strftime('%Y-%m-%d %H:%M')
    upd = (snap or {}).get('updatedAt', '')[:19].replace('T', ' ')

    poller = poller_state(snap)
    h = ['<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">',
         f'<title>Shek Mun AV Room Audit {ts}</title><style>{CSS}</style></head><body><div class="wrap">',
         '<h1>Shek Mun AV &mdash; Room Audit Report</h1>',
         f'<div class="sub">Generated {ts} &middot; monitoring snapshot {upd} &middot; '
         'source: camera snapshots 172.18.22.101-109 + snapshot.json'
         f' &middot; report engine <b>v{VERSION}</b></div>',
         '<div class="note"><b>Reading guide:</b> Lighting and device status are measured data. '
         'Person counts cannot be determined automatically &mdash; the activity column reports the '
         'share of pixels that changed over 12 seconds. A room is <b>Abnormal</b> when a KDS '
         f'reading is at/above {alarm}&deg;C, a device is unreachable, the camera is offline, '
         'or &mdash; in a dual / quad room &mdash; the displays are <b>out of sync</b> (they share '
         'one source, so every display should show the same picture). Out of sync is deliberately '
         'strict: it needs OCR / luminance evidence on both sides, a standby-vs-content mismatch, '
         'and a disagreeing area of at least '
         f'{int(SYNC_MIN_AREA_RATIO * 100)}% of the largest display; anything weaker is only a '
         '<b>CHECK REGION</b> note. Lighting never triggers an Abnormal verdict. A device counts '
         'as unreachable only on an explicit <b>fail</b> &mdash; a device still marked '
         '<b>unknown</b> has simply not been polled yet. Out of sync must repeat on two '
         'consecutive runs before it raises an Abnormal.</div>']
    if poller['stale']:
        h.append("<div class='warn'><b>Monitoring poller just restarted.</b> "
                 f"{poller['unknown']} of {poller['total']} devices are still un-polled "
                 f"(<code>status: unknown</code>, empty <code>checkedAt</code>). Device "
                 'reachability is <b>not</b> judged on this run &mdash; treat any device row '
                 'below as "not measured yet", not as a fault.</div>')

    # summary table
    h.append('<table class="summary"><tr><th>Room</th><th>1. Lighting</th><th>2. Status</th>'
             '<th>3. Displays (monitoring)</th><th>Display: idle / in use</th>'
             '<th>Display sync</th><th>Max KDS</th><th>Snapshot</th></tr>')
    for r in rows:
        if r['label'] in sched:
            h.append(f"<tr><td><b>{r['label']}</b><span class='pill p-sched'>SCHEDULED DOWN</span></td>"
                     "<td colspan='5'>Planned downtime &mdash; area intentionally offline; "
                     "still scanned every run.</td>"
                     f"<td style='text-align:center'><img src=\"{r['shot']}\" style='width:120px'></td></tr>")
            continue
        light = 'ON' if r['mean'] > 90 and r['dark'] < 20 else 'OFF / PARTIAL'
        lcls = 'p-on' if light == 'ON' else 'p-off'
        act = 'Activity' if r['motion'] > 1 else 'Idle'
        acls = 'p-act' if act == 'Activity' else 'p-idle'
        temps = [d['tempC'] for d in r['decoders'] if isinstance(d.get('tempC'), (int, float))]
        mx = f"{max(temps)}&deg;C" if temps else 'n/a'
        mcls = 'bad' if temps and max(temps) >= alarm else ''
        nok = sum(1 for d in r['decoders'] if d['status'] == 'ok')
        dcls = 'ok' if nok == len(r['decoders']) and r['decoders'] else 'bad'
        dstate = r.get('display_state', 'Unknown')
        pcls, plabel, preason = display_pill(dstate)
        h.append(
            f"<tr><td><b>{r['label']}</b></td>"
            f"<td><span class='pill {lcls}'>{light}</span> <span style='color:#6b7280'>"
            f"lum {r['mean']:.0f}</span></td>"
            f"<td><span class='pill {acls}'>{act}</span> <span style='color:#6b7280'>"
            f"{r['motion']:.2f}%</span></td>"
            f"<td class='{dcls}'>{nok}/{len(r['decoders'])} decoder online"
            f"<div style='color:#6b7280;font-size:11px;margin-top:3px'>"
            f"{r.get('display_count') or len(r['decoders'])} &times; "
            f"{r.get('display_type') or 'LED TV'} monitored</div></td>"
            f"<td><span class='pill {pcls}'>{plabel}</span>"
            f"<div style='color:#6b7280;font-size:11px;margin-top:3px'>{preason}</div></td>"
            f"<td><span class='pill {r['sync']['pill']}'>{r['sync']['label']}</span>"
            f"<div style='color:#6b7280;font-size:11px;margin-top:3px'>"
            f"{r['sync']['n']} display region(s) seen / {r['sync']['n_decoders']} decoder(s)</div></td>"
            f"<td class='{mcls}'>{mx}</td>"
            f"<td style='text-align:center'><img src=\"{r['shot']}\" style='width:120px'></td></tr>")
    h.append('</table>')

    for r in rows:
        sched_down = r['label'] in sched
        h.append('<div class="room">')
        h.append(f"<h2>{r['label']} <span style='color:#6b7280;font-weight:normal;font-size:13px'>"
                 f"(172.18.22.{r['ip']})</span>"
                 + ("<span class='pill p-sched'>SCHEDULED DOWN</span>" if sched_down else '') + '</h2>')

        # 1 lighting
        h.append('<h3>1. Light on/off</h3>')
        if sched_down:
            h.append('<div class="warn">Marked as <b>scheduled down</b> for this period &mdash; '
                     'lighting state not assessed as a fault. Room is still scanned on every run.</div>')
        if r['online']:
            light = 'ON' if r['mean'] > 90 and r['dark'] < 20 else 'OFF / PARTIAL'
            h.append(f"<ul><li>Mean luminance <b>{r['mean']:.1f}</b> &middot; dark pixels "
                     f"<b>{r['dark']:.1f}%</b> &middot; bright pixels <b>{r['bright']:.2f}%</b></li>"
                     f"<li>Judgement: <b>{light}</b></li></ul>")
        else:
            h.append('<ul><li>Camera unreachable (HTTP 502 <code>upstream connect failed</code>) '
                     '&mdash; no frame to measure.</li></ul>')

        # 2 usage
        h.append('<h3>2. In use or idle</h3>')
        if r['online']:
            h.append(f"<ul><li>Pixels changing over 12 s: <b>{r['motion']:.2f}%</b> &middot; "
                     f"candidate moving blobs: <b>{r['blobs']}</b></li>"
                     f"<li>Judgement: <b>{'Activity (likely in use)' if r['motion'] > 1 else 'Idle'}</b></li>"
                     "<li style='color:#6b7280'>Person count cannot be confirmed automatically.</li></ul>")
        else:
            h.append('<ul><li>Not measurable &mdash; no camera frame.</li></ul>')

        # 3 TV/LED wall with snapshot inside the cell
        n_disp = r.get('display_count') or len(r['decoders']) or 1
        disp_type = r.get('display_type') or 'LED TV'
        h.append(f'<h3>3. TV / LED wall &mdash; {n_disp} &times; {disp_type} '
                 "(monitored)</h3>")
        h.append('<table class="tv"><tr><th>Device</th><th>IP</th><th>Network</th><th>KDS temp</th>'
                 '<th>Snapshot &amp; screen reading</th></tr>')
        dec = r['decoders'] or [{'name': '(none registered)', 'ip': '-', 'status': '-', 'tempC': None}]
        for idx, d in enumerate(dec):
            st = d.get('status')
            cls = 'ok' if st == 'ok' else ('bad' if st == 'fail' else '')
            temp = f"{d['tempC']}&deg;C" if isinstance(d.get('tempC'), (int, float)) else 'n/a'
            if sched_down and st == 'fail':
                st_txt = 'fail <span style="color:#8a6100">(scheduled down)</span>'
            else:
                st_txt = st
            shot_cell = ''
            if idx == 0:
                cap = (f"{r['label']} live frame &mdash; a red box is a panel the scan "
                       'measured for Idle and picture sync')
                shot_cell = (f"<td class='shot' rowspan='{len(dec)}'>"
                             + overlay_html(r['shot'], r.get('screens'))
                             + f"<div class='cap'>{cap}</div></td>")
            h.append(f"<tr><td><b>{d['name']}</b></td><td>{d['ip']}</td>"
                     f"<td class='{cls}'>{st_txt}</td><td>{temp}</td>{shot_cell}</tr>")
        h.append('</table>')

        scr = r.get('screens', [])
        monitored = [x for x in scr if x.get('monitored', True)]
        boards = [x for x in scr if not x.get('monitored', True)]
        if r['online'] and monitored:
            h.append('<table class="tv" style="margin-top:8px"><tr><th>Display region</th>'
                     '<th>Screen state</th><th>Static</th><th>OCR evidence</th></tr>')
            for si, s in enumerate(monitored):
                st = s['state']
                cls = 'ok' if st.startswith('Active') else (
                    'muted' if st.startswith('Idle') else 'bad')
                ev = s['text'] or '&mdash;'
                if s['box'] is None:
                    where = f'#{si+1} text outside detected regions'
                else:
                    x0, y0, x1, y1 = s['box']
                    where = (f"#{si+1} &middot; {x1-x0}&times;{y1-y0} px @({x0},{y0}) "
                             f"&middot; lum {s['mean']:.0f}")
                    if s.get('promoted'):
                        where += (" &middot; <b>counted as a TV</b> (AVoIP standby text "
                                  'read from this region)')
                h.append(f"<tr><td>{where}</td>"
                         f"<td class='{cls}'>{st}</td>"
                         f"<td>{s['static']*100:.1f}% unchanged</td>"
                         f"<td style='color:#455a64'>{ev}</td></tr>")
            h.append('</table>')
            if boards:
                h.append("<ul><li style='color:#6b7280'>Ignored regions "
                         f"({len(boards)}) &mdash; not counted towards the Idle / "
                         'picture-sync verdict:</li>')
                for b in boards:
                    reason = b.get('skip_reason')
                    if not reason:
                        reason = (f'beyond the {n_disp} declared {disp_type}(s), so '
                                  'treated as whiteboard / noticeboard')
                    if b.get('box'):
                        bx0, by0, bx1, by1 = b['box']
                        pos = f'{bx1-bx0}&times;{by1-by0} px @({bx0},{by0})'
                    else:
                        pos = 'text outside detected regions'
                    txt = (f" &middot; readable text: <i>{b['text'][:70]}</i>"
                           if b.get('text') else '')
                    h.append(f"<li style='color:#6b7280'>{pos} &mdash; {reason}{txt}</li>")
                h.append('</ul>')
            h.append(f"<ul><li><b>Room verdict: {r.get('display_state')}</b></li>"
                     "<li style='color:#6b7280'><b>Idle</b> is narrow on purpose: only the "
                     "AVoIP <i>decoder standby</i> banner, the Windows <i>lock screen</i> "
                     "(clock only, no application) and an <i>all-blank</i> screen. A Windows "
                     "desktop or an application that sits static for a long time is reported "
                     'as <b>Content on screen</b>.</li></ul>')
        elif r['online']:
            h.append("<ul><li class='muted'>No bright display region detected in frame &mdash; "
                     "displays likely switched off.</li></ul>")

        # 3b multi-display picture sync (dual / quad rooms only)
        sy = r.get('sync') or {}
        if sy.get('applicable'):
            vcls = {'out-of-sync': 'bad', 'in-sync': 'ok',
                    'check': 'muted'}.get(sy['verdict'], 'muted')
            h.append('<h3>3b. Multi-display picture sync</h3><ul>')
            h.append(f"<li>{sy.get('n_displays') or sy.get('n_decoders')} display(s) "
                     f"declared &middot; "
                     f"{sy['n']} region(s) isolated in frame &rarr; "
                     f"<span class='{vcls}'>{sy['label']}</span></li>")
            for d in sy['detail']:
                h.append(f'<li>{d}</li>')
            if sy['pairs']:
                corrs = ', '.join(
                    f"#{p['a']}~#{p['b']} " + ('n/a' if p['corr'] is None else f"{p['corr']:+.2f}")
                    for p in sy['pairs'])
                h.append("<li style='color:#6b7280'>Coarse 8&times;8 luminance correlation per "
                         f"pair (information only &mdash; viewing angles differ a great deal): "
                         f"{corrs}</li>")
            h.append('</ul>')

        if r['reserve']:
            h.append('<ul><li style="color:#6b7280">Spare / reserve units (excluded by monitoring): '
                     + ', '.join(f"{d['name']} ({d['status']})" for d in r['reserve']) + '</li></ul>')
        if r['avoip']:
            bad = [d for d in r['avoip'] if is_fault(d)]
            h.append('<ul><li>AVoIP encoders: '
                     + ', '.join(f"{d['name']} <span class='"
                                 f"{'ok' if d['status']=='ok' else ('bad' if is_fault(d) else 'muted')}'>"
                                 f"{d['status']}</span>" for d in r['avoip']) + '</li></ul>')
            if bad and sched_down:
                h.append('<div class="warn">AVoIP offline here is expected &mdash; area is under '
                         'scheduled downtime.</div>')

        # 4 other
        h.append('<h3>4. Other observations</h3><ul>')
        if not r['online']:
            h.append('<li class="bad">Camera offline &mdash; snapshot cannot be retrieved.</li>')
        temps = [d for d in r['decoders'] if isinstance(d.get('tempC'), (int, float))]
        hot = [d for d in temps if d['tempC'] >= alarm]
        warm = [d for d in temps if warn <= d['tempC'] < alarm]
        if hot:
            for d in hot:
                h.append(f"<li class='bad'>{d['name']} KDS at {d['tempC']}&deg;C &mdash; "
                         f"at/above the {alarm}&deg;C alarm threshold.</li>")
        for d in warm:
            h.append(f"<li>{d['name']} KDS at {d['tempC']}&deg;C &mdash; within "
                     f"{alarm - d['tempC']}&deg;C of the alarm threshold (not yet abnormal).</li>")
        if r['online'] and r['motion'] < 0.05 and r['mean'] > 90:
            h.append('<li>Lights on but zero motion &mdash; room appears unattended; consider '
                     'switching lighting off.</li>')
        if r['online'] and r['dark'] > 20:
            h.append(f"<li>Large dark area ({r['dark']:.1f}%) &mdash; check zoned lighting "
                     '(information only, not an Abnormal condition).</li>')
        sy = r.get('sync') or {}
        if sy.get('verdict') == 'out-of-sync':
            h.append("<li class='bad'>Multi-display picture out of sync &mdash; the displays in "
                     "this room share one source and must show the same image. Confirm against "
                     "the snapshot above.</li>")
        elif sy.get('verdict') == 'check':
            h.append("<li class='muted'>Idle displays show different standby banners &mdash; "
                     'worth a visual check (not counted as abnormal).</li>')
        elif sy.get('verdict') == 'unverified' and sy.get('applicable'):
            h.append("<li class='muted'>Display sync could not be verified automatically from "
                     'this frame &mdash; compare the displays by eye.</li>')
        if not hot and not warm and r['online'] and sy.get('verdict') not in ('out-of-sync',):
            h.append('<li>No anomalies detected from measurable data.</li>')
        h.append('</ul></div>')

    h.append('<div class="foot">Generated automatically by Bud &middot; camera snapshots embedded '
             'inline &middot; scheduled-down rooms are still scanned every run and reported, '
             f'never dropped &middot; report engine <b>v{VERSION}</b> '
             f'(<a href="changelog.md">changelog</a>).'
             '<br><span id="runstats"><!--STATS--></span></div>')
    h.append('</div></body></html>')
    return '\n'.join(h)


if __name__ == '__main__':
    os.makedirs(TMP, exist_ok=True)
    _t0 = time.time()
    cfg = load_config()
    snap = fetch_snapshot()
    _t1 = time.time()
    if not os.environ.get('SKIP_GRAB'):
        grab()
    _t2 = time.time()
    rows = analyse(snap, cfg)
    _t3 = time.time()
    with open(os.path.join(OUT, 'av_summary.json'), 'w', encoding='utf-8') as f:
        json.dump([{k: v for k, v in r.items() if k != 'shot'} for r in rows], f, indent=1)
    html = build_html(rows, cfg, snap)
    path = os.path.join(OUT, 'AV_room_audit.html')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    _t4 = time.time()
    print('written', path, len(html), 'bytes')
    print(f'STATS fetch={_t1-_t0:.1f} grab={_t2-_t1:.1f} '
          f'analyse={_t3-_t2:.1f} render={_t4-_t3:.1f} total={_t4-_t0:.1f}')
    for r in rows:
        print(f"{r['label']:12s} online={r['online']} "
              f"lum={r.get('mean', 0):.0f} motion={r.get('motion', 0):.2f}% "
              f"decoders={len(r['decoders'])}")
