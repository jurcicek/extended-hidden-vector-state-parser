#!//usr/bin/python2.4
# -*-  coding: UTF-8 -*-

import glob
import getopt
import sys
from os.path import *
from clnum import *

import codecs
import re

dict = []
alph = {}
confusion = {}

###############################################################
###############################################################

def upMap(top, power):
    mtop = mpf(max(top)[0])
    sum = mpf(0.0)
    for t in top:
        t[0] = pow(power, pow(power, mtop - mpf(t[0])))
        sum += t[0]
    
    for t in top:
        t[0] = t[0]/sum
        
    top.sort(reverse=True)    
    
    return top
    
###############################################################
###############################################################

power = mpf(float(sys.argv[1]))

print(">>>>>>>>>>>>>>>>>>")

mapFile = codecs.open('map.txt', 'r', 'UTF-8')
upMapFile = codecs.open('map.up.txt', 'w', 'UTF-8')
for line in mapFile.readlines():
    line = line.strip().split()
    www = line[0]
    line = line[1:]
    upMapFile.write("%-15s " % www)
    
    top = []
    
    for i in range(0, len(line), 2):
        top.append([float(line[i+1]), line[i]])
    
    top = upMap(top, power)
        
    for t in top:
        upMapFile.write("%-15s %1.6f " % (t[1], t[0]))
    upMapFile.write('\n')

mapFile.close()
upMapFile.close()

print("<<<<<<<<<<<<<<<<<<")

