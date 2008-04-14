#!//usr/bin/python
# -*-  coding: UTF-8 -*-

import os
import glob
import getopt
from xml.dom import minidom
import re
import gmtk
from hiddenObservation import *
from lexMap import *

###################################################################################################
###################################################################################################

dirIn = "../data/train/ho"
dirOut = "../data/train"

conceptFileName = "../data/train/concept.map" 
wordFileName = "../data/train/word.map"

popCard = 5

def usage():
    print("""
    Usage:   genPopGivenC1C2C3C4.py [options] 
    
    Description:
             This script generates:
                1) a DT that maps C1, C2, C3, and C3 into one diminesion
                2) a DPMF that holds probability values for all pops
                3) a SPMF that maps values from the DT 1) to the DPMF
             
    Options: 
             -h                      : print this help message and exit
             -v                      : produce verbose output
             --popCard=NUMBER        : the cardinality of the pop hidden variable {%d}
             --dirIn=DIR             : the input directory where *.hddn files are {%s}
             --dirOut=DIR            : the output directory where to put all output files {%s}
             --conceptMap=FILE       : the concept map file name {%s}
             --wordMap=FILE          : the word map file name {%s} """ 
             % (popCard,
                dirIn,
                dirOut, 
                conceptFileName, 
                wordFileName))

###################################################################################################
###################################################################################################

try:
    opts, args = getopt.gnu_getopt(sys.argv[1:], "hv", 
        ["popCard=",
        "dirIn=", 
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
    elif o == "--popCard":
        popCard = long(a)
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

    print("Generating popGivenC1C2C3C4.* files.")

conceptMap = LexMap().read(conceptFileName)
wordMap = LexMap().read(wordFileName)

dt4 = {}
dt3 = {}
dt2 = {}
for fileName in list:
    if verbose:
        print("Processing file: " + fileName)
    
    ho = HiddenObservation().read(fileName)
    ho.collectConceptsC1C2C3C4(dt4)
    ho.collectConceptsC1C2C3(dt3)
    ho.collectConceptsC1C2(dt2)

##############################################################################
# save pentagrams
numberOfSpmfs = gmtk.saveDt(dirOut, "popGivenC1C2C3C4", dt4)

gmtk.saveCollection(dirOut, "popGivenC1C2C3C4", numberOfSpmfs)
gmtk.saveSpmfs(dirOut, "popGivenC1C2C3C4", numberOfSpmfs, popCard)
gmtk.saveDpmfsPopPush(dirOut, "popGivenC1C2C3C4", numberOfSpmfs, popCard)
##############################################################################
# save quatrograms
numberOfSpmfs = gmtk.saveDt(dirOut, "popGivenC1C2C3", dt3, 3)

gmtk.saveCollection(dirOut, "popGivenC1C2C3", numberOfSpmfs)
gmtk.saveSpmfs(dirOut, "popGivenC1C2C3", numberOfSpmfs, popCard)

# do not generate dpmfs because it will be created during smoothing

##############################################################################
# save trigrams
numberOfSpmfs = gmtk.saveDt(dirOut, "popGivenC1C2", dt2, 2)

gmtk.saveCollection(dirOut, "popGivenC1C2", numberOfSpmfs)
gmtk.saveSpmfs(dirOut, "popGivenC1C2", numberOfSpmfs, popCard)

# do not generate dpmfs because it will be created during smoothing

if verbose:
    print("-------------------------------------------------")
    print("Finish")
    
