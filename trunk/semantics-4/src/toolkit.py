#!//usr/bin/python
# -*-  coding: UTF-8 -*-

#import psyco; psyco.full() 

import codecs
import re
import semantics
from lexMap import mapCmp
from xml.dom import minidom
import os
import sys
import random
from os.path import *

######################################################################################################
######################################################################################################

def sumfVect(fVect, idx):
#    print fVect
    sum = 0
    for each in fVect:
        if idx == 0:
            sum += each
        else:
            sum += each[idx]
        
    return sum
    
def splitByContent(fVect, sBy, idx=2):
    s = sumfVect(fVect, idx)
    sDivided = s / sBy
    
    vSplit = []
    sIndex = 0
    ssOld = -10000
    
    for i in range(sIndex, len(fVect)):
        ss = sumfVect(fVect[sIndex:i], idx)
        
        if sDivided <= ss:
            if abs(sDivided - ssOld) < abs(sDivided - ss):
                vSplit.append(fVect[sIndex:i-1])
                sIndex = i-1
                ssOld = -10000
            else:
                vSplit.append(fVect[sIndex:i])
                sIndex = i
                ssOld = -10000
                
            # print("ss: %f" % ss)
        else:
            ssOld = ss
    else:
        vSplit.append(fVect[sIndex:])
            
    # print vSplit
    
    aSplit = []
    for i in range(len(vSplit)):
        if len(vSplit[i]) != 0:
            aSplit.append(vSplit[i])
            
    return aSplit

######################################################################################################
######################################################################################################

def splitByMinSize(fVect, sMinSize, idx=2):
    vSplit = []
    sIndex = 0
    
    for i in range(sIndex, len(fVect)):
        sMS = sumfVect(fVect[sIndex:i], idx)
        
        if sMinSize <= sMS:
            vSplit.append(fVect[sIndex:i])
            sIndex = i
    else:
        if len(fVect[sIndex:]) != 0:
            if sumfVect(fVect[sIndex:], idx) < sMinSize:
                # add the rest to the previous super bucket
                if len(vSplit):
                    vSplit[-1] = vSplit[-1] + fVect[sIndex:]
                else:
                    vSplit.append(fVect[sIndex:])
            else:
                # create a new superbucket because I have enough data
                vSplit.append(fVect[sIndex:])
            
##    print vSplit
##
##    for each in vSplit:
##        print("Size: %d" % sumfVect(each, idx))
##        
##    aSplit = []
##    for i in range(len(vSplit)):
##        if len(vSplit[i]) != 0:
##            aSplit.append(vSplit[i])
            
    return vSplit

######################################################################################################
######################################################################################################

def splitSequence(seq, size):
        newseq = []
        splitsize = 1.0/size*len(seq)
        for i in range(size):
            newseq.append(seq[int(round(i*splitsize)):int(round((i+1)*splitsize))])
        return newseq

###################################################################################################
###################################################################################################

DEFAULT_DS = None

DATASET_TYPES = {
    'word': DEFAULT_DS,
    'lemma': 'lemmatized',
    'pos': 'pos_tagged',
    'analytical': 'analytical',
    'signed': 'signed',

    'ctx': DEFAULT_DS,

    'speech_act': DEFAULT_DS,
    'domain_speech_act': DEFAULT_DS,
    'domain': DEFAULT_DS,

    'off': DEFAULT_DS,
}

DONT_LOWER_SETS = ['pos', 'rpos', 'analytical', 'ctx']

def getDialogueActs(acts, data_set):
    const_mapping = False
    random_mapping = False
    domain_speech_act_mapping = False
    speech_act_mapping = False
    domain_mapping = False
    ctx_mapping = False
    dont_lower = data_set in DONT_LOWER_SETS

    if data_set.startswith('const'):
        items = data_set.split('_', 1)
        if len(items) == 2:
            const_mapping = items[1]
        else:
            const_mapping = 'constant'

    elif data_set == 'off':
        const_mapping = 'off'

    elif data_set.startswith('random'):
        items = data_set.split('_', 1)
        if len(items) == 2:
            random_mapping = int(items[1]) - 1
        else:
            raise ValueError("Specify random dataset cardinality (eg. random_100)")
        random.seed(fileName)

    elif data_set == 'domain_speech_act':
        domain_speech_act_mapping = True

    elif data_set == 'speech_act':
        speech_act_mapping = True

    elif data_set == 'domain':
        domain_mapping = True

    elif data_set == 'ctx':
        ctx_mapping = True


    last_semantics = 'FIRST_ACT'

    for utter in acts:
        for txt, attrs in utter:
            txt = txt.split()

            speech_act = attrs['speech_act']
            conversational_domain = attrs['conversational_domain']

            if const_mapping:
                txt = [const_mapping for w in txt]
            if random_mapping:
                txt = ['rand%04d' % random.randint(0, random_mapping) for w in txt]
            if domain_speech_act_mapping:
                subs = '%s.%s' % (conversational_domain, speech_act)
                txt = [subs for w in txt]
            if speech_act_mapping:
                subs = '%s' % (speech_act, )
                txt = [subs for w in txt]
            if domain_mapping:
                subs = '%s' % (conversational_domain, )
                txt = [subs for w in txt]
            if ctx_mapping:
                subs = '%s' % (last_semantics, )
                txt = [subs for w in txt]

            txt = ' '.join(txt)

            if not dont_lower:
                txt = txt.lower()

            txt = txt.replace('_', 'x')

            yield txt

        if utter:
            last_semantics = attrs['semantics']
            if not last_semantics:
                last_semantics = 'NONE'
            last_semantics = last_semantics.replace(' ', '')

def readSemantics(files, data_sets, parseType='LR', default_data_set='normalized'):
    from svc.ui.dxml import DXML

    types = []
    for d in data_sets:
        d = DATASET_TYPES[d]
        if d is None:
            d = default_data_set
        types.append(d)

    for fn in files:
        dxml = DXML.readFromFile(fn)
        to_zip = []

        sem_list = []
        for da in dxml.getSemantics():
            sem_list.extend(da)

        to_zip.append(sem_list)

        for set_name, type_name in zip(data_sets, types):
            acts = dxml.getDialogueActs(type_name)
            to_zip.append(list(getDialogueActs(acts, set_name)))

        lengths = [len(i) for i in to_zip]

        if min(lengths) != max(lengths):
            raise ValueError("Bad count of <parametrized_act>s in file %r" % fn)

        file_id = os.path.splitext(os.path.basename(fn))[0]

        for i, item in enumerate(zip(*to_zip)):
            da_id = "%s_%.5d" % (file_id, i) 

            da_semantics = item[0]
            da_txts = item[1:]

            smntcs = [semantics.Semantics(da_id, da_semantics, txt, parseType) for txt in da_txts]
            yield smntcs

###################################################################################################
###################################################################################################

def readDialogFileUnsupervised(semanticsList, fileName, parseType="LR"):
    dialogue = minidom.parse(fileName)
    
    source = basename(fileName)[:-4]
    source = source.replace('-', '_')
    i = 0
    
    for text in dialogue.getElementsByTagName("text"):
        if text.getAttribute("type") == "normalized":
            id = "%s_%.5d" % (source, i) 
        
            t = getNodeText(text)
            t = removeTagsFromText(t).lower()
        
            smntcs = semantics.Semantics(id, "", t, parseType)
            semanticsList.append(smntcs)
        
            i += 1

###################################################################################################
###################################################################################################

def readDialogFileGroupTurns(semanticsList, fileName, parseType="LR"):
    dialogue = minidom.parse(fileName)
    
    source = basename(fileName)[:-4]
    source = source.replace('-', '_')
    i = 0
    
    for turn in dialogue.getElementsByTagName("turn"):
        tt = ""
        ss = ""
        
        for dialogue_act in turn.getElementsByTagName("dialogue_act"):
            t = getNodeText(dialogue_act)
            t = removeTagsFromText(t).lower()
            
            s = dialogue_act.getAttribute("semantics").strip()
    
##            if len(s) == 0:
##                # ignore this dialogue act because 
##                # we do not have semantics for the text
##                continue
    
            tt = tt + ' ' + t
            
            if len(ss) != 0:
                ss = ss + ' , ' + s
            else:
                ss = s
                
        ss = semantics.cleanSmntcs(ss)
        
        id = "%s_%.5d" % (source, i) 
        smntcs = semantics.Semantics(id, ss, tt, parseType)
           
        semanticsList.append(smntcs)
        
        i += 1

###################################################################################################
###################################################################################################

def saveDictionaries(fileNamePrefix, semanticsDictionary, wordDictionary):
    # save dictionaries
    f = open(fileNamePrefix + "/concept.dict", "w")
    l = semanticsDictionary.keys()
    l.sort(mapCmp)
    for concept in l:
        f.write(concept + "\n")
    f.close()
    
    f = open(fileNamePrefix + "/word.dict", "w")
    l = wordDictionary.keys()
    l.sort(mapCmp)
    for word in l:
        f.write(word.encode("utf-8") + "\n")
    f.close()
    
###################################################################################################
###################################################################################################

def testProb(probs, tolerance = 0.001):
    sum = 0
    
    for each in probs:
        sum += each
        
    if abs(sum - 1.0) < tolerance:
        return True

    return False
    
###################################################################################################
###################################################################################################

def testProb2(probs, tolerance = 0.001):
    for i in probs:
        sum = 0
        
        for each in i:
            sum += each
            
        if abs(sum - 1.0) > tolerance:
            return False

    return True
    
###################################################################################################
###################################################################################################

def readHResult(fileName, multiple=True, exclude = False):
    file = open(fileName, 'r')
    
    name = []
    correctness = []
    accuracy = []
    n = []
    sum = 0
    nLines = 0
    
    for line in file.readlines():
        if line[0] == 'C':
            nLines += 1
            
            i = line.find("rec:") + len("rec:")
            
            nm = line[:i-5]
                
            j = line.find(")  [")
            k = line.find("N=") + len("N=")
            l = line.find("]")
            nn = float(line[k:l])
            n.append(nn)
            
            if exclude:
                # exclude semanatics with the length of 1
                if nn == 1:
                    continue
                
            sum += nn
            line = line[i:j].split("(")
            
            correctness.append(float(line[0]))
            accuracy.append(float(line[1]))
            name.append(nm)
                
    if multiple:
        for i in range(len(accuracy)):
            accuracy[i] = accuracy[i]*n[i] / sum * nLines
            
    return name, correctness, accuracy, n, sum

###################################################################################################
###################################################################################################

def readHResultX(fileName):
    file = open(fileName, 'r')
    
    name = []
    sum = 0
    nLines = 0
    vect = []
    
    for line in file.readlines():
        if line[0] == 'C':
            nLines += 1
            
            i = line.find("rec:") + len("rec:")
            
            nm = line[:i-5]
                
            # N = 
            k = line.find("N=") + len("N=")
            l = line.find("]", k)
            nN = float(line[k:l])

            # H =
            k = line.find("H=") + len("H=")
            l = line.find(",", k)
            hH = float(line[k:l])

            # I =
            k = line.find("I=") + len("I=")
            l = line.find(",", k)
            iI = float(line[k:l])
            
            name.append(nm)
            vect.append([hH, iI, nN])

    return name, vect

###################################################################################################
###################################################################################################

def pairNames(firstName, first, secondName, second):
    i = 0
    j = 0
    
    fA = []
    sA = []
    collectedName = []
    
    for i in range(len(firstName)):
        try:
            j = secondName.index(firstName[i])
            
            fA.append(first[i])
            sA.append(second[j])
            collectedName.append(firstName[i])
            
        except ValueError:
            pass
    
    for i in range(len(secondName)):
        try:
            j = firstName.index(secondName[i])

            try:
                k = collectedName.index(secondName[i])
                # it is already there
            except ValueError:
                # it is not there
                
                fA.append(first[i])
                sA.append(second[j])
        except ValueError:
            pass
    
    return fA, sA
