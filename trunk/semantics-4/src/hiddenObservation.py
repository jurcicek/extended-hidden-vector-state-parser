# -*-  coding: UTF-8 -*-

import re
import sys
import codecs
import os.path

import sparseProbability

class HiddenObservation:
    """  This class implements hidden observation with depth 4.
         The first row contains observation if were typed.  
    """
    
    def __init__(self, hiddenObs = None, id = None):
        self.hiddenObs = hiddenObs
        self.id = id

    def __len__(self):
        return len(self.hiddenObs)
        
    def __getitem__(self, i):
        return self.hiddenObs[i]

    def getHidden(self):
        return self.hiddenObs
        
    ######################################################################################################
    ######################################################################################################
    
    def collectConceptsC1C2C3C4(self, dt):
        for hiddenVect in self.hiddenObs:
            hv = hiddenVect[1:5]

            sp = sparseProbability.SparseProbability(dt)
            sp.setValue(hv, hiddenVect[0])

    ######################################################################################################
    ######################################################################################################
    
    def collectConceptsC1C2C3(self, dt):
        for hiddenVect in self.hiddenObs:
            hv = hiddenVect[1:4]
            
            sp = sparseProbability.SparseProbability(dt)
            sp.setValue(hv, hiddenVect[0])

    ######################################################################################################
    ######################################################################################################
    
    def collectConceptsC1C2(self, dt):
        for hiddenVect in self.hiddenObs:
            hv = hiddenVect[1:3]
            
            sp = sparseProbability.SparseProbability(dt)
            sp.setValue(hv, hiddenVect[0])

    ######################################################################################################
    ######################################################################################################
    
    def collectConceptsC2C3C4(self, dt):
        for hiddenVect in self.hiddenObs:
            hv = hiddenVect[2:5]

            sp = sparseProbability.SparseProbability(dt)
            sp.setValue(hv, hiddenVect[1])

    ######################################################################################################
    ######################################################################################################
        
    def getSetOfConcepts(self):
        dct = {}
        for hiddenVect in self.hiddenObs:
            for each in hiddenVect[1:5]:
                dct[each] = 1
                
        return dct.keys()

    ######################################################################################################
    ######################################################################################################
    
    def getSetOfConceptVectors(self):
        dct = {}
        for hiddenVect in self.hiddenObs:
            dct[tuple(hiddenVect[1:5])] = 1
                
        return dct.keys()


    ###############################################################################################
    #
    #   I/O methods
    #
    ###############################################################################################

    def read(self, fileName):
        hiddenFile = codecs.open(fileName, "r", "utf-8")
        
        hidden = []
        for line in hiddenFile.readlines():
            hidden.append(line.strip().split('\t'))
        
        hiddenFile.close()
        
        self.hiddenObs = hidden
        self.id = os.path.splitext(os.path.basename(fileName))[0]
        return self

    ###############################################################################################
    ###############################################################################################

    def save(self, fileNamePrefix, conceptMap, wordMap):
        hddnFile = codecs.open(fileNamePrefix + "/" + self.id + ".hddn", "w", "utf-8")
        
        for hiddenVect in self.hiddenObs:
            if len(hiddenVect) > 0:
                
                hddnFile.write(wordMap[hiddenVect[0]] + "\t")

                for hidden in hiddenVect[1:5]:
                    hddnFile.write(conceptMap[hidden] + "\t")
                
                hddnFile.write(hiddenVect[5] + "\n")
            
        hddnFile.close()

    ###############################################################################################
    ###############################################################################################

    def printHidden(self):
        for hiddenVect in self.hiddenObs:
            if len(hiddenVect) > 0:
                
                print '\t'.join(hiddenVect)
