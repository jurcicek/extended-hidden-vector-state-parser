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

import toolkit
from lexMap import *
from observation import *

###################################################################################################
###################################################################################################

fileNamePrefix = "../data/train"

dirDcd = "../dcd_hldt/push2/dcd"
dirObs = "../data/heldout/ho"
fileDcd = ""
ext = "dcd"
force = False
conceptFileName = "../data/train/concept.map"
wordFileName = "../data/train/word.map"

def usage():
    print("""
    Usage:   extractDcd.py [options] 
    
    Description:
             Extracts hidden variables from gmtkViterbiNew binary dump files. The script expects 
             the file to contain seven rows
             
             The 1st to 4th rows should be concept1pop, concept2pop, concept3pop, concept4pop. 
             The 5th row should be the pop hidden value.
             
             The 6th to 9th rows should be concept1, concept2, concept3, concept4p. 
             The 10th row should be the push hidden value.
             
             The 11th row should be stack transition hidden value. 
             The 12th row should be stack transition counter hidden value. 
             The rows concept* are transformed to correspending 
             text values.
    
    Options: 
             -h                 : print this help message and exit
             -v                 : produce verbose output
             -f                 : dcd files were produced by a force alignment
             --dirDcd=DIR       : input directory for *.dcd ( *.extension) files {%s}
             --dirObs=DIR       : input directory for *.obs coresponding to dcd files {%s}
             --fileDcd=FILE     : input dcd file to be processed {%s}
             --extension=str    : the extension that is used searching for DCD files for default {%s}
             --conceptMap=FILE  : the concept map file name {%s}
             --wordMap=FILE     : the word map file name {%s}
    """ % (dirDcd, dirObs, fileDcd, ext, conceptFileName, wordFileName))
    
###################################################################################################
###################################################################################################

try:
    opts, args = getopt.gnu_getopt(sys.argv[1:], "hvf", 
        ["dirDcd=", 
         "dirObs=", 
         "fileDcd=",
         "extension=", 
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
    elif o == "-f":
        force = True
    elif o == "--dirDcd":
        dirDcd = a
    elif o == "--dirObs":
        dirObs = a
    elif o == "--fileObs":
        fileDcd = a
    elif o == "--extension":
        ext = a
    elif o == "--conceptMap":
        conceptFileName = a
    elif o == "--wordMap":
        wordFileName = a
        

list = glob.glob(dirDcd + "/*." + ext)
if not fileDcd == "":
    list.append(fileDcd)
list.sort()

if verbose:
    print("Start")
    print("-------------------------------------------------")
    print("Extracting DCD files.")

rConceptMap = LexMap().read(conceptFileName).reverse()
rWordMap = LexMap().read(wordFileName).reverse()

gmtkOF = 'I'

for fileName in list:
    if verbose:
        print("Reading file: " + fileName)

    dcdFile = open(fileName, "rb")
    
    try:
        dcd = []
        
        dcdVect = []
        for i in range(4):
            dcdFile.read(4)
        dcdVect.append("_EMPTY_")
        dcdVect.append("_EMPTY_")
        dcdVect.append("_EMPTY_")
        dcdVect.append("_EMPTY_")
        # pop
        dcdFile.read(4)
        dcdVect.append("_UNKNOWN_")
        
        # read concept1, concept2, concept3, concept4, push
        for i in range(4):
            dcdVect.append(rConceptMap[str(struct.unpack(gmtkOF, dcdFile.read(4))[0])])
        # push
        dcdFile.read(4)
        dcdVect.append("_UNKNOWN_")
            
        if force:
            # st
            dcdFile.read(4)
            dcdVect.append("_UNKNOWN_")
            # stc
            dcdVect.append(str(struct.unpack(gmtkOF, dcdFile.read(4))[0]))

        for i in range(len(dcdVect)):
            if dcdVect[i] == "4294967295":
               dcdVect[i] = "_UNKNOWN_"
               
        #print dcdVect
        dcd.append(dcdVect)

        while(True):
            dcdVect = []
            
            # read concept1pop, concept2pop, concept3pop, concept4pop, pop
            for i in range(4):
                dcdVect.append(rConceptMap[str(struct.unpack(gmtkOF, dcdFile.read(4))[0])])
            try:
                dcdVect.append(str(struct.unpack(gmtkOF, dcdFile.read(4))[0]))
            except:
                dcdVect.append("_UNKNOWN_")
                
            # read concept1, concept2, concept3, concept4, push
            for i in range(4):
                try:
                    dcdVect.append(rConceptMap[str(struct.unpack(gmtkOF, dcdFile.read(4))[0])])
                except:
                    dcdVect.append("_EMPTY_")
                    
            try:
                dcdVect.append(str(struct.unpack(gmtkOF, dcdFile.read(4))[0]))
            except:
                dcdVect.append("_UNKNOWN_")
                
            # read stack transition hidden value and stack transition counter hidden value. 
            if force:
                try:
                    dcdVect.append(str(struct.unpack(gmtkOF, dcdFile.read(4))[0]))
                except:
                    dcdVect.append("_UNKNOWN_")
                try:
                    dcdVect.append(str(struct.unpack(gmtkOF, dcdFile.read(4))[0]))
                except:
                    dcdVect.append("_UNKNOWN_")

            for i in range(len(dcdVect)):
                if dcdVect[i] == "4294967295":
                    dcdVect[i] = "_UNKNOWN_"
            
            #print dcdVect
            dcd.append(dcdVect)
    except:
        #print dcdVect
        #raise
        pass

    dcdFile.close()
        
    # save the original dcd file
    dcdExtractFile = codecs.open(fileName + ".txt", "w", "utf-8")
    for dcdVect in dcd:
        for each in dcdVect[:-1]:
            dcdExtractFile.write(each + "\t")
        
        dcdExtractFile.write(dcdVect[-1] + "\n")
        
    dcdExtractFile.close()
    
    # read obs file
##    print dirObs
##    print fileName
##    print splitext(basename(fileName))[0]
    
    brokenDCD = False
    obsFileName = normpath(dirObs +  "/" + splitext(basename(fileName))[0] + ".obs.orig")
    obsFile = codecs.open(obsFileName, 'r', 'utf-8')
    for i, line in enumerate(obsFile):
        obs_line = line.split()
        if i >= len(dcd):
            # output DCD file is not long enough, decoding was broken
            brokenDCD = True
            dcd.append(obs_line)
        dcd[i][0:0] = obs_line
    obsFile.close()
    
    # search for broken DCD files
    for dcdVect in dcd:
        for each in dcdVect:
            if each == '_SINK_':
                # forbidden concept on the stack
                brokenDCD = True
                break
        
        if brokenDCD:
            break
            
    # save the combination of a dcd file and an observation file
    dcdExtractFile = codecs.open(fileName + ".cmb", "w", "utf-8")
    if not brokenDCD:
        for dcdVect in dcd:
            for each in dcdVect[:-1]:
                dcdExtractFile.write(each + "\t")
            
            dcdExtractFile.write(dcdVect[-1] + "\n")
    else:
        for dcdVect in dcd:
            dcdExtractFile.write(dcdVect[0] + "\t")
            dcdExtractFile.write(dcdVect[1] + "\t")
            for i in range(4):
                dcdExtractFile.write("_EMPTY_\t")
            dcdExtractFile.write("0\t")
            for i in range(4):
                dcdExtractFile.write("_EMPTY_\t")
            dcdExtractFile.write("0\n")
    
        
    dcdExtractFile.close()

if verbose:
    print("-------------------------------------------------")
    print("Finish")
