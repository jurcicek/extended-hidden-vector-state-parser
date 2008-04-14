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

popCard = 5
penalty = 10.0

dcptsFileName = "../gen/dcpts.out"
dpmfsFileName = "../gen/dpmfs.out"
popDtFileName = "../data/train/popGivenC1C2C3C4.dt"

conceptFileName = "../data/train/concept.map" 
wordFileName = "../data/train/word.map"

def usage():
    print("""
    Usage:   smoothPopGivenC1C2C3C4.py [options] 
    
    Description:
             This script generates a DPMF that holds probability values for different tuples
             of C1, C2, C3, C4.
             
    Options: 
             -h                      : print this help message and exit
             -v                      : produce verbose output
             --popCard=NUMBER        : the cardinality of the pop hidden variable {%d}
             --penalty=NUMBER        : the penalty that is used tu multiply probability for staying at current state {%e}
             --dirOut=DIR            : the output directory where to put all output files {%s} 
             --dcptsFileName=FILE    : the file with dense CPTs {%s}
             --dpmfsFileName=FILE    : the file with sparse CPTs {%s}
             --popDtFileName=FILE    : the file with word decision tree {%s} 
             --conceptMap=FILE       : the concept map file name {%s}""" 
             % (popCard,
                penalty,
                dirOut,
                dcptsFileName,
                dpmfsFileName,
                popDtFileName,
                conceptFileName))

###################################################################################################
###################################################################################################

try:
    opts, args = getopt.gnu_getopt(sys.argv[1:], "hv", 
        ["dirOut=",
        "dcptsFileName=",
        "dpmfsFileName=",
        "popDtFileName=",
        "conceptMap=",
        "penalty=",
        "popCard="])
         
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
    elif o == "--dcptsFileName":
        dcptsFileName = a
    elif o == "--dpmfsFileName":
        dpmfsFileName = a
    elif o == "--popDtFileName":
        popDtFileName = a
    elif o == "--conceptMap":
        conceptFileName = a
    elif o == "--popCard":
        popCard = int(a)
    elif o == "--penalty":
        penalty = float(a)

if verbose:
    print("Start")
    print("-------------------------------------------------")

    print("Smoothing popGivenC1C2C3C4.")

conceptMap = LexMap().read(conceptFileName)
conceptCard = len(conceptMap)

# read P(C1, C2, C3, C4)
##############################################################################
jointDtC1C2C3C4 = gmtk.readDt(popDtFileName)
jointDcptC1C2C3C4 = gmtk.readDcpt(dcptsFileName, "jointProbC1C2C3C4")
assert toolkit.testProb(jointDcptC1C2C3C4), "Sum of probabilities should be always 1."

jointProbC1C2C3C4 = gmtk.combineDtDcpt1(jointDtC1C2C3C4, jointDcptC1C2C3C4) 

# read P(W | C1, C2, C3, C4)
popDpmfC1C2C3C4 = gmtk.readDpmf(dpmfsFileName, "popGivenC1C2C3C4")
assert toolkit.testProb2(popDpmfC1C2C3C4), "Sum of probabilities should be always 1."

popGivenC1C2C3C4 = gmtk.combineDtDcpt2(jointDtC1C2C3C4, popDpmfC1C2C3C4)

#
# jointProbPC1C2C3C4 = popGivenC1C2C3C4 * jointProbC1C2C3C4
#

jointProbPC1C2C3C4 = popGivenC1C2C3C4.multiple([1, 2, 3, 4], jointProbC1C2C3C4)

##############################################################################
# save pentagrams
popGivenC1C2C3C4 = popGivenC1C2C3C4.insertPenalty(0, penalty, popCard)

gmtk.saveDpmfsProbs(dirOut, "popGivenC1C2C3C4", len(popGivenC1C2C3C4.vectSubList([1, 2, 3, 4])), popCard, popGivenC1C2C3C4, -penalty)

##############################################################################
# save quatrograms
jointProbPC1C2C3 = jointProbPC1C2C3C4.marginalize([0, 1, 2, 3])
popGivenC1C2C3 = jointProbPC1C2C3.conditionalize([1, 2, 3])
popGivenC1C2C3 = popGivenC1C2C3.insertPenalty(0, penalty, popCard)

gmtk.saveDpmfsProbs(dirOut, "popGivenC1C2C3", len(popGivenC1C2C3.vectSubList([1, 2, 3])), popCard, popGivenC1C2C3, -penalty)

##############################################################################
# save trigrams
jointProbPC1C2 = jointProbPC1C2C3.marginalize([0, 1, 2])
popGivenC1C2 = jointProbPC1C2.conditionalize([1, 2])
popGivenC1C2 = popGivenC1C2.insertPenalty(0, penalty, popCard)

gmtk.saveDpmfsProbs(dirOut, "popGivenC1C2", len(popGivenC1C2.vectSubList([1, 2])), popCard, popGivenC1C2, -penalty)

##############################################################################
# save bigrams as CPT
jointProbPC1 = jointProbPC1C2.marginalize([0, 1])
popGivenC1 = jointProbPC1.conditionalize([1])
popGivenC1 = popGivenC1.insertPenalty(0, penalty, popCard)

# in case of conditioning by _SINK_, I have to enable to delete all stack
popGivenC1.setValue([4, int(conceptMap["_SINK_"])], 1)

gmtk.saveDcptBigram(dirOut, "popGivenC1", popCard, conceptCard, popGivenC1)

##############################################################################
# save unigrams as CPT
popUnigram = jointProbPC1.marginalize([0])
popUnigram = popUnigram.insertPenalty(0, penalty, popCard)

gmtk.saveDcptUnigram(dirOut, "popUnigram", popCard, popUnigram)

if verbose:
    print("-------------------------------------------------")
    print("Finish")
    
