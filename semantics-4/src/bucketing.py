#!//usr/bin/python
# -*-  coding: UTF-8 -*-

import codecs

import toolkit
import sparseProbability
import gmtk
from math import log

###################################################################################################
###################################################################################################

def getWordGrams(fileName, wordGrams, c1Grams, c2Grams, c3Grams = {}, fileType='cmb'):
    cmbFile = codecs.open(fileName, "r", "UTF-8")

    for line in cmbFile.readlines():
        splitLine = line.strip().split("\t")
        # splitLine = splitLine[0:1] + splitLine[6:10]
        if fileType == 'cmb':
            splitLine = splitLine[0:1] + splitLine[7:11]
        elif fileType == 'hddn':
            splitLine = splitLine[0:5]
        else:
            ValueError('fileType has unsupported value: %s' % fileType)

        tt0 = tuple(splitLine[0:5])
        tt1 = tt0[1:]

        ###########################################################
        if fileType == 'cmb':
            # exclude grams related to the word _empty_
            if tt0[0] == u'_empty_':
                continue
            
            # there is an excess of vectors of u'_EMPTY_', u'_EMPTY_', u'_EMPTY_', u'_EMPTY_'
            if tt1 == (u'_EMPTY_', u'_EMPTY_', u'_EMPTY_', u'_EMPTY_'):
                continue
        ###########################################################

        tt2 = tt1[1:]
        tt3 = tt2[1:]

        wordGrams[tt0] = wordGrams.get(tt0, 0) + 1
        c1Grams[tt1] = c1Grams.get(tt1, 0) + 1
        c2Grams[tt2] = c2Grams.get(tt2, 0) + 1
        c3Grams[tt3] = c3Grams.get(tt3, 0) + 1

    cmbFile.close()

###################################################################################################
###################################################################################################

def getPopGrams(fileName, popGrams, c1Grams):
    cmbFile = codecs.open(fileName, "r", "UTF-8")
    
    c1Gram = None
    c1GramOld = None
    pop = None
    
    for line in cmbFile.readlines():
        splitLine = line.strip().split("\t")

        c1GramOld = c1Gram
        c1Gram = splitLine[6:10]
        pop = splitLine[5]
        
        if pop == u'_UNKNOWN_':
            # in the cmb file is not written pop variable = the first frame
            continue
            
        tt0 = tuple([pop] + c1GramOld)
        tt1 = tt0[1:]

        ###########################################################
        # there is an excess of vectors of u'_EMPTY_', u'_EMPTY_', u'_EMPTY_', u'_EMPTY_'
        
        if tt1 == (u'_EMPTY_', u'_EMPTY_', u'_EMPTY_', u'_EMPTY_'):
            continue
        ###########################################################
        
        popGrams[tt0] = popGrams.get(tt0, 0) + 1
        c1Grams[tt1] = c1Grams.get(tt1, 0) + 1

    cmbFile.close()

###################################################################################################
###################################################################################################

def getPushGrams(fileName, pushGrams, c1Grams):
    cmbFile = codecs.open(fileName, "r", "UTF-8")
    
    c1Gram = None
    c1GramOld = None
    push = None
    
    for line in cmbFile.readlines():
        splitLine = line.strip().split("\t")

        c1GramOld = c1Gram
        c1Gram = splitLine[6:10]
        push = splitLine[10]
        
        if push == u'_UNKNOWN_':
            # in the cmb file is not written push variable = the first frame
            continue
            
        tt0 = tuple([push] + c1GramOld)
        tt1 = tt0[1:]

        ###########################################################
        # there is an excess of vectors of u'_EMPTY_', u'_EMPTY_', u'_EMPTY_', u'_EMPTY_'
        
        if tt1 == (u'_EMPTY_', u'_EMPTY_', u'_EMPTY_', u'_EMPTY_'):
            continue
        ###########################################################
        
        pushGrams[tt0] = pushGrams.get(tt0, 0) + 1
        c1Grams[tt1] = c1Grams.get(tt1, 0) + 1

    cmbFile.close()

###################################################################################################
###################################################################################################
    
def getCardinalities(ngrams):
    cards = {}
    
    for each in ngrams.keys():
        ee = each[1:]
        cards[ee] = cards.get(ee, 0) + 1
        
    return cards
    
###################################################################################################
###################################################################################################

def computeRatio(c, wC, ratioType):
    if ratioType == "bahl":
        ratio = c
        add = c
    else: 
        # Chen and Goodman
        ratio = c/wC
        add = c
    
    return ratio, add
    
###################################################################################################
###################################################################################################

def buildBuckets(hist, card, linX, logX, constX, ratioType = "chen"):
    buckets = {}
    count = 0
    
    for each in hist.keys():
        ratio, add = computeRatio(float(hist[each]), float(card[each]), ratioType)
        buckets[ratio] = buckets.get(ratio, 0) + add
    
    for each in buckets.keys():
        X = buckets[each]
        X = linX*X + logX*log(X) + constX
        buckets[each] = X
        
    return buckets

###################################################################################################
###################################################################################################

def fillBoundaries(buckets, number, splitType = "equal"):
    lst = buckets.keys()
    lst.sort()
    
    bckts = []
    for each in lst:
        bckts.append((each, buckets[each]))
    
    if splitType == "equal":
        if len(bckts) < number:
            number = len(bckts)
            print """
               The number of buckets is too high. I can generate only %d buckets.
            """ % number

        superBuckets = toolkit.splitByContent(bckts, number, 1)
    else:
        # min split
        superBuckets = toolkit.splitByMinSize(bckts, number, 1)
    
    i = None
    boundareis = []
    for i in range(len(superBuckets)-1):
        boundareis.append((superBuckets[i][0][0], superBuckets[i+1][0][0]))

    if len(superBuckets) > 0:
        if number == 1 or i == None: 
            # add the only one super bucket that spans all words (== no bucketing)
            boundareis.append((superBuckets[0][0][0], superBuckets[0][-1][0]))
        else:
            # add the last bucket
            boundareis.append((superBuckets[i+1][0][0], superBuckets[i+1][-1][0]))

    return boundareis
    
###################################################################################################
###################################################################################################

def searchBucket(boundareis, ratio):
    for bucket in range(len(boundareis)):
       if boundareis[bucket][0] <= ratio and ratio < boundareis[bucket][1]:
           return bucket
           
    return len(boundareis) - 1

###################################################################################################
###################################################################################################

def getHistories(hist, card, boundareis, ratioType):
    histories = []
    
    for i in range(len(boundareis)):
        histories.append([])
        
    for each in hist.keys():
        ratio, add = computeRatio(float(hist[each]), float(card[each]), ratioType)
        
        bucket = searchBucket(boundareis, ratio)
        histories[bucket].append(each)
        
    return histories
