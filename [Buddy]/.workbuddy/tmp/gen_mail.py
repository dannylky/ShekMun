import json
import os
import time
from PIL import Image, ImageDraw

OUT = r'C:/Work/Projects/ShekMun/[Buddy]'
TMP = os.path.join(OUT, '.workbuddy', 'tmp')
rows = json.load(open(os.path.join(OUT, 'av_summary.json'), encoding='utf-8'))
cfg = json.load(open(os.path.join(OUT, 'av_monitor_config.json'), encoding='utf-8'))
sched = cfg['scheduled_down']
ts = time.strftime('%Y-%m-%d %H:%M')

# fresh contact sheet
IPS = ['101', '102', '103', '104', '105', '106', '107', '108', '109']
LABEL = {'101': 'SM-11-01', '102': 'SM-11-02', '103': 'SM-11-03', '104': 'SM-11-04',
         '105': 'SM-11-05', '106': 'SM-11-06', '107': 'SM-11-07', '108': 'SM-11-08',
         '109': 'Common Area'}
CW, CH = 640, 360
sheet = Image.new('RGB', (CW * 3, CH * 3 + 60), (245, 246, 248))
d = ImageDraw.Draw(sheet)
d.text((16, 20), f'Shek Mun AV - all room cameras - {ts}', fill=(30, 35, 45))
for i, ip in enumerate(IPS):
    x, y = (i % 3) * CW, (i // 3) * CH + 60
    p = os.path.join(TMP, 's1', f'{ip}.jpg')
    if os.path.exists(p) and os.path.getsize(p) > 5000:
        sheet.paste(Image.open(p).convert('RGB').resize((CW, CH)), (x, y))
    else:
        d.rectangle([x, y, x + CW, y + CH], fill=(225, 228, 235))
        d.text((x + 40, y + CH // 2), 'OFFLINE', fill=(180, 40, 40))
    d.rectangle([x, y, x + CW, y + 22], fill=(30, 35, 45))
    tag = LABEL[ip] + ('  [SCHEDULED DOWN]' if LABEL[ip] in sched else '')
    d.text((x + 8, y + 6), f'{tag}   (172.18.22.{ip})', fill=(255, 255, 255))
sheet_path = os.path.join(OUT, f'all_rooms_{time.strftime("%Y%m%d_%H%M")}.jpg')
sheet.save(sheet_path, quality=85)

CSS = ("body{font-family:'Segoe UI',Arial,'Microsoft JhengHei',sans-serif;color:#1f2430;"
       "font-size:14px;line-height:1.5;}"
       "table{border-collapse:collapse;width:100%;font-size:13px;margin:12px 0;}"
       "th{background:#eef2f7;text-align:left;padding:8px 10px;border:1px solid #dfe3ea;}"
       "td{padding:8px 10px;border:1px solid #dfe3ea;}"
       ".pill{display:inline-block;font-size:11px;font-weight:bold;padding:2px 8px;"
       "border-radius:9px;}"
       ".p-on{background:#e6f4ea;color:#186a3b;}.p-off{background:#fce8e6;color:#a52714;}"
       ".p-idle{background:#eef2f7;color:#4b5563;}.p-act{background:#e8f0fe;color:#174ea6;}"
       ".p-sched{background:#fef7e0;color:#8a6100;}"
       ".ok{color:#186a3b;font-weight:bold;}.bad{color:#a52714;font-weight:bold;}"
       ".note{background:#eef2f7;border-left:4px solid #607d8b;padding:10px 12px;font-size:12px;"
       "color:#455a64;margin:12px 0;}"
       ".warn{background:#fff8e1;border-left:4px solid #f9a825;padding:10px 12px;font-size:13px;"
       "margin:12px 0;}")

h = [f'<html><head><meta charset="utf-8"><style>{CSS}</style></head><body>',
     '<h2 style="margin:0 0 4px">Shek Mun AV &mdash; Room Audit</h2>',
     f'<div style="color:#6b7280;font-size:12px;margin-bottom:14px">Generated {ts} &middot; '
     'cameras 172.18.22.101-109 &middot; monitoring snapshot.json</div>',
     '<table><tr><th>Room</th><th>1. Lighting</th><th>2. Status</th>'
     '<th>3. Displays</th><th>Max KDS</th></tr>']

for r in rows:
    if r['label'] in sched:
        h.append(f"<tr><td><b>{r['label']}</b> <span class='pill p-sched'>SCHEDULED DOWN</span></td>"
                 '<td colspan="4">Planned downtime &mdash; reported for information only; '
                 'still scanned on every run.</td></tr>')
        continue
    light = 'ON' if r['mean'] > 90 and r['dark'] < 20 else 'OFF / PARTIAL'
    lcls = 'p-on' if light == 'ON' else 'p-off'
    act = 'Activity' if r['motion'] > 1 else 'Idle'
    acls = 'p-act' if act == 'Activity' else 'p-idle'
    t = [x['tempC'] for x in r['decoders'] if isinstance(x.get('tempC'), (int, float))]
    mx = f"{max(t)}&deg;C" if t else 'n/a'
    mcls = 'bad' if t and max(t) >= 42 else ''
    nok = sum(1 for x in r['decoders'] if x['status'] == 'ok')
    dcls = 'ok' if nok == len(r['decoders']) else 'bad'
    h.append(f"<tr><td><b>{r['label']}</b></td>"
             f"<td><span class='pill {lcls}'>{light}</span> <span style='color:#6b7280'>"
             f"lum {r['mean']:.0f} / dark {r['dark']:.0f}%</span></td>"
             f"<td><span class='pill {acls}'>{act}</span> <span style='color:#6b7280'>"
             f"{r['motion']:.2f}% changed</span></td>"
             + f"<td class='{dcls}'>{nok}/{len(r['decoders'])} decoder online</td>"
             f"<td class='{mcls}'>{mx}</td></tr>")
h.append('</table>')

h.append('<div class="warn"><b>Action needed</b><ul style="margin:6px 0 0 18px">')
hot = [f"{x['name']} {x['tempC']}°C" for r in rows if r['label'] not in sched
       for x in r['decoders'] if isinstance(x.get('tempC'), (int, float)) and x['tempC'] >= 42]
if hot:
    h.append(f'<li>KDS temperature near the 45&deg;C threshold: {", ".join(hot)}</li>')
dim = [r['label'] for r in rows if r['label'] not in sched and r['online'] and r['dark'] > 20]
if dim:
    h.append(f'<li>Large dark area / partial lighting: {", ".join(dim)}</li>')
lit = [r['label'] for r in rows if r['label'] not in sched and r['online']
       and r['motion'] < 0.05 and r['mean'] > 90]
if lit:
    h.append(f'<li>Lights on but no motion (possibly unattended): {", ".join(lit)}</li>')
h.append('</ul></div>')

h.append('<div class="note"><b>How to read this report</b><br>'
         'Lighting and device status are measured values. Person counts cannot be determined '
         'automatically &mdash; the activity column is the percentage of pixels that changed over '
         '12 seconds. Screen on/off and inter-display sync must be confirmed by eye: open the '
         'attached <b>AV_room_audit.html</b>, where each room&rsquo;s live snapshot is embedded '
         'inside its TV / LED wall table cell.</div>')

h.append('<p style="font-size:13px">Attachments: '
         '<b>AV_room_audit.html</b> (full report with snapshots in the TV/LED cells) &middot; '
         '<b>' + os.path.basename(sheet_path) + '</b> (3&times;3 contact sheet).</p>')
h.append('</body></html>')

body = '\n'.join(h)
open(os.path.join(TMP, 'mail_body.html'), 'w', encoding='utf-8').write(body)
print('sheet:', sheet_path)
print('body bytes:', len(body))
