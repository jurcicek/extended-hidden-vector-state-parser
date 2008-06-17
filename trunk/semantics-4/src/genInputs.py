#!/usr/bin/env python2.4

import os.path
from glob import glob
import codecs
import sys

from svc.scripting import *
from svc.ui.dxml import DXML

from lexMap import LexMap
from semantics import Semantics, removeTextFromSemantics, splitSmntcsToMlf
from svc.ui.smntcs import input
import observation
import random

class InputGenerator(Script):
    """Input file generator for semantic parser

    This program creates .hddn, .obs and .obs.orig files needed for training
    semantic model, it also generates reference MLF and PTB files. It can
    generate list of files for subsequential usage. Concrete dataset from input
    XML files can be selected.
    """
    options = {
        'parseType': String,
        'files': (Required, Multiple, String),
        'dataSet': (Multiple, Required, String),
        'outDir': (Required, String),
        'outList': (Multiple, String),
        'unsList': (Multiple, String),
        'conceptMap': String,
        'outputMlf': String,
        'outputMlfDcd': String,
        'outputMlfSmntcs': String,
        'origDataSets': String,
        'extraExt': String,
        'txtInput': Flag,
        'pdtDir': String,
        'inputChain': String,
        'useEmpty': Integer,
    }

    debugMain = True

    def splitDatasetEmpty(self, semantics, useEmpty=False):
        """Return lists of filled and empty semantics
        """
        filled = []
        empty = []
        for all_smntcs in semantics:
            first = all_smntcs[0]
            if not useEmpty and first.isEmpty():
                empty.append(all_smntcs)
            else:
                filled.append(all_smntcs)
        return filled, empty

    def firstSymbols(self, semantics):
        """Return list of semantics

        From list of tuples create list of first items in these tuples.  Used
        for creating list of Semantics from list of multiple Semantics.
        """
        ret = []
        for all_smntcs in semantics:
            ret.append(all_smntcs[0])
        return ret

    def mapObs(self, observations, maps, markUW=False, unseen='_unseen_', counting=True):
        """Map `observations` into output symbols using `maps`

        `observations` and `maps` are sequences of the same length. Items of
        `maps` must implement mapping protocol (has_key, __getitem__). Every
        item `observations[i]` is replaced with `maps[i][observations[i]]`. If
        observations[i] is not found in maps[i] and markUW is True, it is
        replaced using `maps[i][unseen]` (parameter unseen defaults to
        `_unseen_`).

        If markUW is False (default), no unseen substitution is done.

        Seen and unseen observations are handled using countSeen and
        countUnseen attributes. If `observations[i]` is found in `maps[i]`,
        `countSeen[i]` is increased, otherwise `countUnseen[i]` is increased.

        :Returns:
            New list of mapped observations.
        """
        ret = []
        for i, (map, obs) in enumerate(zip(maps, observations)):
            if map.has_key(obs):
                obs = map[obs]
                if counting: self.countSeen[i] += 1
            elif markUW:
                obs = map[unseen]
                if counting: self.countUnseen[i] += 1
            ret.append(obs)
        return ret

    def saveMultiObs(self, multi_obs, fn, maps, markUW=False, counting=True):
        """Save `multi_obs` into file `fn` using symbol `maps`

        `multi_obs` is tuple of lists. These lists contains multiple
        observations for the whole dialogue. 
        
        These lists of observations are zipped together and mappend using
        `mapObs` method and `maps` and `markUW` parameters into output symbols
        and saved into file `fn`.
        """
        obsFile = codecs.open(fn, "w", "utf-8")
        
        for line in zip(*multi_obs):
            line_cols = self.mapObs(line, maps, markUW, counting=counting)
            obsFile.write('\t'.join(line_cols) + "\n")
            
        obsFile.close()

    def writeOrigFiles(self, dirOut, orig_semantics):
        """Write original observations os `orig_semantics` into `dirOut`
        """
        for smntcs in orig_semantics:
            # save an observation file 
            if len(smntcs) != 2:
                raise ValueError("Original semantics must contain exactly these datasets: word, lemma")
            file_id = smntcs[0].id 
            word_obs = smntcs[0].getObs(self.parseType).obs

            fn = os.path.join(dirOut, file_id+'.obs.orig')
            self.saveMultiObs([obs], fn, [{}], markUW=False, counting=False)

    def writeObservationFiles(self, dirOut, semantics, maps, extra_ext='', add_ext='', markUW=True):
        """Write observation files of `semantics` into `dirOut`

        `semantics` is list of tuples. These tuples contains multiple Semantics
        for one dialogue. For every dialogue two files are created in directory
        `dirOut`. File name of this files are following:
            - dialogue_id + `extra_ext` + '.obs' + `add_ext` (with _unseen_ symbols)
        """
        for multi_smntcs in semantics:
            # save an observation file 
            file_id = multi_smntcs[0].id 
            multi_obs = [s.getObs(self.parseType).obs for s in multi_smntcs]

            fn = os.path.join(dirOut, file_id+extra_ext+'.obs'+add_ext)
            self.saveMultiObs(multi_obs, fn, maps, markUW=markUW)

    def writeHiddenFiles(self, dirOut, semantics, conceptMap, symMap):
        """Write hidden observation files of `semantics` into `dirOut`

        For every Semantic in `semantics` create HiddenObservation instance and
        save it into `dirOut` using `conceptMap` and `symMap`
        """
        for smntcs in semantics:
            # save hidden variables
            smntcs.getHiddenObs(self.parseType).save(dirOut, conceptMap, symMap)

    def writeMLF_SMNTCSFile(self, mlf_fn, semantics, ext='.lab'):
        mlf = codecs.open(mlf_fn, "w", "UTF-8")
        try:
            mlf.write("#!MLF!#\n")
            for smntcs in semantics:
                idLab = os.path.splitext(os.path.splitext(os.path.basename(smntcs.id))[0])[0]
                mlf.write('"*/' + idLab + ext +'"\n')
                mlf.write(smntcs.semantics + "\n")
                mlf.write(".\n")
        finally:
            mlf.close()

    def writeMLF_DCDFile(self, mlf_fn, semantics, ext='.lab'):
        mlf = codecs.open(mlf_fn, "w", "UTF-8")
        try:
            mlf.write("#!MLF!#\n")
            for smntcs in semantics:
                smntcsWithoutText = removeTextFromSemantics(smntcs.semantics)
                smntcsSplit = splitSmntcsToMlf(smntcsWithoutText)
    
                idLab = os.path.splitext(os.path.splitext(os.path.basename(smntcs.id))[0])[0]
                mlf.write("#######################################\n")
                mlf.write('"*/' + idLab + '.lab"\n')
                mlf.write("#######################################\n")
    
                for each in smntcsSplit:
                    mlf.write(each + "\n")
        finally:
            mlf.close()

    def writeMLFFile(self, mlf_fn, semantics, ext='.lab'):
        mlf = codecs.open(mlf_fn, "w", "UTF-8")
        try:
            mlf.write("#!MLF!#\n")
            for smntcs in semantics:
                smntcsWithoutText = removeTextFromSemantics(smntcs.semantics)
                smntcsSplit = splitSmntcsToMlf(smntcsWithoutText)
    
                idLab = os.path.splitext(os.path.splitext(os.path.basename(smntcs.id))[0])[0]
                mlf.write('"*/' + idLab + '.lab"\n')
    
                for each in smntcsSplit:
                    mlf.write(each + "\n")
        finally:
            mlf.close()

    def writePTBFile(self, ptb_fn, semantics):
        fw = codecs.open(ptb_fn, "w", "UTF-8")
        try:
            for smntcs in semantics:
                smntcsWithoutText = removeTextFromSemantics(smntcs.semantics)
                smntcsWithoutText = Semantics('id', smntcsWithoutText, 'x')
                try:
                    fw.write(smntcsWithoutText.getPTBSemantics() + '\n')
                except ValueError:
                    fw.write("(TOP x)\n")
        finally:
            fw.close()
        
    def writeListFile(self, lst_fn, template, semantics):
        """Write list of `semantics` into file `lst_fn` using `template`

        Template is string processed using standard % operator. The only one
        allowed key is 'id', so `template` can look like
        'data/train/ho/%(id)s'. Every occurence of %(id)s are substituted using
        dialogue id. List of these files is stored into file `lst_fn`.
        """
        fw = file(lst_fn, 'w')
        try:
            for smntcs in semantics:
                fw.write(template % {'id': smntcs.id} + '\n')
        finally:
            fw.close()

    def readSemantics(self, files, dataSets, parseType, origDataSet, txtInput=False, pdtDir=None, inputChain='none'):
        if txtInput:
            reader = input.MultiReader(files, input.TXTReader)
            if 'lemma' in dataSets or 'pos' in dataSets:
                if pdtDir is None:
                    raise ValueError("Couldn't find PDT-2.0, no directory supplied")
                reader = input.PDTReader(pdtDir, reader, online=False)
        else:
            reader = input.MultiReader(files, input.DXMLReader)
        reader = input.InputChain(inputChain, reader)
        generator = input.InputGenerator(reader, dataSets, origDataSet)
        for da_fn, da_id, da_semantics, da_txts in generator.readInputs():
            s = [Semantics(da_id, da_semantics, ' '.join(txt), parseType) for txt in da_txts]
            yield s

    def main(self, files, outDir, conceptMap=None, outList=[], outputMlf=None,
            outputMlfDcd=None, outputMlfSmntcs=None, unsList=[], dataSet=None,
            parseType='LR', extraExt='', origDataSets='word,lemma',
            txtInput=False, pdtDir=None, inputChain='none', useEmpty=False):

        dataSets = []
        dataMaps = []
        for set_map in dataSet:
            s, m = set_map.rsplit(':', 1)
            m = LexMap().read(m)
            dataSets.append(s)
            dataMaps.append(m)

        if txtInput and ('lemma' in dataSets or 'pos' in dataSets) and not pdtDir:
            raise ValueError("If you wish to use txt input together with lemma or pos dataset, you must say, where to find PDT-2.0")

        self.countSeen = [0] * len(dataSets)
        self.countUnseen = [0] * len(dataSets)

        self.parseType = parseType

        globfiles = set()
        for fn in files:
            if os.path.isdir(fn):
                globfiles |= set(glob(os.path.join(fn, '*.xml')))
            else:
                globfiles.add(fn)
        globfiles = sorted(globfiles)

        origDataSets = origDataSets.split(',')
        if len(origDataSets) != 2:
            raise ValueError("Option origDataSets must contain two datasets separated with comma")

        semantics = self.readSemantics(globfiles, dataSets, parseType, origDataSets[0], txtInput, pdtDir, inputChain)
        orig_semantics = self.readSemantics(globfiles, origDataSets, parseType, origDataSets[0], txtInput, pdtDir, inputChain)
        orig_maps = [{}, {}]

        semantics, empty_semantics = self.splitDatasetEmpty(semantics, useEmpty)
        orig_semantics, empty_orig_semantics = self.splitDatasetEmpty(orig_semantics, useEmpty)

        simpleMap = dataMaps[0]
        simple_semantics = self.firstSymbols(semantics)
        simple_empty_semantics = self.firstSymbols(empty_semantics) 

        for item in outList:
            fn, templ = item.split(':', 1)
            self.writeListFile(fn, templ, simple_semantics)

        self.writeObservationFiles(outDir, semantics, dataMaps, extra_ext=extraExt)
        self.writeObservationFiles(outDir, orig_semantics, orig_maps, add_ext='.orig', markUW=False)

        if conceptMap is not None:
            conceptMap = LexMap().read(conceptMap)
            self.writeHiddenFiles(outDir, simple_semantics, conceptMap, simpleMap)

        if unsList:
            self.writeObservationFiles(outDir, empty_semantics, dataMaps, extra_ext=extraExt)
            self.writeObservationFiles(outDir, empty_orig_semantics, orig_maps, add_ext='.orig', markUW=False)
            for item in unsList:
                fn, templ = item.split(':', 1)
                self.writeListFile(fn, templ, simple_empty_semantics)

        if outputMlf is not None:
            self.writeMLFFile(outputMlf, simple_semantics)
            self.writePTBFile(outputMlf+'.ptb', simple_semantics)

        if outputMlfDcd is not None:
            self.writeMLF_DCDFile(outputMlfDcd, simple_semantics)

        if outputMlfSmntcs is not None:
            self.writeMLF_SMNTCSFile(outputMlfSmntcs, simple_semantics, ext='.rec')
    
    def printRunningTokens(self, dataSets, fw=None):
        if fw is None:
            fw = sys.stdout

        fw.write("% Amount of unseen words in data sets:\n")
        for setName, seen, unseen in zip(dataSets, self.countSeen, self.countUnseen):
            fw.write("%%     %10s : %5.2f%%\n" % (setName, float(unseen) / (seen+unseen) * 100))

    optionsDoc = {
    'parseType': "Semantics tree parse type",
    'outDir':
        """Output directory of .hddn, .obs and .obs.orig files. Both sentences
        with and without semantic annotation are stored here.
        """,
    'outList':
        """Option used to generate file with list of sentences with semantic
        annotation. You can specify it multiple times to create multiple lists.
        Example: `--outList=train.list:./train/ho/%(id)s.obs` will create file
        `train.list` with lines like `./train/ho/ID.obs` where `ID` are
        identifiers of distinct sentences.
        """,
    'unsList':
        """Option used to generate file with list of sentences without semantic
        annotation. Use it like --outList option.
        """,
    'files': "Input files, directories are searched for *.xml files.",
    'conceptMap': "File with concept mapping",
    'outputMlf': "Output MLF file",
    'outputMlfDcd': "Output MLF file (DCD variation)",
    'outputMlfSmntcs': "Output MLF file (Smntcs variation)",
    'dataSet': "Dataset selector in form: `parametrized_act:type=lemmatized;map_file`",
    'extraExt': "Extra extension added before .obs, for example .1 will lead to .1.obs and .1.obs.orig"
    }


def main():
    script = InputGenerator()
    script.run()

if __name__ == '__main__':
    main()
