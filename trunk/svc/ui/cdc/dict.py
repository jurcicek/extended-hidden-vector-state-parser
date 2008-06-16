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
import locale
from glob import glob

from xml import sax
from xml.sax.handler import ContentHandler

from svc.scripting import *

class WordsSAX(PythonEgg, ContentHandler):
    def __init__(self, text_type):
        self._text_type = text_type
        self._catch_text = False
        self._words = set()

    def startElement(self, name, attrs):
        if name == 'text' and attrs.get('type') == self._text_type:
            self._catch_text = True
    
    def endElement(self, name):
        if name == 'text' and self._catch_text:
            self._catch_text = False

    def characters(self, chars):
        if self._catch_text:
            self._words |= set(chars.lower().split())

    def getWords(self):
        return self._words

class DictManager(ExScript):
    options = {
        'command': ExScript.CommandParam,
        'xmldict.options': (Required, Multiple, String),
        'xmldict.texttype': String,
        'xmldict.outenc': String,
        'txtdict.options': OptionAlias,
        'txtdict.inenc': OptionAlias,
        'txtdict.outenc': OptionAlias,
        'dprocess.options': OptionAlias,
        'dprocess.inenc': String,
        'dprocess.outenc': OptionAlias,
        'tprocess.options': OptionAlias,
        'tprocess.inenc': OptionAlias,
        'tprocess.outenc': OptionAlias,
    }

    posOpts = ['command', 'options', Ellipsis]

    def alphSort(self, list):
        return sorted(list, cmp=locale.strcoll)

    def printDict(self, dict, fw=sys.stdout, outenc='utf-8'):
        fw.write('\n'.join(self.alphSort(dict)).encode(outenc))

    def printTransDict(self, dict, fw=sys.stdout, outenc='utf-8'):
        lst = []
        keys = self.alphSort(dict.keys())
        for key in keys:
            if dict[key] is not None:
                lst.append(u'%s\t\t%s' % (key, dict[key]))
            else:
                lst.append(u'%s\t' % (key, ))
        fw.write('\n'.join(lst).encode(outenc))

    def loadDict(self, fn, norm_col, enc='utf-8'):
        ret = set()
        f = file(fn)
        try:
            for orig_line in f:
                orig_line = orig_line.decode(enc)
                line = orig_line.lower()
                line = line.split()
                try:
                    norm_word = line[norm_col]
                except IndexError:
                    self.logger.error("Error: bad column in line: %s", orig_line)
                    continue
                ret.add(norm_word)
            return ret
        finally:
            f.close()

    def loadTransDict(self, fn, orig_col, norm_col, enc='utf-8'):
        ret = {}
        f = file(fn)
        try:
            for orig_line in f:
                orig_line = orig_line.decode(enc)
                line = orig_line.lower()
                line = line.split()
                try:
                    orig_word = line[orig_col]
                    norm_word = line[norm_col]
                except IndexError:
                    self.logger.error("Error: bad column in line: %s", orig_line)
                    continue
                if orig_word in ret:
                    #self.logger.warn("Word '%s' can have multiple normalized forms", orig_word)
                    pass
                ret[orig_word] = norm_word
            return ret
        finally:
            f.close()

    @ExScript.command
    def xmldict(self, options, texttype='normalized', outenc='utf-8'):
        files = set(options)

        handler = WordsSAX(texttype)

        while files:
            fn = files.pop()
            if os.path.isdir(fn):
                self.logger.info('Expanding dir: %s', fn)
                files |= set(glob('%s/*.xml' % fn))
            else:
                self.logger.info('Processing: %s', fn)
                try:
                    sax.parse(fn, handler)
                except sax.SAXParseException, e:
                    self.logger.error('XML error: %s', e)

        self.printDict(handler.words, sys.stdout, outenc)

    @ExScript.command
    def txtdict(self, options, inenc='utf-8', outenc='utf-8'):
        words = set()
        files = set(options)

        while files:
            fn = files.pop()
            if os.path.isdir(fn):
                self.logger.info('Expanding dir: %s', fn)
                files |= set(glob('%s/*.xml' % fn))
            else:
                self.logger.info('Processing: %s', fn)
                f = file(fn)
                try:
                    for line in f:
                        line = line.decode(inenc)
                        words |= set(line.lower().split())
                finally:
                    f.close()

        self.printDict(words, sys.stdout, outenc)

    @ExScript.command
    def dprocess(self, options, inenc='utf-8', outenc='utf-8'):
        dict = set()
        op = dict.update
        for item in options:
            if item == 'OR':
                self.logger.info('Operation: OR')
                op = dict.update
            elif item == 'AND':
                self.logger.info('Operation: AND')
                op = dict.intersection_update
            elif item == 'XOR':
                self.logger.info('Operation: XOR')
                op = dict.symmetric_difference_update
            elif item == 'SUB':
                self.logger.info('Operation: SUB')
                op = dict.difference_update
            else:
                item = item.split(':')
                fn = item[0]
                self.logger.info('File: %s' % fn)
                if len(item) == 1:
                    norm_col = 0
                elif len(item) == 2:
                    norm_col = int(item[1])
                else:
                    raise ValueError("You must use at last 1 colon")
                fn_dict = self.loadDict(fn, norm_col, inenc)
                op(fn_dict)
                op = dict.update

        self.printDict(dict, sys.stdout, outenc)

    @ExScript.command
    def tprocess(self, options, inenc='utf-8', outenc='utf-8'):
        fdict = set()
        tdict = {}
        for item in options:
            item = item.split(':')
            fn = item[0]
            self.logger.info('File: %s' % fn)

            if len(item) == 1:
                norm_col = 0
                load_fdict = True
            elif len(item) == 2:
                norm_col = int(item[1])
                load_fdict = True
            elif len(item) == 3:
                norm_col = int(item[1])
                orig_col = int(item[2])
                load_fdict = False
            else:
                raise ValueError("You must use at last 2 colon")

            if load_fdict:
                self.logger.info("Loading dictionary: %s", fn)
                fn_fdict = self.loadDict(fn, norm_col, inenc)
                fdict.update(fn_fdict)
            else:
                self.logger.info("Loading translation dictionary: %s", fn)
                fn_tdict = self.loadTransDict(fn, orig_col, norm_col, inenc)
                tdict.update(fn_tdict)

        fdict = dict((key, None) for key in fdict)
        for key, value in tdict.iteritems():
            if key in fdict:
                fdict[key] = value

        self.printTransDict(fdict, sys.stdout, outenc)

def main():
    locale.setlocale(locale.LC_ALL, '')
    script = DictManager()
    script.run()

if __name__ == '__main__':
    main()
