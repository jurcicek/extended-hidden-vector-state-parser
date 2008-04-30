#!//usr/bin/python
# -*-  coding: UTF-8 -*-

import os
import getopt
import glob
from xml.dom import minidom
import re
import gmtk
from hiddenObservation import *
from lexMap import *

######################################################################################################
######################################################################################################

dirIn = "../data/train/ho"
dirOut = "../data/train"

conceptFileName = "../data/train/concept.map" 
wordFileName = "../data/train/word.map"

def usage():
    print("""
    Usage:   genConcept1GivenC2C3C4.py [options] 
    
    Description:
             This script generates:
                1) a DT that maps C2, C3, and C4 into one diminesion
                2) a DPMF that holds probability values for all C1
                3) a SPMF that maps values from the DT 1) to the DPMF
                4) it does the same for linear smoothing (for smaller dimensions)
             
    Options: 
             -h                      : print this help message and exit
             -v                      : produce verbose output
             --dirIn=DIR             : the input directory where *.hddn files are {%s}
             --dirOut=DIR            : the output directory where to put all output files {%s}
             --conceptMap=FILE       : the concept map file name {%s}
             --wordMap=FILE          : the word map file name {%s} """ 
             % (dirIn,
                dirOut, 
                conceptFileName, 
                wordFileName))

###################################################################################################
###################################################################################################

try:
    opts, args = getopt.gnu_getopt(sys.argv[1:], "hv", 
        ["dirIn=", 
        "dirOut=", 
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
    elif o == "--dirIn":
        dirIn = a
    elif o == "--dirOut":
        dirOut = a
    elif o == "--conceptMap":
        conceptFileName = a
    elif o == "--wordMap":
        wordFileName = a

list = glob.glob(dirIn + "/*.hddn")
list.sort()

if verbose:
    print("Start")
    print("-------------------------------------------------")

    print("Generating concept1GivenC2C3C4.* files.")

conceptMap = LexMap().read(conceptFileName)
wordMap = LexMap().read(wordFileName)
conceptCard = len(conceptMap)
wordCard = len(wordMap)

dt4 = {}
dt3 = {}
for fileName in list:
    if verbose:
        print("Processing file: " + fileName)
    
    ho = HiddenObservation().read(fileName)
    ho.collectConceptsC1C2C3C4(dt4)
    ho.collectConceptsC1C2C3(dt3)

##############################################################################
# save quatrograms
numberOfSpmfs = gmtk.saveDt(dirOut, "concept1GivenC2C3C4", dt4, 3)

gmtk.saveCollection(dirOut, "concept1GivenC2C3C4", numberOfSpmfs)
gmtk.saveSpmfs(dirOut, "concept1GivenC2C3C4", numberOfSpmfs, conceptCard)
gmtk.saveDpmfsConcept(dirOut, "concept1GivenC2C3C4", numberOfSpmfs, conceptCard, type="c1")

##############################################################################
# save trigrams
numberOfSpmfs = gmtk.saveDt(dirOut, "concept1GivenC2C3", dt3, 2)

gmtk.saveCollection(dirOut, "concept1GivenC2C3", numberOfSpmfs)
gmtk.saveSpmfs(dirOut, "concept1GivenC2C3", numberOfSpmfs, conceptCard)

# do not generate dpmfs because it will be created during smoothing


if verbose:
    print("-------------------------------------------------")
    print("Finish")
    