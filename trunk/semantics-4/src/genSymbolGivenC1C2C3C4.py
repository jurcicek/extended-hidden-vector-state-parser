#!/usr/bin/env python2.4

import os.path
from glob import glob
import codecs
import sys

from svc.scripting import *
from svc.map import SymMap
from svc.utils import ADict

import toolkit
import gmtk
from observation import Observation
from hiddenObservation import HiddenObservation
from sparseProbability import SparseProbability

CONCEPT_GROUPS = [
    ['AMOUNT', 'LENGTH', 'NUMBER'],
    ['STATION'],
    ['TRAIN_TYPE'],
]

CONCEPT_ROOTS = set(['ACCEPT', 'ARRIVAL', 'DELAY', 'DEPARTURE', 'DISTANCE','DURATION', 'PLATFORM', 'PRICE', 'REJECT'])

class SymbolGivenC1C2C3C4(Script):
    options = {
        'files': (Required, Multiple, String),
        'conceptMap': (Required, String),
        'symMap': (Required, String),
        'outDir': (Required, String),
        'negExamples': String,
        'posExamples': String,
        'symName': String,
        'extraExt': String,
        'obsColumn': Integer,
        'writeConst': String,
        'appendConst': String,
    }

    def mapSet(self, symbols, mapping):
        ret = set()
        for c in symbols:
            if mapping.has_key(c):
                ret.add(int(mapping[c]))
        return ret

    def mapInt(self, vector):
        return [int(i) for i in vector]

    def mapVector(self, vector, map):
        return [map[i] for i in vector]

    def mapHiddenObservation(self, ho, conceptMap):
        h_id = ho.id
        h_obs = ho.getHidden()
        h_obs = [self.mapInt(v) for v in h_obs]
        return HiddenObservation(h_obs, h_id)

    def setupMaps(self, conceptMap, symMap):
        self.conceptMap = SymMap.readFromFile(conceptMap, format=(int, unicode)).inverse
        self.symMap = SymMap.readFromFile(symMap, format=(int, unicode)).inverse

    def mapExamples(self, dict):
        _unseen_ = self.symMap['_unseen_']
        ret = {}
        for concept_word, count in dict.iteritems():
            if len(concept_word) != 2:
                # TODO: REMOVE: used only with bigram_lemma
                continue
            c, w = concept_word
            if c not in self.conceptMap:
                continue
            c = self.conceptMap[c]
            w = self.symMap.get(w, _unseen_)
            if c not in ret:
                ret[c] = ADict()
            ret[c][w] += count
        return ret

    def getSkipSymbols(self):
        symbols = set(['_empty_', '_dummy_', '_sink_'])
        return self.mapSet(symbols, self.symMap)

    def getEmptyWord(self):
        empty = '_empty_'
        return self.symMap[empty]

    def getUnseenWord(self):
        empty = '_unseen_'
        return self.symMap[empty]

    def getEmptyHist(self):
        vector = ['_EMPTY_'] * 4
        return self.mapVector(vector, self.conceptMap)

    def generateHO(self, file_ids, extraExt='', obsColumn=0):
        """Yields tuples (positive, negative)
        """
        for file_id in file_ids:
            ho_fn = file_id + '.hddn'
            ho = HiddenObservation().read(ho_fn)
            ho_map = self.mapHiddenObservation(ho, self.conceptMap)

            o_fn = file_id+extraExt+'.obs'
            o_file = file(o_fn)
            obs = []
            try:
                for line in o_file:
                    line = line.split()
                    obs.append(int(line[obsColumn]))
            finally:
                o_file.close()
            o_map = Observation(obs, ho.id)
            yield ho_map, o_map

    def makeDTS(self, generator):
        dt4 = {}
        dt3 = {}
        dt2 = {}

        histories = set()

        for ho, o in generator:
            ho.collectConceptsC1C2C3C4(dt4)
            ho.collectConceptsC1C2C3(dt3)
            ho.collectConceptsC1C2(dt2)
            histories |= set(ho.getSetOfConceptVectors())

        return (dt4, dt3, dt2), histories

    def makeSparseProb(self, histories, pos_ex, neg_ex):
        EPSILON = 0.01
        symCard = len(self.symMap)
        skipSymbols = self.getSkipSymbols()
        emptyWord = self.getEmptyWord()
        emptyHist = self.getEmptyHist()
        _unseen_ = self.getUnseenWord()

        table = SparseProbability()

        for hist_tuple in histories:
            hist = list(hist_tuple)
            if hist == emptyHist:
                table.setValue([ emptyWord ] + emptyHist, 1.0)
            if hist[0] in pos_ex:
                # Apply positive examples
                counts = pos_ex[hist[0]]
                for w in range(symCard):
                    if w not in skipSymbols:
                        if w in counts:
                            table.setValue([ w ] + hist, 1.0)
                        else:
                            table.setValue([ w ] + hist, EPSILON)
            else:
                # No positive examples, set nonzero probability for all posible
                # words
                for w in range(symCard):
                    if w not in skipSymbols:
                        table.setValue([ w ] + hist, 1.0)

            # Apply negative examples
            if hist[0] in neg_ex:
                counts = neg_ex[hist[0]]
                for w, count in counts.iteritems():
                    index = [ w ] + hist
                    if table.getSafeValue(index) >= EPSILON:
                        table.setValue(index, EPSILON)
            
            # Probability of _unseen_ is set to nonzero
            table.setValue([ _unseen_ ] + hist, 1.0)

            # Normalize sum to one, keep zeros zeros
            sum = 0.
            for w in range(symCard):
                sum += table.getSafeValue([w] + hist)

            for w in range(symCard):
                index = [ w ] + hist
                if table.getSafeValue(index) >= EPSILON:
                    new_value = table.getSafeValue(index)/sum
                    table.setValue(index, new_value)

        return table

    def storeResults(self, outDir, symName, (dt4, dt3, dt2), word_C, constFile=None, constAppend=True):
        wordCard = len(self.symMap)
        # Save 5-grams
        NAME = '%sGivenC1C2C3C4' % symName
        numberOfSpmfs = gmtk.saveDt(outDir, NAME, dt4, 4)
        gmtk.saveCollection(outDir, NAME, numberOfSpmfs)
        gmtk.saveSpmfs(outDir, NAME, numberOfSpmfs, wordCard)

        number = len(word_C.vectSubList([1, 2, 3, 4]))
        gmtk.saveDpmfsProbs(outDir, NAME, number, wordCard, word_C)

        if constFile:
            if constAppend:
                const_fw = file(constFile, 'a')
            else:
                const_fw = file(writeConst, 'w')
            try:
                const_fw.write("\n% the cardinality should be CONCEPT_CARD^DEPTH_OF_STACK, but I know that the stack values are sparse\n")
                const_fw.write("#define JOINT_C1C2C3C4_CARD     %d\n" % numberOfSpmfs)
            finally:
                const_fw.close()

        # save 4-grams
        NAME = '%sGivenC1C2C3' % symName
        numberOfSpmfs = gmtk.saveDt(outDir, NAME, dt3, 3)
        gmtk.saveCollection(outDir, NAME, numberOfSpmfs)
        gmtk.saveSpmfs(outDir, NAME, numberOfSpmfs, wordCard)

        # save 3-grams
        NAME = '%sGivenC1C2' % symName
        numberOfSpmfs = gmtk.saveDt(outDir, NAME, dt2, 2)
        gmtk.saveCollection(outDir, NAME, numberOfSpmfs)
        gmtk.saveSpmfs(outDir, NAME, numberOfSpmfs, wordCard)

    def main(self, files, conceptMap, symMap, outDir, symName='word',
            extraExt='', obsColumn=0, negExamples=None, posExamples=None,
            writeConst=None, appendConst=None):

        if writeConst is not None and appendConst is not None:
            raise ValueError("Use only writeConst or appendConst, not both")

        self.setupMaps(conceptMap, symMap)

        globfiles = set()
        for fn in files:
            if os.path.isdir(fn):
                globfiles |= set(glob(os.path.join(fn, '*.hddn')))
            else:
                globfiles.add(fn)

        file_ids = set()
        for fn in globfiles:
            file_id = fn.replace('.hddn', '')
            file_ids.add(file_id)
        file_ids = sorted(file_ids)

        if negExamples and negExamples != 'off':
            neg_ex = ADict.readFromFile(negExamples)
            neg_ex = self.mapExamples(neg_ex)
        else:
            neg_ex = {}

        if posExamples and posExamples != 'off':
            pos_ex = ADict.readFromFile(posExamples)
            pos_ex = self.mapExamples(pos_ex)
        else:
            pos_ex = {}

        if writeConst:
            constFile = writeConst
            constAppend = False
        else:
            constFile = appendConst
            constAppend = True

        ho_generator = self.generateHO(file_ids, extraExt, obsColumn)
        dts, histories = self.makeDTS(ho_generator)

        word_C = self.makeSparseProb(histories, pos_ex, neg_ex)

        self.storeResults(outDir, symName, dts, word_C, constFile, constAppend)

    optionsDoc = {
    'files':
        """Input hidden observation files, directories are searched for *.hddn files.
        Corresponding *.obs are processed sinultaneusly.""",
    }

def main():
    script = SymbolGivenC1C2C3C4()
    script.run()

if __name__ == '__main__':
    main()
