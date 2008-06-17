#!/usr/bin/env python2.4

import os
import sys
from glob import glob
from StringIO import StringIO

from svc.scripting import *

from svc.ui.smntcs import input
from lexMap import LexMap, mapCmp
import semantics

EXTRA_CONCEPTS = {
    "_EMPTY_": 1,
    "_DUMMY_": 1,
    "_SINK_": 1,
}
LARGE_NUMBER = 999999
EXTRA_SYMBOLS = {
    "_empty_": LARGE_NUMBER,
    "_dummy_": LARGE_NUMBER,
    "_sink_": LARGE_NUMBER,
    "_unseen_": LARGE_NUMBER,
}

class MapGenerator(Script):
    """Mapping generator for semantic parser

    This script generates symbol maps from input files using given dataSet.
    dataSet is string containing XML tag name and XML tag attributes with value
    to load from input XML files. For example
    --dataSet=parametrized_act:type=lemmatized or --dataSet=dialogue_act.

    It can optionally generate concept mapping. It can also write necessary
    data constants into files.

    If --text is specified, output mappings will be identical. 
    """
    options = {
        'files': (Required, Multiple, String),
        'symMap': String,
        'pruneCount': Float,
        'conceptMap': String,
        'dataSet': String,
        'defaultDataSet': String,
        'text': Flag,
        'writeConst': String,
        'appendConst': String,
        'symName': String,
        'inputChain': String,
        'useEmpty': Integer,
        'stats': String,
    }

    debug = False

    def createSemanticReader(self, files, data_set, default_data_set, inputChain='none'):
        reader = input.MultiReader(files, input.DXMLReader)
        reader = input.InputChain(inputChain, reader)
        generator = input.InputGenerator(reader, [data_set], default_data_set)
        return generator

    def addSymbols(self, generator, useEmpty=False):
        d = dict()
        for da_fn, da_id, da_semantics, da_txts in generator.readInputs():
            s = [semantics.Semantics(da_id, da_semantics, ' '.join(txt), 'LR') for txt in da_txts]
            if useEmpty or not s[0].isEmpty():
                s[0].addWords(d)
        return d

    def addConcepts(self, generator, useEmpty=False):
        d = dict()
        for da_fn, da_id, da_semantics, da_txts in generator.readInputs():
            s = [semantics.Semantics(da_id, da_semantics, ' '.join(txt), 'LR') for txt in da_txts]
            if useEmpty or not s[0].isEmpty():
                s[0].addConcepts(d)
        return d

    def printDict(self, d):
        for key in sorted(d.keys()):
            print key.encode('utf-8')

    def pruneSymbolsAbs(self, d, pruneCount):
        wd = {}
        for each in d.keys():
            if d[each] > pruneCount:
                wd[each] = d[each]
        return wd

    def pruneSymbolsNum(self, d, pruneCount):
        wd = {}
        items = sorted(d.items(), key=lambda i:i[1])
        return dict(items[-pruneCount:])

    def _pruneGetBucket(self, words):
        if not words:
            return 0, []
        rcount = words[0][1]
        ret = []
        b_sum = 0.
        while words:
            word, count = words[0]
            if count == rcount:
                b_sum += count
                del words[0]
                ret.append((word, count))
            else:
                break
        return b_sum, ret

    def pruneSymbolsRel(self, d, pruneRatio):
        wd = {}
        words = sorted(d.items(), key=lambda x: x[1])
        total = len(words)
        cutoff = round(total * pruneRatio)
        ret = {}
        pruned = 0
        while words:
            b_sum, bucket = self._pruneGetBucket(words)
            b_size = len(bucket)
            if pruned+b_size < cutoff:
                pruned += b_size
            else:
                ret.update(bucket)
        return ret

    def pruneSymbolsMass(self, d, pruneRatio):
        wd = {}
        words = sorted(d.items(), key=lambda x: x[1])
        total = sum(c for w, c in words)
        cutoff = round(total * pruneRatio)
        ret = {}
        pruned = 0
        while words:
            b_sum, bucket = self._pruneGetBucket(words)
            if pruned+b_sum < cutoff:
                pruned += b_sum
            else:
                ret.update(bucket)
        return ret

    def pruneSymbols(self, d, pruneCount):
        if 0.0 < pruneCount < 1.0:
            return self.pruneSymbolsRel(d, pruneCount)
        elif -1.0 <= pruneCount <= 0.0:
            return self.pruneSymbolsMass(d, -pruneCount)
        elif 1.0 <= pruneCount:
            return self.pruneSymbolsAbs(d, pruneCount)
        elif pruneCount < -1.0:
            return self.pruneSymbolsNum(d, -pruneCount)

    def printPruned(self, orig, pruned, fw=None, symName=None):
        if fw is None:
            fw = sys.stdout
        lo = len(orig)
        lp = len(pruned)
        if symName is None:
            symName = ''
        else:
            symName = ' (%s)' % symName
        fw.write("%% I pruned %0.1f%% symbols%s from the original vocabulary.\n" % ((lo-lp)/float(lo)*100, symName))

    def writeSymbolStats(self, stat_fn, orig, pruned, symName, dataSet):
        fw = file(stat_fn, 'a')
        o_tokens = sum(orig.values())
        o_symbols = len(orig)
        p_tokens = sum(pruned.values())
        p_symbols = len(pruned)
        oov = 1.-(float(p_tokens)/o_tokens)
        pruned_rate = 1.-(float(p_symbols)/o_symbols)
        fw.write("%s_total_tokens=%d\n" % (symName, o_tokens))
        fw.write("%s_total_symbols=%d\n" % (symName, o_symbols))
        fw.write("%s_tokens=%d\n" % (symName, p_tokens))
        fw.write("%s_symbols=%d\n" % (symName, p_symbols))
        fw.write("%s_oov=%.5f\n" % (symName, oov))
        fw.write("%s_pruned_rate=%.5f\n" % (symName, pruned_rate))
        fw.write("%s_dataset=%r\n" % (symName, dataSet))
        fw.close()

    def saveMap(self, fn, d, text=False):
        dir, fn = os.path.split(fn)
        map = LexMap(fn).create(d, text)
        map.save(dir)

    def saveDict(self, fn, d):
        l = d.keys()
        l.sort(mapCmp)
        try:
            f = open(fn, "w")
            for word in l:
                f.write(word.encode("utf-8") + "\n")
        finally:
            f.close()

    def main(self, files, symMap=None, conceptMap=None, dataSet=None,
            defaultDataSet=None, pruneCount=0, text=False, writeConst=None,
            appendConst=None, symName=None, inputChain='none', useEmpty=False,
            stats=None):

        if writeConst is not None and appendConst is not None:
            raise ValueError("Use only writeConst or appendConst, not both")

        if dataSet is None:
            dataSet = 'word'
        if defaultDataSet is None:
            defaultDataSet = 'word'

        if symName is None:
            symName = dataSet

        if writeConst:
            const_fw = file(writeConst, 'w')
        elif appendConst:
            const_fw = file(appendConst, 'a')
        else:
            const_fw = StringIO('w')

        globfiles = set()
        for fn in files:
            if os.path.isdir(fn):
                globfiles |= set(glob(os.path.join(fn, '*.xml')))
            else:
                globfiles.add(fn)
        globfiles = sorted(globfiles)

        generator = self.createSemanticReader(globfiles, dataSet, defaultDataSet, inputChain)

        if conceptMap is not None:
            conceptDict = self.addConcepts(generator, useEmpty)
            conceptDict.update(EXTRA_CONCEPTS)
            self.saveMap(conceptMap, conceptDict, text)
            self.saveDict(conceptMap + '.dict', conceptDict)
            const_fw.write("#define CONCEPT_CARD   %d\n\n" % len(conceptDict))
            

        if symMap is not None:
            symDict = self.addSymbols(generator, useEmpty)
            symDictP = self.pruneSymbols(symDict, pruneCount)
            self.printPruned(symDict, symDictP, symName=dataSet)
            self.printPruned(symDict, symDictP, fw=const_fw, symName=dataSet)
            if stats is not None:
                self.writeSymbolStats(stats, symDict, symDictP, symName, dataSet)
            symDictP.update(EXTRA_SYMBOLS)
            self.saveMap(symMap, symDictP, text)
            self.saveDict(symMap + '.dict', symDictP)
            const_fw.write("#define %s_CARD   %d\n\n" % (symName.upper(), len(symDictP)))

        const_fw.close()

    optionsDoc = {
    'files':
        "Input files, directories are searched for *.xml files",
    'symMap':
        "Output symbol map (without extension). Files .dict and .map are created.",
    'pruneCount':
        """Symbol pruning control. There are three possible pruning modes.
        
        * Absolute pruning 1. It prunes all symbols occuring in training data no
        more than `pruneCount` (eg. --pruneCount=3).

        * Absolute pruning 2. It uses at least `pruneCount` symbols and other
        symbols are pruned. To specify this pruning mode use negative values of
        `pruneCount` (eg. --pruneCount=-200 will use at least 200 symbols).

        * Relative pruning 1. It prunes `pruneCount*totalCount` symbols from
        training data (eg. --pruneCount=0.20 will prune 20% of symbols).

        * Relative pruning 2. It computes cummulative distribution function
        (CDF) of symbols and prunes all symbols under `pruneCount` value of
        CDF. To specify this pruning mode use negative values of `pruneCount`
        (eg. --pruneCount=-0.20 will prune symbols equivalent to 20% of words.
        Let's assume, that corpora has total 1000 words (not unique), it will
        prune symbols representing 200 least frequent words (not unique)).
        """,
    'conceptMap':
        "If specified, it will create concept map (.dict and .map files)",
    'dataSet':
        "For creating symbol map this dataSet is used",
    'defaultDataSet':
        "Main dataSet (for example 'off' must have 'word' default dataset) ",
    'text':
        """Create textual (instead of numerical) maps, used for human readable
        output
        """,
    'writeConst':
        "Write data constants into this file",
    'appendConst':
        """Append data constants to this file (cannot be used with
        --writeConst)
        """,
    'symName': 
        """Symbol name. Used in data constant definition. If it is not specified,
        dataSet value will be used.
        """,
    'stats':
        """File to write symbol statistics to.
        """,
    }


def main():
    script = MapGenerator()
    script.run()

if __name__ == '__main__':
    main()
