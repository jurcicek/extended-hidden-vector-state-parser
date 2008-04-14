#!/usr/bin/env python2.4

import os
import xml.dom.minidom

from svc.scripting.externals import *
from svc.ui.mlf import MLF, ConceptMLF, ROOT_CONCEPT

ENTITY_CONCEPTS = ['AMOUNT', 'AREA', 'DELAY', 'DURATION', 'LENGTH', 'NUMBER', 'PERSON', 'PLATFORM', 'STATION', 'THROUGH', 'TIME', 'TRAIN_TYPE']

SKIP_CONCEPTS = [ROOT_CONCEPT, 'GREETING', 'ARRIVAL', 'DEPARTURE', 'ACCEPT', 'THROUGH', 'REJECT', 'ACCEPT', 'REF', 'BACK', 'DISTANCE', 'PRICE', 'TRANSFER', 'WAIT']

SKIP_TITLES = ['to', 'from']

class TreeProcessor(PythonEgg):
    def strAV(self, av):
        av_str = []
        for a, v in av:
            if v is None:
                av_str.append('%s' % (a,))
            else:
                av_str.append('%s=%s' % (a, v))
        return ', '.join(av_str)

class NadraziProcessor(TreeProcessor):
    def __init__(self, dataDirs):
        super(NadraziProcessor, self).__init__()
        self._dataDirs = dataDirs
        self._cache = {}

    def getDataDirs(self):
        return self._dataDirs

    def locateFile(self, fn):
        for dn in self.dataDirs:
            full_fn = os.path.join(dn, fn)
            if os.path.exists(full_fn):
                return full_fn
        else:
            return None

    def loadFile(self, full, turnId):
        dom = xml.dom.minidom.parse(full)
        turn_info = []
        for node in dom.getElementsByTagName('dialogue_act'):
            da = {}
            da['speech_act'] = node.attributes['speech_act'].nodeValue
            da['conversational_domain'] = node.attributes['conversational_domain'].nodeValue
            da['speaker'] = node.parentNode.attributes['speaker'].nodeValue
            da['turn_id'] = turnId
            turn_info.append(da)
        return turn_info

    def getTurnInfo(self, turnId):
        base = os.path.split(turnId)[1]
        base, turnNo = base.rsplit('_', 1)
        turnNo = int(turnNo)
        base = base.replace('_', '-') + '.xml'
        full = self.locateFile(base)
        if full is None:
            raise ValueError("File not found: %s" % base)

        if full not in self._cache:
            self._cache[full] = self.loadFile(full, turnId)

        return self._cache[full][turnNo]

    def entityAV(self, tree):
        attr_title = tree.label.lower()
        av = []
        for label, subtree, orig_stack in tree.preOrderStack():
            stack = orig_stack[:]
            if label in ENTITY_CONCEPTS:
                while stack and stack[0].label in SKIP_CONCEPTS:
                    del stack[0]
                if not stack:
                    continue
                attribute = '_'.join(s.label.lower() for s in stack)
                if attribute == attr_title:
                    attr_title = None
                value = '"' + ' '.join(s.label for s in subtree) + '"'
                av.append((attribute, value))

        if attr_title is not None and attr_title not in SKIP_TITLES:
            av.insert(0, (attr_title, None))
        return av

    def removeDUMMY(self, tree, dummy='_DUMMY_'):
        i = 0
        while i < len(tree):
            it = tree[i]
            if it.label == dummy:
                tree[i:i+1] = it[:]
                continue
            self.removeDUMMY(it, dummy)
            i += 1

    def process(self, fn, tree):
        info = self.getTurnInfo(fn)

        speech_act = info['speech_act']
        speaker = info['speaker']
        domain = info['conversational_domain']

        self.removeDUMMY(tree)
        av = []
        for child in tree:
            if len(child) == 0:
                # skip leafs
                continue
            av.extend(self.entityAV(child))
        av.extend([('speaker', speaker)])

        return '%s.%s(%s)' % (domain, speech_act, self.strAV(av))


class Intentions(ExternalScript):
    settingsFiles = ['settings.path', 'settings']

    options = {
        'command': ExScript.CommandParam,
        'rootConcepts.mlf': (Required, String),
        '__premain__.cfgfile': (Multiple, String),
    }

    posOpts = ['command', {'rootConcepts': ['mlf']}]

    def __extractIntentionsFile(self, fn, data_dir, out_fn):
        self.logger.info('Making intention level from: %s', fn)
        if not os.path.exists(fn):
            self.logger.warn('File does not exists, skipping: %s', fn)
            return
        mlf = ConceptMLF.readFromFile(fn)
        fw = MLF()
        processor = NadraziProcessor([data_dir])
        for mlf_fn, tree in mlf.iteritems():
            fw[mlf_fn] = ['%s\n' % processor.process(mlf_fn, tree)]

        dirname = os.path.split(fn)[0]
        fw.writeToFile(os.path.join(dirname, out_fn))

    def _extractIntentionsDir(self, dir):
        fn_word = os.path.join(dir, 'semantics.mlf.smntcs')
        self.__extractIntentionsFile(fn_word, self.settings['DATA_DIR'], 'intentions.mlf')
        fn_lemma = os.path.join(dir, 'semantics.lemma.mlf.smntcs')
        self.__extractIntentionsFile(fn_lemma, self.settings['DATA_DIR'], 'intentions.lemma.mlf')

    @ExScript.command
    def rootConcepts(self, mlf):
        mlf = ConceptMLF.readFromFile(mlf)
        s = set()
        for fn, tree in mlf.iteritems():
            for t in tree:
                s.add(t.label)
        for label in sorted(s):
            print label

    @ExScript.command
    def extractIntentions(self):
        self._extractIntentionsDir(self.settings['FA_TRN'])
        self._extractIntentionsDir(self.settings['DCD_HLDT'])
        self._extractIntentionsDir(self.settings['DCD_TST'])

    @ExScript.command
    def all(self):
        self.extractIntentions()

    def premain(self, cfgfile=[], *args, **kwargs):
        ret = super(Intentions, self).premain(*args, **kwargs)
        for fn in cfgfile:
            self.sourceEnv(fn)
        return ret


def __main__():
    s = Intentions()
    s.run()

if __name__ == '__main__':
    __main__()
