# SVC library - usefull Python routines and classes
# Copyright (C) 2006-2008 Jan Svec, honza.svec@gmail.com
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
from glob import glob

from svc.utils import all_same

from svc.egg import PythonEgg
from svc.ui.dxml import DXML
from svc.ui import pdt

import codecs
import re
from xml.dom import minidom
import sys
import random
from os.path import *

DEFAULT_DS = None

DONT_LOWER_SETS = ['pos', 'rpos', 'analytical', 'word+pos']

DONT_REMOVE_UNDERSCORES = ['speech_act', 'domain_speech_act', 'domain',
        'signed', 'bigram_word', 'bigram_lemma', 'bigram_pos']

REMOVE_SINGLE_UNDERSCORE = ['signed']

DATASET_TYPES = {
    'word': 'normalized',
    'lemma': 'lemmatized',
    'pos': 'pos_tagged',

    # Experimental
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

def removeNEs(s):
    s = re.sub(r'\[[^\]]*\]', '', s)
    s = re.sub(r' +', ' ', s)
    return s

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
                da_dict['da_conversational_domain'] = ''
                da_dict['da_speech_act'] = ''
                da_dict['speaker'] = self.speaker
                da_dict['id'] = "%s_%.5d" % (file_id, i) 
                da_dict['fn'] = 'stdin'
                da_dict['ne_source'] = da
                da_dict[self.type] = removeNEs(da).split()

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
                da_dict['da_conversational_domain'] = ''
                da_dict['da_speech_act'] = ''
                da_dict['speaker'] = self.speaker
                da_dict['id'] = "%s_%.5d" % (file_id, i) 
                da_dict['fn'] = self.fn
                da_dict['ne_source'] = da
                da_dict[self.type] = removeNEs(da).split()

                yield da_dict
                i += 1

class DXMLReader(object):
    def __init__(self, fn, ne_type='normalized'):
        self.fn = fn
        self.ne_type = ne_type

    def __iter__(self):
        dxml = DXML.readFromFile(self.fn)
        types = dxml.getDialogueTypes()
        utters = zip(dxml.getUtterances(), dxml.getDialogueActs(self.ne_type, removeNE=False), 
                     *[dxml.getDialogueActs(t) for t in types])
        file_id = os.path.splitext(os.path.basename(self.fn))[0]

        i = 0

        for multi_utter in utters:
            utter_attrs = multi_utter[0]
            multi_utter = multi_utter[1:]
            for multi_da in zip(*multi_utter):
                ne_typed = multi_da[0][0]
                multi_da = multi_da[1:]
                attrs = multi_da[0][1]
                txts = [da[0] for da in multi_da]


                da_dict = {}
                da_dict['semantics'] = attrs.get('semantics', '')
                da_dict['da_conversational_domain'] = attrs.get('conversational_domain', '')
                da_dict['da_speech_act'] = attrs.get('speech_act', '')
                da_dict['speaker'] = utter_attrs.get('speaker', 'unknown')
                da_dict['id'] = "%s_%.5d" % (file_id, i) 
                da_dict['fn'] = self.fn
                da_dict['ne_source'] = ne_typed

                for t, txt in zip(types, txts):
                    da_dict[t] = txt.split()
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
                gen = parser.parse(morph.process(txt))
                lemmatized = []
                pos_tagged = []
                for orig, lemma, pos, anl in gen:
                    if lemma is not None:
                        lemmatized.append(lemma)
                    if pos is not None:
                        pos_tagged.append(pos)
                da['lemmatized'] = lemmatized
                da['pos_tagged'] = pos_tagged
                yield da
        else:
            das = list(self.parent)
            txts = []
            for da in das:
                txts.append(da[self.type])
            txts = [' '.join(i) for i in txts]
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
                da['lemmatized'] = lemmatized
                da['pos_tagged'] = pos_tagged
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
    def __init__(self, reader, data_sets, default_data_set, noUnderscores=True):
        super(InputGenerator, self).__init__()
        self.reader = reader
        self.data_sets = data_sets
        self.default_data_set = default_data_set
        self.no_underscores = noUnderscores

    def readDAs(self):
        for da in self.reader:
            da = self.renameDA(da)
            da = self.synthDA(da)
            da = self.postprocessDA(da)
            self.checkDA(da)
            yield da

    __iter__ = readDAs

    def renameDA(self, da):
        for ds, dt in DATASET_TYPES.iteritems():
            if dt in da:
                da[ds] = da.pop(dt)
        return da

    def checkDA(self, da):
        for ds in self.data_sets:
            if ds not in da:
                raise KeyError("Dialogue act (id %s) doesn't have dataset %r" % (da['id'], ds))

    def synthDA(self, da):
        da = self.synthDA_fromDefaultDS(da)
        da = self.synthBigrams(da)
        return da

    def synthDA_fromDefaultDS(self, da):
        txt = da[self.default_data_set]

        da['off'] = ['off' for w in txt]

        conversational_domain = da['da_conversational_domain']
        if not conversational_domain:
            conversational_domain = 'none'
        speech_act = da['da_speech_act']
        if not speech_act:
            speech_act = 'none'

        da['domain_speech_act'] = [conversational_domain+'.'+speech_act for w in txt]
        da['speech_act'] = [speech_act for w in txt]
        da['domain'] = [conversational_domain for w in txt]

        return da

    def synthBigrams(self, da):
        for ds in self.data_sets:
            if ds.startswith('bigram_'):
                old_ds = ds[len('bigram_'):]
                symbols = da[old_ds]
                new_symbols = []
                for i in range(len(symbols)):
                    bigram = symbols[i-1:i+1]
                    new_symbols.append('_'.join(bigram))
                da[ds] = new_symbols
        return da

    def postprocessDA(self, da):
        for ds in DATASET_TYPES:
            if ds not in da:
                continue
            if ds not in DONT_LOWER_SETS:
                da[ds] = [w.lower() for w in da[ds]]

            if self.no_underscores:
                remove_single_underscore = ds in REMOVE_SINGLE_UNDERSCORE
                if ds not in DONT_REMOVE_UNDERSCORES:
                    da[ds] = self.removeUnderscores(da[ds], remove_single_underscore)

        ne_source = da['ne_source']
        ne_part = []
        ne_typed = []
        i = 0
        j = 0
        for match in re.finditer(r'\[(?P<type>\w*)\](?P<content>.*?)\[/(?P=type)\]', ne_source):
            normal = ne_source[i:match.start()].strip()
            if normal:
                for w in normal.split():
                    ne_typed.append(None)
                    ne_part.append(j)
                j += 1
            type = match.group('type')
            content = match.group('content').strip()
            for w in content.split():
                ne_typed.append(type)
                ne_part.append(j)
            j += 1
            i = match.end()
        else:
            normal = ne_source[i:].strip()
            if normal:
                for w in normal.split():
                    ne_typed.append(None)
                    ne_part.append(j)
                j += 1

        da['ne_typed'] = ne_typed
        da['ne_part'] = ne_part

        da['requested'] = zip(*[da[ds] for ds in self.data_sets])

        return da

    def readInputs(self):
        for da in self:
            da_fn = da['fn']
            da_id = da['id']
            da_semantics = da['semantics']

            da_txts = []
            for data_set in self.data_sets:
                da_txts.append(da[data_set])
            
            lengths = [len(i) for i in da_txts]

            if all_same(lengths, 0):
                print >> sys.stderr, 'Empty dialogue act: id=%r' % (da_id, )
                continue

            if not all_same(lengths):
                print >> sys.stderr, 'Invalid dialogue act: id=%r (parametrized acts have different lengths)' % (da_id, )
                continue

            yield da_fn, da_id, da_semantics, da_txts

    def removeUnderscores(self, line, remove=False):
        if not remove:
            return [w.replace('_', 'x') for w in line]
        else:
            return [w.replace('_', 'x') for w in line if w != '_']



class JoinActs(object):
    def __init__(self, parent):
        self.parent = parent

    def __iter__(self):
        for da in self.parent:
            speech_act = da.get('da_speech_act', '').upper()
            semantics = da.get('semantics', '')
            da['semantics'] = '%s(%s)' % (speech_act, semantics)
            yield da

class Filler(object):
    def __init__(self, parent):
        self.parent = parent

    def __iter__(self):
        for da in self.parent:
            semantics = da.get('da_semantics', '')
            da['semantics'] = '_FILLER_(%s)' % (semantics, )
            yield da

class MakeOtherInfo(object):
    def __init__(self, parent):
        self.parent = parent

    def __iter__(self):
        for da in self.parent:
            semantics = da.get('da_semantics', '')
            if not semantics:
                da['semantics'] = 'OTHER_INFO'
            yield da

class MakeSpeechAct(object):
    def __init__(self, parent):
        self.parent = parent

    def __iter__(self):
        for da in self.parent:
            semantics = da.get('semantics', '')
            if not semantics:
                da['semantics'] = da.get('da_speech_act', 'OTHER_INFO').upper()
            yield da


class SelectSpeechActs(object):
    def __init__(self, parent):
        self.parent = parent

    def __iter__(self):
        for da in self.parent:
            speech_act = da.get('da_speech_act', '')
            if speech_act not in ['thanking', 'closing', 'opening', 'acknowledgement', 'request_info', 'present_info']:
                if 'conf' in speech_act:
                    speech_act = 'present_info'
                else:
                    speech_act = 'other'
            da['da_speech_act'] = speech_act
            yield da

class OnlyActs(object):
    def __init__(self, only, parent):
        self.parent = parent
        self.only = only

    def __iter__(self):
        for da in self.parent:
            speech_act = da.get('da_speech_act', '')
            if speech_act == self.only:
                yield da

def InputChain(type, reader):
    if type == 'none':
        return reader
    elif type == 'join_acts':
        return JoinActs(reader)
    elif type == 'join_acts_selected':
        reader = SelectSpeechActs(reader)
        return JoinActs(reader)
    elif type == 'filler':
        return Filler(reader)
    elif type == 'make_other_info':
        return MakeOtherInfo(reader)
    elif type == 'make_speech_act':
        return MakeSpeechAct(reader)
    elif type.startswith('only_'):
        only = type[len('only_'):]
        reader = SelectSpeechActs(reader)
        reader = OnlyActs(only, reader)
        return reader
    else:
        raise ValueError("Unknown input chain type: %r" % type)
