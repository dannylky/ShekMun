from PIL import Image, ImageDraw

NAMES = [
    ('101', 'SM-11-01'), ('102', 'SM-11-02'), ('103', 'SM-11-03'),
    ('104', 'SM-11-04'), ('105', 'SM-11-05'), ('106', 'SM-11-06'),
    ('107', 'SM-11-07'), ('108', 'SM-11-08'), ('109', 'Common Area'),
]
CW, CH = 640, 360
canvas = Image.new('RGB', (CW * 3, CH * 3 + 60), (15, 23, 42))
d = ImageDraw.Draw(canvas)
d.text((16, 18), 'Shek Mun AV - all room cameras - 2026-09-21 08:49', fill=(226, 232, 240))

for i, (ip, name) in enumerate(NAMES):
    x = (i % 3) * CW
    y = (i // 3) * CH + 60
    try:
        im = Image.open(f'm1/{ip}.jpg').convert('RGB').resize((CW, CH))
        canvas.paste(im, (x, y))
    except Exception:
        d.rectangle([x, y, x + CW, y + CH], fill=(40, 40, 55))
        d.text((x + 24, y + CH // 2), 'OFFLINE / 502 upstream connect failed', fill=(248, 113, 113))
    d.rectangle([x, y, x + CW, y + 22], fill=(0, 0, 0))
    d.text((x + 8, y + 6), f'{name}   (172.18.22.{ip})', fill=(255, 255, 255))

canvas.save('C:/Work/Projects/ShekMun/[Buddy]/all_rooms_20260921_0849.jpg', quality=88)
print('saved')
