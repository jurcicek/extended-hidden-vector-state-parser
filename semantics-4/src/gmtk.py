#!//usr/bin/python
# -*-  coding: UTF-8 -*-

import codecs
import re
import sparseProbability
from lexMap import mapCmp

sinkIndex = 2
failIndex = 0
probPruneToZeroConst = 1.0e-110

###################################################################################################
###################################################################################################

def probPruneToZero(prob):
    if prob < probPruneToZeroConst:
        return 0.0
    
    return prob
    
###################################################################################################
###################################################################################################

def readDcpt(fileName, name):
    """ This function read one dense CPT from the output of GMTK. 
        
    """
    dcptsFile = open(fileName, "r")
    
    dcptLines = dcptsFile.readlines()
    for i in range(len(dcptLines)):
        line = dcptLines[i].strip()

        if line == name:
            # I found dcpt in which I am interested in
            numOfParents = int(dcptLines[i+1].split('%')[0])
            cardinality = int(dcptLines[i+2].split('%')[0])
            probs = dcptLines[i+3].split('%')[0].strip().split(' ')
            probs = [float(x) for x in probs]
            
            return probs
    
######################################################################################################
######################################################################################################

def saveDcptZerogram(fileNamePrefix, dcptName, selfCard, parentsCardinality=[]):
    mdcptsFile = open(fileNamePrefix + "/" + dcptName + ".dcpt", "w")
    
    mdcptsFile.write("1 % number of Dense Conditional Probability Trees\n\n")

    mdcptsFile.write("0 % index of DCPT \n")
    mdcptsFile.write("%s %% DCPT name \n" % (dcptName))
    mdcptsFile.write("%d %% number of parents \n" % len(parentsCardinality))
    if len(parentsCardinality) == 0:
        mdcptsFile.write("%d %% self cardinality\n" % selfCard)
    else:
        for each in parentsCardinality:
            mdcptsFile.write("%d " % each)
        mdcptsFile.write("% parents cardinality\n")
            
        mdcptsFile.write("%d %% self cardinality\n" % selfCard)
    
    pow = 1
    for each in parentsCardinality:
        pow *= each
        
    for i in range(pow):
        for j in range(selfCard):
            mdcptsFile.write("%.3e " % (1/float(selfCard)))
        mdcptsFile.write("\n")
    
    mdcptsFile.close()

######################################################################################################
######################################################################################################

def saveDcptUnseen(fileNamePrefix, dcptName, selfCard, wordMap):
    """ Save Dcpt so that only _unseen_ word has non zero probability.
    """
    mdcptsFile = open(fileNamePrefix + "/" + dcptName + ".dcpt", "w")
    
    mdcptsFile.write("1 % number of Dense Conditional Probability Trees\n\n")

    mdcptsFile.write("0 % index of DCPT \n")
    mdcptsFile.write("%s %% DCPT name \n" % (dcptName))
    mdcptsFile.write("%d %% number of parents \n" % 0)
    mdcptsFile.write("%d %% self cardinality\n" % selfCard)
    
    for j in range(selfCard):
        if j == int(wordMap["_unseen_"]):
            mdcptsFile.write("%.3e " % 1)
        else:
            mdcptsFile.write("%.3e " % 0)
    mdcptsFile.write("\n")
    
    mdcptsFile.close()

######################################################################################################
######################################################################################################

def saveDcptUnigram(fileNamePrefix, dcptName, selfCard, sp):
    
    mdcptsFile = open(fileNamePrefix + "/" + dcptName + ".dcpt", "w")
    
    mdcptsFile.write("1 % number of Dense Conditional Probability Trees\n\n")

    mdcptsFile.write("0 % index of DCPT \n")
    mdcptsFile.write("%s %% DCPT name \n" % (dcptName))
    mdcptsFile.write("%d %% number of parents \n" % 0)
    mdcptsFile.write("%d %% self cardinality\n" % selfCard)
    
    for j in range(selfCard):
        value = probPruneToZero(sp.getSafeValue([j]))
        num = "%.3e " % value
                
        # normalize string output for exponent e+00 and e-00
        num = num.replace('e+00' , 'e-00')
        mdcptsFile.write(num)

    mdcptsFile.write("\n")
    
    mdcptsFile.close()

######################################################################################################
######################################################################################################

def saveDcptBigram(fileNamePrefix, dcptName, selfCard, biCard, sp):
    
    mdcptsFile = open(fileNamePrefix + "/" + dcptName + ".dcpt", "w")
    
    mdcptsFile.write("1 % number of Dense Conditional Probability Trees\n\n")

    mdcptsFile.write("0 % index of DCPT \n")
    mdcptsFile.write("%s %% DCPT name \n" % (dcptName))
    mdcptsFile.write("%d %% number of parents \n" % 1)
    mdcptsFile.write("%d %% parents cardinality\n" % biCard)
    mdcptsFile.write("%d %% self cardinality\n" % selfCard)
    
    for i in range(biCard):
        sum = 0
        for j in range(selfCard):
            sum += sp.getSafeValue([j, i])
        
        if abs(sum - 1.0) < 0.001:
            for j in range(selfCard):
                value = probPruneToZero(sp.getSafeValue([j, i]))
                num = "%.3e " % value

                # normalize string output for exponent e+00 and e-00
                num = num.replace('e+00' , 'e-00')
                mdcptsFile.write(num)
        else:
            # normalize output so that it sums to one 
            for j in range(selfCard):
                value = probPruneToZero((sp.getSafeValue([j, i]) + 1e-120) /(sum + 1e-120*selfCard))
                num = "%.3e " % value
                
                # normalize string output for exponent e+00 and e-00
                num = num.replace('e+00' , 'e-00')
                mdcptsFile.write(num)
            
        mdcptsFile.write("\n")
    
    mdcptsFile.close()

###################################################################################################
###################################################################################################

def readDt(fileName):
    dtFile = open(fileName, "r")
    
    sp = sparseProbability.SparseProbability()
    
    dtLines = dtFile.readlines()
    for i in range(len(dtLines)):
        line = dtLines[i].strip()
        line = line.split('\t')
        
        if line[0] == '-1':
            splt = line[1].split('%')
            idx = int(splt[0].strip())
            
            if idx: 
                # only indexes that are not equal to zero
                stack = splt[1].strip()
                stack = stack[1:-1]
                stack = stack.split(',')
                concepts = [int(x) for x in stack]
                concepts.reverse()
                
                # P(C1, C2, C2, C4)
                sp.setValue(concepts, idx)
            
    return sp

###################################################################################################
###################################################################################################

def combineDtDcpt1(sProbability, prob):
    sp = sparseProbability.SparseProbability()
    
    for each in sProbability.vectList():
        # P(C1, C2, C3, C4) = value
        idx = sProbability.getValue(each)
        sp.setValue(each, prob[idx])
        
    return sp
    
###################################################################################################
###################################################################################################

def combineDtDcpt2(sProbability, prob):
    sp = sparseProbability.SparseProbability()
    
    for each in sProbability.vectList():
        idx = sProbability.getValue(each)
        for i in range(len(prob[0])):
            # P(W | C1, C2, C3, C4) = value
            # P(C1 | C2, C3, C4) = value
            if prob[idx][i] != 0.0:
                sp.setValue([i]+each, prob[idx][i])
        
    return sp

######################################################################################################
######################################################################################################

def saveDt(fileNamePrefix, dtName, dt, depth = 4, fIndex = failIndex):
    i = 1 # count leafs
    
    l4 = dt.keys()
    l4.sort(mapCmp)
    
    dts = []
    dts.append("1 % number of Decision Trees\n")
    dts.append("0 % index of DT\n\n")
    
    dts.append("%s %% DT name\n" % dtName) 
    dts.append("%d %% number of parents\n" % (depth))
    
    dts.append("\n%% (C4,C3,C2,C1)\n\n")

    dts.append("%d\t%d" % (depth-1, len(l4)+1))
    for l4key in l4:
        dts.append("\t%s" % l4key)
    dts.append("\tdefault\n")

    for l4key in l4:
        l3 = dt[l4key].keys()
        l3.sort(mapCmp)
        
        dts.append("\t%d\t%d" % (depth-2, len(l3)+1))
        for l3key in l3:
            dts.append("\t%s" % l3key)
        dts.append("\tdefault\n")
        
        if depth == 2:
            for l3key in l3:
                dts.append("\t\t\t-1\t%-7d" % i)
                dts.append("%% [%s,%s]\n" % (l4key,l3key))
                i += 1
            dts.append("\t\t\t-1\t%d %% fail index\n\n" % fIndex)                
        else:
            for l3key in l3:
                l2 = dt[l4key][l3key].keys()
                l2.sort(mapCmp)
    
                dts.append("\t\t%d\t%d" % (depth-3, len(l2)+1))
                for l2key in l2:
                    dts.append("\t%s" % l2key)
                dts.append("\tdefault\n")
    
                if depth == 3:
                    for l2key in l2:
                        dts.append("\t\t\t\t-1\t%-7d" % i)
                        dts.append("%% [%s,%s,%s]\n" % (l4key,l3key,l2key))
                        i += 1
                    dts.append("\t\t\t\t-1\t%d %% fail index\n\n" % fIndex)
                else:
                    for l2key in l2:
                        l1 = dt[l4key][l3key][l2key].keys()
                        l1.sort(mapCmp)
    
                        dts.append("\t\t\t%d\t%d" % (depth-4, len(l1)+1))
                        for l1key in l1:
                            dts.append("\t%s" % l1key)
                        dts.append("\tdefault\n")
    
                        if depth == 4:
                            for l1key in l1:
                                dts.append("\t\t\t\t\t-1\t%-7d" % i)
                                dts.append("%% [%s,%s,%s,%s]\n" % (l4key,l3key,l2key,l1key))
                                i += 1
                            dts.append("\t\t\t\t\t-1\t%d %% fail index\n\n" % fIndex)
                        else:
                            raise ValueEror, "Invalid depth value: %d" % depth
                    
                    dts.append("\t\t\t-1\t%d %% fail index\n\n" % fIndex)
            dts.append("\t\t-1\t%d %% fail index\n\n" % fIndex)
    dts.append("\t-1\t%d %% fail index\n\n" % fIndex)
    
    
    dtFile = open(fileNamePrefix + "/" + dtName +".dt", "w")
    
    for line in dts:
        dtFile.write(line)
    
    dtFile.close()
    
##    return i - 1
    return i

######################################################################################################
######################################################################################################

def saveDtBucketing(fileNamePrefix, dtName, dt, depth = 4, fIndex = failIndex):
    i = 1 # count leafs
    
    l4 = dt.keys()
    l4.sort(mapCmp)
    
    dts = []
    dts.append("1 % number of Decision Trees\n")
    dts.append("0 % index of DT\n\n")
    
    dts.append("%s %% DT name\n" % dtName) 
    dts.append("%d %% number of parents\n" % (depth))
    
    dts.append("\n%% (C4,C3,C2,C1)\n\n")

    dts.append("%d\t%d" % (depth-1, len(l4)+1))
    for l4key in l4:
        dts.append("\t%s" % l4key)
    dts.append("\tdefault\n")

    for l4key in l4:
        l3 = dt[l4key].keys()
        l3.sort(mapCmp)
        
        dts.append("\t%d\t%d" % (depth-2, len(l3)+1))
        for l3key in l3:
            dts.append("\t%s" % l3key)
        dts.append("\tdefault\n")
        
        if depth == 2:
            for l3key in l3:
                dts.append("\t\t\t-1\t%-7d" % dt[l4key][l3key])
                dts.append("%% [%s,%s]\n" % (l4key,l3key))
                i += 1
            dts.append("\t\t\t-1\t%d %% fail index\n\n" % fIndex)                
        else:
            for l3key in l3:
                l2 = dt[l4key][l3key].keys()
                l2.sort(mapCmp)
    
                dts.append("\t\t%d\t%d" % (depth-3, len(l2)+1))
                for l2key in l2:
                    dts.append("\t%s" % l2key)
                dts.append("\tdefault\n")
    
                if depth == 3:
                    for l2key in l2:
                        dts.append("\t\t\t\t-1\t%-7d" % dt[l4key][l3key][l2key])
                        dts.append("%% [%s,%s,%s]\n" % (l4key,l3key,l2key))
                        i += 1
                    dts.append("\t\t\t\t-1\t%d %% fail index\n\n" % fIndex)
                else:
                    for l2key in l2:
                        l1 = dt[l4key][l3key][l2key].keys()
                        l1.sort(mapCmp)
    
                        dts.append("\t\t\t%d\t%d" % (depth-4, len(l1)+1))
                        for l1key in l1:
                            dts.append("\t%s" % l1key)
                        dts.append("\tdefault\n")
    
                        if depth == 4:
                            for l1key in l1:
                                dts.append("\t\t\t\t\t-1\t%-7d" % dt[l4key][l3key][l2key][l1key])
                                dts.append("%% [%s,%s,%s,%s]\n" % (l4key,l3key,l2key,l1key))
                                i += 1
                            dts.append("\t\t\t\t\t-1\t%d %% fail index\n\n" % fIndex)
                        else:
                            raise ValueEror, "Invalid depth value: %d" % depth
                    
                    dts.append("\t\t\t-1\t%d %% fail index\n\n" % fIndex)
            dts.append("\t\t-1\t%d %% fail index\n\n" % fIndex)
    dts.append("\t-1\t%d %% fail index\n\n" % fIndex)
    
    
    dtFile = open(fileNamePrefix + "/" + dtName +".dt", "w")
    
    for line in dts:
        dtFile.write(line)
    
    dtFile.close()
    
##    return i - 1
    return i

######################################################################################################
######################################################################################################

def saveDtBackoff(fileNamePrefix, dtName, dt, depth = 4, fIndex = failIndex):
    i = 1 # count leafs
    
    l4 = dt.keys()
    l4.sort(mapCmp)
    
    dts = []
    dts.append("1 % number of Decision Trees\n")
    dts.append("0 % index of DT\n\n")
    
    dts.append("%s %% DT name\n" % dtName) 
    dts.append("%d %% number of parents\n" % (depth))
    
    dts.append("\n%% (C1,C2,C3,C4)\n\n")

    dts.append("%d\t%d" % (0, len(l4)+1))
    for l4key in l4:
        dts.append("\t%s" % l4key)
    dts.append("\tdefault\n")

    for l4key in l4:
        l3 = dt[l4key][0].keys()
        l3.sort(mapCmp)
        
        dts.append("\t%d\t%d" % (1, len(l3)+1))
        for l3key in l3:
            dts.append("\t%s" % l3key)
        dts.append("\tdefault\n")
        
        if depth == 2:
            for l3key in l3:
                dts.append("\t\t\t-1\t%-7d" % 0)
                dts.append("%% [%s,%s]\n" % (l4key,l3key))
                i += 1
            dts.append("\t\t\t-1\t%d %% backoff\n\n" % 0)                
        else:
            for l3key in l3:
                l2 = dt[l4key][0][l3key][0].keys()
                l2.sort(mapCmp)
    
                dts.append("\t\t%d\t%d" % (2, len(l2)+1))
                for l2key in l2:
                    dts.append("\t%s" % l2key)
                dts.append("\tdefault\n")
    
                if depth == 3:
                    for l2key in l2:
                        dts.append("\t\t\t\t-1\t%-7d" % 0)
                        dts.append("%% [%s,%s,%s]\n" % (l4key,l3key,l2key))
                        i += 1
                    dts.append("\t\t\t\t-1\t%d %% backoff\n\n" % 1)
                else:
                    for l2key in l2:
                        l1 = dt[l4key][0][l3key][0][l2key][0].keys()
                        l1.sort(mapCmp)
    
                        dts.append("\t\t\t%d\t%d" % (3, len(l1)+1))
                        for l1key in l1:
                            dts.append("\t%s" % l1key)
                        dts.append("\tdefault\n")
    
                        if depth == 4:
                            for l1key in l1:
                                dts.append("\t\t\t\t\t-1\t%-7d" % 0)
                                dts.append("%% [%s,%s,%s,%s]\n" % (l4key,l3key,l2key,l1key))
                                i += 1
                            dts.append("\t\t\t\t\t-1\t%d %% backoff\n\n" % 1)
                        else:
                            for l1key in l1:
                                l0 = dt[l4key][0][l3key][0][l2key][0][l1key][0].keys()
                                l0.sort(mapCmp)
            
                                dts.append("\t\t\t\t%d\t%d" % (4, len(l0)+1))
                                for l0key in l0:
                                    dts.append("\t%s" % l0key)
                                dts.append("\tdefault\n")
            
                                if depth == 5:
                                    for l0key in l0:
                                        dts.append("\t\t\t\t\t\t-1\t%-7d" % 0)
                                        dts.append("%% [%s,%s,%s,%s,%s]\n" % (l4key,l3key,l2key,l1key,l0key))
                                        i += 1
                                    dts.append("\t\t\t\t\t\t-1\t%d %% backoff\n\n" % 1)
                                else:
                                    raise ValueEror, "Invalid depth value: %d" % depth
                                    
                            dts.append("\t\t\t\t-1\t%d %% backoff\n\n" % (depth - 3))
                    dts.append("\t\t\t-1\t%d %% backoff\n\n" % (depth - 2))
            dts.append("\t\t-1\t%d %% backoff\n\n" % (depth - 1))
    dts.append("\t-1\t%d %% backoff\n\n" % (depth - 0))
    
    
    dtFile = open(fileNamePrefix + "/" + dtName +".dt", "w")
    
    for line in dts:
        dtFile.write(line)
    
    dtFile.close()
    
##    return i - 1
    return i

######################################################################################################
######################################################################################################

def saveCollection(fileNamePrefix, cllctnName, numberOfSpmfs):
    cllctnFile = open(fileNamePrefix + "/" + cllctnName +".cllctn", "w")
    
    cllctnFile.write("1 % one collection\n")
    cllctnFile.write("0 % index 0\n\n")
    
    cllctnFile.write("%s %% the collection name\n" % cllctnName)
    cllctnFile.write("%d %% the length of the collection\n" % (numberOfSpmfs))
    
    for i in range(numberOfSpmfs):
        cllctnFile.write("%s_%.4d\n" % (cllctnName, i))
        
    cllctnFile.close()
    
######################################################################################################
######################################################################################################

def saveSpmfs(fileNamePrefix, spmfsName, numberOfSpmfs, selfCard):
    spmfsFile = open(fileNamePrefix + "/" + spmfsName + ".spmfs", "w")
    
    spmfsFile.write("%d %% number of Sparse Probability Mass Functions\n\n" % (numberOfSpmfs))
    
    for i in range(numberOfSpmfs):
        spmfsFile.write("%d %% index of SPMF \n" % i)
        spmfsFile.write("%s_%.4d %% SPMF name \n" % (spmfsName ,i))
        spmfsFile.write("%d %% cardinality of X1 (self cardinality)\n" % selfCard)
        spmfsFile.write("%d %% number of values with non-zero probability\n" % selfCard)
        
        for j in range(selfCard):
            spmfsFile.write("%d " % j)
        
        spmfsFile.write("\n")
        spmfsFile.write("%s_%.4d %% DPFM name \n" % (spmfsName ,i))
        
        spmfsFile.write("\n")
            
    
######################################################################################################
######################################################################################################

def openToWriteDpmfsFile(fileNamePrefix, dpmfsName, numberOfDpmfs, selfCard):
    dpmfsFile = open(fileNamePrefix + "/" + dpmfsName + ".dpmfs", "w")
    
    dpmfsFile.write("%d %% number of Dense Probability Mass Functions\n\n" % (numberOfDpmfs))
    
    dpmfsFile.write("%d %% index of DPMF \n" % 0)
    dpmfsFile.write("%s_%.4d %% DPMF name \n" % (dpmfsName , 0))
    dpmfsFile.write("%d %% cardinality of X1 (self cardinality)\n" % selfCard)
    return dpmfsFile

######################################################################################################
######################################################################################################

def writeEmptyDpmfsVector(normSink, selfCard, dpmfsFile):
    if normSink < 0 :
        v = []
        for j in range(selfCard):
            if j == 1:
                v.append(-1/float(selfCard)*normSink)
            else:
                v.append(1/float(selfCard))
        sum = 0
        for each in v:
            sum += each
                
        for j in range(selfCard):
            v[j] = v[j] / sum
            
        for each in v:
            dpmfsFile.write("%.3e " % probPruneToZero(each))
    else:
        for j in range(selfCard):
            # this case should be with zero probability (unprobable)
            if j == normSink:
                # only one option is probable
                dpmfsFile.write("%.3e " % 1)
            else:
                dpmfsFile.write("%.3e " % 0)
    dpmfsFile.write("\n\n")

######################################################################################################
######################################################################################################

def saveDpmfs(fileNamePrefix, dpmfsName, numberOfDpmfs, selfCard, normSink = sinkIndex, wordDpmfs = False):
    # I need one zero vect just in case of a bad vector
    numberOfDpmfs += 1
    
    dpmfsFile = openToWriteDpmfsFile(fileNamePrefix, dpmfsName, numberOfDpmfs, selfCard)
    
    writeEmptyDpmfsVector(normSink, selfCard, dpmfsFile)
        
    for i in range(1, numberOfDpmfs):
        dpmfsFile.write("%d %% index of DPMF \n" % i)
        dpmfsFile.write("%s_%.4d %% DPMF name \n" % (dpmfsName ,i))
        dpmfsFile.write("%d %% cardinality of X1 (self cardinality)\n" % selfCard)
        
        # hack generation of _empty_ word, allow only [_EMPTY_, ..., _EMPTY_] stack to 
        # generate this word
        
        if wordDpmfs:
            if i != 1:
                dpmfsFile.write("%.3e " % 0)
                
                for j in range(1, selfCard):
                    dpmfsFile.write("%.3e " % (1/float(selfCard-1)))
            else:
                dpmfsFile.write("%.3e " % 1)
                
                for j in range(1, selfCard):
                    dpmfsFile.write("%.3e " % 0)
        else:
            for j in range(selfCard):
                dpmfsFile.write("%.3e " % (1/float(selfCard)))
        
        dpmfsFile.write("\n\n")

######################################################################################################
######################################################################################################

def saveDpmfsConcept(fileNamePrefix, dpmfsName, numberOfDpmfs, selfCard, normSink = sinkIndex, type="c1"):
    # I need one zero vect just in case of a bad vector
    numberOfDpmfs += 1
    
    dpmfsFile = openToWriteDpmfsFile(fileNamePrefix, dpmfsName, numberOfDpmfs, selfCard)
    
    writeEmptyDpmfsVector(normSink, selfCard, dpmfsFile)
        
    for i in range(1, numberOfDpmfs):
        dpmfsFile.write("%d %% index of DPMF \n" % i)
        dpmfsFile.write("%s_%.4d %% DPMF name \n" % (dpmfsName ,i))
        dpmfsFile.write("%d %% cardinality of X1 (self cardinality)\n" % selfCard)
        
        # hack generation of _empty_ word, allow only [_EMPTY_, ..., _EMPTY_] stack to 
        # generate this word
        
        if type == "c1":
            # _EMPTY_
            dpmfsFile.write("%.3e " % 0)
            # _DUMMY_
            dpmfsFile.write("%.3e " % (1/float(selfCard-2)))
            # _SINK_
            dpmfsFile.write("%.3e " % 0)
            
            for j in range(3, selfCard):
                dpmfsFile.write("%.3e " % (1/float(selfCard-2)))
            
        else: # type == c2, c3, c4
            # _EMPTY_
            dpmfsFile.write("%.3e " % 0)
            # _DUMMY_
            dpmfsFile.write("%.3e " % 0)
            # _SINK_
            dpmfsFile.write("%.3e " % 0)
            
            for j in range(3, selfCard):
                dpmfsFile.write("%.3e " % (1/float(selfCard-3)))
        
        dpmfsFile.write("\n\n")

######################################################################################################
######################################################################################################

def saveDpmfsPopPush(fileNamePrefix, dpmfsName, numberOfDpmfs, selfCard, v=[14,13,12,11,10]):
    # I need one zero vect just in case of a bad vector
    numberOfDpmfs += 1
    
    dpmfsFile = open(fileNamePrefix + "/" + dpmfsName + ".dpmfs", "w")
    dpmfsFile.write("%d %% number of Dense Probability Mass Functions\n\n" % (numberOfDpmfs))

    sum = 0.0
    for each in v:
        sum += each
    for j in range(selfCard):
            v[j] = v[j] / sum
    
    dpmfsFile.write("%d %% index of DPMF \n" % 0)
    dpmfsFile.write("%s_%.4d %% DPMF name \n" % (dpmfsName , 0))
    dpmfsFile.write("%d %% cardinality of X1 (self cardinality)\n" % selfCard)
    for j in range(selfCard):
        # this case should be with zero probability (unprobable)
        if j == selfCard-1:
            # only one option is probable
            dpmfsFile.write("%.3e " % 1)
        else:
            dpmfsFile.write("%.3e " % 0)
    dpmfsFile.write("\n\n")    
    
    for i in range(1, numberOfDpmfs):
        dpmfsFile.write("%d %% index of DPMF \n" % i)
        dpmfsFile.write("%s_%.4d %% DPMF name \n" % (dpmfsName ,i))
        dpmfsFile.write("%d %% cardinality of X1 (self cardinality)\n" % selfCard)
        
        for j in range(selfCard):
            dpmfsFile.write("%.3e " % (v[j]))
        
        dpmfsFile.write("\n\n")

######################################################################################################
######################################################################################################

def saveDpmfsProbs(fileNamePrefix, dpmfsName, numberOfDpmfs, selfCard, sp, normSink = sinkIndex):
    # I need one zero vect just in case of a bad vector
    numberOfDpmfs += 1
    
    dpmfsFile = openToWriteDpmfsFile(fileNamePrefix, dpmfsName, numberOfDpmfs, selfCard)
    
    writeEmptyDpmfsVector(normSink, selfCard, dpmfsFile)
    
    # get probabilities
    dm = sp.getDim()
    lst = sp.vectSubList(range(1, dm))
    #random.shuffle(lst)
    for i in range(len(lst)):
        lst[i].reverse()
    # make sure that lst is in the same order as saving in saveDt where lst is sorted
    # if you do not do it, you will end up with mixed propabilities
    lst.sort(mapCmp)
    for i in range(len(lst)):
        lst[i].reverse()
    
    for i in range(len(lst)):
        rr = lst[i][:]
        rr.reverse()
        
        dpmfsFile.write("%d %% index of DPMF [C4,C3,C2,C1] = %s\n" % ((i + 1), str(rr)))
        dpmfsFile.write("%s_%.4d %% DPMF name \n" % (dpmfsName ,i + 1))
        dpmfsFile.write("%d %% cardinality of X1 (self cardinality)\n" % selfCard)
        
        sum = 0
        for j in range(selfCard):
            sum += sp.getSafeValue([j] + lst[i])
        
        if abs(sum - 1.0) < 0.001:
            for j in range(selfCard):
                num = "%.3e " % probPruneToZero(sp.getSafeValue([j] + lst[i]))
                
                # normalize output for exponent e+00 and e-00
                num = num.replace('e+00' , 'e-00')
                
                dpmfsFile.write(num)
        else:
            # normalize output so that it sums to one 
            for j in range(selfCard):
                value = probPruneToZero((sp.getSafeValue([j] + lst[i]) + 1e-120) /(sum + 1e-120*selfCard))
                num = "%.3e " % value
                
                # normalize string output for exponent e+00 and e-00
                num = num.replace('e+00' , 'e-00')
                dpmfsFile.write(num)
        
        dpmfsFile.write("\n\n")

######################################################################################################
######################################################################################################

def readDpmf(fileName, name):
    """ This function read one sparse CPT from the output of GMTK. 
        
    """
    dpmfsFile = open(fileName, "r")
    
    table = []
    dpmfsLines = dpmfsFile.readlines()
    for i in range(len(dpmfsLines)):
        line = dpmfsLines[i].strip()

        if line[:len(name)] == name:
            # I found dspmf in which I am interested in
            probs = line.split(' ')[2:]
            probs = [float(x) for x in probs]
            
            table.append(probs)

    if table == []:
        raise NameError, "I can not find dpmf of name %s" % name
        
    return table
