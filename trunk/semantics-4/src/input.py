import os
from glob import glob

from svc.egg import PythonEgg
from svc.ui.dxml import DXML
from svc.ui import pdt

import codecs
import re
import semantics
from lexMap import mapCmp
from xml.dom import minidom
import sys
import random
from os.path import *

DEFAULT_DS = None

DONT_LOWER_SETS = ['pos', 'rpos', 'analytical']

DATASET_TYPES = {
    'word': 'normalized',
    'lemma': 'lemmatized',
    'pos': 'pos_tagged',
    'word+pos': 'word_pos',
    'analytical': 'analytical',

    'conf_word': 'confused',
    'conf_lemma': 'confused_lemmatized',
    'conf_pos': 'confused_pos_tagged',

    'signed': 'signed',

    'speech_act': DEFAULT_DS,
    'domain_speech_act': DEFAULT_DS,
    'domain': DEFAULT_DS,

    'off': DEFAULT_DS,
}

class StdInReader(object):
    def __init__(self, type='normalized', speaker='unknown', encoding='iso-8859-2'):
        self.type = type
        self.speaker = speaker
        self.encoding = encoding

    def __iter__(self):
        file_id = 'stdin'

        i = 0
        while True:
            try:
                line = unicode(raw_input(), self.encoding)
            except EOFError:
                break
            das = line.split(';')
            for da in das:
                da_dict = {}
                da_dict['semantics'] = ''
                da_dict['conversational_domain'] = ''
                da_dict['speech_act'] = ''
                da_dict['speaker'] = self.speaker
                da_dict['id'] = "%s_%.5d" % (file_id, i) 
                da_dict['fn'] = 'stdin'
                da_dict[self.type] = da

                yield da_dict
                i += 1

class TXTReader(object):
    def __init__(self, fn, type='normalized', speaker='unknown', encoding='iso-8859-2'):
        self.fn = fn
        self.type = type
        self.speaker = speaker
        self.encoding = encoding

    def __iter__(self):
        file_id = os.path.splitext(os.path.basename(self.fn))[0]
        fr = codecs.open(self.fn, 'r', self.encoding)
        try:
            lines = list(fr)
        finally:
            fr.close()

        i = 0
        for line in lines:
            das = line.split(';')
            for da in das:
                da_dict = {}
                da_dict['semantics'] = ''
                da_dict['conversational_domain'] = ''
                da_dict['speech_act'] = ''
                da_dict['speaker'] = self.speaker
                da_dict['id'] = "%s_%.5d" % (file_id, i) 
                da_dict['fn'] = self.fn
                da_dict[self.type] = da

                yield da_dict
                i += 1

class DXMLReader(object):
    def __init__(self, fn):
        self.fn = fn

    def __iter__(self):
        dxml = DXML.readFromFile(self.fn)
        types = dxml.getDialogueTypes()
        utters = zip(dxml.getUtterances(), *[dxml.getDialogueActs(t) for t in types])
        file_id = os.path.splitext(os.path.basename(self.fn))[0]

        i = 0

        for multi_utter in utters:
            utter_attrs = multi_utter[0]
            multi_utter = multi_utter[1:]
            for multi_da in zip(*multi_utter):
                attrs = multi_da[0][1]
                txts = [da[0] for da in multi_da]

                da_dict = {}
                da_dict['semantics'] = attrs.get('semantics', '')
                da_dict['conversational_domain'] = attrs.get('conversational_domain', '')
                da_dict['speech_act'] = attrs.get('speech_act', '')
                da_dict['speaker'] = utter_attrs.get('speaker', 'unknown')
                da_dict['id'] = "%s_%.5d" % (file_id, i) 
                da_dict['fn'] = self.fn

                for t, txt in zip(types, txts):
                    da_dict[t] = txt
                yield da_dict
                i += 1

        dxml.unlink()

class PDTReader(object):
    def __init__(self, pdt20dir, parent, online=True, type='normalized'):
        self.parent = parent
        self.online = online
        self.type = type
        self.m = pdt.Morphology(pdt20dir)
        self.p = pdt.PDT20Parser()

    def __iter__(self):
        parser = self.p
        morph = self.m
        if self.online:
            for da in self.parent:
                txt = da[self.type]
                gen = parser.parse(morph.process([txt]))
                lemmatized = []
                pos_tagged = []
                for orig, lemma, pos, anl in gen:
                    if lemma is not None:
                        lemmatized.append(lemma)
                    if pos is not None:
                        pos_tagged.append(pos)
                da['lemmatized'] = ' '.join(lemmatized)
                da['pos_tagged'] = ' '.join(pos_tagged)
                yield da
        else:
            das = list(self.parent)
            txts = []
            for da in das:
                txts.append(da[self.type])
            gen = parser.parse(morph.process(txts))
            pdts = []
            for orig, lemma, pos, anl in gen:
                if orig == '<s>':
                    lemmatized = []
                    pos_tagged = []
                    pdts.append((lemmatized, pos_tagged))
                    continue
                if lemma is not None:
                    lemmatized.append(lemma)
                if pos is not None:
                    pos_tagged.append(pos)
            for da, (lemmatized, pos_tagged) in zip(das, pdts):
                da['lemmatized'] = ' '.join(lemmatized)
                da['pos_tagged'] = ' '.join(pos_tagged)
                yield da

class MultiReader(object):
    def __init__(self, fns, readerClass, mask='*', *args, **kwargs):
        self.fns = fns
        self.readerClass = readerClass
        self.args = args
        self.kwargs = kwargs
        self.mask = mask

    def __iter__(self):
        globfiles = set()
        for fn in self.fns:
            if os.path.isdir(fn):
                globfiles |= set(glob(os.path.join(fn, self.mask)))
            else:
                globfiles.add(fn)

        for fn in sorted(globfiles):
            for i in self.readerClass(fn, *self.args, **self.kwargs):
                yield i

class InputGenerator(PythonEgg):
    def __init__(self, reader, data_sets, default_data_set):
        super(InputGenerator, self).__init__()
        self.reader = reader
        self.data_sets = data_sets
        self.types = []
        for d in self.data_sets:
            d = DATASET_TYPES[d]
            if d is DEFAULT_DS:
                d = DATASET_TYPES[default_data_set]
            self.types.append(d)

    def readInputs(self):
        for da in self.reader:
            self.synthDA(da)

            da_fn = da['fn']
            da_id = da['id']
            da_semantics = da['semantics']

            da_txts = self.mapDialogueAct(da)
            yield da_fn, da_id, da_semantics, da_txts

    def synthDA_LemmaPos(self, da):
        try:
            txt_word = da[DATASET_TYPES['word']].split()
            txt_pos = da[DATASET_TYPES['pos']].split()
        except KeyError:
            # Return DA unchanged
            return da
        ret = []
        for word, pos in zip(txt_word, txt_pos):
            if pos[0] == 'C':
                ret.append(pos)
            else:
                ret.append(word)
        da[DATASET_TYPES['word+pos']] = ' '.join(ret)
        return da

    def synthDA(self, da):
        da = self.synthDA_LemmaPos(da)
        return da

    def readSemantics(self, parseType='LR'):
        for da_fn, da_id, da_semantics, da_txts in self.readInputs():
            smntcs = [semantics.Semantics(da_id, da_semantics, ' '.join(txt), parseType) for txt in da_txts]
            yield smntcs

    def removeUnderscores(self, line):
        return [w.replace('_', 'x') for w in line]

    def mapDialogueAct(self, da):
        ret = []
        for data_set, type in zip(self.data_sets, self.types):
            const_mapping = False
            random_mapping = False
            dont_lower = data_set in DONT_LOWER_SETS

            if data_set.startswith('const'):
                items = data_set.split('_', 1)
                if len(items) == 2: const_mapping = items[1]
                else:               const_mapping = 'constant'
            elif data_set == 'off':
                const_mapping = 'off'
            elif data_set.startswith('random'):
                items = data_set.split('_', 1)
                if len(items) == 2: random_mapping = int(items[1]) - 1
                else:               raise ValueError("Specify random dataset cardinality (eg. random_100)")
                random.seed(fileName)
            elif data_set == 'domain_speech_act':
                const_mapping = da['conversational_domain'] + '.' + da['speech_act']
            elif data_set == 'speech_act':
                const_mapping = da['speech_act']
            elif data_set == 'domain':
                const_mapping = da['conversational_domain']

            if type not in da:
                raise KeyError("Generated dialogue act (id %s) doesn't have type %r" % (da['id'], type))

            txt = da[type].split()

            if const_mapping:
                txt = [const_mapping for w in txt]
            if random_mapping:
                txt = ['rand%04d' % random.randint(0, random_mapping) for w in txt]

            if not dont_lower:
                txt = [w.lower() for w in txt]
            ret.append(self.removeUnderscores(txt))
        return ret

