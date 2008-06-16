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

import sys
import os

from svc.scripting import *

from glob import glob
from xml import sax
from xml.sax.handler import ContentHandler
from xml.sax.saxutils import XMLFilterBase, XMLGenerator

class UtteranceFilter(PythonEgg, ContentHandler):
    def __init__(self, textType='normalized'):
        self._textType = textType
        self._utterances = []
        self._catchText = False

    def startElement(self, name, attrs):
        if name == 'utterance':
            self.__utter = [None, None, []]
            startTime = float(attrs.get('start_time'))
            endTime = float(attrs.get('end_time'))
            self.__utter[0] = startTime
            self.__utter[1] = endTime
        elif name == 'text' and attrs.get('type') == self._textType:
            self._catchText = True
    
    def endElement(self, name):
        if name == 'utterance':
            self._utterances.append(tuple(self.__utter))
            del self.__utter
        elif name == 'text':
            self._catchText = False

    def characters(self, chars):
        if self._catchText:
            words = chars.split()
            if words:
                self.__utter[2].extend(words)
    
    def getUtterances(self):
        return self._utterances

class DXML2HTK(ExScript):
    options  = {
        'command': ExScript.CommandParam,
        'mkseg.files': (Multiple, String),
        'mkseg.pfiles': (Multiple, String),
        'mkseg.pmeth': String,
        'mkseg.mlf': (Required, String),
        'mkseg.script': (Required, String),
        'mkseg.winsize': Float,
    }

    optionsDoc = {
        'winsize': "Size of window in ms, defaults to 10ms",
    }

    posOpts = ['command', 'files', Ellipsis]

    def setParametrizations(self, pfiles):
        self._pfilesCache = {}
        to_process = set()
        for fn in pfiles:
            if os.path.isdir(fn):
                to_process |= set(glob('%s/*' % fn))
            else:
                to_process.add(fn)

        for fn in to_process:
            fn_base_ext = os.path.basename(fn)
            fn_base, fn_ext = os.path.splitext(fn_base_ext)
            self._pfilesCache[fn_base] = fn

    def resolveParametrization(self, fn_base, method='none'):
        if method == 'none':
            pass
        elif method == 'nadrazi':
            fn_base = fn_base.split('~')[-1]
        else:
            raise ValueError("Unknown resolving method: %r" % method)
        return self._pfilesCache[fn_base]

    @ExScript.command
    def mkseg(self, mlf, script, files=[], pfiles=[], winsize=10., pmeth='none'):
        self.setParametrizations(pfiles)

        fw_mlf = file(mlf, 'w')
        fw_script = file(script, 'w')
        try:
            fw_mlf.write('#!MLF!#\n')

            for fn in files:
                self.logger.info("Processing file %r", fn)
                fn_base_ext = os.path.basename(fn)
                fn_base = os.path.splitext(fn_base_ext)[0]
                try:
                    fn_rec = self.resolveParametrization(fn_base, pmeth)
                    fn_rec_ext = os.path.splitext(fn_rec)[1]
                except KeyError:
                    self.logger.warn("No parametrization for %r, skipping", fn)
                    continue

                handler = UtteranceFilter()
                sax.parse(fn, handler)
                for i, (t1, t2, words) in enumerate(handler.utterances):
                    t1 = t1 * 1000 / winsize
                    t2 = t2 * 1000 / winsize

                    fn_rec_i = '%s_%05d%s' % (fn_base, i, fn_rec_ext)
                    fw_script.write('%s=%s[%d,%d]\n' % (fn_rec_i, fn_rec, t1, t2))

                    fn_lab_i = '%s_%05d.lab' % (fn_base, i)
                    fw_mlf.write('"*/%s"\n' % fn_lab_i)
                    for w in words:
                        fw_mlf.write((w + '\n').encode('iso-8859-2'))
                    fw_mlf.write('.\n')

                    self.logger.debug("Processing subfile %r", fn_lab_i)
        finally:
            fw_mlf.close()
            fw_script.close()

def main():
    script = DXML2HTK()
    script.run()

if __name__ == '__main__':
    main()

