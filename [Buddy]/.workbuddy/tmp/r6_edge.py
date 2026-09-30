# -*- coding: utf-8 -*-
import sys, os
import numpy as np
from PIL import Image
sys.path.insert(0, r"C:/Work/Projects/ShekMun/[Buddy]")
import av_scan
B = r"C:/Work/Projects/ShekMun/[Buddy]/.workbuddy/tmp/live6"
g = av_scan.gray(B+'/g0.jpg')

def scan(name, fixed, rng, axis):
    print("--- %s ---" % name)
    vals = []
    for v in rng:
        if axis == 'x':
            vals.append((v, float(g[10:150, v].mean())))
        else:
            vals.append((v, float(g[v, 760:1060].mean())))
    print('  ' + ' '.join('%d:%.0f' % t for t in vals))

scan('right edge (cols)', None, range(1040, 1080), 'x')
scan('left edge  (cols)', None, range(745, 785), 'x')
scan('top edge   (rows)', None, range(0, 40), 'y')
scan('bottom edge(rows)', None, range(185, 235), 'y')
