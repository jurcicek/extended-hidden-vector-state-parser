#!//usr/bin/python
# -*-  coding: UTF-8 -*-

import os
import glob
import getopt
from xml.dom import minidom
from hiddenObservation import *
import re
import gmtk
from lexMap import *

###################################################################################################
###################################################################################################

dirOut = "../data/train"
spmfsFile = "../data/train/wordGivenC1C2C3C4.spmfs"

def usage():
    print("""
    Usage:   genJointProbC1C2C3C4.py [options] 
    
    Description:
             This script generates a DPMF that holds probability values for different tuples
             of C1, C2, C3, C4.
             
    Options: 
             -h                : print this help message and exit
             -v                : produce verbose output
             --spmfsFile=file  : the file containing the cardinality of the joint C1, C2, C3, C4 variable {%s}
             --dirOut=DIR      : the output directory where to put all output files {%s} """
             % (spmfsFile,
                dirOut))

###################################################################################################
###################################################################################################

try:
    opts, args = getopt.gnu_getopt(sys.argv[1:], "hv", 
        ["spmfsFile=",
        "dirOut="])
         
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
    elif o == "--spmfsFile":
        spmfsFile = a
    elif o == "--dirOut":
        dirOut = a

if verbose:
    print("Start")
    print("-------------------------------------------------")

    print("Generating jointProbC1C2C3C4.* files.")

spmf = open(spmfsFile, "r")
spmfLine = spmf.readline()
jointC1C2C3C4Card = int(spmfLine.split(" ")[0])
spmf.close()

if verbose:
    print("Cardinality of C1C2C3C4 is %d" % jointC1C2C3C4Card)

gmtk.saveDcptZerogram(dirOut, "jointProbC1C2C3C4", jointC1C2C3C4Card)

if verbose:
    print("-------------------------------------------------")
    print("Finish")
    
