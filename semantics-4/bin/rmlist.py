#!/usr/bin/env python

import sys
import os

for fn in sys.stdin:
    try:
        fn = fn.strip()
        os.remove(fn)
    except:
        print sys.exc_info()[1]

