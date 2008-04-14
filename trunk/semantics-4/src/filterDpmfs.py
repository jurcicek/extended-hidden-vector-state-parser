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

dpmfsFileName = "../gen/dpmfs.out"
dpmfsFileNameFltrd = "../gen/dpmfs.out.fltrd"

def usage():
    print("""
    Usage:   filterDpmfs.py [options] 
    
    Description:
             This script remove all unnecessary variables from dpmfs file.
             
    Options: 
             -h                          : print this help message and exit
             -v                          : produce verbose output
             --dpmfsFileName=FILE        : the file with sparse CPTs {%s}
             --dpmfsFileNameFltrd=FILE   : the output filtered file with sparse CPTs {%s}""" 
             % (dpmfsFileName,
                dpmfsFileNameFltrd))

###################################################################################################
###################################################################################################

def testDpmf(each):
    if each.startswith("popGivenC1C2C3C4"):
        return True
    if each.startswith("pushGivenC1C2C3C4"):
        return True
    if each.startswith("s1GivenC1C2C3C4"):
        return True
    if each.startswith("s2GivenC1C2C3C4"):
        return True
    if each.startswith("s3GivenC1C2C3C4"):
        return True


###################################################################################################
###################################################################################################

###################################################################################################
###################################################################################################

###################################################################################################
###################################################################################################

try:
    opts, args = getopt.gnu_getopt(sys.argv[1:], "hv", 
        ["dpmfsFileName=",
        "dpmfsFileNameFltrd="])
         
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
    elif o == "--dpmfsFileName":
        dpmfsFileName = a
    elif o == "--dpmfsFileNameFltrd":
        dpmfsFileNameFltrd = a

if verbose:
    print("Start")
    print("-------------------------------------------------")

inFile = open(dpmfsFileName, "r")
outFile = open(dpmfsFileNameFltrd, "w")
lines = inFile.readlines()

counter = 0
for each in lines:
    if len(each) > 0 and each[0].isalpha() and not testDpmf(each):
        counter += 1

outFile.write("% dense PMFs\n")
outFile.write("%d\n" % counter)
counter = 0
for each in lines:
    if len(each) > 0 and each[0].isalpha() and not testDpmf(each): 
        outFile.write("%d\n" % counter)
        outFile.write(each)
        counter += 1
        
outFile.write("\n")
        
inFile.close()
outFile.close()

if verbose:
    print("-------------------------------------------------")
    print("Finish")

    
