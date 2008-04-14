# -*-  coding: UTF-8 -*-

import re
import sys
import codecs

countUnseen = 0
countSeen = 0

class Observation:
    """  This class implements an observation class.
    """
    
    def __init__(self, obs = None, id = None):
        self.obs = obs
        self.id = id
    
    def __getitem__(self, i):
        return self.obs[i]
    
    ###############################################################################################
    ###############################################################################################
    
    def getSefOfWords(self):
        return self.obs
        
    ###############################################################################################
    ###############################################################################################

    def markUnseenWords(self, wordMap):
        global countUnseen
        global countSeen
        
        obs = []
        
        for each in self.obs:
            if wordMap.has_key(each):
                obs.append(each)
                countSeen += 1
            else:
                obs.append('_unseen_')
                countUnseen += 1
                
        return obs
        
    ###############################################################################################
    #
    #   I/O methods
    #
    ###############################################################################################

    def read(self, fileName, rWordMap = None, ignoreErrors = False):
        obsFile = codecs.open(fileName, "r", "utf-8")
        
        obs = []
        for each in obsFile.readlines():
            each = each.strip()
            if not each == "":
                if rWordMap:
                    try:
                        obs.append(rWordMap[each])
                    except KeyError:
                        if ignoreErrors:
                            obs.append(each)
                        else:
                            raise
                else:
                    obs.append(each)
                
        obsFile.close()
        
        self.obs = obs
        
        return self
        
    ###############################################################################################
    ###############################################################################################

    def save(self, fileNamePrefix, wordMap, ext = ".obs", markUW = False):
        obsFile = codecs.open(fileNamePrefix + "/" + self.id + ext, "w", "utf-8")
        
        if markUW:
            obs = self.markUnseenWords(wordMap)
        else:
            obs = self.obs
            
        for each in obs:
            if wordMap.has_key(each):
                obsFile.write(wordMap[each] + "\n")
            else:
                obsFile.write(each + "\n")
            
        obsFile.close()


