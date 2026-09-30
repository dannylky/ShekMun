import numpy as np, os, sys
from PIL import Image
sys.path.insert(0, r"C:\Work\Projects\ShekMun\[Buddy]")
import av_scan
D = r"C:\Work\Projects\ShekMun\[Buddy]\.workbuddy\tmp\live2c"
fs = [np.asarray(Image.open(os.path.join(D,f'g{i}.jpg')).convert('RGB'), dtype=np.float32) for i in range(3)]

BOXES = [("left-wall TV",(255,52,477,189)), ("right-wall TV",(861,51,1092,185))]
for n, bx in BOXES:
    print("== %s %s ==" % (n, bx))
    for i, f in enumerate(fs):
        p = f[bx[1]:bx[3], bx[0]:bx[2]]
        l = p.mean(axis=2)
        d1 = p[:,:,2]-p[:,:,1]; d2 = p[:,:,1]-p[:,:,0]
        st = av_scan.region_structure(l)
        hue = av_scan.standby_hue(p)
        lock = av_scan.lock_screen_signature(p)
        fing = av_scan.standby_fingerprint(st, l.mean(), st.get('darkshare'))
        print("   g%d lum %6.1f dark %.3f band %.3f B-R %+6.1f | hue %s | lock %s | fingerprint %s" % (
            i, l.mean(), st['darkshare'], st['band'], (p[:,:,2]-p[:,:,0]).mean(),
            ("%.1f/%.1f" % hue) if hue else "None", lock, fing))
    z = av_scan.panel_zoom_ocr([f.astype(np.uint8) for f in fs], bx)
    print("   OCR(standby):", z or '<none>')
    # generic OCR of the panel crop
    from PIL import ImageOps
    c = Image.fromarray(fs[0][bx[1]:bx[3], bx[0]:bx[2]].astype(np.uint8)).convert('L')
    c = ImageOps.autocontrast(c, cutoff=2); c = c.resize((c.width*3, c.height*3), Image.LANCZOS)
    try:
        t = [it['text'] for it in av_scan.ocr_frame(np.asarray(c.convert('RGB')))]
        print("   OCR(all)  :", t[:8])
    except Exception as e:
        print("   OCR err", e)
    for i, f in enumerate(fs[:1]):
        im = Image.fromarray(fs[0].astype(np.uint8))
        im.crop(bx).resize(((bx[2]-bx[0])*2,(bx[3]-bx[1])*2), Image.LANCZOS).save(
            os.path.join(D, 'pan_%s.png' % n.split()[0]))
print("\nsaved panel crops")
