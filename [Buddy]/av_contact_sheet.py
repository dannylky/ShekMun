import json, os, time
from PIL import Image, ImageDraw

OUT = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(OUT, '.workbuddy', 'tmp')
rows = json.load(open(os.path.join(OUT, 'av_summary.json'), encoding='utf-8'))
cfg = json.load(open(os.path.join(OUT, 'av_monitor_config.json'), encoding='utf-8'))
sched = cfg['scheduled_down']

CW, CH = 420, 260
sheet = Image.new('RGB', (CW * 3, CH * 3), (255, 255, 255))
d = ImageDraw.Draw(sheet)

for i, r in enumerate(rows[:9]):
    p = os.path.join(TMP, 's1', f'{r["ip"]}.jpg')
    if r['online'] and os.path.exists(p):
        im = Image.open(p).convert('RGB')
    else:
        im = Image.new('RGB', (640, 360), (238, 240, 245))
        dd = ImageDraw.Draw(im)
        dd.text((30, 160), f'{r["label"]} - camera unreachable (HTTP 502)', fill=(150, 40, 40))
    im.thumbnail((CW, CH - 30))
    x, y = (i % 3) * CW, (i // 3) * CH
    sheet.paste(im, (x + (CW - im.width) // 2, y + 24))
    tag = r['label'] + (' [SCHEDULED DOWN]' if r['label'] in sched else '')
    d.text((x + 8, y + 6), tag, fill=(20, 24, 32))
    d.text((x + 8, y + CH - 18),
           f'lum {r.get("mean",0):.0f} | dark {r.get("dark",0):.0f}% | motion {r.get("motion",0):.2f}%',
           fill=(90, 95, 105))
    d.rectangle([x, y, x + CW - 1, y + CH - 1], outline=(215, 220, 228))

ts = time.strftime('%Y%m%d_%H%M')
out = os.path.join(OUT, f'all_rooms_{ts}.jpg')
sheet.save(out, 'JPEG', quality=80)
print('SHEET:', out)
