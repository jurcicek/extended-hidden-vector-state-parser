#!//usr/bin/python2.4
# -*-  coding: UTF-8 -*-

import glob
import getopt
import sys
from os.path import *
from xml.dom import minidom

import codecs
import re

pa = {'a':'a',u'á':'A','b':'b','c':'c',u'č':'C','d':'d',u'ď':'D','e':'e',u'é':'E',u'ě':'e',
    'f':'f',
    'g':'g','h':'h','i':'i',u'í':'I','j':'j','k':'k','l':'l','m':'m','m':'M','n':'n',
    'n':'N',u'ň':'~','o':'o',u'ó':'O',u'ö':'O','p':'p','r':'r',u'ř':'R','s':'s',u'š':'S','t':'t',
    u'ť':'T','u':'u',u'ú':'U',u'ů':'U',u'ü':'u','v':'v','w':'v','y':'i',u'ý':'I','x':'k','z':'z',u'ž':'Z'}

dict = []
alph = {}
confusion = {}

###############################################################
###############################################################
def cost(a,b):
##    if a == b:
##        return 0
    
    pa_a = pa[a]
    pa_b = pa[b]
    
    return 1 - confusion[pa_a][pa_b]

###############################################################
###############################################################

def levenshtein(a,b):
    "Calculates the Levenshtein distance between a and b."
    n, m = len(a), len(b)
    if n > m:
        # Make sure n <= m, to use O(min(n,m)) space
        a,b = b,a
        n,m = m,n
        
    current = range(n+1)
    for i in range(1,m+1):
        previous, current = current, [i]+[0.0]*n
        
        for j in range(1,n+1):
            insertion    = previous[j]   + 3.0
            deletion     = current[j-1]  + 3.0
            substitution = previous[j-1] + 1.2*cost(a[j-1], b[i-1])
            
            current[j] = min(insertion, deletion, substitution)
            
    return current[n]

###############################################################
###############################################################

def readConfTable(filename):
    global confusion
    
    f = open(filename, 'r')
    
    lines = f.readlines()
    
    alph = lines[0].split()
    alph = alph[1:-1]

    i = 1
    confusion = {}
    for a in alph:
        confusion[a] = {}
        
        nums = lines[i].split()
        
        j = 1
        sum = 0.0
        for b in alph:
            confusion[a][b] = float(nums[j])
            sum += confusion[a][b]
            j += 1
        
        # normalization
        for b in alph:
            confusion[a][b] = confusion[a][b]/sum
        
        i += 1
       
       
    f.close()
    
    f = open('confusion.out', 'w')
    for a in alph:
        # normalization
        for b in alph:
            f.write("%2.3f " % confusion[a][b])
        f.write('\n')
    f.close()
    
###############################################################
###############################################################

def mapWord(dict, www):
    top = []
    for word in dict:
        top.append([levenshtein(word, www), www, word])
    
    top.sort()    
    
    return top
    
###############################################################
###############################################################

readConfTable('confusion.txt')

dictFile = codecs.open('dict.txt', 'r', 'UTF-8')
for word in dictFile.readlines():
    dict.append(word.strip())
dictFile.close()

num   = int(sys.argv[1])

print(">>>>>>>>>>>>>>>>>>")

mapFile = codecs.open('map.txt', 'w', 'UTF-8')

for www in dict:
    print www.encode('ascii', 'replace')
    
    top = mapWord(dict, www)
    
    mapFile.write("%-15s " % top[2][1])
    for t in top[:num]:
        mapFile.write("%-15s %1.6f " % (t[2], t[0]))
    mapFile.write('\n')


dictFile.close()

print("<<<<<<<<<<<<<<<<<<")

