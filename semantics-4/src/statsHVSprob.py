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
import heapq
from operator import *

import toolkit
from lexMap import *
from observation import *
import gmtk

##############################################################################
##############################################################################

dirIn = '/home/filip/cued/ehvs/semantics-4/build/test/gen/scale'

conceptFileName = dirIn + "/../../maps/concept.map"
wordFileName = dirIn + "/../../maps/s1.map"

def usage():
    print("""
    Usage:   statsHVSprob.py [options] 
    
    Description:
             It reads dcpts.out file and print the c1GivenC2 probs and s1GivenC1 probs.
             
             
    Options: 
             -h                 : print this help message and exit
             -v                 : produce verbose output
             --conceptMap=FILE  : the concept map file name {%s}
             --wordMap=FILE     : the word map file name {%s}
    """ % (conceptFileName, wordFileName))
    
###################################################################################################
###################################################################################################

try:
    opts, args = getopt.gnu_getopt(sys.argv[1:], "hv", 
        ["conceptMap=", 
         "wordMap="])
         
except getopt.GetoptError, exc:
    print("ERROR: " + exc.msg)
    usage()
    sys.exit(2)

verbose = True

for o, a in opts:
    if o == "-h":
        usage()
        sys.exit()
    elif o == "-v":
        verbose = True
    elif o == "--conceptMap":
        conceptFileName = a
    elif o == "--wordMap":
        wordFileName = a
        

if verbose:
    print("Start")
    print("-------------------------------------------------")

conceptMap = LexMap().read(conceptFileName)
wordMap = LexMap().read(wordFileName)

concepts = conceptMap.keys()
concepts.sort(gmtk.mapCmp)

rConceptMap = conceptMap.reverse()
rWordMap = wordMap.reverse()

pushGivenC1 = gmtk.readDcptBigram(dirIn+'/dcpts.out', 'pushGivenC1')

for eachConcept in concepts:
    yGivenEachConcept =  pushGivenC1[int(conceptMap[eachConcept])]
    
    yGivenEachConcept = dict(zip(range(len(yGivenEachConcept)), yGivenEachConcept))
    yGivenEachConcept = heapq.nlargest(10, yGivenEachConcept.iteritems(), itemgetter(1))

    print eachConcept
    
    for k, v in yGivenEachConcept:
        if v > 1e-10:
            print 'P_push(%20s|%15s) = %.20f' % (str(k), eachConcept, v)

concept1GivenC2 = gmtk.readDcptBigram(dirIn+'/dcpts.out', 'concept1GivenC2')
# concept1GivenC2[x][y] = P(y|x)

for eachConcept in concepts:
    yGivenEachConcept =  concept1GivenC2[int(conceptMap[eachConcept])]
    
    yGivenEachConcept = dict(zip(range(len(yGivenEachConcept)), yGivenEachConcept))
    yGivenEachConcept = heapq.nlargest(10, yGivenEachConcept.iteritems(), itemgetter(1))

    print eachConcept
    
    for k, v in yGivenEachConcept:
        if v > 1e-10:
            print 'P(%20s|%15s) = %.20f' % (rConceptMap[str(k)], eachConcept, v)

#print concept1GivenC2

s1GivenC1 = gmtk.readDcptBigram(dirIn+'/dcpts.out', 's1GivenC1')

for eachConcept in concepts:
    yGivenEachConcept =  s1GivenC1[int(conceptMap[eachConcept])]
    
    yGivenEachConcept = dict(zip(range(len(yGivenEachConcept)), yGivenEachConcept))
    yGivenEachConcept = heapq.nlargest(10, yGivenEachConcept.iteritems(), itemgetter(1))

    print eachConcept
    
    for k, v in yGivenEachConcept:
        if v > 1e-10:
            print 'P(%20s|%15s) = %.20f' % (rWordMap[str(k)], eachConcept, v)


if verbose:
    print("-------------------------------------------------")
    print("Finish")
