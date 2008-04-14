# -*-  coding: UTF-8 -*-

import re
import sys
import codecs
import os.path
from types import *
from lexMap import mapCmp

class SparseProbability:
    """  Implements sparse probability table.
    """
    
    def __init__(self, tree = None):
        
        if tree == None:
            self.tree = {}
        else:
            self.tree = tree
    
    def __getitem__(self, i):
        return self.tree[i]
    
    def __len__(self):
        return len(self.vectList())
        
    def getDim(self):
        localTree = self.tree
        
        for i in range(100):
            if isinstance(localTree, dict):
                localTree = localTree[localTree.keys()[0]]
            else:
                return i
            
    ###################################################################################################
    ###################################################################################################
    
    def setValue(self, vector, value):
        vect = vector[:]
        vect.reverse()
        
        localTree = self.tree
        
        for i in range(len(vect)-1):
            if localTree.has_key(vect[i]):
                localTree = localTree[vect[i]]
            else:
                # the whole vect is not in the tree
                # I have to add the rest of the vect
                for j in range(i, len(vect) - 1):
                    localTree[vect[j]] = {}
                    localTree = localTree[vect[j]]
                
                # set finally the value
                localTree[vect[-1]] = value
                break
        else:
            # the whole vect (it's porion except last column) is in the tree
            # so, modify the value or add the value
            localTree[vect[-1]] = value
        
    ###################################################################################################
    ###################################################################################################
    
    def getValue(self, vector):
        vect = vector[:]
        vect.reverse()
        
        localTree = self.tree
        
        for i in range(len(vect)-1):
            if localTree.has_key(vect[i]):
                localTree = localTree[vect[i]]
            else:
                raise KeyError, "There is no key " + str(vect[i]) + ":" + str(i) + " in " + str(vect)
        else:
            return localTree[vect[-1]]
 
    ###################################################################################################
    ###################################################################################################
    
    def getSafeValue(self, vector):
        try:
            return self.getValue(vector)
        except:
            return 0
            
    ###################################################################################################
    ###################################################################################################
    
    def addValue(self, vector, value):
        try:
            v = self.getValue(vector)
            self.setValue(vector, v + value)
        except:
            # there is now previous value
            self.setValue(vector, value)
        
    ###################################################################################################
    ###################################################################################################

    def vectRec(self, list, tree, stack):
        for each in tree.keys():
            if type(tree[each]) == DictType:
                self.vectRec(list, tree[each], stack[:] + [each])
            else:
                list.append(stack[:] + [each])
        
    def vectList(self):
        list = []
        
        for each in self.tree.keys():
            if type(self.tree[each]) == DictType:
                self.vectRec(list, self.tree[each], [each])
            else:
                list.append([each])
        
        list.sort(mapCmp)
        
        for i in range(len(list)):
            list[i].reverse()

        return list
        
    ###################################################################################################
    ###################################################################################################
    
    def vectSubList(self, indexes):
        v = self.vectList()
        
        collect = []
        d = {}
        for each in v:
            cV = self.compactVect(each, indexes)
            tcV = tuple(cV)
            
            if not d.has_key(tcV):
                d[tcV] = 1
                collect.append(cV)
        
        return collect
    
    ###################################################################################################
    ###################################################################################################
    
    def compactVect(self, vect, indexes):
        v = []
        
        for each in indexes:
            v.append(vect[each])
            
        return v
        
    ###################################################################################################
    ###################################################################################################
    
    def marginalize(self, indexes):
        """ Marginalize sparse probability distribution. Keep only indexes.
        
            Example: Sum{indexes=[0, 1]} P(C1, C2, C3, C4) = P(C1, C2)
        """
        sp = SparseProbability()
        
        list = self.vectList()
        
        for each in list:
            cEach = self.compactVect(each, indexes)
            gP = self.getValue(each)
            
            sp.addValue(cEach, gP)
        
        return sp

    ###################################################################################################
    ###################################################################################################

    def conditionalize(self, indexes):
        """ Compute conditional probability  given indexes of parents.
        
            Example: P(C1|C2) = P(C1, C2) / P(C2)
        """
        
        marg = self.marginalize(indexes)

        sp = SparseProbability()
        
        list = self.vectList()
        for each in list:
            cEach = self.compactVect(each, indexes)
            gP = self.getValue(each)
            mP = marg.getValue(cEach)
            
            try:
                sp.setValue(each, gP / mP)
            except ZeroDivisionError:
                sp.setValue(each, 0.0)
        
        return sp

    ###################################################################################################
    ###################################################################################################
    
    def normJoint(self):
        """ The method normalize all probabilities so that the prbaility sums to one.
        """
        
        list = self.vectList()
        sum = 0.0
        sp = SparseProbability()
        
        for each in list:
            sum += self.getValue(each)
            
        for each in list:
            sp.setValue(each, self.getValue(each) / sum)
    
        return sp
        
    ###################################################################################################
    ###################################################################################################
    
    def multiple(self, indexes, spMult):
        """ Multiply sparse probability distribution. Using given indexes.
        
            Example:  
            sp.P(W, C1, C2, C3, C4) = self.P(W | C1, C2, C3, C4) * spMult.P(C1, C2, C3, C4)
        """
        sp = SparseProbability()
        
        list = self.vectList()
        
        for each in list:
            cEach = self.compactVect(each, indexes)
            gP = self.getValue(each)
            mP = spMult.getValue(cEach)
            
            sp.setValue(each, gP*mP)
        
        return sp

    ###################################################################################################
    ###################################################################################################
    
    def insertPenalty(self, index, penalty, selfCard):
        """ Insert penalty to particular index of the fisrt variable
            and then normalize to unity.
        """
        sp = SparseProbability()
        
        dm = self.getDim()
        lst = self.vectSubList(range(1, dm))
        
        for i in range(len(lst)):
            # copy probability
            for j in range(selfCard):
                if j == index:
                    # copy value and add penalty
                    sp.setValue([j] + lst[i], self.getSafeValue([j] + lst[i]) * penalty)
                else:
                    # just copy
                    sp.setValue([j] + lst[i], self.getSafeValue([j] + lst[i]))
                    
            # normalize probability to sum to unity
            sum = 0
            for j in range(selfCard):
                sum += sp.getSafeValue([j] + lst[i])
        
            for j in range(selfCard):
                sp.setValue([j] + lst[i], (sp.getSafeValue([j] + lst[i]) + 1e-120) /(sum + 1e-120*selfCard))

        return sp
