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

pushCard = 5
penalty = 10.0

dcptsFileName = "../gen/dcpts.out"
dpmfsFileName = "../gen/dpmfs.out"
pushDtFileName = "../data/train/pushGivenC1C2C3C4.dt"

conceptFileName = "../data/train/concept.map" 
wordFileName = "../data/train/word.map"

def usage():
    print("""
    Usage:   smoothPushGivenC1C2C3C4.py [options] 
    
    Description:
             This script generates a DPMF that holds probability values for different tuples
             of C1, C2, C3, C4.
             
    Options: 
             -h                      : print this help message and exit
             -v                      : produce verbose output
             --pushCard=NUMBER        : the cardinality of the push hidden variable {%d}
             --penalty=NUMBER        : the penalty that is used tu multiply probability for staying at current state {%e}
             --dirOut=DIR            : the output directory where to put all output files {%s} 
             --dcptsFileName=FILE    : the file with dense CPTs {%s}
             --dpmfsFileName=FILE    : the file with sparse CPTs {%s}
             --pushDtFileName=FILE    : the file with word decision tree {%s} 
             --conceptMap=FILE       : the concept map file name {%s}""" 
             % (pushCard,
                penalty,
                dirOut,
                dcptsFileName,
                dpmfsFileName,
                pushDtFileName,
                conceptFileName))

###################################################################################################
###################################################################################################

try:
    opts, args = getopt.gnu_getopt(sys.argv[1:], "hv", 
        ["dirOut=",
        "dcptsFileName=",
        "dpmfsFileName=",
        "pushDtFileName=",
        "conceptMap=",
        "penalty=",
        "pushCard="])
         
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
    elif o == "--pushDtFileName":
        pushDtFileName = a
    elif o == "--conceptMap":
        conceptFileName = a
    elif o == "--pushCard":
        pushCard = int(a)
    elif o == "--penalty":
        penalty = float(a)

if verbose:
    print("Start")
    print("-------------------------------------------------")

    print("Smoothing pushGivenC1C2C3C4.")

conceptMap = LexMap().read(conceptFileName)
conceptCard = len(conceptMap)

# read P(C1, C2, C3, C4)
##############################################################################
jointDtC1C2C3C4 = gmtk.readDt(pushDtFileName)
jointDcptC1C2C3C4 = gmtk.readDcpt(dcptsFileName, "jointProbC1C2C3C4")
assert toolkit.testProb(jointDcptC1C2C3C4), "Sum of probabilities should be always 1."

jointProbC1C2C3C4 = gmtk.combineDtDcpt1(jointDtC1C2C3C4, jointDcptC1C2C3C4) 

# read P(W | C1, C2, C3, C4)
pushDpmfC1C2C3C4 = gmtk.readDpmf(dpmfsFileName, "pushGivenC1C2C3C4")
assert toolkit.testProb2(pushDpmfC1C2C3C4), "Sum of probabilities should be always 1."

pushGivenC1C2C3C4 = gmtk.combineDtDcpt2(jointDtC1C2C3C4, pushDpmfC1C2C3C4)

#
# jointProbPC1C2C3C4 = pushGivenC1C2C3C4 * jointProbC1C2C3C4
#

jointProbPC1C2C3C4 = pushGivenC1C2C3C4.multiple([1, 2, 3, 4], jointProbC1C2C3C4)

##############################################################################
# save pentagrams
pushGivenC1C2C3C4 = pushGivenC1C2C3C4.insertPenalty(0, penalty, pushCard)

gmtk.saveDpmfsProbs(dirOut, "pushGivenC1C2C3C4", len(pushGivenC1C2C3C4.vectSubList([1, 2, 3, 4])), pushCard, pushGivenC1C2C3C4, -penalty)

##############################################################################
# save quatrograms
jointProbPC1C2C3 = jointProbPC1C2C3C4.marginalize([0, 1, 2, 3])
pushGivenC1C2C3 = jointProbPC1C2C3.conditionalize([1, 2, 3])
pushGivenC1C2C3 = pushGivenC1C2C3.insertPenalty(0, penalty, pushCard)

gmtk.saveDpmfsProbs(dirOut, "pushGivenC1C2C3", len(pushGivenC1C2C3.vectSubList([1, 2, 3])), pushCard, pushGivenC1C2C3, -penalty)

##############################################################################
# save trigrams
jointProbPC1C2 = jointProbPC1C2C3.marginalize([0, 1, 2])
pushGivenC1C2 = jointProbPC1C2.conditionalize([1, 2])
pushGivenC1C2 = pushGivenC1C2.insertPenalty(0, penalty, pushCard)

gmtk.saveDpmfsProbs(dirOut, "pushGivenC1C2", len(pushGivenC1C2.vectSubList([1, 2])), pushCard, pushGivenC1C2, -penalty)

##############################################################################
# save bigrams as CPT
jointProbPC1 = jointProbPC1C2.marginalize([0, 1])
pushGivenC1 = jointProbPC1.conditionalize([1])
pushGivenC1 = pushGivenC1.insertPenalty(0, penalty, pushCard)

# in case of conditioning by _SINK_, I have to enable to delete all stack
pushGivenC1.setValue([4, int(conceptMap["_SINK_"])], 1)

gmtk.saveDcptBigram(dirOut, "pushGivenC1", pushCard, conceptCard, pushGivenC1)

##############################################################################
# save unigrams as CPT
pushUnigram = jointProbPC1.marginalize([0])
pushUnigram = pushUnigram.insertPenalty(0, penalty, pushCard)

gmtk.saveDcptUnigram(dirOut, "pushUnigram", pushCard, pushUnigram)

if verbose:
    print("-------------------------------------------------")
    print("Finish")
    
