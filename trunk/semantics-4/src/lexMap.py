# -*-  coding: UTF-8 -*-

import re
import sys
import codecs
import os.path
from types import *
    
def conceptCmp(x, y):
    if isinstance(x, (long, int)) or isinstance(y, (long, int)):
        return cmp(x, y)
    else:
        xx = x.lower()
        yy = y.lower()
        
        if xx == "_empty_" and yy == "_empty_":
            return 0
        elif xx == "_empty_":
            return -1
        elif yy == "_empty_":
            return 1
        
        if xx == "_dummy_" and yy == "_dummy_":
            return 0
        elif xx == "_dummy_":
            return -1
        elif yy == "_dummy_":
            return 1
            
        if xx == "_sink_" and yy == "_sink_":
            return 0
        elif xx == "_sink_":
            return -1
        elif yy == "_sink_":
            return 1
            
        if xx == "_unseen_" and yy == "_unseen_":
            return 0
        elif xx == "_unseen_":
            return -1
        elif yy == "_unseen_":
            return 1
            
##        if xx[0] == "_":
##            return -1
##        if yy[0] == "_":
##            return 1
        
##        return cmp(xx, yy)
        
    return cmp(x, y)

def mapCmp(x, y):
    if not isinstance(x, ListType) and not isinstance(x, ListType):
        return conceptCmp(x, y)
        
    if (isinstance(x, ListType) or isinstance(x, TupleType)) and \
        (isinstance(y, ListType)  or isinstance(y, TupleType)):
        for i in range(len(x)):
            cC = conceptCmp(x[i], y[i])
            if cC != 0:
                return cC
        return 0
    
    raise TypeError, "Unsupported types of variables"

######################################################################################################
######################################################################################################

class LexMap:
    """  This class implements map object for a wordMap and a conceptMap.
    """
    
    def __init__(self, id=None):
        self.id = id
        self.copy = False

    def __len__(self):
        return len(self.lexMap)
        
    def __getitem__(self, i):
        return self.lexMap[i]
        
    def has_key(self, i):
        return self.lexMap.has_key(i)
        
    def keys(self):
        return self.lexMap.keys()

    def values(self):
        return self.lexMap.values()
    ######################################################################################################
    ######################################################################################################
    
    def create(self, dictionary, copy = False):
        self.copy = copy
        
        l = dictionary.keys()
        l.sort(mapCmp)

        i = 0
        lexMap = {}
        for lex in l:
            if copy:
                lexMap[lex] = lex
            else:
                lexMap[lex] = str(i)
            i += 1
        self.lexMap = lexMap

        return self

    ######################################################################################################
    ######################################################################################################
    
    def reverse(self):
        lexKeys = self.lexMap.keys()
        
        reverseMapList = {}
        for each in lexKeys:
            reverseMapList[self.lexMap[each]] = each
            
        return reverseMapList

    ###############################################################################################
    #
    #   I/O methods
    #
    ###############################################################################################

    def read(self, fileName):
        self.lexMap = {}
        
        mapFile = codecs.open(fileName, "r", "utf-8")
        for line in mapFile.readlines():
            lineSplit = line.strip().split('\t')
            self.lexMap[lineSplit[1]] = lineSplit[0]
        mapFile.close()
        
        self.id = os.path.splitext(os.path.basename(fileName))[0]

        return self
        
    ######################################################################################################
    ######################################################################################################
    
    def save(self, fileNamePrefix, copy = None):
        """ Save maps
        """
        
        if not copy:
            copy = self.copy
            
        f = codecs.open(fileNamePrefix + "/" + self.id, "w", "utf-8")

        l = self.lexMap.keys()
        l.sort(mapCmp)

        i = 0
        lexMap = {}
        for lex in l:
            if copy:
                lexMap[lex] = lex
            else:
                lexMap[lex] = str(i)
                
            f.write(lexMap[lex] + "\t" + lex + "\n")
            i += 1
            
        self.lexMap = lexMap
 

######################################################################################################
######################################################################################################

class CopyMap:
    """  This class implements copy map object.
    """
    
    def __init__(self, id=None):
        self.id = id

    def __getitem__(self, i):
        return i
        
    def create(self, dictionary):
        return self

    def reverseMap(self):
        return CopyMap()

    ###############################################################################################
    #
    #   I/O methods
    #
    ###############################################################################################

    def read(self, fileName):
        return self
        
    ######################################################################################################
    ######################################################################################################
    
    def save(self, fileNamePrefix):
        return
