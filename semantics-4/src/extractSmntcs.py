#!//usr/bin/python
# -*-  coding: UTF-8 -*-

import sys
import getopt
import os
from os.path import *
import glob
from xml.dom import minidom
import re
import struct
import codecs
from StringIO import StringIO

import toolkit
from lexMap import *
from observation import *
from semantics import *

###################################################################################################
###################################################################################################

fileNamePrefix = "../data/train"

dirCmb = "../dcd_hldt/push2/dcd"
#dirCmb = "../fa_hlft/dcd"
dirSmntcs = "../dcd_hldt/push2"
#dirSmntcs = "../fa_hldt"
ext = "cmb"
force = False
outputMlf = "../dcd_hldt/push2/semantics.mlf"
lemmatized = False

conceptFileName = fileNamePrefix + "/" + "concept.map"
wordFileName = fileNamePrefix + "/" + "word.map"

def usage():
    print("""
    Usage:   extractSmntcs.py [options] 
    
    Description:
             Extracts semantics from *.cmb files into the format that can be found in the original dialogue
             annotation. Basically, it compresses the information that is in *.cmb files.
    
    Options: 
             -h                 : print this help message and exit
             -v                 : produce verbose output
             --dirCmb=DIR       : input directory for *.cmb files {%s}
             --dirSmntcs=DIR    : input directory for *.smntcs coresponding to dcd files {%s}
             --outputMlf=FILE   : the file name of an output MLF file {%s}
             --lemmatized       : if the output files will be lemmatized {%s}
    """ % (dirCmb, dirSmntcs, outputMlf, lemmatized))
    
###################################################################################################
###################################################################################################

try:
    opts, args = getopt.gnu_getopt(sys.argv[1:], "hv", 
        ["dirCmb=", 
         "dirSmntcs=", 
         "outputMlf=",
         "lemmatized"])
         
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
    elif o == "--dirCmb":
        dirCmb = a
    elif o == "--dirSmntcs":
        dirSmntcs = a
    elif o == "--outputMlf":
        outputMlf = a
    elif o == "--lemmatized":
        lemmatized = True
        
lst = glob.glob(dirCmb + "/*." + ext)
#lst = lst[:10]
lst.sort()

if verbose:
    print("Start")
    print("-------------------------------------------------")
    print("Extracting SMNTCS files from %d files." % len(lst))

if lemmatized:
    outputMlfFile = StringIO()
    outputPush2MlfFile = StringIO()
    outputMlfFileLab = StringIO()
    outputTrnFile = StringIO()
    outputPtbFile = StringIO()
else:
    outputMlfFile = codecs.open(outputMlf, "w", "UTF-8")
    outputPush2MlfFile = codecs.open(outputMlf + ".push2.mlf", "w", "UTF-8")
    outputMlfFileLab = codecs.open(outputMlf + ".dcd", "w", "UTF-8")
    outputTrnFile = codecs.open(outputMlf + ".trn", "w", "UTF-8")
    outputPtbFile = codecs.open(outputMlf + ".ptb", "w", "UTF-8")


outputMlfFileSmntcs = codecs.open(outputMlf + ".smntcs", "w", "UTF-8")
outputPush2MlfFileSmntcs = codecs.open(outputMlf + ".push2.smntcs", "w", "UTF-8")

outputMlfFile.write("#!MLF!#\n")
outputPush2MlfFile.write("#!MLF!#\n")
outputMlfFileLab.write("#!MLF!#\n")
outputMlfFileSmntcs.write("#!MLF!#\n")
outputPush2MlfFileSmntcs.write("#!MLF!#\n")


trn_id = 0

for fileName in lst:
    push2 = False
    
    if verbose:
        print("Reading file: " + fileName)

    smntcs = readSemanticsFromCMBFile(fileName, lemmatized=lemmatized)
    smntcsWithoutText = removeTextFromSemantics(smntcs)
    try:
        Semantics('id', smntcsWithoutText, 'x')
    except ValueError:
        smntcs = ""
        smntcsWithoutText = ""
    

    if re.search(r'[A-Z]\([A-Z]', smntcs) != None:
        push2 = True
    if re.search(r'\), [a-z]', smntcs) != None:
        push2 = True

    smntcsWTSplit = splitSmntcsToMlf(smntcsWithoutText)
    
    idLab = splitext(splitext(basename(fileName))[0])[0]
    outputMlfFile.write('"*/' + idLab + '.rec"\n')
    if push2:
        outputPush2MlfFile.write('"*/' + idLab + '.rec"\n')

    outputMlfFileLab.write("#######################################\n")
    outputMlfFileLab.write('"*/' + idLab + '.lab"\n')
    outputMlfFileLab.write("#######################################\n")

    for each in smntcsWTSplit:
        outputMlfFile.write(each + "\n")
        if push2:
            outputPush2MlfFile.write(each + "\n")
            
        outputMlfFileLab.write(each + "\n")
        if each != ".":
            if each == "(":
                outputTrnFile.write("LEFT" + " ")
            elif each == ")":
                outputTrnFile.write("RIGHT" + " ")
            else:
                outputTrnFile.write(each + " ")
                
    try:
        outputPtbFile.write(Semantics('id', smntcs.encode('ascii','replace'), 'x').getPTBSemantics() + '\n')
    except ValueError:
        outputPtbFile.write("(TOP x)\n")
    
    outputTrnFile.write("(spk1_%.5d)\n" %trn_id)
    trn_id += 1 
    
    outputMlfFileSmntcs.write('"*/' + idLab + '.rec"\n')
    outputMlfFileSmntcs.write(smntcs + "\n")
    outputMlfFileSmntcs.write(".\n")

    if push2:
        outputPush2MlfFileSmntcs.write('"*/' + idLab + '.rec"\n')
        outputPush2MlfFileSmntcs.write(smntcs + "\n")
        outputPush2MlfFileSmntcs.write(".\n")

outputMlfFile.close()
outputPush2MlfFile.close()
outputMlfFileLab.close()
outputTrnFile.close()
outputPtbFile.close()

if verbose:
    print("-------------------------------------------------")
    print("Finish")

