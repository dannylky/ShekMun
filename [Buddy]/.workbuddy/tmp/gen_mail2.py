import json
import os
import io
import time
import base64
from PIL import Image, ImageDraw

OUT = r'C:/Work/Projects/ShekMun/[Buddy]'
TMP = os.path.join(OUT, '.workbuddy', 'tmp')
rows = json.load(open(os.path.join(OUT, 'av_summary.json'), encoding='utf-8'))
cfg = json.load(open(os.path.join(OUT, 'av_monitor_config.json'), encoding='utf-8'))
sched = cfg['scheduled_down']
NOW = time.strftime('%Y-%m-%d %H:%M')

WIDTH = int(os.environ.get('IMG_W', '160'))
QUAL = int(os.environ.get('IMG_Q', '40'))


def embed(path, width=WIDTH, q=QUAL):
    im = Image.open(path).convert('RGB')
    w, h = im.size
    im = im.resize((width, int(h * width / w)))
    buf = io.BytesIO()
    im.save(buf, 'JPEG', quality=q, optimize=True)
    return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()


def placeholder(label):
    im = Image.new('RGB', (640, 360), (238, 240, 245))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 639, 359], outline=(190, 195, 205), width=3)
    d.text((40, 150), f'{label}', fill=(90, 95, 105))
    d.text((40, 175), 'camera unreachable - HTTP 502', fill=(150, 40, 40))
    return im.resize((WIDTH, int(360 * WIDTH / 640)))


def to_uri(im):
    buf = io.BytesIO()
    im.save(buf, 'JPEG', quality=QUAL, optimize=True)
    return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()


# ---------- evaluate anomalies ----------
anomalies = {}
for r in rows:
    if r['label'] in sched:
        continue
    issues = []
    if not r['online']:
        issues.append('camera offline')
    bad_dec = [d['name'] for d in r['decoders'] if d.get('status') != 'ok']
    if bad_dec:
        issues.append('decoder ' + ', '.join(bad_dec))
    bad_av = [d['name'] for d in r['avoip'] if d.get('status') != 'ok']
    if bad_av:
        issues.append('AVoIP ' + ', '.join(bad_av))
    temps = [d for d in r['decoders'] if isinstance(d.get('tempC'), (int, float))]
    if temps and max(d['tempC'] for d in temps) >= 42:
        issues.append(f"KDS {max(d['tempC'] for d in temps)}C")
    if r['online'] and r['dark'] > 20:
        issues.append(f"partial lighting ({r['dark']:.0f}% dark)")
    if r['online'] and r['motion'] < 0.05 and r['mean'] > 90:
        issues.append('lights on, unattended')
    if issues:
        anomalies[r['label']] = issues

status = 'Ok' if not anomalies else 'Abnormal'
names = ', '.join(anomalies.keys())
subject = f'HSUHK@Shek Mun Audit report- {NOW} / Status: {status}' + (f' ({names})' if names else '')

CSS = ("body{font-family:'Segoe UI',Arial,'Microsoft JhengHei',sans-serif;color:#1f2430;"
       "font-size:14px;line-height:1.5;background:#fff;margin:0;padding:16px;}"
       "table{border-collapse:collapse;width:100%;font-size:13px;margin:10px 0;}"
       "th{background:#eef2f7;text-align:left;padding:7px 8px;border:1px solid #dfe3ea;}"
       "td{padding:7px 8px;border:1px solid #dfe3ea;vertical-align:top;}"
       ".pill{display:inline-block;font-size:11px;font-weight:bold;padding:2px 8px;"
       "border-radius:9px;}"
       ".p-on{background:#e6f4ea;color:#186a3b;}.p-off{background:#fce8e6;color:#a52714;}"
       ".p-idle{background:#eef2f7;color:#4b5563;}.p-act{background:#e8f0fe;color:#174ea6;}"
       ".p-sched{background:#fef7e0;color:#8a6100;}"
       ".ok{color:#186a3b;font-weight:bold;}.bad{color:#a52714;font-weight:bold;}"
       ".note{background:#eef2f7;border-left:4px solid #607d8b;padding:10px 12px;font-size:12px;"
       "color:#455a64;margin:12px 0;}"
       ".warn{background:#fff8e1;border-left:4px solid #f9a825;padding:10px 12px;font-size:13px;"
       "margin:12px 0;}"
       "td.shot{width:180px;text-align:center;background:#fafbfc;}"
       "td.shot img{width:160px;border:1px solid #dfe3ea;border-radius:4px;display:block;"
       "margin:0 auto 5px;}"
       ".cap{font-size:11px;color:#6b7280;}")

h = [f'<html><head><meta charset="utf-8"><style>{CSS}</style></head><body>',
     f'<h2 style="margin:0 0 4px">HSUHK@Shek Mun Audit report &mdash; {NOW}</h2>',
     f'<div style="color:#6b7280;font-size:12px;margin-bottom:12px">Status: '
     f'<b style="color:{"#a52714" if status == "Abnormal" else "#186a3b"}">{status}</b>'
     + (f' &middot; {names}' if names else '')
     + ' &middot; cameras 172.18.22.101-109 &middot; monitoring snapshot.json</div>',
     '<table><tr><th>Room</th><th>1. Lighting</th><th>2. Status</th>'
     '<th>3. TV / LED wall &amp; snapshot</th><th>4. Notes</th></tr>']

for r in rows:
    p = os.path.join(TMP, 's1', f'{r["ip"]}.jpg')
    if r['online'] and os.path.exists(p):
        uri = embed(p)
    else:
        uri = to_uri(placeholder(r['label']))

    if r['label'] in sched:
        dec = r['decoders']
        dl = ', '.join(f"{d['name']} <span class='bad'>{d['status']}</span>" for d in dec) or 'n/a'
        h.append(f"<tr><td><b>{r['label']}</b><br><span class='pill p-sched'>SCHEDULED DOWN</span></td>"
                 '<td colspan="2">Planned downtime &mdash; not treated as a fault. '
                 'Area is still scanned on every run.</td>'
                 f"<td class='shot'><img src=\"{uri}\" alt='{r['label']}'>"
                 f"<div class='cap'>{r['label']} &mdash; camera unreachable (HTTP 502)</div></td>"
                 f"<td>Displays: {dl}<br>AVoIP: "
                 + ', '.join(f"{d['name']} <span class='bad'>{d['status']}</span>"
                             for d in r['avoip']) + '</td></tr>')
        continue

    light = 'ON' if r['mean'] > 90 and r['dark'] < 20 else 'OFF / PARTIAL'
    lcls = 'p-on' if light == 'ON' else 'p-off'
    act = 'Activity' if r['motion'] > 1 else 'Idle'
    acls = 'p-act' if act == 'Activity' else 'p-idle'
    t = [d['tempC'] for d in r['decoders'] if isinstance(d.get('tempC'), (int, float))]
    mx = f"{max(t)}&deg;C" if t else 'n/a'
    mcls = 'bad' if t and max(t) >= 42 else ''
    nok = sum(1 for d in r['decoders'] if d['status'] == 'ok')
    dcls = 'ok' if nok == len(r['decoders']) else 'bad'
    dec_rows = '<br>'.join(
        f"{d['name']} &middot; {d['ip']} &middot; "
        f"<span class='{'ok' if d['status']=='ok' else 'bad'}'>{d['status']}</span> &middot; "
        f"{(str(d['tempC'])+'&deg;C') if isinstance(d.get('tempC'), (int, float)) else 'n/a'}"
        for d in r['decoders']) or 'none registered'
    notes = anomalies.get(r['label'])
    note_txt = ('<span class="bad">' + '<br>'.join(notes) + '</span>') if notes else \
        '<span class="ok">No anomalies</span>'

    h.append(
        f"<tr><td><b>{r['label']}</b><br><span style='color:#6b7280;font-size:11px'>"
        f"172.18.22.{r['ip']}</span></td>"
        f"<td><span class='pill {lcls}'>{light}</span><br><span style='color:#6b7280;font-size:11px'>"
        f"lum {r['mean']:.0f} &middot; dark {r['dark']:.0f}%</span></td>"
        f"<td><span class='pill {acls}'>{act}</span><br><span style='color:#6b7280;font-size:11px'>"
        f"{r['motion']:.2f}% changed / 12s</span></td>"
        f"<td class='shot'><img src=\"{uri}\" alt='{r['label']}'>"
        f"<div class='cap'>{r['label']} live frame</div>"
        f"<div style='font-size:11px;text-align:left;margin-top:6px'>{dec_rows}</div></td>"
        f"<td>{note_txt}</td></tr>")
h.append('</table>')

h.append('<div class="note"><b>How to read this</b><br>Lighting, device reachability and KDS '
         'temperature are measured values. Screen on/off and picture-sync across displays '
         '<b>cannot</b> be machine-verified &mdash; check the snapshot in each room&rsquo;s '
         'TV / LED wall cell. Person count is not available; the activity figure is the share of '
         'pixels that changed over 12 seconds.</div>')
h.append('<p style="font-size:12px;color:#6b7280">Full report with full-size snapshots: '
         'attached <b>AV_room_audit.html</b>. Some mail clients block inline images &mdash; '
         'if the frames do not appear, open the attachment.</p>')
h.append('</body></html>')

body = '\n'.join(h)
open(os.path.join(TMP, 'mail_body2.html'), 'w', encoding='utf-8').write(body)
print('SUBJECT:', subject)
print('body bytes:', len(body))
