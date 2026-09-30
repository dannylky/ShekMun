import numpy as np, os, sys
from PIL import Image
sys.path.insert(0, r"C:\Work\Projects\ShekMun\[Buddy]")
import av_scan

cfg = av_scan.load_config()
regions = cfg.get('display_regions') or {}
prof = {k: av_scan.standby_profiles(cfg, k) for k in (cfg.get('standby_profiles') or {})}
print("standby_profiles rooms:", list(prof.keys()))
refs_all = []
for k, v in prof.items():
    print("   %s: %d profile(s)" % (k, len(v)))

CAMS = {'SM-11-01':'101','SM-11-02':'102','SM-11-03':'103','SM-11-04':'104',
        'SM-11-05':'105','SM-11-06':'106','SM-11-07':'107','SM-11-08':'108'}
BASE = r"C:\Work\Projects\ShekMun\[Buddy]\.workbuddy\tmp\v26probe"
os.makedirs(BASE, exist_ok=True)
import subprocess

print("\n%-10s %-22s %6s %6s %8s %8s  %s" % ("room","region","lum","band","hue","ncc","verdict"))
for room, ip in CAMS.items():
    rs = regions.get(room)
    if not rs: continue
    d = os.path.join(BASE, room); os.makedirs(d, exist_ok=True)
    fs = []
    for i in range(2):
        p = os.path.join(d, 'g%d.jpg' % i)
        if not os.path.exists(p):
            subprocess.run(["curl","-s","-m","20","-o",p,"http://172.18.22.%s/snapshot/snapshot"%ip], check=False)
        try: fs.append(np.asarray(Image.open(p).convert('RGB'), dtype=np.float32))
        except Exception: pass
    if not fs: 
        print("%-10s  <no frame>" % room); continue
    f = fs[0]
    refs = prof.get(room) or []
    for r in rs:
        b = r['box']; x0,y0,x1,y1 = b
        f2 = f[y0:y1, x0:x1]
        l = f2.mean(axis=2); st = av_scan.region_structure(l)
        hue = av_scan.standby_hue(f2)
        hm = av_scan.standby_hue_match(f2, st, l.mean(), require_band=False)
        ncc = None
        if refs:
            pr = av_scan.standby_row_profile(l)
            ncc = max(av_scan.profile_ncc(pr, rr) for rr in refs)
        print("%-10s %-22s %6.1f %6.3f %8s %8s  hue=%s ncc_ok=%s" % (
            room, r.get('label','')[:22], l.mean(), st['band'],
            ("%.1f" % hue[0]) if hue else "-",
            ("%.3f" % ncc) if ncc is not None else "-",
            hm, (ncc is not None and ncc >= av_scan.STANDBY_NCC_MIN)))
