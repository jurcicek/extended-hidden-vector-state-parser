#!/usr/bin/env python2.4

import os
import sys
from svc.scripting.externals import *
from svc.osutils import mkdirp
from svc.ui import pdt
from svc.ui.dxml import DXML
from glob import glob
import xml.dom.minidom 
import codecs
import re
import shutil

sys.path.insert(0, 'src')
import genInputs
import input

class HVSParser(ExternalScript):
    externalMethodDirs = ['bin/hvsparser', 'bin/semantics']

    externalMethods = {
        'decode': OmitStdout,
        'setCommonParams': OmitStdout,
    }

    options = {
        'command': ExScript.CommandParam, 
        '__premain__.variable': (Multiple, String),
        '__premain__.cfgfile': (Multiple, String),
        'files': (Multiple, Required, String),
        'outDir': (Required, String),
    }

    settingsFiles = ['settings', 'settings.path']

    posOpts = ['files', Ellipsis, 'outDir']

    shortOpts = {
            's': 'variable'
    }

    def premain(self, cfgfile=[], variable=[], *args, **kwargs):
        ret = super(HVSParser, self).premain(*args, **kwargs)
        for fn in cfgfile:
            self.sourceEnv(fn)
        for v in variable:
            try:
                name, value = v.split('=', 1)
            except ValueError:
                raise ValueError("Bad varible (%s), must have the form: VARNAME=value" % v)
            self.settings[name] = value
        return ret

    def main(self, files, outDir):
        data_sets = []
        for name in ['S1', 'S2', 'S3']:
            data_sets.append('%s:%s' % (self.settings[name+'_DATASET'], self.settings[name+'_MAP']))

        tmpDir = os.path.normpath(outDir)+'.tmp'
        mkdirp(tmpDir)
        mkdirp(outDir)

        unsList = '%s/obs.list:%s/%%(id)s.obs' % (tmpDir, tmpDir)
        unsList2 = '%s/obs.2.list:%s/%%(id)s.2.obs' % (tmpDir, tmpDir)
        outList = '%s/out.list:%s/%%(id)s.dcd' % (tmpDir, tmpDir)

        parseType = self.settings['PARSE_TYPE']
        origDataSets = self.settings['ORIG_DATASETS']

        pdtDir = self.settings['PDT20_TOOLS']

        generator = genInputs.InputGenerator()
        generator.main(files, tmpDir, unsList = [unsList, outList],
                dataSet=data_sets[:1], parseType=parseType,
                origDataSets=origDataSets, txtInput=True, pdtDir=pdtDir)
        generator.main(files, tmpDir, unsList = [unsList2],
                dataSet=data_sets[1:], parseType=parseType,
                origDataSets=origDataSets, txtInput=True, pdtDir=pdtDir,
                extraExt='.2')
        
        self.setCommonParams()
        self.decode(tmpDir, outDir)
        if not self.debugMain:
            shutil.rmtree(tmpDir, True)

def __main__():
    s = HVSParser()
    s.run()

if __name__ == '__main__':
    __main__()
