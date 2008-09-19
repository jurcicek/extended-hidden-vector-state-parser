#!//usr/bin/python
# -*-  coding: UTF-8 -*-

import os
import glob
import getopt
from xml.dom import minidom
import codecs
import os.path
import re
import toolkit
from hiddenObservation import *
from lexMap import *

######################################################################################################
######################################################################################################

def saveHiddenDts(dts, dtsName, hidden):
    dtsFile = dts.append(dtsName + " % DT name\n")
    dtsFile = dts.append("1 % number of parents\n")
    
    stackTransCounter = 0

    dts.append("0\t%d" % (len(hidden)+1))
    for i in range(len(hidden)):
        dts.append("\t%d" % i)
    dts.append("\tdefault\n")
    
    for hv in hidden:
        dts.append("\t-1\t")

        if hv[0] != wordMap["_empty_"]:
            dts.append("1")
        else:
            dts.append("0")
        dts.append("\n")

    dts.append("\t-1\t0\n")
        
######################################################################################################
######################################################################################################

dirIn = "../data/train/ho"
dirOut = "../data/train"

conceptFileName = "../data/train/concept.map" 
wordFileName = "../data/train/word.map"

def usage():
    print("""
    Usage:   genHiddenObservationGivenWC1C2C3C4Stc.py [options] 
    
    Description:
             This script generates DTs (decision trees) for GMTK that constrain   
             what values are allowed to be in the stack. 
             
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

    print("Generating observation files and hidden files.")

conceptMap = LexMap().read(conceptFileName)
wordMap = LexMap().read(wordFileName)

dts = []
i = 0
for fileName in list:
    if verbose:
        print("Processing file: " + fileName)

    dtName = os.path.splitext(os.path.basename(fileName))[0] + "_st"
    
    dts.append("%d %% DT number\n" % (i))
    i += 1

    hidden = HiddenObservation().read(fileName)
    saveHiddenDts(dts, dtName, hidden)
    dts.append("\n")

dts.insert(0, "%d %% Number of DTs\n\n" % (i))

dtsFile = codecs.open(dirOut + "/stackTypeGivenStc.dts", "w", "utf-8")

for line in dts:
    dtsFile.write(line)
    
dtsFile.close()
    
if verbose:
    print("-------------------------------------------------")
    print("Finish")
    