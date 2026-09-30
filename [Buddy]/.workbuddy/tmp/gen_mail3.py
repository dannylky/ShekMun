import json, os, time

OUT = r'C:/Work/Projects/ShekMun/[Buddy]'
TMP = os.path.join(OUT, '.workbuddy', 'tmp')
rows = json.load(open(os.path.join(OUT, 'av_summary.json'), encoding='utf-8'))
cfg = json.load(open(os.path.join(OUT, 'av_monitor_config.json'), encoding='utf-8'))
sched = cfg['scheduled_down']
NOW = time.strftime('%Y-%m-%d %H:%M')
KDS_ALARM = 45

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
    if temps and max(d['tempC'] for d in temps) >= KDS_ALARM:
        issues.append(f"KDS {max(d['tempC'] for d in temps)}C (over {KDS_ALARM}C)")
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
       ".pill{display:inline-block;font-size:11px;font-weight:bold;padding:2px 8px;border-radius:9px;}"
       ".p-on{background:#e6f4ea;color:#186a3b;}.p-off{background:#fce8e6;color:#a52714;}"
       ".p-idle{background:#eef2f7;color:#4b5563;}.p-act{background:#e8f0fe;color:#174ea6;}"
       ".p-sched{background:#fef7e0;color:#8a6100;}"
       ".ok{color:#186a3b;font-weight:bold;}.bad{color:#a52714;font-weight:bold;}"
       ".muted{color:#4b5563;font-weight:bold;}"
       ".note{background:#eef2f7;border-left:4px solid #607d8b;padding:10px 12px;font-size:12px;"
       "color:#455a64;margin:12px 0;}"
       ".warn{background:#fff8e1;border-left:4px solid #f9a825;padding:10px 12px;font-size:13px;margin:12px 0;}"
       ".sub{color:#6b7280;font-size:11px;}")

h = [f'<html><head><meta charset="utf-8"><style>{CSS}</style></head><body>',
     f'<h2 style="margin:0 0 4px">HSUHK@Shek Mun Audit report &mdash; {NOW}</h2>',
     f'<div style="color:#6b7280;font-size:12px;margin-bottom:12px">Status: '
     f'<b style="color:{"#a52714" if status == "Abnormal" else "#186a3b"}">{status}</b>'
     + (f' &middot; {names}' if names else '')
     + ' &middot; cameras 172.18.22.101-109 &middot; source: monitoring snapshot.json</div>',
     '<table><tr><th>Room</th><th>1. Lighting</th><th>2. Use</th>'
     '<th>3. TV / LED wall &mdash; screen state<br>(snapshot in attached report)</th>'
     '<th>4. Notes</th></tr>']

for r in rows:
    if r['label'] in sched:
        dec_rows = '<br>'.join(
            f"{d['name']} &middot; {d['ip']} &middot; "
            f"<span class='{'ok' if d['status']=='ok' else 'bad'}'>{d['status']}</span> "
            f"<span class='sub'>(scheduled down)</span>" for d in r['decoders']) or 'none registered'
        h.append(f"<tr><td><b>{r['label']}</b><br><span class='pill p-sched'>SCHEDULED DOWN</span></td>"
                 '<td colspan="3">Planned downtime &mdash; reported for information only, '
                 'not raised as a fault. Still scanned on every run.</td>'
                 f"<td>{dec_rows}</td>"
                 f"<td class='sub'>Camera unreachable (HTTP 502). Area excluded from the "
                 f"Ok/Abnormal verdict.</td></tr>")
        continue

    light = 'ON' if r['mean'] > 90 and r['dark'] < 20 else 'OFF / PARTIAL'
    lcls = 'p-on' if light == 'ON' else 'p-off'
    act = 'Activity' if r['motion'] > 1 else 'Idle'
    acls = 'p-act' if act == 'Activity' else 'p-idle'
    t = [d['tempC'] for d in r['decoders'] if isinstance(d.get('tempC'), (int, float))]
    mx = f"{max(t)}&deg;C" if t else 'n/a'
    mcls = 'bad' if t and max(t) >= KDS_ALARM else ''
    nok = sum(1 for d in r['decoders'] if d['status'] == 'ok')
    ds = r.get('display_state', 'Unknown')
    if ds.startswith('Idle'):
        spill, plabel, preason = 'p-idle', 'IDLE', ds.split('&ndash;')[1].strip()
    elif ds.startswith('Active'):
        spill, plabel, preason = 'p-act', 'IN USE', 'content on screen'
    elif ds.startswith('Off'):
        spill, plabel, preason = 'p-off', 'OFF', 'display dark'
    else:
        spill, plabel, preason = 'p-idle', 'UNCONFIRMED', 'content not readable'
    scr_rows = '<br>'.join(
        (('text outside detected regions') if s['box'] is None
         else f"{s['box'][2]-s['box'][0]}&times;{s['box'][3]-s['box'][1]} px")
        + f" &middot; <span class='{'ok' if s['state'].startswith('Active') else ('muted' if s['state'].startswith('Idle') else '')}'>{s['state']}</span>"
        + (f"<br><span class='sub'>{s['text'][:80]}</span>" if s['text'] else '')
        for s in r.get('screens', [])) or '&mdash;'
    dec_rows = '<br>'.join(
        f"{d['name']} &middot; {d['ip']} &middot; "
        f"<span class='{'ok' if d['status']=='ok' else 'bad'}'>{d['status']}</span> &middot; "
        f"{(str(d['tempC'])+'&deg;C') if isinstance(d.get('tempC'), (int, float)) else 'n/a'}"
        for d in r['decoders']) or 'none registered'
    disp = (f"<div><span class='pill {spill}'>{plabel}</span> "
            f"<span class='sub'>{preason}</span></div>"
            f"<div class='sub' style='margin-top:4px'>{scr_rows}</div>"
            f"<div style='margin-top:5px'><span class='{'ok' if nok==len(r['decoders']) else 'bad'}'>"
            f"{nok}/{len(r['decoders'])} decoder(s) online</span> &middot; max KDS "
            f"<span class='{mcls}'>{mx}</span></div>"
            f"<div class='sub' style='margin-top:4px'>{dec_rows}</div>")
    notes = list(anomalies.get(r['label'], []))
    if ds.startswith('Idle'):
        notes.append('<span class="muted">Display idle</span>')
    note_txt = ('<br>'.join(notes)) if notes else '<span class="ok">No anomalies</span>'

    h.append(
        f"<tr><td><b>{r['label']}</b><br><span class='sub'>172.18.22.{r['ip']}</span></td>"
        f"<td><span class='pill {lcls}'>{light}</span><br><span class='sub'>"
        f"lum {r['mean']:.0f} &middot; dark {r['dark']:.0f}%</span></td>"
        f"<td><span class='pill {acls}'>{act}</span><br><span class='sub'>"
        f"{r['motion']:.2f}% pixels changed / 12s</span></td>"
        f"<td>{disp}</td>"
        f"<td>{note_txt}</td></tr>")
h.append('</table>')

if anomalies:
    items = ''.join(f'<li><b>{k}</b> &mdash; {"; ".join(v)}</li>' for k, v in anomalies.items())
    h.append(f'<div class="warn"><b>Action needed</b><ul style="margin:6px 0 0 18px">{items}</ul></div>')

h.append('<div class="note"><b>How to read this</b><br>Lighting, device reachability and KDS '
         'temperature are measured values. A room is <b>Abnormal</b> only when a KDS reading is at '
         f'or above <b>{KDS_ALARM}&deg;C</b>, a display/AVoIP device is unreachable, or the camera '
         'is offline. Display screen state comes from OCR of each camera frame: a screen showing '
         'the <b>AVoIP decoder standby</b> banner or a <b>Windows idle / lock screen</b> (clock '
         'only, no application) is reported as <b>Idle</b>; anything else with readable content is '
         '<b>Active</b>. Picture-sync between displays still has to be confirmed by eye &mdash; '
         'open the attached <b>AV_room_audit.html</b>, where each room&rsquo;s live frame sits '
         'inside its TV / LED wall cell. Person count is not available; the &ldquo;Use&rdquo; '
         'column is the share of pixels that changed over 12 seconds.</div>')
h.append('<p style="font-size:12px;color:#6b7280">Attachments: <b>AV_room_audit.html</b> '
         '(full report, snapshot inside each TV / LED wall cell) &middot; '
         '<b>all_rooms_*.jpg</b> (3x3 contact sheet).</p>')
h.append('</body></html>')

body = '\n'.join(h)
open(os.path.join(TMP, 'mail_body3.html'), 'w', encoding='utf-8').write(body)
print('SUBJECT:', subject)
print('body bytes:', len(body))
for r in rows:
    print(f"  {r['label']:12s} online={r['online']} lum={r.get('mean',0):.0f} "
          f"dark={r.get('dark',0):.0f} motion={r.get('motion',0):.2f} "
          f"dec={len(r['decoders'])} ok={sum(1 for d in r['decoders'] if d['status']=='ok')}")
