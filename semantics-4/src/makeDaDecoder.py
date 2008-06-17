#!/usr/bin/env python2.4

import sys
import os
import codecs
import tempfile
from math import log10

from svc.scripting.externals import *
from svc.utils import ADict
from svc.map import SymMap
from svc.osutils import mkdirp
from svc.template import ExTemplate
from svc.ui.smntcs import input

NgramCount = ExternalMethod('ngram-count', etype=ExecNoStdout)
Ngram = ExternalMethod('ngram', etype=ExecList, logger=lambda obj, line:None)
MakeNgramPFSG = ExternalMethod('make-ngram-pfsg', etype=ExecGenerator, logger=lambda obj, line:None)
PFSGToFsm = ExternalMethod('pfsg-to-fsm', etype=ExecGenerator)
PFSGToFsmNoStdout = ExternalMethod('pfsg-to-fsm', etype=ExecNoStdout)
FSMCompile = ExternalMethod('fsmcompile', etype=ExecNoStdout)
FSMCompileGenerator = ExternalMethod('fsmcompile', etype=ExecGenerator)
FSMMinimize = ExternalMethod('fsmminimize', etype=ExecGenerator)
FSMPrint = ExternalMethod('fsmprint', etype=ExecGenerator)

class MakeDaDecoder(ExternalScript):
    externalMethodDirs = ['bin/semantics']

    externalMethods = {
        'dacoderFilter': ExecGenerator,
    }

    options = {
        'dataTrn': (Required, String),
        'dataHldt': (Required, String),
        'dataTst': (Required, String),
        'dataLm': (Required, String),
    }

    def genTrainDAs(self, dataTrn):
        reader = input.MultiReader([dataTrn], input.DXMLReader)
        return input.InputGenerator(reader, ['word'], 'word')

    def splitByParse(self, input):
        counter = 0
        ret = ['']
        for i in input:
            ret[-1] += i
            if i == '(':
                counter += 1
            elif i == ')':
                counter -= 1
                if counter == 0:
                    ret.append('')
        ret = [''.join(j) for j in (i.strip() for i in ret) if j]
        return ret

    def omitConcepts(self, input, noRemove=None):
        w = []
        for i in input:
            if i == ',':
                i = ' '
            if i in '()':
                w.append(' ')
            w.append(i)
            if i in '()':
                w.append(' ')
        w = ''.join(w).split()
        n_removed = 0
        i = 0
        while i < len(w):
            if w[i] == '(':
                del w[i]
                if (noRemove == 'first' and n_removed == 0) or (noRemove == 'all'):
                    continue
                del w[i-1]
                i = i-1
                n_removed += 1
                continue
            elif w[i] == ')':
                del w[i]
                continue
            else:
                i += 1
        return w

    def collectDAs(self, das):
        ret = []
        old_fn = None
        dlg = []
        for da in das:
            if old_fn != da['fn']:
                if dlg:
                    ret.append(dlg)
                dlg = []
                old_fn = da['fn']
            da_speaker = da['speaker']
            da_type = (da['da_conversational_domain'], da['da_speech_act'])
            da_words = da['word']
            fa = self.splitByParse(' '.join(da['fa_trn']))
            for k in fa:
                k = self.omitConcepts(k, noRemove='first')
                dlg.append( (da_speaker, da_type, k) )
        else:
            if dlg:
                ret.append(dlg)
        return ret

    def computePriors(self, separ):
        counts = [(k, len(v)) for (k,v) in separ.iteritems()]
        s = 0.
        for da, count in counts:
            s += count

        return [log10(v/s) for (k,v) in sorted(counts)]
    
    def mapDAtype(self, da_speaker, da_type, type='selected', with_speaker=False):
        da_1, da_2 = da_type
        da = None
        if type == 'speech_act':
            if not da_2:
                da = None
            da = '%s' % (da_2, )
        elif type == 'domain':
            if not da_1:
                da = None
            da = '%s' % (da_1, )
        elif type == 'selected':
            if da_2 in ['thanking', 'closing', 'opening', 'acknowledgement', 'request_info', 'present_info']:
                da = '%s' % (da_2, )
            elif 'conf' in da_2:
                da = 'present_info'
            else:
                da = 'other'
        elif type == 'speaker':
            da = da_speaker
        else:
            if not (da_1 and da_2):
                da = None
            da = '%s_%s' % (da_1, da_2)
        if not da:
            return None
        elif with_speaker:
            return da_speaker + '_' + da
        else:
            return da

    def separateDAs(self, dlgs):
        ret = ADict(default=list)
        for dlg in dlgs:
            for da_speaker, da_type, da_words in dlg:
                da = self.mapDAtype(da_speaker, da_type)
                if da is None:
                    continue
                ret[da].append(da_words)
        return ret

    def writeDAs(self, separ, dataLm):
        mkdirp(dataLm)

        for da, da_words in separ.iteritems():
            fn = self.mapTXT(dataLm, da)
            fw = codecs.open(fn, 'w', 'utf-8')
            try:
                for item in da_words:
                    fw.write("%s\n" % (' '.join(item),))
            finally:
                fw.close()

    def makeLMs(self, separ, dataLm, vocabFile):
        for da in separ:
            fn = self.mapTXT(dataLm, da)
            fn_lm = self.mapLM(dataLm, da)
            NgramCount('-map-unk', '_unseen_', '-unk', '-text', fn, '-order', '3', '-lm', fn_lm, '-wbdiscount', '-vocab', vocabFile)
            # NgramCount('-unk', '-text', fn, '-order', '3', '-lm', fn_lm, '-wbdiscount', '-vocab', vocabFile)
            # NgramCount('-text', fn, '-order', '3', '-lm', fn_lm, '-vocab', vocabFile)

    def convertLMtoFSM(self, fn_lm, sym_file=None):
        if sym_file is not None:
            PFSGToFsmNoStdout('symbolfile=%s' % sym_file, stdin=MakeNgramPFSG(fn_lm), env={})
        else:
            def fsmgen():
                for line in PFSGToFsm('scale=-1', stdin=MakeNgramPFSG(fn_lm), env={}):
                    # GAWK hack
                    line = line.replace(',', '.')
                    yield line
            return FSMPrint(stdin=FSMMinimize(stdin=FSMCompileGenerator(stdin=fsmgen())))

    def makeFMStxt(self, separ, dataLm):
        isym_map = None
        isym_fn = os.path.join(dataLm, 'dacoder.fsm.isym')
        fsm = os.path.join(dataLm, 'dacoder.fsm.txt')
        fsm_fw = file(fsm, 'w')
        add = 1
        da_map = SymMap.readFromFile(os.path.join(dataLm, 'dialogue_act.fsm.isym'))
        for da in separ:
            fn = self.mapTXT(dataLm, da)
            fn_lm = self.mapLM(dataLm, da)
            fn_fsm = self.mapFSM(dataLm, da)

            da_num_op = da_map['operator_'+da]
            da_num_us = da_map['user_'+da]

            if isym_map is None:
                self.convertLMtoFSM(fn_lm, isym_fn)
                isym_map = SymMap.readFromFile(isym_fn)
                _empty_ = isym_map.add('_empty_')
                _operator_ = isym_map.add('_operator_')
                _user_ = isym_map.add('_user_')
                for i in separ:
                    isym_map.add('user_%s' % i)
                    isym_map.add('operator_%s' % i)
                isym_map.writeToFile(isym_fn)

            s0 = None
            states = set()
            for line in self.convertLMtoFSM(fn_lm):
                # GAWK hack
                line = line.replace(',', '.')
                splitted = line.split()

                if s0 is None:
                    s0 = int(splitted[0])+add
                    print >> fsm_fw, '0\t%d\t%d\t%d\t0' % (s0, _operator_, da_num_op, )
                    print >> fsm_fw, '0\t%d\t%d\t%d\t0' % (s0, _user_, da_num_us, )

                if len(splitted) in (1, 2):
                    state_no = int(splitted[0])
                    if len(splitted) == 2:
                        weight = float(splitted[1])
                    else:
                        weight = 0.
                    print >> fsm_fw, '%d\t0\t%d\t0\t%e' % (state_no + add, _empty_, weight)
                    states.add(state_no)
                elif len(splitted) in (3, 4):
                    state_no_1 = int(splitted[0])
                    state_no_2 = int(splitted[1])
                    isym = int(splitted[2])
                    if len(splitted) == 4:
                        weight = float(splitted[3])
                    else:
                        weight = 0.
                    print >> fsm_fw, '%d\t%d\t%d\t0\t%e' % (state_no_1+add, state_no_2+add, isym, weight)
                    states.add(state_no_1)
                    states.add(state_no_2)
                else:
                    raise ValueError("Unknown FSM line: %r" % line)
            add += max(states)+1
        for i in separ:
            for j in ['user', 'operator']:
                da = '%s_%s' % (j, i)
                isym = isym_map[da]
                osym = da_map[da]
                print >> fsm_fw, '0\t0\t%d\t%d\t0' % (isym, osym)
        print >> fsm_fw, '0'
        fsm_fw.close()
        da_map.writeToFile(os.path.join(dataLm, 'dacoder.fsm.osym'))
        FSMCompile('-t', fsm, '-F', os.path.join(dataLm, 'dacoder.fsm'))

    def mapTXT(self, dataLm, lm_name):
        return os.path.join(dataLm, lm_name+'.txt')

    def mapLM(self, dataLm, lm_name):
        return os.path.join(dataLm, lm_name+'.lm')

    def mapFSM(self, dataLm, lm_name):
        return os.path.join(dataLm, lm_name+'.fsm')

    def makeDaVocab(self, separ):
        ret = set()
        for da, sentences in separ.iteritems():
            ret.add('operator_'+da)
            ret.add('user_'+da)
        return ret

    def collectVocab(self, separ):
        ret = set()
        for key, sentences in separ.iteritems():
            for words in sentences:
                ret |= set(words)
        return ret

    def writeVocab(self, vocab, fn):
        fw = codecs.open(fn, 'w', 'utf-8')
        for w in sorted(vocab):
            print >> fw, w
        fw.close()

    def createDAseq(self, dlgs):
        ret = []
        for dlg in dlgs:
            this_dlg = []
            ret.append(this_dlg)
            for da_speaker, da_type, da_words in dlg:
                da = self.mapDAtype(da_speaker, da_type, with_speaker=True)
                if da is None:
                    continue
                this_dlg.append( da )
        return ret
    
    def writeDAseq(self, fn, da_seq):
        fw = codecs.open(fn, 'w', 'utf-8')
        for dlg in da_seq:
            print >> fw, ' '.join(dlg)
        fw.close()

    def makeDALM(self, fn, fn_lm, fn_fsm, da_vocab):
        NgramCount('-text', fn, '-order', '2', '-lm', fn_lm, '-wbdiscount', '-vocab', da_vocab)
        fw = file(fn_fsm+'.txt', 'w')
        for line in PFSGToFsm('symbolfile=%s' % (fn_fsm+'.isym',), 'scale=-1', stdin=MakeNgramPFSG(fn_lm)):
            line = line.replace(',', '.')
            print >> fw, line,
        fw.close()
        FSMCompile(fn_fsm+'.txt', '-F', fn_fsm)

    def prepareFSMinput(self, dlgs):
        ret = []
        for das in dlgs:
            ref = []
            words = []
            for (speaker, da_type, da_words) in das:
                da = self.mapDAtype(speaker, da_type, with_speaker=True)
                if da is None:
                    continue
                ref.append(da)
                words.append('_%s_' % speaker)
                words.extend(da_words)
                words.append('_empty_')
            ret.append( (tuple(ref), tuple(words)) )
        return ret

    def evaluateFSM(self, dataLm, dlgs):
        prepared_input = self.prepareFSMinput(dlgs)
        def genFSMlines():
            for ref, words in prepared_input:
                yield (' '.join(words) + '\n').encode('utf-8')
        ret = []
        for (ref, words), output_line in zip(prepared_input, self.dacoderFilter(dataLm, stdin=genFSMlines())):
            hyp = tuple(output_line.split())
            yield (ref, hyp) 

    def evaluateDir(self, outDir, prefix, dataDir):
        dlgs = self.collectDAs(self.genTrainDAs(dataDir))

        fw_orig = file(os.path.join(outDir, prefix + '_ref.mlf'), 'w')
        fw_hyp = file(os.path.join(outDir, prefix + '_hyp.mlf'), 'w')
        try:
            print >> fw_orig, '#!MLF!#'
            print >> fw_hyp, '#!MLF!#'
            i = 0
            for ref, hyp in self.evaluateFSM(outDir, dlgs):
                ref = ' '.join(ref)
                hyp = ' '.join(hyp)
                print >> fw_orig, '"*/%05d"' % i
                print >> fw_hyp, '"*/%05d"' % i

                print >> fw_orig, ref
                print >> fw_orig, '.'

                print >> fw_hyp, hyp
                print >> fw_hyp, '.'
                i += 1
        finally:
            fw_orig.close()
            fw_hyp.close()

    def main(self, dataTrn, dataHldt, dataLm, dataTst):
        dataLmHldt = os.path.join(dataLm, 'hldt')
        dlgLmHldtTxt = os.path.join(dataLmHldt, 'dialogue_act.txt')
        dlgLmTxt = os.path.join(dataLm, 'dialogue_act.txt')
        dlgLm = os.path.join(dataLm, 'dialogue_act.lm')
        dlgLmFSM = os.path.join(dataLm, 'dialogue_act.fsm')

        das = self.genTrainDAs(dataTrn)
        dlgs = self.collectDAs(das)
        separ = self.separateDAs(dlgs)

        da_seq = self.createDAseq(dlgs)
        daVocabFile = os.path.join(dataLm, 'da_vocab.txt')
        daVocab = self.makeDaVocab(separ)
        self.writeVocab(daVocab, daVocabFile)
        self.writeDAseq(dlgLmTxt, da_seq)
        self.makeDALM(dlgLmTxt, dlgLm, dlgLmFSM, daVocabFile)

        vocab = self.collectVocab(separ)
        vocabFile = os.path.join(dataLm, 'vocab.txt')
        self.writeVocab(vocab, vocabFile)

        self.writeDAs(separ, dataLm)
        self.makeLMs(separ, dataLm, vocabFile)
        self.makeFMStxt(separ.keys(), dataLm)

        self.evaluateDir(dataLm, 'hldt', dataHldt)
        self.evaluateDir(dataLm, 'tst', dataTst)

if __name__ == '__main__':
    s = MakeDaDecoder()
    s.run()
