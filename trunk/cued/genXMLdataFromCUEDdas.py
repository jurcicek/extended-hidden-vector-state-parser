#!/usr/bin/env python2.5

from string import *
from glob import *
import re
import os

inputCuedSemanticsTrain   = 'towninfo-train.sem'
inputCuedSemanticsHeldout = 'towninfo-heldout.sem'
inputCuedSemanticsTest    = 'towninfo-test.sem'

maxProcessedDAs = 18000
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

        # split slots
        slots = splitByComma(slots)
        
        stats['das'] += 1
        if len(slots[0]) > 0:
            stats['slot'+str(len(slots))] += 1
        else:
            stats['slot0'] += 1
            return

        for each_slot in slots:
            slot = Slot(each_slot)
            slot.parse()
            
            self.slots.append(slot)

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
    try:
        conceptStats[concept] += 1
    except KeyError:
        conceptStats[concept] = 1
    
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

            print strip(sentence), ' <=> ', strip(das)
            print da.render()
            
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
