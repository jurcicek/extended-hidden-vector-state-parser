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

def translate(wordGrams, wordMap, conceptMap):
    newWordGrams = {}
    for eachGram in wordGrams.keys():
        newWordGrams[(conceptMap[eachGram[0]], 
                      conceptMap[eachGram[1]],
                      conceptMap[eachGram[2]],
                      conceptMap[eachGram[3]])] = wordGrams[eachGram]
    
    return newWordGrams
    
###################################################################################################
###################################################################################################

dirOut = "../gen"
dirCmb = "../fa_trn/dcd"

conceptFileName = "../data/train/concept.map"
wordFileName = "../data/train/word.map"

def usage():
    print("""
    Usage:   backoffWordHistory.py [options] 
    
    Description:
             Compute backoff model for word history.
    
    Options: 
             -h                        : print this help message and exit
             -v                        : produce verbose output
             -t                        : produce text output that is not suitable for GMTK, but it is human readable
             -n                        : turn off smoothing 
             --dirOut=DIR              : the output directory where to put all output files {%s} 
             --dirCmb=DIR              : input directory for *.dcd ( *.extension) files {%s}
             --conceptMap=FILE         : the concept map file name {%s}
             --wordMap=FILE            : the word map file name {%s}
    """ % (dirOut, 
           dirCmb, 
           conceptFileName, 
           wordFileName))
##############################################################################

def printGrams(f, gram):
    k = gram.keys()
    k.sort()
    
    for each in k:
        f.write("%s = %s\n" % (str(each), str(gram[each])))

###################################################################################################
###################################################################################################

try:
    opts, args = getopt.gnu_getopt(sys.argv[1:], "hvtn", 
        ["dirOut=",
         "dirCmb=", 
         "conceptMap=", 
         "wordMap="])
         
except getopt.GetoptError, exc:
    print("ERROR: " + exc.msg)
    usage()
    sys.exit(2)

verbose = None
text = None
noSmoothing = False

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
    elif o == "--dirOut":
        dirOut = a
    elif o == "--dirCmb":
        dirCmb = a
    elif o == "--conceptMap":
        conceptFileName = a
    elif o == "--wordMap":
        wordFileName = a
        
lst = glob.glob(dirCmb + "/*.cmb")
##lst = lst[:300]
lst.sort()

if verbose:
    print("Start word history backoff-ing")
    print("-------------------------------------------------")

conceptMap = LexMap().read(conceptFileName)
wordMap = LexMap().read(wordFileName)
rConceptMap = LexMap().read(conceptFileName).reverse()
rWordMap = LexMap().read(wordFileName).reverse()

wordGrams = {}
c1Grams = {}
c2Grams = {}

for fileName in lst:
    bucketing.getWordGrams(fileName, wordGrams, c1Grams, c2Grams)


c1Grams[(u'_EMPTY_', u'_EMPTY_', u'_EMPTY_', u'_EMPTY_')] = 999999

# number of stacks [c1, c2, c3, c4] is lower than for training
# because during force alingnment was not decoded many _DUMMY_
# concepts

if not text:
    c1Grams = translate(c1Grams, wordMap, conceptMap)
    
c1Grams4 = c1Grams
c1Grams3 = reduceGrams(c1Grams4)
c1Grams2 = reduceGrams(c1Grams3)
c1Grams1 = reduceGrams(c1Grams2)

if verbose:
    print("Number of c1Grams4: %d" % len(c1Grams4))
    print("Number of c1Grams3: %d" % len(c1Grams3))
    print("Number of c1Grams2: %d" % len(c1Grams2))
    print("Number of c1Grams1: %d" % len(c1Grams1))

if not noSmoothing:
    c1Grams4 = pruneGrams(c1Grams4, 8)
    c1Grams3 = pruneGrams(c1Grams3, 6)
    c1Grams2 = pruneGrams(c1Grams2, 4)
    c1Grams1 = pruneGrams(c1Grams1, 2)

if verbose:
    print("Number of pruned c1Grams4: %d" % len(c1Grams4))
    print("Number of pruned c1Grams3: %d" % len(c1Grams3))
    print("Number of pruned c1Grams2: %d" % len(c1Grams2))
    print("Number of pruned c1Grams1: %d" % len(c1Grams1))

##c1Grams0 = {}
##c1Grams0[('alfa'),]=1
##c1Grams0[('beta'),]=1
##c1Grams0[('gama'),]=1
##c1Grams1 = {}
##c1Grams1[('alfa', 'ALFA')]=1
##c1Grams1[('alfa', 'BETA')]=1
##c1Grams1[('beta', 'ALFA')]=1
##c1Grams1[('beta', 'BETA')]=1
##c1Grams2 = {}
##c1Grams2[('alfa', 'BETA', 'GAMA')]=5
##c1Grams3 = {}
##c1Grams3[('alfa', 'BETA', 'GAMA', 'DELTA')]=6

tree = {}
buildTree(tree, c1Grams1)
buildTree(tree, c1Grams2)
buildTree(tree, c1Grams3)
buildTree(tree, c1Grams4)

#print tree['alfa']

gmtk.saveDtBackoff(dirOut, "backoffC1C2C3C4", tree, 4)

# save stats
bStats = file(dirOut+"/backoffC1C2C3C4"+'.stats', 'w')

bStats.write("Number of c1Grams4: %d\n" % len(c1Grams4))
bStats.write("Number of c1Grams3: %d\n" % len(c1Grams3))
bStats.write("Number of c1Grams2: %d\n" % len(c1Grams2))
bStats.write("Number of c1Grams1: %d\n" % len(c1Grams1))
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

# save the cardinality of bucketing of C1C2C3C4
### !!! remeber you are rewriting the file because you clean the file
##print("I am rewriting " + dirOut + "/data_constants")
##
##file = open(dirOut + "/data_constants", "w")
##file.write("\n% the cardinality should be CONCEPT_CARD^DEPTH_OF_STACK, but I know that the stack values are sparse\n")
##file.write("#define WORD_BUCKET_C1C2C3C4_CARD     %d\n" % len(histories))
##file.write("#define JOINT_FA_C1C2C3C4_CARD   %d\n" % len(c1Grams))
##file.close()

if verbose:
    print("-------------------------------------------------")
    print("Finish")

