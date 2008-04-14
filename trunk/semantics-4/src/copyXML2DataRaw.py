#!//usr/bin/python
# -*-  coding: UTF-8 -*-

import os
import glob
from os.path import *
import getopt
from xml.dom import minidom
import toolkit
import semantics
from lexMap import *
import shutil
import random
import datetime

dirIn = "/home/filip/cvs-skola/DIALOGUE/data/xml-anotated"
dirTrain = "../data_raw/train"

dataReduction = 100
trainDataReduction = 100

weightTrain = 72
dirHeldout = "../data_raw/heldout"
weightHeldout = 8
dirTest = "../data_raw/test"
weightTest = 20

randomize = False

def usage():
    print("""
    Usage:   copyXML2DataRaw.py [options] 
    
    Description:
             Copy xml annotations to specified directories. Allows to specify 
             the split ratio between directries. You can specifie if you want randomize the
             selection of heldout and test dialogues. Otherwise, the seelection will be done 
             according the alphabetical order.
             
    Options: 
             -h                      : print this help message and exit
             -v                      : produce verbose output
             -r                      : randomize selection of heldout and test data
             --dataReduction         : the percentage of data which should be considered {%d} 
             --trainDataReduction    : the percentage of training data which should be considered {%d} 
             --dirIn=DIR             : the input directory where *.xml files are {%s}
             --dirTrain=DIR          : the train directory where *.xml files will be placed {%s} 
             --weightTrain=NUMBER    : the proportion of train files {%d}
             --dirHeldout=DIR        : the heldout directory where *.xml files will be placed {%s}
             --weightTrain=NUMBER    : the proportion of heldout files {%d}
             --dirTest=DIR           : the test directory where *.xml files will be placed {%s}
             --weightTrain=NUMBER    : the proportion of test files {%d} """
             % (dataReduction,
                trainDataReduction,
                dirIn, 
                dirTrain,
                weightTrain,
                dirHeldout,
                weightHeldout,
                dirTest,
                weightTest))

###################################################################################################
###################################################################################################

def splitData(list, weightTrain, weightHeldout, weightTest, rnd = True):
    # set the same seed for all train, heldout, and test sets (on all computers with the same data)
    random.seed("start")
    if rnd:
        random.seed(str(datetime.date.today()))
    random.shuffle(list)
    
    numOfFiles = len(list)
    
    sumOfWeights = weightTrain + weightHeldout + weightTest
    
    numOfTrain = int(weightTrain / float(sumOfWeights) * numOfFiles)
    numOfHeldout = int(weightHeldout / float(sumOfWeights) * numOfFiles)
    numOfTest = numOfFiles - numOfTrain - numOfHeldout
    

    train = list[0:numOfTrain]
    heldout = list[numOfTrain:numOfTrain + numOfHeldout]
    test = list[numOfTrain + numOfHeldout:numOfFiles]

    return train, heldout, test
    
###################################################################################################
###################################################################################################

def readXMLsAppendDate(fName):
    ff = open(fName, "r")
    
    ll = []
    for each in ff.readlines():
        ee = each.strip().split("\t")
        
        if len(ee) == 1:
            ee.append(str(datetime.date.today()))
#            print ee
            
        ll.append(ee)

    ff.close()
    
    return ll

###################################################################################################
###################################################################################################
def xmlCmp(x, y):
    
    if x[1] < y[1]:
        return -1
    elif x[1] > y[1]:
        return 1
    elif x[0] < y[0]:
        return -1
    elif x[0] > y[0]:
        return 1
    
    return 0
    
def saveXMLsAppendDate(fName, ll):
    ff = open(fName, "w")
    
    ll.sort(xmlCmp)
    
    for each in ll:
        if each[1] == "":
            each[1] = str(datetime.date.today())
            
        ff.write(basename(each[0]) + "\t" + each[1] + "\n")

    ff.close()

###################################################################################################
###################################################################################################

def appendDate(ll):
    for i in range(len(ll)):
        ll[i] = [ll[i], str(datetime.date.today())]
    
    return ll
    
###################################################################################################
###################################################################################################

def loadLists(dirIn):
    trainList = readXMLsAppendDate(dirIn + "/.train.list")
    heldoutList = readXMLsAppendDate(dirIn + "/.heldout.list")
    testList = readXMLsAppendDate(dirIn + "/.test.list")
   
    return trainList, heldoutList, testList

###################################################################################################
###################################################################################################

def saveLists(dirIn, trainList, heldoutList, testList):
    shutil.copy(dirIn + "/.train.list", dirIn + "/.train.list.bak")
    shutil.copy(dirIn + "/.heldout.list", dirIn + "/.heldout.list.bak")
    shutil.copy(dirIn + "/.test.list", dirIn + "/.test.list.bak")
    
    saveXMLsAppendDate(dirIn + "/.train.list", trainList)
    saveXMLsAppendDate(dirIn + "/.heldout.list", heldoutList)
    saveXMLsAppendDate(dirIn + "/.test.list", testList)

###################################################################################################
###################################################################################################

def extractList(list, trainList):
    train = []
    
    for each in list:
        for teach in trainList:
            if each.find(teach[0]) != -1:
                train.append(each)
                break
                
    return train
    
###################################################################################################
###################################################################################################

def removeLists(list, trainList, heldoutList, testList):
    slist = trainList + heldoutList + testList
    
    listClean = []
    
    for each in list:
        f = False
        for teach in slist:
            if each.find(teach[0]) != -1:
                f = True
                break
                
        if not f:
            listClean.append(each)

    return listClean
    
###################################################################################################
###################################################################################################

try:
    opts, args = getopt.gnu_getopt(sys.argv[1:], "hvr", 
        ["dataReduction=",
        "trainDataReduction=",
        "dirIn=", 
        "dirTrain=",
        "weightTrain=",
        "dirHeldout=",
        "weightHeldout=",
        "dirTest=",
        "weightTest="])
         
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
    elif o == "-r":
        randomize = True
    elif o == "--dataReduction":
        dataReduction = float(a)
    elif o == "--trainDataReduction":
        trainDataReduction = float(a)
    elif o == "--dirIn":
        dirIn = a
    elif o == "--dirTrain":
        dirTrain = a
    elif o == "--weightTrain":
        weightTrain = int(a)
    elif o == "--dirHeldout":
        dirHeldout = a
    elif o == "--weightHeldout":
        weightHeldout = int(a)
    elif o == "--dirTest":
        dirTest = a        
    elif o == "--weightTest":
        weightTest = int(a)

list = glob.glob(dirIn + "/*.xml")
list.sort()

if verbose:
    print("Start")
    print("-------------------------------------------------")
    
    print("Freeing target directories.")
    
# remove old files
for file in glob.glob(dirTrain + "/*.xml"):
    os.remove(file)
for file in glob.glob(dirHeldout + "/*.xml"):
    os.remove(file)
for file in glob.glob(dirTest + "/*.xml"):
    os.remove(file)

if verbose:
    print("Copying of XMLs.")

trainList, heldoutList, testList = loadLists(dirIn)

train = extractList(list, trainList)
heldout = extractList(list, heldoutList)
test = extractList(list, testList)

listClean = removeLists(list, trainList, heldoutList, testList)
trainNew, heldoutNew, testNew = splitData(listClean, weightTrain, weightHeldout, weightTest, randomize)

train = train + trainNew
heldout = heldout + heldoutNew
test = test + testNew

if dataReduction > 0.0 and dataReduction < 100.0:
    train = train[:int(len(train)*dataReduction/100.0 + 0.6)]
    heldout = heldout[:int(len(heldout)*dataReduction/100.0 + 0.6)]
    test = test[:int(len(test)*dataReduction/100.0 + 0.6)]
if dataReduction == 0.0:
    train = train[:11]
    heldout = heldout[:1]
    test = test[:1]

if trainDataReduction > 0.0 and trainDataReduction < 100.0:
    train = train[:int(len(train)*trainDataReduction/100.0 + 0.6)]
if trainDataReduction == 0.0:
    train = train[:11]

for each in train:
    shutil.copy(each, dirTrain)

for each in heldout:
    shutil.copy(each, dirHeldout)

for each in test:
    shutil.copy(each, dirTest)
    
saveLists(dirIn, trainList + appendDate(trainNew), 
                 heldoutList + appendDate(heldoutNew), 
                 testList + appendDate(testNew))
    
if verbose:
    print("-------------------------------------------------")
    print("Finish")

