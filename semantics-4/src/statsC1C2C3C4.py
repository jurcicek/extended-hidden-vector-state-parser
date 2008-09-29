#!//usr/bin/python
# -*-  coding: UTF-8 -*-

import sys
import getopt
import os
from os.path import *
import glob
from xml.dom import minidom
import re
import struct
import codecs
from copy import *

import toolkit
import sparseProbability
import gmtk
import bucketing
from lexMap import *
from observation import *
from math import log

##############################################################################
##############################################################################

noPruning = True
dirOut = '/home/filip/cued/ehvs/semantics-4/build/test/data-txt/trn'
dirHO = dirOut+'/ho'

###################################################################################################
###################################################################################################

def reduceGrams(grams):
    reducedGrams = {}
    
    for each in grams.keys():
        reducedGrams[each[:-1]] = reducedGrams.get(each[:-1], 0) + grams[each]
            
    return reducedGrams

###################################################################################################
###################################################################################################

def pruneGrams(grams, limit = 8):
    prunedGrams = {}
    
    for each in grams.keys():
        if grams[each] > limit:
            prunedGrams[each] = grams[each]

    return prunedGrams

###################################################################################################
###################################################################################################

def cleanGrams(grams1, grams2):
    cleanedGrams = deepcopy(grams2)
    
    for each in grams1.keys():
        if cleanedGrams.get(each[:-1], 0) > 0:
            del cleanedGrams[each[:-1]]

    return cleanedGrams

###################################################################################################
###################################################################################################

def buildTree(tree, grams):
    for eachGram in grams.keys():
##        print ">>> ", tree, eachGram
        treeLeaf = tree
                
        for each in eachGram:
##            print each
            if treeLeaf.has_key(each):
                treeLeaf = treeLeaf[each][0]
##                print "+++ ", treeLeaf
            else:
                treeLeaf[each] = [{},grams[eachGram]]
##                print "--- ", treeLeaf
        
##        print "<<< ", tree, eachGram
##        print
        
    return
    
    
###################################################################################################
###################################################################################################

def usage():
    print("""
    Usage:   statsCC1C2C3C4.py [options] 
    
    Description:
             Compute statistics of HVS histories.
    
    Options: 
             -h                        : print this help message and exit
             -v                        : produce verbose output
             -p                        : turn off pruning of histories when you perform smoothing
             --dirOut=DIR              : the output directory where to put all output files {%s} 
             --dirCmb=DIR              : input directory for *.dcd ( *.extension) files {%s}
    """ % (dirOut, 
           dirHO))
##############################################################################

def printGrams(f, gram):
    k = gram.keys()
    k.sort()
    
    for each in k:
        f.write("%s = %s\n" % (str(each), str(gram[each])))

###################################################################################################
###################################################################################################

try:
    opts, args = getopt.gnu_getopt(sys.argv[1:], "hvtnp", 
        ["dirOut=",
         "dirCmb="])
         
except getopt.GetoptError, exc:
    print("ERROR: " + exc.msg)
    usage()
    sys.exit(2)

for o, a in opts:
    if o == "-h":
        usage()
        sys.exit()
    elif o == "-v":
        verbose = True
    elif o == "-t":
        text = True
    elif o == "-n":
        noSmoothing = True
    elif o == "-p":
        noPruning = True
    elif o == "--dirOut":
        dirOut = a
    elif o == "--dirCmb":
        dirHO = a
    elif o == "--conceptMap":
        conceptFileName = a
    elif o == "--wordMap":
        wordFileName = a

print("Start word history backoff-ing")
print("-------------------------------------------------")

lst = glob.glob(dirHO + "/*.hddn")
##lst = lst[:300]
lst.sort()

print len(lst)

wordGrams = {}
c1Grams = {}
c2Grams = {}

for fileName in lst:
    bucketing.getWordGrams(fileName, wordGrams, c1Grams, c2Grams, fileType='hddn')

    
c1Grams[(u'_EMPTY_', u'_EMPTY_', u'_EMPTY_', u'_EMPTY_')] = 999999

# number of stacks [c1, c2, c3, c4] is lower than for training
# because during force alingnment was not decoded many _DUMMY_
# concepts

c1Grams4 = c1Grams
c1Grams3 = reduceGrams(c1Grams4)
c1Grams2 = reduceGrams(c1Grams3)
c1Grams1 = reduceGrams(c1Grams2)

print("Number of c1Grams4: %d" % len(c1Grams4))
print("Number of c1Grams3: %d" % len(c1Grams3))
print("Number of c1Grams2: %d" % len(c1Grams2))
print("Number of c1Grams1: %d" % len(c1Grams1))

# save stats
bStats = file(dirOut+"/C1C2C3C4"+'.stats', 'w')

bStats.write("Number of c1Grams4: %d\n" % len(c1Grams4))
bStats.write("Number of c1Grams3: %d\n" % len(c1Grams3))
bStats.write("Number of c1Grams2: %d\n" % len(c1Grams2))
bStats.write("Number of c1Grams1: %d\n" % len(c1Grams1))

if not noPruning:
    c1Grams4 = pruneGrams(c1Grams4, 8)
    c1Grams3 = pruneGrams(c1Grams3, 6)
    c1Grams2 = pruneGrams(c1Grams2, 4)
    c1Grams1 = pruneGrams(c1Grams1, 2)

print("Number of pruned c1Grams4: %d" % len(c1Grams4))
print("Number of pruned c1Grams3: %d" % len(c1Grams3))
print("Number of pruned c1Grams2: %d" % len(c1Grams2))
print("Number of pruned c1Grams1: %d" % len(c1Grams1))

bStats.write("Number of pruned c1Grams4: %d\n" % len(c1Grams4))
bStats.write("Number of pruned c1Grams3: %d\n" % len(c1Grams3))
bStats.write("Number of pruned c1Grams2: %d\n" % len(c1Grams2))
bStats.write("Number of pruned c1Grams1: %d\n" % len(c1Grams1))

bStats.write("\nPruned c1Grams4:\n")
printGrams(bStats, c1Grams4)
bStats.write("\nPruned c1Grams3:\n")
printGrams(bStats, c1Grams3)
bStats.write("\nPruned c1Grams2:\n")
printGrams(bStats, c1Grams2)
bStats.write("\nPruned c1Grams1:\n")
printGrams(bStats, c1Grams1)

bStats.close()

print("-------------------------------------------------")
print("Finish")

