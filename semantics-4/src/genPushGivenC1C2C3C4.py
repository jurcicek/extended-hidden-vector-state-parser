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

pushCard = 5
maxPush = 1

def usage():
    print("""
    Usage:   genPushGivenC1C2C3C4.py [options] 
    
    Description:
             This script generates:
                1) a DT that maps C1, C2, C3, and C3 into one diminesion
                2) a DPMF that holds probability values for all pushs
                3) a SPMF that maps values from the DT 1) to the DPMF
             
    Options: 
             -h                 : print this help message and exit
             -v                 : produce verbose output
             --pushCard=NUMBER  : the cardinality of the push hidden variable {%d}
             --maxPush=NUMBER   : the maximum of inserted concept into the stachk {1,2} {%d}
             --dirIn=DIR        : the input directory where *.hddn files are {%s}
             --dirOut=DIR       : the output directory where to put all output files {%s}
             --conceptMap=FILE  : the concept map file name {%s}
             --wordMap=FILE     : the word map file name {%s} """ 
             % (pushCard,
                maxPush,
                dirIn,
                dirOut, 
                conceptFileName, 
                wordFileName))

###################################################################################################
###################################################################################################

try:
    opts, args = getopt.gnu_getopt(sys.argv[1:], "hv", 
        ["pushCard=",
        "maxPush=",
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
    elif o == "--pushCard":
        pushCard = long(a)
    elif o == "--maxPush":
        maxPush = long(a)
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

    print("Generating pushGivenC1C2C3C4.* files.")

conceptMap = LexMap().read(conceptFileName)
wordMap = LexMap().read(wordFileName)

dt4 = {}
dt3 = {}
dt2 = {}
for fileName in list:
    if verbose:
        print("Processing file: " + fileName)
    
    HiddenObservation().read(fileName).collectConceptsC1C2C3C4(dt4)
    HiddenObservation().read(fileName).collectConceptsC1C2C3(dt3)
    HiddenObservation().read(fileName).collectConceptsC1C2(dt2)

##############################################################################
# save pentagrams
numberOfSpmfs = gmtk.saveDt(dirOut, "pushGivenC1C2C3C4", dt4)

gmtk.saveCollection(dirOut, "pushGivenC1C2C3C4", numberOfSpmfs)
gmtk.saveSpmfs(dirOut, "pushGivenC1C2C3C4", numberOfSpmfs, pushCard)

if maxPush == 1: 
    v = [44,43,0,0,0]
else:    
    v = [44,43,42,0,0]
gmtk.saveDpmfsPopPush(dirOut, "pushGivenC1C2C3C4", numberOfSpmfs, pushCard, v)

##############################################################################
# save quatrograms
numberOfSpmfs = gmtk.saveDt(dirOut, "pushGivenC1C2C3", dt3, 3)

gmtk.saveCollection(dirOut, "pushGivenC1C2C3", numberOfSpmfs)
gmtk.saveSpmfs(dirOut, "pushGivenC1C2C3", numberOfSpmfs, pushCard)

# do not generate dpmfs because it will be created during smoothing

##############################################################################
# save trigrams
numberOfSpmfs = gmtk.saveDt(dirOut, "pushGivenC1C2", dt2, 2)

gmtk.saveCollection(dirOut, "pushGivenC1C2", numberOfSpmfs)
gmtk.saveSpmfs(dirOut, "pushGivenC1C2", numberOfSpmfs, pushCard)

# do not generate dpmfs because it will be created during smoothing

if verbose:
    print("-------------------------------------------------")
    print("Finish")
    
