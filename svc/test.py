#!/usr/bin/env python2.4

from svc.ui.pdt import  PDTParser

parser = PDTParser()
txt = file('output/fm_file').read()
gen = parser.parse(txt)
for item in gen:
    for sub_item in item:
        print sub_item
    print
    print

