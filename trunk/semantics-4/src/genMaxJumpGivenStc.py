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

        dts.append(hv[5])
        
        dts.append("\n")

    dts.append("\t-1\t0\n")
        
######################################################################################################
######################################################################################################

dirIn = "../data/train_txt/ho"
dirOut = "../data/train_txt"

def usage():
    print("""
    Usage:   genMaxJumpGivenStc.py [options] 
    
    Description:
             This script generates DTs (decision trees) for GMTK that constrain   
             what values are allowed to be in the stack. 
             
    Options: 
             -h                      : print this help message and exit
             -v                      : produce verbose output
             --dirIn=DIR             : the input directory where *.hddn files are {%s}
             --dirOut=DIR            : the output directory where to put all output files {%s}
             """ 
             % (dirIn,
                dirOut))

###################################################################################################
###################################################################################################

try:
    opts, args = getopt.gnu_getopt(sys.argv[1:], "hv", 
        ["dirIn=", 
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
    elif o == "--dirIn":
        dirIn = a
    elif o == "--dirOut":
        dirOut = a

list = glob.glob(dirIn + "/*.hddn")
list.sort()
    
if verbose:
    print("Start")
    print("-------------------------------------------------")

    print("Generating observation files and hidden files.")

dts = []
i = 0
for fileName in list:
    if verbose:
        print("Processing file: " + fileName)

    dtName = os.path.splitext(os.path.basename(fileName))[0] + "_mj"
    
    dts.append("%d %% DT number\n" % (i))
    i += 1

    hidden = HiddenObservation().read(fileName)
    saveHiddenDts(dts, dtName, hidden)
    dts.append("\n")

dts.insert(0, "%d %% Number of DTs\n\n" % (i))

dtsFile = codecs.open(dirOut + "/maxJumpGivenStc.dts", "w", "utf-8")

for line in dts:
    dtsFile.write(line)
    
dtsFile.close()
    
if verbose:
    print("-------------------------------------------------")
    print("Finish")
    
