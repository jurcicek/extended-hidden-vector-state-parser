#!/usr/bin/env python2.4

import os
from svc.scripting.externals import *
from svc.osutils import mkdirp
from svc.ui import pdt
from svc.ui.dxml import DXML
from svc.ui.mlf import MLF
from glob import glob
import xml.dom.minidom 
import codecs
import re
import tempfile

LOWER_DATASETS = ['lemmatized']

class PDTTools(ExternalScript):
    externalMethodDirs = ['bin/pdttools']

    externalMethods = {
        'runPDT': ExScript.command,
        'runPDTtagger': ExScript.command,
        'moveResults': ExScript.command,
        'deleteResults': ExScript.command,
    }

    options = {
        'command': ExScript.CommandParam, 
        '__premain__.cfgfile': (Multiple, String),
        '__premain__.variable': (Multiple, String),
        'all.type_prefix': String,
        'all.full_pdt': Flag,
        'all.deleteResults': Flag,
        'mktxt.type': String,
        'mktxt.lower': Flag,
        'mktxt.new_sen_file': String,
        'mlfparametrize.mlf': (Required, String),
        'mlfparametrize.source_type': String,
        'mlfparametrize.target_type': String,
        'mlfparametrize.inDir': OptionAlias,
        'mlfparametrize.outDir': OptionAlias,
        'mlfparametrize.use_empty': Flag,
        'splitCSTS.csts': String,
        'parametrize.new_type': (Required, String),
        'parametrize.sen_file': (Required, String),
        'inDir': String,
        'outDir': String,
    }

    settingsFiles = ['settings.path']

    posOpts = ['command', {'parametrize': ['new_type', 'sen_file'],
                           'mktxt': ['type'],
                           'mlfparametrize': ['mlf', 'inDir', 'outDir'],
                          }
              ]

    shortOpts = {
            's': 'variable'
    }

    def getInputXMLs(self):
        return sorted(glob(os.path.join(self.inDir, '*.xml')))

    def getWorkDir(self):
        return self.settings['PDT_WORK_DIR']

    @ExScript.command
    def makeDirs(self):
        self.logger.info("Making build directories")
        mkdirp(self.workDir)
        mkdirp(self.outDir)

    @ExScript.command
    def mktxt(self, type='normalized', lower=False, new_sen_file=None):
        self.logger.info("Making build directories")
        self.makeDirs()
        self.logger.info("Getting text from XMLs")
        if new_sen_file is None:
            fn = os.path.join(self.settings['PDT_WORK_DIR'], 'sen_file')
        else:
            fn = new_sen_file
        fw = codecs.open(fn, 'w', pdt.PDT_ENCODING)
        try:
            for fn in self.getInputXMLs():
                dxml = DXML.readFromFile(fn)
                acts = dxml.getDialogueActs(type)
                for utter in acts:
                    for txt, attrs in utter:
                        if not txt:
                            self.logger.info("Empty <dialogue_act> in file: %s", fn)
                        if lower:
                            txt = txt.lower() + '\n'
                        else:
                            txt = txt.upper() + '\n'
                        fw.write(txt)
        finally:
            fw.close()

    @ExScript.command
    def mlfparametrize(self, mlf, inDir=None, outDir=None,
            source_type='normalized', target_type='decoded', use_empty=False):
        self.setupDirs(inDir, outDir)
        foo, new_sen_file = tempfile.mkstemp()
        self.logger.info("Reading MLF")
        mlf = MLF.readFromFile(mlf)
        self.logger.info("Making build directories")
        self.makeDirs()
        self.logger.info("Getting text from XMLs")
        if new_sen_file is None:
            fn = os.path.join(self.settings['PDT_WORK_DIR'], 'sen_file')
        else:
            fn = new_sen_file
        fw = codecs.open(fn, 'w', 'utf-8')
        try:
            for fn in self.getInputXMLs():
                dxml = DXML.readFromFile(fn)
                acts = dxml.getDialogueActs(source_type)
                idx = 0
                for utter in acts:
                    for txt, attrs in utter:
                        if not txt:
                            self.logger.info("Empty <dialogue_act> in file: %s", fn)
                        key = "*/%s_%05d" % (os.path.splitext(os.path.basename(fn))[0], idx)
                        if key in mlf:
                            line = mlf[key]
                        elif not use_empty:
                            line = [txt + '\n']
                        else:
                            line = ['\n']
                        line = '\n'.join(line)
                        fw.write(line)
                        idx += 1
        finally:
            fw.close()

        self.parametrize(target_type, new_sen_file)
        os.remove(new_sen_file)


    @ExScript.command
    def splitCSTS(self, csts=None):
        self.logger.info("Splitting output CSTS")
        PDT_WORK_DIR = self.settings['PDT_WORK_DIR']
        if csts is None:
            csts = os.path.join(PDT_WORK_DIR, 'sen_file.csts')

        parser = pdt.PDT20Parser()
        parser.split(csts)

    def _readDAFromSenFile(self, fr):
        line = fr.readline()
        line = line.strip()
        line = line.rstrip('.')
        return line

    @ExScript.command
    def parametrize(self, new_type, sen_file):
        self._multiParametrize([(new_type, sen_file)])

    def _multiParametrize(self, args):
        self.logger.info("Parametrizing XMLs")
        types = [a[0] for a in args]
        fns = [a[1] for a in args]
        frs = [codecs.open(fn, 'r', 'utf-8') for fn in fns]
        try:
            for fn in self.getInputXMLs():
                dxml = DXML.readFromFile(fn)
                txts = dxml.getTexts()
                acts = dxml.getDialogueActs()
                for fr, new_type in zip(frs, types):
                    new_acts = []
                    new_txts = []
                    for utter, (foo1, attrs_txt) in zip(acts, txts):
                        new_utter_acts = []
                        new_text = []
                        for da_text, attrs_act in utter:
                            if not da_text:
                                # Skip empty <dialogue_act>
                                if new_type == types[0]:
                                    # Warn only once
                                    self.logger.info("Empty <dialogue_act> in file: %s", fn)
                            new_txt = self._readDAFromSenFile(fr)
                            if new_type in LOWER_DATASETS:
                                new_txt = new_txt.lower()
                            new_text.append(new_txt)
                            new_utter_acts.append((new_txt, attrs_act))
                        new_text = ' '.join(new_text)
                        new_txts.append((new_text, attrs_txt))
                        new_acts.append(new_utter_acts)

                    dxml.setTexts(new_type, new_txts)
                    dxml.setDialogueActs(new_type, new_acts)

                fn_base = os.path.basename(fn)
                dxml.writeToFile(os.path.join(self.outDir, fn_base))
                dxml.unlink()
        finally:
            for fr in frs:
                fr.close()

    @ExScript.command
    def all(self, moveResults=True, deleteResults=False, type_prefix='', full_pdt=False, env={}):
        self.invokeCommand('makeDirs')
        self.invokeCommand('mktxt')
        if full_pdt:
            self.runPDT(env=env)
        else:
            self.runPDTtagger(env=env)
        self.invokeCommand('splitCSTS')
        if full_pdt:
            self._multiParametrize([(type_prefix+'lemmatized', os.path.join(self.workDir, 'sen_file.lemma')),
                                    (type_prefix+'pos_tagged', os.path.join(self.workDir, 'sen_file.pos')),
                                    (type_prefix+'analytical', os.path.join(self.workDir, 'sen_file.anl'))])
        else:
            self._multiParametrize([(type_prefix+'lemmatized', os.path.join(self.workDir, 'sen_file.lemma')),
                                    (type_prefix+'pos_tagged', os.path.join(self.workDir, 'sen_file.pos'))])
        if deleteResults:
            self.deleteResults(int(self.debugMain), env=env)
        elif moveResults:
            self.moveResults(int(self.debugMain), env=env)

    def setupDirs(self, inDir, outDir):
        if inDir is not None:
            self.inDir = inDir
        else:
            self.inDir = self.settings['ANNOTATED_DIR']
        if outDir is not None:
            self.outDir = outDir
        else:
            self.outDir = os.path.join(self.settings['PDT_WORK_DIR'], 'parametrized')

    def main(self, inDir=None, outDir=None, **kwargs):
        self.setupDirs(inDir, outDir)
        return super(PDTTools, self).main(**kwargs)

    def premain(self, cfgfile=[], variable=[], *args, **kwargs):
        ret = super(PDTTools, self).premain(*args, **kwargs)
        for fn in cfgfile:
            self.sourceEnv(fn)
        for v in variable:
            try:
                name, value = v.split('=', 1)
            except ValueError:
                raise ValueError("Bad varible (%s), must have the form: VARNAME=value" % v)
            self.settings[name] = value
        return ret

    @ExScript.command
    def moveResults(self, keep=False, env={}):
        super(PDTTools, self).moveResults(int(keep), env=env)

def __main__():
    s = PDTTools()
    s.run()

if __name__ == '__main__':
    __main__()

