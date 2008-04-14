#!/usr/bin/env python2.4

import os.path
from glob import glob
import codecs

from svc.scripting import *

import toolkit
import gmtk
from lexMap import LexMap
from observation import Observation
from hiddenObservation import HiddenObservation
from sparseProbability import SparseProbability

CONCEPT_GROUPS = [
    ['AMOUNT', 'LENGTH', 'NUMBER'],
    ['STATION'],
    ['TRAIN_TYPE'],
]

CONCEPT_ROOTS = set(['ACCEPT', 'ARRIVAL', 'DELAY', 'DEPARTURE', 'DISTANCE',
        'DURATION', 'PLATFORM', 'PRICE', 'REJECT'])

class SymbolGivenC1C2C3C4(Script):
    options = {
        'files': (Required, Multiple, String),
        'conceptMap': (Required, String),
        'symMap': (Required, String),
        'outDir': (Required, String),
        'negExamples': String,
        'noNegExamples': Flag,
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

    def makeIntegerMap(self, map):
        map.lexMap = dict((k, int(v)) for (k,v) in map.lexMap.iteritems())
        return map

    def setupMaps(self, conceptMap, symMap):
        conceptMap = LexMap().read(conceptMap)
        self.conceptMap = self.makeIntegerMap(conceptMap)
        symMap = LexMap().read(symMap)
        self.symMap = self.makeIntegerMap(symMap)

    def getLeafConceptsGroups(self):
        return [self.mapSet(i, self.conceptMap) for i in CONCEPT_GROUPS]

    def getRootConcepts(self):
        return self.mapSet(CONCEPT_ROOTS, self.conceptMap)

    def getSkipSymbols(self):
        symbols = set(['_empty_', '_dummy_', '_sink_'])
        return self.mapSet(symbols, self.symMap)

    def getEmptyWord(self):
        empty = '_empty_'
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

    def collectNegExamples(self, neg_ex, ho, o):
        skipSymbols = self.getSkipSymbols()
        rootConcepts = self.getRootConcepts()
        leafGroups = self.getLeafConceptsGroups()
        symbols = o.getSefOfWords()
        concepts = ho.getSetOfConcepts()
        for rootConcept in rootConcepts:
            if rootConcept in concepts:
                # the utterance can be used as negative example 
                
                for leafConcepts in leafGroups:
                    # you have one group of dependent concepts (generally numbers)
                    ok = True
                    for leafConcept in leafConcepts:
                        if leafConcept in concepts:
                            ok = False
                    
                    if ok:
                        # all words in the utterance can be used as negative
                        # exapmles beceause they are not connected with
                        # lexConceptsDependent (the example does not contain
                        # lexConceptsDependent)
                        
                        for leafConcept in leafConcepts:
                            if leafConcept not in neg_ex:
                                neg_ex[leafConcept] = {}
                            for sym in symbols:
                                if sym in skipSymbols:
                                    continue
                                neg_ex[leafConcept].setdefault(sym, 0)
                                neg_ex[leafConcept][sym] += 1

                # the example was already used
                break

    def makeDTS_CollectExmpls(self, generator, collectNegEx=True, collectPosEx=True):
        rootConcepts = self.getRootConcepts()
        leafGroups = self.getLeafConceptsGroups()

        dt4 = {}
        dt3 = {}
        dt2 = {}

        neg_ex = {}
        histories = set()

        for ho, o in generator:
            ho.collectConceptsC1C2C3C4(dt4)
            ho.collectConceptsC1C2C3(dt3)
            ho.collectConceptsC1C2(dt2)
            histories |= set(ho.getSetOfConceptVectors())

            if collectNegEx:
                self.collectNegExamples(neg_ex, ho, o)

        word_C = self.makeSparseProb(histories, neg_ex)

        return dt4, dt3, dt2, word_C, neg_ex

    def makeSparseProb(self, histories, neg_ex):
        EPSILON = 3.3e-90
        symCard = len(self.symMap)
        skipSymbols = self.getSkipSymbols()
        emptyWord = self.getEmptyWord()
        emptyHist = self.getEmptyHist()

        table = SparseProbability()

        for hist_tuple in histories:
            hist = list(hist_tuple)
            if hist == emptyHist:
                table.setValue([ emptyWord ] + emptyHist, 1.0)
            else:
                # Set nonzero probability for all posible words
                for w in range(symCard):
                  if w not in skipSymbols:
                      table.setValue([ w ] + hist, 1.0)

            # Apply negative examples
            for w in neg_ex.get(hist[0], []):
                index = [ w ] + hist
                if table.getSafeValue(index) >= EPSILON:
                    table.setValue(index, EPSILON)

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

    def storeResults(self, outDir, symName, (dt4, dt3, dt2, word_C, neg_ex), constFile=None, constAppend=True):
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

    def printNegExamples(self, neg_ex, fw=None):
        if fw is None:
            fw = sys.stdout

        triples = []

        rconceptMap = self.conceptMap.reverse()
        rsymMap = self.symMap.reverse()

        for concept, c_value in neg_ex.iteritems():
            for word, count in c_value.iteritems():
                c = rconceptMap[concept].encode('utf-8')
                s = rsymMap[word].encode('utf-8')
                triples.append((c, s, str(count)))

        triples.sort()
        for line in triples:
            fw.write('\t'.join(line) + '\n')

    def storeNegExamples(self, fn, neg_ex):
        fw = file(fn, 'w')
        try:
            self.printNegExamples(neg_ex, fw=fw)
        finally:
            fw.close()

    def main(self, files, conceptMap, symMap, outDir, symName='word',
            extraExt='', obsColumn=0, negExamples=None, posExamples=None,
            writeConst=None, appendConst=None, noNegExamples=False):

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

        ho_generator = self.generateHO(file_ids, extraExt, obsColumn)
        dts = self.makeDTS_CollectExmpls(ho_generator, collectNegEx=not noNegExamples)

        if writeConst:
            constFile = writeConst
            constAppend = False
        else:
            constFile = appendConst
            constAppend = True

        self.storeResults(outDir, symName, dts, constFile, constAppend)

        if negExamples:
            self.storeNegExamples(negExamples, dts[-1])

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
