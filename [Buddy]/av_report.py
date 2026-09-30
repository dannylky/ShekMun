#!/usr/bin/env python
"""One-shot Shek Mun AV audit pipeline.

Steps
  1. av_scan.py            - grab 3 camera passes, OCR screens, write AV_room_audit.html
                             + av_summary.json
  2. av_contact_sheet.py   - build the 3x3 contact sheet jpg
  3. av_mail.py            - build the email body + compute the subject line

Prints machine readable RESULT lines at the end so the caller can pick up the
subject / attachment paths.  Set SKIP_GRAB=1 to reuse the frames already on disk.
"""
import os
import re
import sys
import time
import json
import subprocess

OUT = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(OUT, '.workbuddy', 'tmp')
PY = sys.executable

# token estimation: ~4 characters per token for the mostly-Latin/markup text we ship
CHARS_PER_TOKEN = 4.0
# fixed cost of one hourly run that the pipeline itself cannot see:
# skill file + system prompt + tool calls/results other than the mail body
EST_OVERHEAD = int(os.environ.get('EST_OVERHEAD', 3000))


def est_tokens(text):
    return int(round(len(text) / CHARS_PER_TOKEN))


# keep this many hours of contact sheets / raw frames on disk (0 disables cleanup)
KEEP_HOURS = float(os.environ.get('KEEP_HOURS', 48))

# --- run throttle -------------------------------------------------------
# The scheduler replays missed slots as a burst when WorkBuddy starts up again
# (after the machine was off overnight). 16 daily slots that were all missed
# would otherwise produce 16 near-identical reports back to back, so a run is
# refused unless at least MIN_RUN_MIN minutes have passed since the previous
# completed run. 45 min never blocks the hourly cadence, only catch-up bursts.
# FORCE=1 overrides (manual runs). MIN_RUN_MIN=0 disables the throttle.
MIN_RUN_MIN = float(os.environ.get('MIN_RUN_MIN', 45))
LAST_RUN = os.path.join(TMP, 'last_run.json')


def last_run_age_min():
    try:
        with open(LAST_RUN, encoding='utf-8') as f:
            return (time.time() - json.load(f)['ts']) / 60.0
    except Exception:
        return None


def note_last_run(subject):
    try:
        with open(LAST_RUN, 'w', encoding='utf-8') as f:
            json.dump({'ts': time.time(), 'subject': subject}, f)
    except Exception:
        pass


def cleanup(keep_hours=KEEP_HOURS):
    """Delete old contact sheets and raw camera passes.

    One run per hour produces ~16 jpg/day, which piles up fast. Only files older than
    the retention window go, and only files matching the pipeline's own naming.
    """
    if keep_hours <= 0:
        return 0
    cutoff = time.time() - keep_hours * 3600
    removed = 0
    for f in sorted(os.listdir(OUT)):
        if not (f.startswith('all_rooms_') and f.endswith('.jpg')):
            continue
        p = os.path.join(OUT, f)
        try:
            if os.path.getmtime(p) < cutoff:
                os.remove(p)
                removed += 1
        except OSError:
            pass
    for d in ('s1', 's2', 's3'):
        pd = os.path.join(TMP, d)
        if not os.path.isdir(pd):
            continue
        for f in sorted(os.listdir(pd)):
            p = os.path.join(pd, f)
            try:
                if os.path.getmtime(p) < cutoff:
                    os.remove(p)
                    removed += 1
            except OSError:
                pass
    return removed


def plain_stats(s):
    """Strip HTML from the stats block so RESULT stats= stays readable in the log."""
    import html as _html
    return re.sub(r'\s+', ' ', _html.unescape(re.sub(r'<[^>]+>', ' ', s))).strip()


def inject(path, html_stats):
    """Replace the <!--STATS--> placeholder written by the earlier stages."""
    if not path or not os.path.exists(path):
        return
    with open(path, encoding='utf-8') as f:
        s = f.read()
    if '<!--STATS-->' not in s:
        return
    with open(path, 'w', encoding='utf-8') as f:
        f.write(s.replace('<!--STATS-->', html_stats))


def run(script, env=None):
    e = dict(os.environ)
    if env:
        e.update(env)
    p = subprocess.run([PY, os.path.join(OUT, script)], cwd=OUT, env=e,
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    print(p.stdout.strip())
    if p.returncode != 0:
        print(p.stderr.strip(), file=sys.stderr)
    return p.stdout


def main():
    os.makedirs(TMP, exist_ok=True)

    # ---- throttle: refuse a catch-up burst ------------------------------
    age = last_run_age_min()
    if (MIN_RUN_MIN > 0 and not os.environ.get('FORCE')
            and age is not None and age < MIN_RUN_MIN):
        print(f'RESULT skip=last run was {age:.0f} min ago '
              f'(min interval {MIN_RUN_MIN:g} min) &mdash; catch-up of a missed '
              f'slot, nothing to do. No email will be sent.')
        return 0

    t0 = time.time()
    skip = {'SKIP_GRAB': '1'} if os.environ.get('SKIP_GRAB') else None
    scan_out = run('av_scan.py', skip)
    t1 = time.time()
    sheet_out = run('av_contact_sheet.py')
    t2 = time.time()
    mail_out = run('av_mail.py')
    t3 = time.time()

    sheet = (re.search(r'SHEET:\s*(.+)', sheet_out) or [None, None])[1]
    subject = (re.search(r'SUBJECT:\s*(.+)', mail_out) or [None, None])[1]
    sheet = sheet.strip() if sheet else None
    if not sheet:                       # fall back to the newest contact sheet
        cands = sorted(f for f in os.listdir(OUT) if f.startswith('all_rooms_'))
        sheet = os.path.join(OUT, cands[-1]) if cands else None
    if not subject:
        subject = ('HSUHK@Shek Mun Audit report- '
                   + time.strftime('%Y-%m-%d %H:%M') + ' / Status: Unknown')

    # ---- run statistics: elapsed time + estimated tokens ----
    html_path = os.path.join(OUT, 'AV_room_audit.html')
    body_path = os.path.join(TMP, 'mail_body.html')
    body = open(body_path, encoding='utf-8').read() if os.path.exists(body_path) else ''
    html_len = os.path.getsize(html_path) if os.path.exists(html_path) else 0
    stage = (re.search(r'STATS\s+(.+)', scan_out) or [None, ''])[1].strip()
    total_s = t3 - t0
    body_tok = est_tokens(body)
    html_tok = int(round(html_len / CHARS_PER_TOKEN))
    total_tok = body_tok + EST_OVERHEAD
    now = time.strftime('%Y-%m-%d %H:%M:%S')

    stats_html = (f'<b>Run stats</b> &mdash; generated {now} in <b>{total_s:.1f} s</b> '
                  f'(scan {t1-t0:.1f} s &middot; contact sheet {t2-t1:.1f} s &middot; '
                  f'email body {t3-t2:.1f} s)'
                  + (f' &middot; scan internals: {stage}' if stage else '') + '.<br>'
                  f'Estimated LLM tokens for this run: <b>~{total_tok:,}</b> '
                  f'(mail body ~{body_tok:,} tok + skill/tool overhead ~{EST_OVERHEAD:,} tok); '
                  f'the HTML attachment is {html_len//1024} KB '
                  f'(~{html_tok:,} tok only if it is pulled into context). '
                  f'Estimate assumes ~{CHARS_PER_TOKEN:g} characters per token.')
    inject(html_path, stats_html)
    inject(body_path, stats_html)

    try:
        n = cleanup()
        if n:
            print(f'RESULT cleanup=removed {n} file(s) older than {KEEP_HOURS:g} h')
    except Exception as e:
        print(f'RESULT cleanup=failed ({e})')

    note_last_run(subject)
    print('RESULT stats=' + plain_stats(stats_html))
    print('RESULT subject=' + subject)
    print('RESULT html=' + html_path)
    if sheet:
        print('RESULT sheet=' + sheet)
    print('RESULT body=' + body_path)


if __name__ == '__main__':
    main()
