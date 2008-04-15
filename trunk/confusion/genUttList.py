#!//usr/bin/python2.4
# -*-  coding: UTF-8 -*-

import glob
import getopt
import sys
import os
from os.path import *
from xml.dom import minidom
import codecs
import re

uttList = []
dict = {}

###################################################################################################
###################################################################################################

def getNodeText(node):
    """ I am able to get get text form dialogue_act, but only without named entities.
    """
    
    s = ""
    for child in node.childNodes:
        if child.nodeType == child.TEXT_NODE:
            s += child.data
        else:
            s += getNodeText(child)
    return s
    
###################################################################################################
###################################################################################################

def removeTagsFromText(text):
    t = text.strip()
    t = re.sub(r' +', ' ', t)
    t = re.sub(r'\[[^\]]*\]', "", t)
    t = re.sub(r' +', ' ', t)
    t = t.strip()
    
    return t

###################################################################################################
###################################################################################################

def readDialogFile(uttList, fileName):
    dialogue = minidom.parse(fileName)
    
    for ne_typed_text in dialogue.getElementsByTagName("dialogue_act"):
        t = getNodeText(ne_typed_text)
        t = removeTagsFromText(t).lower()
        
        uttList.append(t)
        
###################################################################################################
###################################################################################################



lst = glob.glob(os.path.join(sys.argv[1], '*.xml'))
lst.sort()
#lst = lst[:100]

for fileName in lst:
    print("Reading file: " + fileName)
    readDialogFile(uttList, fileName)

print(">>>>>>>>>>>>>>>>>>")

###############################################################
uttFile = codecs.open('utt.txt', 'w', 'UTF-8')
for utt in uttList:
    uttFile.write(utt + ';\n')
    
    words = utt.split()
    
    for word in words:
        dict[word] = 1
uttFile.close()

###############################################################
uttFile = codecs.open('uttlm.txt', 'w', 'UTF-8')
for utt in uttList:
    if utt == "":
        utt = "empty_sentence"
    uttFile.write(utt + '\n')
    
uttFile.close()

###############################################################
dictFile = codecs.open('dict.txt', 'w', 'UTF-8')
dict_keys = dict.keys()
dict_keys.sort()
for word in dict_keys:
    dictFile.write(word + '\n')
dictFile.close()

print("<<<<<<<<<<<<<<<<<<")
