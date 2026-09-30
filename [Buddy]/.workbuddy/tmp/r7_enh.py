# -*- coding: utf-8 -*-
import sys, os
import numpy as np
from PIL import Image, ImageOps, ImageFilter
sys.path.insert(0, r"C:/Work/Projects/ShekMun/[Buddy]")
import av_scan
OUT = r"C:/Work/Projects/ShekMun/[Buddy]/.workbuddy/tmp/live7"
rgb0 = Image.open(os.path.join(OUT,"g0.jpg")).convert("RGB")

BOXES = {'L':(179,61,402,196), 'R':(802,57,1020,191)}

def hp(img, rad=12):
    """high-pass: remove the slow glare gradient"""
    a = np.asarray(img.convert('L'), dtype=np.float32)
    bl = np.asarray(img.convert('L').filter(ImageFilter.GaussianBlur(rad)), dtype=np.float32)
    d = a - bl
    d = d - d.min()
    if d.max() > 0: d = d / d.max() * 255
    return Image.fromarray(d.astype(np.uint8))

for k, b in BOXES.items():
    c = rgb0.crop(b).convert('L')
    print("=== %s %s ===" % (k, b))
    variants = {
      'raw x2'      : c.resize((c.width*2, c.height*2), Image.LANCZOS),
      'auto x2'     : ImageOps.autocontrast(c, cutoff=2).resize((c.width*2,c.height*2), Image.LANCZOS),
      'auto x3'     : ImageOps.autocontrast(c, cutoff=2).resize((c.width*3,c.height*3), Image.LANCZOS),
      'hp+auto x3'  : ImageOps.autocontrast(hp(c), cutoff=1).resize((c.width*3,c.height*3), Image.LANCZOS),
      'hp+auto x4'  : ImageOps.autocontrast(hp(c), cutoff=1).resize((c.width*4,c.height*4), Image.LANCZOS),
      'eq x3'       : ImageOps.equalize(c).resize((c.width*3,c.height*3), Image.LANCZOS),
    }
    for name, im in variants.items():
        t = [x['text'] for x in av_scan.ocr_frame(np.asarray(im.convert('RGB')))]
        hit = any(key in ' '.join(t).upper() for key in ('AVOIP','DECODER','STANDBY','VIDEO'))
        print("   %-12s %-6s %s" % (name, 'HIT' if hit else '', (' | '.join(t))[:130] if t else '(none)'))

# pattern match: L vs R (same room, same instant) and controls
def sig(img, size=(128,80)):
    h = hp(img).resize(size, Image.LANCZOS)
    a = np.asarray(h, dtype=np.float32)
    a = (a - a.mean()) / (a.std() + 1e-6)
    return a
sL = sig(rgb0.crop(BOXES['L']))
sR = sig(rgb0.crop(BOXES['R']))
print("\nNCC L vs R (high-pass normalised) = %.3f" % float((sL*sR).mean()))
