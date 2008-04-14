#!/usr/bin/env python

import sys
import os
import shutil
from svc.osutils import mkdirp

def cut_dir(path, chop_dir='/'):
    ret = []
    while True:
        path, base = os.path.split(path)
        if not path:
            break
        ret.append(base)
        if path == chop_dir:
            break
        if path == '/':
            break
    rstr = ret.pop()
    while ret:
        rstr = os.path.join(rstr, ret.pop())
    return rstr

to_dir = sys.argv[1]
if len(sys.argv) == 3:
    chop_dir = sys.argv[2]
else:
    chop_dir = '/'

for fn in sys.stdin:
    try:
        fn = fn.rstrip()
        if not fn:
            continue
        if os.path.isdir(fn):
            continue
        new_fn = os.path.join(to_dir, cut_dir(fn, chop_dir))
        mkdirp(os.path.split(new_fn)[0])
        shutil.copy(fn, new_fn)
    except:
        print sys.exc_info()[1]


