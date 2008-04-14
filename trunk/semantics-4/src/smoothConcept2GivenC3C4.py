#!//usr/bin/python
# -*-  coding: UTF-8 -*-

import os
import glob
import getopt
from xml.dom import minidom
import re
import toolkit

from hiddenObservation import *
from lexMap import *
import gmtk

###################################################################################################
###################################################################################################

dirOut = "../gen"

dcptsFileName = "../gen/dcpts.out"
dpmfsFileName = "../gen/dpmfs.out"
wordDtFileName = "../data/train/wordGivenC1C2C3C4.dt"
concept2DtFileName = "../data/train/concept2GivenC3C4.dt"

conceptFileName = "../data/train/concept.map" 
wordFileName = "../data/train/word.map"

def usage():
    print("""
    Usage:   smoothConcept2GivenC2C3C4.py [options] 
    
    Description:
             This script smoothes concept2 conditional probability.
             
    Options: 
             -h                          : print this help message and exit
             -v                          : produce verbose output
             --dirOut=DIR                : the output directory where to put all output files {%s} 
             --dcptsFileName=FILE        : the file with dense CPTs {%s}
             --dpmfsFileName=FILE        : the file with sparse CPTs {%s}
             --wordDtFileName=FILE       : the file with word decision tree {%s} 
             --concept2DtFileName=FILE   : the file with concept2 decision tree {%s} 
             --conceptMap=FILE           : the concept map file name {%s}
             --wordMap=FILE              : the word map file name {%s} """ 
             % (dirOut,
                dcptsFileName,
                dpmfsFileName,
                wordDtFileName,
                concept2DtFileName,
                conceptFileName, 
                wordFileName))

###################################################################################################
###################################################################################################

try:
    opts, args = getopt.gnu_getopt(sys.argv[1:], "hv", 
        ["dirOut=",
        "dcptsFileName=",
        "dpmfsFileName=",
        "wordDtFileName=",
        "concept2DtFileName=",
        "conceptMap=",
        "wordMap="])
         
except getopt.GetoptError, exc:
    print("ERROR: " + exc.msg)
    usage()
    sys.exit(2)

verbose = None

for o, a in opts:
    if o == "-h":
        usage()
        sys.exit()
    elif o == "-v":
        verbose = True
    elif o == "--dirOut":
        dirOut = a
    elif o == "--dcptsFileName":
        dcptsFileName = a
    elif o == "--dpmfsFileName":
        dpmfsFileName = a
    elif o == "--wordDtFileName":
        wordDtFileName = a
    elif o == "--concept2DtFileName":
        concept2DtFileName = a
    elif o == "--conceptMap":
        conceptFileName = a
    elif o == "--wordMap":
        wordFileName = a
    
if verbose:
    print("Start")
    print("-------------------------------------------------")

    print("Smoothing concept1GivenC2C3C4.")

conceptMap = LexMap().read(conceptFileName)
wordMap = LexMap().read(wordFileName)
conceptCard = len(conceptMap)
wordCard = len(wordMap)

jointDtC1C2C3C4 = gmtk.readDt(wordDtFileName)
jointDcptC1C2C3C4 = gmtk.readDcpt(dcptsFileName, "jointProbC1C2C3C4")
assert toolkit.testProb(jointDcptC1C2C3C4), "Sum of probabilities should be always 1."

jointProbC1C2C3C4 = gmtk.combineDtDcpt1(jointDtC1C2C3C4, jointDcptC1C2C3C4) 
jointProbC2C3C4 = jointProbC1C2C3C4.marginalize([1, 2, 3])

### waste of time :-)
##concept1DtC2C3C4 = gmtk.readDt(concept1DtFileName)
##concept1DpmfC2C3C4 = gmtk.readDpmf(dpmfsFileName, "concept1GivenC2C3C4")
##assert toolkit.testProb2(concept1DpmfC2C3C4), "Sum of probabilities should be always 1."
##
##concept1GivenC2C3C4 = gmtk.combineDtDcpt2(concept1DtC2C3C4, concept1DpmfC2C3C4)
##concept1GivenC2C3C4X = jointProbC1C2C3C4.conditionalize([1, 2, 3])
##
##if verbose:
##    print "Orig : Probs %4d : Parents %4d" % (len(concept1GivenC2C3C4.vectList()), len(concept1GivenC2C3C4.vectSubList([1, 2, 3])))
##    print "Comp : Probs %4d : Parents %4d" % (len(concept1GivenC2C3C4X.vectList()), len(concept1GivenC2C3C4X.vectSubList([1, 2, 3])))
##
##gmtk.saveDpmfsProbs(dirOut, "concept1GivenC2C3C4", len(concept1GivenC2C3C4.vectSubList([1, 2, 3])), conceptCard, concept1GivenC2C3C4)
##gmtk.saveDpmfsProbs(dirOut, "concept1GivenC2C3C4X", len(concept1GivenC2C3C4X.vectSubList([1, 2, 3])), conceptCard, concept1GivenC2C3C4X)

##############################################################################
# save bigrams as CPT
jointProbC2C3 = jointProbC2C3C4.marginalize([0, 1])
concept2GivenC3 = jointProbC2C3.conditionalize([1])

# in case of conditioning by _SINK_ I have to enable to generate _SINK_ concept only
# otherwise I would see _SINK_ concept in the stack
concept2GivenC3.setValue([int(conceptMap["_SINK_"]), int(conceptMap["_SINK_"])], 1)
# do the same for _DUMMY_
concept2GivenC3.setValue([int(conceptMap["_SINK_"]), int(conceptMap["_DUMMY_"])], 1)

gmtk.saveDcptBigram(dirOut, "concept2GivenC3", conceptCard, conceptCard, concept2GivenC3)

##############################################################################
# save unigrams as CPT
concept2Unigram = jointProbC2C3.marginalize([0])
gmtk.saveDcptUnigram(dirOut, "concept2Unigram", conceptCard, concept2Unigram)

################################################################################
### save zerograms as CPT
##gmtk.saveDcptZerogram(dirOut, "concept1Zerogram", conceptCard)

if verbose:
    print("-------------------------------------------------")
    print("Finish")
    
