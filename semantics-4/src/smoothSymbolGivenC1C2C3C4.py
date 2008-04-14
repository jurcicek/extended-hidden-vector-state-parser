#!/usr/bin/env python2.4

from svc.scripting import *

from lexMap import LexMap
import gmtk

class SymbolSmoother(Script):
    options = {
        'conceptMap': (Required, String),
        'symbolMap': (Required, String),
        'symbolDt': (Required, String),
        'symbolName': (Required, String),
        'dcpts': (Required, String),
        'dpmfs': (Required, String),
        'outDir': (Required, String),
    }

    debug = False

    def main(self, conceptMap, symbolMap, symbolDt, dcpts, dpmfs, symbolName, outDir):
        conceptMap = LexMap().read(conceptMap)
        symbolMap = LexMap().read(symbolMap)

        _sink_ = int(symbolMap['_sink_'])
        _SINK_ = int(conceptMap['_SINK_'])

        conceptCard = len(conceptMap)
        symbolCard = len(symbolMap)

        jointDtC1C2C3C4 = gmtk.readDt(symbolDt)
        jointDcptC1C2C3C4 = gmtk.readDcpt(dcpts, "jointProbC1C2C3C4")
        jointProbC1C2C3C4 = gmtk.combineDtDcpt1(jointDtC1C2C3C4, jointDcptC1C2C3C4) 

        symbolDpmfC1C2C3C4 = gmtk.readDpmf(dpmfs, "%sGivenC1C2C3C4" % symbolName)
        symbolGivenC1C2C3C4 = gmtk.combineDtDcpt2(jointDtC1C2C3C4, symbolDpmfC1C2C3C4)

        jointProbSymbolC1C2C3C4 = symbolGivenC1C2C3C4.multiple([1, 2, 3, 4], jointProbC1C2C3C4)
        gmtk.saveDpmfsProbs(outDir, "%sGivenC1C2C3C4" % symbolName,
                len(symbolGivenC1C2C3C4.vectSubList([1, 2, 3, 4])), 
                symbolCard, symbolGivenC1C2C3C4)


        jointProbSymbolC1C2C3 = jointProbSymbolC1C2C3C4.marginalize([0, 1, 2, 3])
        symbolGivenC1C2C3 = jointProbSymbolC1C2C3.conditionalize([1, 2, 3])
        gmtk.saveDpmfsProbs(outDir, "%sGivenC1C2C3" % symbolName,
                len(symbolGivenC1C2C3.vectSubList([1, 2, 3])),
                symbolCard, symbolGivenC1C2C3)

        jointProbSymbolC1C2 = jointProbSymbolC1C2C3.marginalize([0, 1, 2])
        symbolGivenC1C2 = jointProbSymbolC1C2.conditionalize([1, 2])
        gmtk.saveDpmfsProbs(outDir, "%sGivenC1C2" % symbolName,
                len(symbolGivenC1C2.vectSubList([1, 2])),
                symbolCard, symbolGivenC1C2)

        jointProbSymbolC1 = jointProbSymbolC1C2.marginalize([0, 1])
        symbolGivenC1 = jointProbSymbolC1.conditionalize([1])

        # in case of conditioning by _SINK_ I have to enable to generate _sink_ word only
        # otherwise I would see _SINK_ concept in the stack
        # TODO: Turn it into validator
        symbolGivenC1.setValue([_sink_, _SINK_], 1)

        gmtk.saveDcptBigram(outDir, "%sGivenC1" % symbolName,
                symbolCard, conceptCard, symbolGivenC1)

        symbolUnigram = jointProbSymbolC1.marginalize([0])

        # I need to enable to decode _unseen_ word only ! so set the probability of
        # generating _empty_ to zero 
        symbolUnigram.setValue([int(symbolMap["_empty_"])], 0)
        # normalize sum of probabilities to one
        symbolUnigram = symbolUnigram.normJoint()

        gmtk.saveDcptUnigram(outDir, "%sUnigram" % symbolName,
                symbolCard, symbolUnigram)

        gmtk.saveDcptUnseen(outDir, "%sZerogram" % symbolName,
                symbolCard, symbolMap)

def main():
    script = SymbolSmoother()
    script.run()

if __name__ == '__main__':
    main()
