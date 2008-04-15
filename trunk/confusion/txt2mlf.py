#!//usr/bin/python2.4
# -*-  coding: UTF-8 -*-

import glob
import getopt
import sys
from os.path import *
from xml.dom import minidom

import codecs
import re

uttFile = codecs.open(sys.argv[2], 'r', 'UTF-8')
outUttFile = codecs.open(sys.argv[3], 'w', 'UTF-8')

i = 1

outUttFile.write("#!MLF!#\n")
for utt in uttFile.readlines():
    outUttFile.write('"*/%06d.%s"\n' % (i, sys.argv[1]))
    
    words = utt.strip().split()
    for word in words:
        outUttFile.write(word + "\n")
    outUttFile.write(".\n")
    
    i += 1
    
uttFile.close()
outUttFile.close()
