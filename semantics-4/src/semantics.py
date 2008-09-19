# -*-  coding: UTF-8 -*-

import re
import sys
import codecs

import toolkit
from observation import Observation
from hiddenObservation import HiddenObservation

###################################################################################################
###################################################################################################

def getDepthOfComposedStack(stackNew, stackOld):
    lngth = lngthNew = len(stackNew)
    lngthOld = len(stackOld)
    if lngthNew > lngthOld:
        lngth = lngthOld
    
    for i in range(lngth):
        if stackNew[i] != stackOld[i]:
            return i
    
    return lngth
    
###################################################################################################
###################################################################################################

def addRelevantPartOfStack(oldDepth, depth, stack):
    smntcs = ""
    
    if oldDepth >= depth:
        for i in range(oldDepth - depth):
            smntcs += "),"  
    
    for each in stack[depth:]:
        if each.islower():
            smntcs += " " + each + " "
        else:
            smntcs += "," + each + "("  

    return smntcs
    
###################################################################################################
###################################################################################################

# I have to correct this function so that I will be able to read CMB file with 
# parse trees different to RL-YOUNG type

def readSemanticsFromCMBFile(fileName, lemmatized=False):
    cmbFile = codecs.open(fileName, "r", "UTF-8")
    
    smntcs = ""
    oldStack = []
    oldDepth = 0
    for line in cmbFile.readlines():
        splitLine = line.strip().split("\t")
        
        #splitLine = splitLine[0:1] + splitLine[6:10]
        if lemmatized:
            splitLine = splitLine[1:2] + splitLine[7:11]
        else:
            splitLine = splitLine[0:1] + splitLine[7:11]
        
        stack = []
        for each in splitLine[0:5]:
            if each != "_EMPTY_" and each != "_empty_":
                stack.append(each)
    
        if stack == []:
            continue
                
        stack.reverse()
        depth = getDepthOfComposedStack(stack, oldStack)
        smntcs += addRelevantPartOfStack(oldDepth, depth, stack)
    
        oldDepth = len(stack) - 1 
        oldStack = stack
    
    for i in range(oldDepth):
        smntcs += ")"  
        
    return cleanSmntcs(smntcs)

###################################################################################################
###################################################################################################

def getDepthOfSemantics(text):
    parentheses = 0
    maxParentheses = 0
    
    for i in range(len(text)):
        if text[i] == '(':
            parentheses +=1
        elif text[i] == ')':
            parentheses -=1
            if parentheses < 0:
                raise ValueError("Missing a left parenthesis.") 
                    
        if maxParentheses < parentheses:
            maxParentheses = parentheses
            
    return maxParentheses

###################################################################################################
###################################################################################################



def removeTextFromSemantics(smntcs):
    """
    Only pure EHVS semantics will be returned. All words (imput
    tokens) will be removed. Also concepts like _DUMMY_ and _SINK_
    are removed.
    """    
    smntcsOld = smntcs
    
##    print ">>> " + smntcs.encode('ascii', 'backslashreplace')
    
    # remove words with underline
    smntcs = smntcs.replace("_dummy_","")
    smntcs = smntcs.replace("_unseen_","")
    
    # remove rest of the words
    smntcs = re.sub(r'[^A-Z_(),]+', "", smntcs)
    smntcs = re.sub(r'_+', "_", smntcs)
    
    smntcs = cleanSmntcs(smntcs)

    # remove _DUMMY_ concept, but only leaves
    #  if _DUMMY_ is not a leave, keep it in semantics, it is decoding mistake
    smntcs = removeLeafConcept(smntcs, "_DUMMY_")
    
    smntcs = smntcs.strip()

    smntcs = cleanSmntcs(smntcs)

    if not smntcs.find("_DUMMY_") == -1 and smntcs != "_DUMMY_":
        print("Error: _DUMMY_ is not a leaf in:")
        print("--- " + smntcsOld.encode('ascii', 'replace'))
        print("+++ " + smntcs)

    if not smntcs.find("_SINK_") == -1:
        print("Error: _SINK_ is in semantic:")
        print("--- " + smntcsOld.encode('ascii', 'replace'))
        print("+++ " + smntcs)

    if len(smntcsOld) == 0 or \
      (smntcsOld[0] == "_" and not smntcsOld[1].isupper()) or \
      (smntcsOld[0] != "_" and not smntcsOld[0].isupper()) or \
      (smntcsOld[-1] != ")" and not smntcsOld[-1].isupper()):
        print("Error: there is no root concept in semantic:")
        print("--- " + smntcsOld.encode('ascii', 'backslashreplace'))
        print("+++ " + smntcs)

##    print "<<< " + smntcs

    return smntcs


def removeConceptsFromSemantics(smntcs):
    """
    Only pure text is on the otput of this function. All concepts are removed from the input semnatics. 
    """

    # remove rest of the words
    text = re.sub(r'[A-Z_(),]+', " ", smntcs)
    text = re.sub(r'\ +', " ", text)
    text = re.sub(r'_+', "_", text)
    
    text = text.strip()

    return text

def getCuedDA(smntcs):
    DA = ""
    
    return DA
    
######################################################################################################
######################################################################################################


def cleanSmntcs(smntcs):
    for i in range(5):
        smntcs = smntcs.strip()
        
        smntcs = re.sub(r' +\(', '(', smntcs)
        smntcs = re.sub(r'\( +', '(', smntcs)
        smntcs = re.sub(r' +\)', ')', smntcs)
        smntcs = re.sub(r'\) +', ')', smntcs)
        smntcs = re.sub(r' ?,', ',', smntcs)
        smntcs = re.sub(r', ?', ',', smntcs)
        smntcs = re.sub(r' +', ' ', smntcs)
        smntcs = re.sub(r' +', ' ', smntcs)
        
        smntcs = re.sub(r'^,+', "", smntcs)
        smntcs = re.sub(r',+$', "", smntcs)
        smntcs = re.sub(r',+', ",", smntcs)
        
        
        smntcs = smntcs.replace("()","")

        smntcs = smntcs.replace("),)", "))")
        smntcs = smntcs.replace("(,", "(")
        smntcs = smntcs.replace(",)", ")")
        smntcs = smntcs.replace("((", "(")
        smntcs = smntcs.replace(" )", ")")
        smntcs = smntcs.replace(" (", "(")

        # remove underline form deleted words
        smntcs = smntcs.replace("(_)","")
        smntcs = smntcs.replace(",_,",",")

    for i in range(4):
        # remove repeated words, be beware of _SINK_DUMMY_ it was result of transforming _,_ in _SINK_,_DUMMY_ 
        smntcs = re.sub(r'([(),])([A-Z_]+),\2', r'\1\2', smntcs)
        smntcs = re.sub(r'^([A-Z_]+),\1,', r'\1,', smntcs)
        smntcs = re.sub(r',([A-Z_]+),\1$', r',\1', smntcs)
        smntcs = re.sub(r'^([A-Z_]+),\1$', r'\1', smntcs)
        
    return smntcs

###################################################################################################
###################################################################################################

def removeLeafConcept(smntcs, concept):
    smntcs = smntcs.replace("(" + concept + ")","")
    smntcs = smntcs.replace("(" + concept + ",","(")
    smntcs = smntcs.replace("," + concept + ")",")")
    smntcs = smntcs.replace("," + concept + ",",",")
    smntcs = re.sub(r'^' + concept + r',', "", smntcs)
    smntcs = re.sub(r',' + concept + r'$', "", smntcs)
    
    # I want to keep at least something in the semantics. I cannot remove the last concept in the semantics.
    # smntcs = re.sub(r'^' + concept + r'$', "", smntcs)
    
    return smntcs

###################################################################################################
###################################################################################################

def splitSmntcsToMlf(smntcs):
    smntcsSplit = []
##    smntcsSplit = [smntcs]
    
    i = 0
    for j in range(len(smntcs)):
        if smntcs[j] == ",":
            if smntcs[i:j] != "":
                smntcsSplit.append(smntcs[i:j])
            i = j + 1
        if smntcs[j] == "(":
            if smntcs[i:j] != "":
                smntcsSplit.append(smntcs[i:j])
            smntcsSplit.append("(")
            i = j + 1
        if smntcs[j] == ")":
            if smntcs[i:j] != "":
                smntcsSplit.append(smntcs[i:j])
            smntcsSplit.append(")")
            i = j + 1
    
    if smntcs[i:] != "":
        smntcsSplit.append(smntcs[i:])

    smntcsSplit.append(".")

    return smntcsSplit
    
###################################################################################################
###################################################################################################

class Semantics:
    """  
    This class implements basic processing for abstract semantic annotation acording to He and Young (2005).
    """
    
    def __init__(self, id, semantics, text, parseType="LR"):
        # this variable is used by parseLeaves()
        self.parseType = parseType
        
        self.tokenizeText(text)
        self.id = id

        self.semantics = cleanSmntcs(semantics)
        self.createSemanticsTree()
        
    def __str__(self):
        return (self.semantics+":"+self.text)

    def tokenizeText(self, text):
        self.text = text.strip()
        self.text = re.sub(r' +', ' ', self.text)
        if not len(self.text) == 0:
            self.wordList = self.text.split(' ')
            
            wl = []
            for word in self.wordList:
                if not word[0] == "[":
                    wl.append(word)
                else:
                    print word
            
            self.wordList = wl
        else:
            self.text = ""
            self.wordList = []
        
        if self.parseType == "RL":
            # reverse the text because we are going to create right-left parse derivation
            self.wordList.reverse()
            self.text = " ".join(self.wordList)
            
    def isEmpty(self):
        if len(self.semantics) == 0:
            return True
        
        return self.semantics.isspace()
        
    def isValid(self):
        return True

    def splitByComma(self, text):
        parentheses = 0
        splitList = []
        
        oldI=0
        for i in range(len(text)):
            if text[i] == '(':
                parentheses +=1
            elif text[i] == ')':
                parentheses -=1
                if parentheses < 0:
                    raise ValueError("Missing a left parenthesis.") 
            elif text[i] == ',':
                if parentheses == 0:
                    if oldI == i:
                        raise ValueError("Splited segmend do not have to start with a comma.") 
                    else:
                        splitList.append(text[oldI:i].strip())
                        oldI = i+1
        else:
            splitList.append(text[oldI:].strip())
            
        return splitList

    def parseRoot(self, semantics):
##      print "R:"+smntcs
        smntcs = semantics.strip()
        
        try:
            l = smntcs.index('(')
        except ValueError:
            return [smntcs, []]
        
        if l == 0:
            raise ValueError("Empty root concept: %s" % semantics) 
            
        try:
            r = smntcs.rindex(')')
        except ValueError:
            raise ValueError("Missing a right parenthesis.") 
        
        return [smntcs[:l], self.parseLeaves(smntcs[l+1:r])]
        
    def parseLeaves(self, semantics):
##      print "L:"+semantics
        semantics = semantics.strip()
        if semantics:
            smntcsList = self.splitByComma(semantics)
        else:
            smntcsList = []
      
        if self.parseType == "RL":
            # reverse the tree because we are going to create right-left parse derivation
            smntcsList.reverse()
            
            # reverse text inside of the tree leaf
            if len(smntcsList) == 1 and smntcsList[0].islower():
                wordList = smntcsList[0].split(' ')                
                wordList.reverse()
                smntcsList[0] = " ".join(wordList)
            
        list = []
        for item in smntcsList:
            list.append(self.parseRoot(item))
        
        return list
        
    def createSemanticsTree(self):
        try:
            self.semanticsTree = self.parseLeaves(self.semantics)
        except ValueError:
            x = str(sys.exc_value) + " : " + self.id + " : " + self.semantics + " : " + self.text
            raise ValueError(x.encode("ascii", "backslashreplace"))
        
    def addConceptsRec(self,conceptPair,dictionary):
        if conceptPair[0].isupper():
            try:
                dictionary[conceptPair[0]] += 1
            except KeyError:
                dictionary[conceptPair[0]] = 1
        
        for item in conceptPair[1]:
            self.addConceptsRec(item,dictionary)
        
    def addConcepts(self, dictionary):
        for conceptPair in self.semanticsTree:
            self.addConceptsRec(conceptPair,dictionary)

    def addWords(self, dictionary):
        for word in self.wordList:
            try:
                dictionary[word] += 1
            except KeyError:
                dictionary[word] = 1
      
    def getObs(self, type="LR"):
        obs = []
        
        obs.append("_empty_")
        #obs.append("_dummy_")

        for word in self.wordList:
            obs.append(word)

        #obs.append("_dummy_")
        obs.append("_empty_")
            
        return Observation(obs, self.id)

    def getHiddenObs(self, type="LR"):
        if type == "LR":
            # this is the original He and Young derivation of a parse tree 
            # (only left-to-right trees)
            return self.getLRParseTree()
        if type == "LRRL":
            # this is my new version of a parse tree.
            # I generate LRRL parse tree. If I do want to generate a RL parse tree
            # I have to skip some vector state during traning or decoding
            return self.getLRRLParseTree()
        if type == "LRRL-FT":
            # It generate the same parse tree except that at RL part are ommited vector states
            # with concepts FROM and TO at c_t[1] position (this is because I know that prepositions 
            # (concepts) FROM, TO only predceeds the concept STATION
            
            return self.getLRRLParseTree(removeFT = True)
    
    def getLRParseTree(self):
        hidden = []
        
        hidden.append(["_empty_","_EMPTY_","_EMPTY_","_EMPTY_", "_EMPTY_", "1"])
        hidden.append(["_empty_","_DUMMY_","_EMPTY_","_EMPTY_", "_EMPTY_", "0"])
        
        stack = ["_empty_","_EMPTY_","_EMPTY_","_EMPTY_", "_EMPTY_"]
        for conceptPair in self.semanticsTree:
            self.addLRParseTreeRec(stack[:], hidden, conceptPair)
        hidden.append(stack[:] + ["1"])
            
        # modify the skip limit counter
        self.recountJumpIndex(hidden)
        
        return HiddenObservation(hidden, self.id)
    
    def addLRParseTreeRec(self,stack,hidden,conceptPair):
        for concept in conceptPair[0].split(' '):
            if concept.islower(): 
                # it is a word
                stack[0] = concept
            else:
                stack.insert(1, concept)
                del stack[-1]
                stack[0] = "_empty_"
            
            try:
                if not conceptPair[1][0][0].islower():
                    hidden.append(stack[:] + ["1"])
                    hidden.append(["_empty_","_DUMMY_"]+stack[1:-1] + ["0"])
            except IndexError:
                hidden.append(stack[:] + ["1"])
                hidden.append(["_empty_","_DUMMY_"]+stack[1:-1] + ["0"])
                
            for item in conceptPair[1]:
                self.addLRParseTreeRec(stack[:],hidden,item)
        
    def getLRRLParseTree(self, removeFT = False):
        hidden = []
        
        hidden.append(["_empty_","_EMPTY_","_EMPTY_","_EMPTY_", "_EMPTY_", "1"])
        hidden.append(["_empty_","_DUMMY_","_EMPTY_","_EMPTY_", "_EMPTY_", "0"])
        
        stack = ["_empty_","_EMPTY_","_EMPTY_","_EMPTY_", "_EMPTY_"]
        for conceptPair in self.semanticsTree:
            self.addLRRLParseTreeRec(stack[:], hidden, conceptPair, removeFT)
        hidden.append(stack[:]+["1"])
        
        # modify the skip limit counter
        self.recountJumpIndex(hidden)
        
        return HiddenObservation(hidden, self.id)

    def recountJumpIndex(self, hidden):
        jump = 0
        for i in range(len(hidden)-1, -1, -1):
            old = hidden[i][5]
            hidden[i][5] = str(int(round((jump+0.001)/2.0)))
            
            if old == "1":
                jump = 0
            
            jump += 1
    
    def addLRRLParseTreeRec(self,stack,hidden,conceptPair, removeFT = False):
        for concept in conceptPair[0].split(' '):
            if concept.islower(): 
                # it is a word
                stack[0] = concept
            else:
                stack.insert(1, concept)
                del stack[-1]
                stack[0] = "_empty_"
            
            if len(conceptPair[1]) == 0:
                leaf = ["1"]
            else:
                leaf = ["0"]
                  
            # LR parse part 
            try:
                if not conceptPair[1][0][0].islower():
                    hidden.append(stack[:]+leaf)
                    hidden.append(["_empty_","_DUMMY_"]+stack[1:-1]+["0"])
                    lrStack = stack[:]
            except IndexError:
                hidden.append(stack[:]+leaf)
                hidden.append(["_empty_","_DUMMY_"]+stack[1:-1]+["0"])
                lrStack = stack[:]
                
            for item in conceptPair[1]:
                self.addLRRLParseTreeRec(stack[:],hidden,item, removeFT)
    
                # RL parse part
                try:
                    if removeFT:
                        if lrStack[1] == "FROM" or lrStack[1] == "TO":
                            # skip this vector state
                            continue
                        
                    if not conceptPair[1][0][0].islower():
                        hidden.append(lrStack+["0"])
                        hidden.append(["_empty_","_DUMMY_"]+lrStack[1:-1]+["0"])
                except IndexError:
                    if removeFT:
                        if lrStack[0] == "FROM" or lrStack[0] == "TO":
                            # skip this vector state
                            continue
                            
                    hidden.append(lrStack[:]+["0"])
                    hidden.append(["_empty_","_DUMMY_"]+lrStack[1:-1]+["0"])

    def getSemanticsRec(self,conceptPair):
        smntcs = ""
        
        if conceptPair[0].isupper():
            smntcs += conceptPair[0]
            if len(conceptPair[1]) > 0:
                smntcs += "("
                
                for item in conceptPair[1]:
                    smntcs += self.getSemanticsRec(item) + ","
                
                smntcs = smntcs[:-1]
            smntcs += ")"
        else: 
            smntcs = conceptPair[0]
        return smntcs
        
    def getSemantics(self):
        smntcs = ""
        
        for conceptPair in self.semanticsTree:
            smntcs += self.getSemanticsRec(conceptPair) + ","
        
        smntcs = smntcs[:-1]
        return smntcs

    def getPTBSemanticsRec(self,conceptPair):
        smntcs = ""
        
        if conceptPair[0].isupper():
            smntcs += conceptPair[0]
            if len(conceptPair[1]) > 0:
                
                for item in conceptPair[1]:
                    smntcs += ' (' + self.getPTBSemanticsRec(item) + ")"
                
                #smntcs = smntcs[:-1]
            else:
                smntcs += " (POST x)"
        else: 
            words = conceptPair[0].split(' ')
            
            if len(words) > 1:
                smntcs = ""
                for each in words:
                    smntcs += '(POST ' + each + ') '
                smntcs = smntcs[:-1]
            else:
                smntcs = 'POST ' + conceptPair[0]
                
        return smntcs
        
    def getPTBSemantics(self):
##        print self.semantics
##        print self.semanticsTree
        
        smntcs = "(TOP "
        
        for conceptPair in self.semanticsTree:
            smntcs += '(' + self.getPTBSemanticsRec(conceptPair) + ") "
        
        smntcs = smntcs[:-1]
        return smntcs + ')'

    def getCUEDSlot(self, pair):
        """
        Only one slot is exported.
        """
        
##        print pair
        
        slot = pair[0].lower()
        equal = ""
        value = ''
        try:
            if pair[1][0][0] == 'NOT':
                equal = '!='
                try:
                    value = pair[1][0][1][0]
                except IndexError:
                    value = ''
                    equal = ''
            else:
                equal = '='
                try:
                    value = pair[1][0][0]
                except IndexError:
                    value = ''
                    equal = ''
        except IndexError:
            pass
        
        # translate value
        if value == 'VALUE':
            value = '"'+value.lower()+'"'
        
        try:
            vst = value.startswith('VALUE_')
            if vst:
                value = '"'+value[len('VALUE_'):].replace("_", " ")+'"'
        except AttributeError:
            value = ''
            equal = ''
        
        
        return slot+equal+value
        
    def getCUEDSpeechAct(self, pair):
        """
        Export one DA in CUED format. Ofcourse it export all its 
        slots.
        """
        
        speechAct = pair[0].lower()
        
        slots = ''
        for eachSlot in pair[1]:
            slots += self.getCUEDSlot(eachSlot)+','
            
        slots = slots[:-1]
        
        return speechAct+'('+slots+')'
        
    def getCUEDSemantics(self):
        """
        CUED format is used for the output. We expect that
        semantics has only one root, then slots, and finaly 
        values. Between slot and value can be placed concept 
        'NOT' which will translated into '!-'. All value concepts 
        must start with 'VALUE_'. All values are placed into into 
        "" and '_' are replaced with ' '. 
        """

        smntcs = ''
        
        for conceptPair in self.semanticsTree:
            smntcs += self.getCUEDSpeechAct(conceptPair)+ ","
        
        smntcs = smntcs[:-1]
        
        return smntcs
        
