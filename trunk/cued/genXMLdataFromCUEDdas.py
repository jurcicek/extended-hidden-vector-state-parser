#!/usr/bin/env python2.5

from string import *
from glob import *
import re
import os
import heapq
from operator import *

inputCuedSemanticsTrain   = 'towninfo-train.sem'
inputCuedSemanticsHeldout = 'towninfo-heldout.sem'
inputCuedSemanticsTest    = 'towninfo-test.sem'

maxProcessedDAs = 28000
outputDir = "/home/filip/cued/ehvs/cued/xml/"

#filterOutSlotsNumberTrain   = range(2,12)
#filterOutSlotsNumberHeldout = range(2,12)
#filterOutSlotsNumberTest    = range(2,12)

filterOutSlotsNumberTrain   = (0,2,3,4,5,6,7,8,9,10,11,12)
filterOutSlotsNumberHeldout = (0,2,3,4,5,6,7,8,9,10,11,12)
filterOutSlotsNumberTest    = (0,2,3,4,5,6,7,8,9,10,11,12)

filterOutSpeechActs = ('xxx', 
##                       'ask',
##                       'affirm', 
##                       'bye', 
##                       'confirm', 
##                       'deny', 
##                       'hello',
##                       'inform',
##                       'negate',
##                       'repeat',
##                       'reqalts',
##                       'reqmore',
##                       'request',
##                       'restart',
##                       'select',
##                       'thankyou',
                       )
# there is definitely problem with speech acts negate and deny

conceptStats = {}
alignmentStats = {}
##alignmentStats['none'] = -1
stats = {}

def splitByComma(text):
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

class Slot:
    def __init__(self, slot):
        # data normalisation:
        # both name and phone.name has their equivalents
        self.slot = slot
##        self.slot = re.sub('^name', 'venue.name',slot)
##        self.slot = re.sub('^phone.name', 'venue.name',self.slot)
        self.name = ''
        self.value = ''
        self.equal = False

    def parse(self):
        self.equal = True
        i = self.slot.find('!=')
        if i == -1:
          i = self.slot.find('=')
          if i == -1:
              self.name = self.slot
              
              return
        else:
            self.equal = False

        self.name = self.slot[:i]

        self.value = self.slot[i:]
        self.value = self.value.replace('!', '')
        self.value = self.value.replace('=', '')
        self.value = self.value.replace('"', '')

        return

    def findValue(self, text, values):
        for each in values:
            v = each.replace(' ', '').lower()
            v = v.replace("'", '')
            n = re.search(v, text)
            
            if n == None: 
                n = -1
            else:
                n = n.start()
                
            if n >= 0:
                break
                
        return n
        
    def align(self, text):
        text = text.replace(' ', '').lower()
        text = text.replace("'", '')
        name = self.name
        value = self.value
        
        dontcare = ["s not important",'t (really)* (erm)* care','t (really)* (erm)* mind', 'forget about', 'im not interested in', 'anything', 't matter', 'i oov (really)* mind', 'i dont want any', 'any kind of', 'doesnt need to be', 'doesnt have to play', 'no i just want']
        
        # rule based alignment
        if value == 'find':
            value = ["(just)* looking for","(just)* looking to", 'want to find']
        elif value == 'central':
            value = ["centr", 'middle']
        elif name == 'area' and value == 'dontcare':
            value = dontcare + ["somewhere", "anywhere", 'any part']
        elif name == 'pricerange' and value == 'dontcare':
            value = dontcare + ["any price range",]
        elif name == 'near' and value == 'dontcare':
            value = dontcare + ["near",]
        elif name == 'drinks' and value == 'dontcare':
            value = dontcare + ["different type",]
        elif value == 'dontcare':
            value = dontcare
        elif value == 'bar':
            value = ["bar", 'sells? beer', 'get a? drink', 'for a drink']
        elif value == 'cocktails':
            value = ["cocktail",]
        elif value == 'drinks':
            value = ["drink", 'alcohol']
        elif value == '1':
            value = ["one star",]
        elif value == '2':
            value = ["two star",]
        elif value == '3':
            value = ["three star",]
        elif value == '4':
            value = ["four star",]
        elif value == '5':
            value = ["five star",]
        elif value == 'restaurant':
            value = ["restaurant", 'to eat', 'food', 'meal', 'want dinner', 'oov']
        elif value == 'expensive':
            value = ["expensive", 'luxurious', 'fancy', 'smart', 'hogh price', 'the best']
        elif value == 'cheap':
            value = ["cheap", 'basic', 'dont have much money']
        elif value == 'moderate':
            value = ["moderate", 'midprice', 'medium', 'intermediate', 'reasonably', 'range', 'at oov price', 'better than a cheap', 'mid range', 'oov price', 'beer bar', 'too expesive']
        elif value == 'Westside Shopping':
            value = ["westside shopping", 'shopping centre', 'supermarket', 'shopping area']
        elif value == 'River Jay':
            value = ["river side",'river jay', 'riverside', 'river']
        elif value == 'Railway Station':
            value = ["station",]
        elif value == 'Tourist Information':
            value = ["information",]
        elif value == 'Saint Petersburg':
            value = ["peters",]
        elif value == 'Hotel Primus':
            value = ["primus",]
        elif value == 'Alexander Hotel':
            value = ["hotel",]
        elif value == 'Alexandra Hotel':
            value = ["hotel",]
        elif value == 'Char Sue':
            value = ["Char Sue", 'chow oov']
        elif value == 'hotel':
            value = ["hotel", 'hostel', 'place to stay', 'to stay']
        elif value == 'snacks':
            value = ["snack",]
        elif value == 'Italian':
            value = ["italian", 'pizza']
        elif name == 'addr' and value == '':
            value = ["address", 'name', 'riverside', 'river', 'where is', 'where can i', 'location', 'where that is']
        elif name == 'venue.name' and value == '':
            value = ['name']
        elif name == 'phone' and value == '':
            value = ['phone', 'number']
        elif name == 'price' and value == '':
            value = ["what price is it",'how much .* cost', 'riverside', 'tell me how much', 'they charge', 'cost', 'whats the', 'price', 'how much', 'how expensive']
        elif name == 'area' and value == '':
            value = ["what part","where is",'area', 'which part']
        elif name == 'near' and value == '':
            value = ["near","closest"]
        elif name == 'food' and value == '':
            value = ["food","cuisine", 'type of']
        elif name == 'stars' and value == '':
            value = ["star",]
        elif name == 'pricerange' and value == '':
            value = ["what sort of prices", 'pricerange', 'what kind of price', 'how expensive', 'how much', 'typical price']
        else:
            value = [value,]

        if len(value[0]) == 0:
            value[0] = name
            
        self.n = self.findValue(text, value)
        
        if self.n == -1:
            incrementAlignment(self.name+'|'+self.value)
            incrementAlignment('_BAD_')
        else:
            incrementAlignment('_OK_')
    
    def render(self):
        if len(self.name) == 0:
            name = 'EMPTYSLOT'
        else:
            name = self.name
            
        name = name.replace('.', '_DOT_')
        name = name.upper()
        incrementConceptStats(name)

        if self.value == 'dontcare' or self.value == 'none':
            value = '('+'VALUE_'+self.value.upper()+')'
        elif len(self.value) == 0:
            value = ''
        else:
            value = '(VALUE_'+name+')'
        
        incrementConceptStats(value)

        if self.equal:
            slot = name+value
        else:
            slot = name+'(NOT'+value+')'
            incrementConceptStats('NOT')
        
        return slot
    
    def renderCUED(self):
        name = self.name
            
        if self.equal:
            equal = '='
        else:
            equal = '!='
        
        if self.value == 'dontcare' or self.value == 'none':
            value = self.value
        elif len(self.value) == 0:
            value = ''
            equal = ''
        else:
            value = 'value_'+name

        return name+equal+value
    
class DialogueAct:
    def __init__(self, da, text):
        self.text = text
        self.textWords = split(self.text)
        self.dialogueAct = da
        self.speechAct = ""
        self.slots = []

        return

    def sortSlots(self):
        again = True
        
        while again:
            again = False
            for i in range(1, len(self.slots)):
                if self.slots[i-1].n > self.slots[i].n:
                    slot = self.slots[i]
                    self.slots[i] = self.slots[i-1]
                    self.slots[i-1] = slot
                    
                    again = True
                    break
                    
    
    def parse(self):
        numOfDAs = len(splitByComma(self.dialogueAct))
        if numOfDAs > 1:
            raise ValueError('Too many DAs in input text.')

        # get the speech-act
        i = self.dialogueAct.index("(")
        self.speechAct = self.dialogueAct[:i]
        slots = self.dialogueAct[i:]
        slots = slots.replace('(', '')
        slots = slots.replace(')', '')

        stats['das'] += 1

        if slots == '':
            # no slots to process
            return
            
        # split slots
        slots = splitByComma(slots)
        
        if len(slots[0]) > 0:
            stats['slot'+str(len(slots))] += 1
        else:
            stats['slot0'] += 1
            return

        for each_slot in slots:
            slot = Slot(each_slot)

            slot.parse()
            
            if len(slots) > 1:
                slot.align(self.text)
            else:
                slot.n = -1
            
            self.slots.append(slot)

        if len(slots) > 1:
            self.sortSlots()
        
        return

    def render(self):
        DA = self.speechAct.upper()
        incrementConceptStats(DA)

        if len(self.slots) > 0:
            rendered_slots = ""

            for each_slot in self.slots:
                rendered_slots += each_slot.render() + ','

            # remove the last comma
            rendered_slots = re.sub(r',$', '', rendered_slots)

            DA += '('+rendered_slots+')'

        return DA

    def renderCUED(self):
        DA = self.speechAct
        rendered_slots = ""
        
        if len(self.slots) > 0:
            rendered_slots = ""

            for each_slot in self.slots:
                rendered_slots += each_slot.renderCUED() + ','

            # remove the last comma
            rendered_slots = re.sub(r',$', '', rendered_slots)

        DA += '('+rendered_slots+')'

        return DA

    def getAlignment(self):
        s = ''
        for each_slot in self.slots:
            s += each_slot.name+':'+str(each_slot.n)+' '
        
        return s
        
    def unAligned(self):
        if len(self.slots) > 1:
            for each_slot in self.slots:
                if each_slot.n == -1:
                    return True
                
        return False
        
    def getNumOfSlots(self):
        return len(self.slots)

    def getEHVSXML(self):
        xml = """<?xml version="1.0" encoding="utf-8"?>
<task comment="" dialect="native" modified-by="cuedSemParser" description="" hour="" min="" gender="" specification="" system="jasonTown" saved-by="cuedSemParser" month="" volume="" dialog="" processing-state="approved" pin="" year="" transcription_level="" last-change="" quality="" day="" update_code="">
  <turn speaker="user" number="1">
    <utterance overlap_time="" start_time="" overlap="" length="" speaker="user" end_time="">
      <text type="transcription">
        %s
      </text>
      <text type="normalized">
        %s 
      </text>
      <text type="lemmatized">
        %s
      </text>
      <text type="pos_tagged">
        %s
      </text>
      <ne_typed_text>
        %s 
      </ne_typed_text>
      <dialogue_act speech_act="" conversational_domain="task" semantics="%s">
        %s
      </dialogue_act>
      <parametrized_act speech_act="" type="lemmatized" conversational_domain="task" semantics="%s">
        %s
      </parametrized_act>
      <parametrized_act speech_act="" type="pos_tagged" conversational_domain="frame" semantics="%s">
        %s
      </parametrized_act>
    </utterance>
  </turn>
</task>""" %   (self.text, 
                self.text,
                self.text,
                'POS '*len(self.textWords),
                self.text,
                self.render(),
                self.text,
                self.render(),
                self.text,
                self.render(),
                'POS '*len(self.textWords))
                
        return xml

def incrementConceptStats(concept):
    global conceptStats
    
    try:
        conceptStats[concept] += 1
    except KeyError:
        conceptStats[concept] = 1
    
    return

def incrementAlignment(concept):
    global alignmentStats
    
    try:
        alignmentStats[concept] += 1
    except KeyError:
        alignmentStats[concept] = 1
    
    return

def printConceptStats(listFileName):
    cStatsFile = file(outputDir+listFileName+'.conceptStats', 'w')
    
    concepts = conceptStats.keys()
    concepts.sort()
    for each in concepts:
        cStatsFile.write(each+'\n')

    cStatsFile.write('----------------------------------------\n')
    cStatsFile.write('----------------------------------------\n')
    cStatsFile.write('----------------------------------------\n')
    cStatsFile.write('----------------------------------------\n')

    for each in concepts:
        cStatsFile.write(each+'\t'+str(conceptStats[each])+'\n')
    cStatsFile.close()
        
    return
    
def transformCuedDAs(counter, inputFile, outputDir, listFileName, filterOutSlotsNumber = []):
    listFile = file(outputDir+listFileName, 'w')
    cuedFile = file(outputDir+listFileName+'.cued', 'w')

    global conceptStats
    conceptStats = {}
    
    stats['das'] = 0
    stats['slot0'] = 0
    stats['slot1'] = 0
    stats['slot2'] = 0
    stats['slot3'] = 0
    stats['slot4'] = 0
    stats['slot5'] = 0
    stats['slot6'] = 0

    sem = file(inputFile, 'r')
    semLines = sem.readlines()[:maxProcessedDAs]

    for line in semLines:
        splt = split(line, '<=>')
        sentence = splt[0]

        if len(line) != 0:
            das = splt[1] 
    
            sentence = strip(sentence)
            da = DialogueAct(strip(das), strip(sentence))
    
            da.parse()
    
            if da.getNumOfSlots() in filterOutSlotsNumber:
                continue
    
            if da.speechAct in filterOutSpeechActs:
                continue

            if da.unAligned():
                print strip(sentence), ' <=> ', strip(das)
                print 'EHVS: ', da.render()
                print 'CUED: ', da.renderCUED()
                print 'Alig: ', da.getAlignment()
                print
            
            cuedFile.write(strip(sentence)+' <=> '+da.renderCUED()+'\n')
            
            xml = file(outputDir+'%05d.xml' % counter, 'w')
            xml.write(da.getEHVSXML())
            xml.close()
            
            listFile.write('%05d.xml' % counter + '\t2008-09-15\n')
            
            counter += 1
    
    listFile.close()
    cuedFile.close()
    
    print 'DAs : ', stats['das']
    print 'slot0: ', stats['slot0']
    print 'slot1: ', stats['slot1']
    print 'slot2: ', stats['slot2']
    print 'slot3: ', stats['slot3']
    print 'slot4: ', stats['slot4']
    print 'slot5: ', stats['slot5']
    print 'slot6: ', stats['slot6']

    ali = heapq.nlargest(100, alignmentStats.iteritems(), itemgetter(1))

    for k, v in ali:
        print k+'='+str(v)
    
    printConceptStats(listFileName)
    
    return counter
    
def main():
    print "SEM parser"
    print "---------------------------------------------"
    
    for f in glob(outputDir +'*'):
        os.remove(f)
     
    counter = transformCuedDAs(0, inputCuedSemanticsTrain, outputDir,
        '.train.list', filterOutSlotsNumberTrain)
    counter = transformCuedDAs(counter, inputCuedSemanticsHeldout, outputDir,
        '.heldout.list', filterOutSlotsNumberHeldout)
    counter = transformCuedDAs(counter, inputCuedSemanticsTest, outputDir,
        '.test.list', filterOutSlotsNumberTest)
    
if __name__ == '__main__':
    main()
