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

from svc.scripting import *
from svc.utils import issequence
from svc.ui.pdt import FMAnalyzer, EXPTagger, PDTParser, PDT_ENCODING
from xml import sax
from xml.sax.handler import ContentHandler
from xml.sax.saxutils import XMLFilterBase, XMLGenerator

FMORPH_DIR = '/opt/FMorph'
EXPTAGGER_DIR = '/opt/EXPtagger'

def path_translate(fn, dir):
	"""Translate filename `fn` in `dir`

	If `dir` is None, do nothing.
	"""
	if dir is not None:
		tail = os.path.split(fn)[1]
		fn = os.path.join(dir, tail)
	return fn

def path_mkoutpath(fn, dir):
    if not os.path.isabs(fn):
        return os.path.join(dir, fn)
    else:
        return fn

def shutil_mkpath(fn):
    pass



class SentenceFilter(PythonEgg, ContentHandler):
    def __init__(self, text_type):
        self._text_type = text_type
        self._sentences = []
        self._catch_text = False

    def startElement(self, name, attrs):
        if name == 'text' and attrs.get('type') == self._text_type:
            self._catch_text = True
            self._catched = False
    
    def endElement(self, name):
        if name == 'text' and self._catch_text:
            self._catch_text = False
            if not self._catched:
                self._sentences.append("None")

    def characters(self, chars):
        if self._catch_text:
            chars = chars.strip()
            if chars:
                self._sentences.append(chars)
                self._catched = True

    def getSentences(self):
        return self._sentences

class TaggingFilter(XMLFilterBase):
    TAG_INDENT = 6
    CHAR_INDENT = 9

    def __init__(self, new_type, tags, insert_after):
        self._after = insert_after
        self._new_type = new_type
        self._tags = tags
        self._write_tag = False
        self._eat_tag = False

    def startElement(self, name, attrs):
        if name == 'text' and attrs.get('type') == self._new_type:
            self._eat_tag = True
        else:
            self._eat_tag = False
        if name == 'text' and attrs.get('type') == self._after:
            self._write_tag = True
        if not self._eat_tag:
            XMLFilterBase.startElement(self, name, attrs)

    def characters(self, chars):
        if not self._eat_tag:
            XMLFilterBase.characters(self, chars)
    
    def endElement(self, name):
        if not self._eat_tag:
            XMLFilterBase.endElement(self, name)
        if name == 'text' and self._write_tag:
            self._write_tag = False

            writer = self.getContentHandler()
            writer.characters('\n' + ' '*self.TAG_INDENT)
            writer.startElement('text', {'type': self._new_type})
            if self._tags:
                line = self._tags.pop(0)
                writer.characters('\n' + ' '*self.CHAR_INDENT)
                writer.characters(line)
                writer.characters('\n' + ' '*self.TAG_INDENT)
            writer.endElement('text')

class DAFiller(XMLFilterBase):
    TAG_INDENT = 6
    CHAR_INDENT = 9

    def __init__(self, text_type, error_callback=None):
        self._error_callback = error_callback
        self.text_type = text_type
        self._catch_full_line = False
        self._write_full_line = False
        self._full_line = []
        self._whole_line = []
        self._da_line_len = 0
        self._da_attrs = {}
        self._da_count = 0
        self._eat_tag = False
        self._turn_no = None
        self._dialogue = None

    def startElement(self, name, attrs):
        if name == 'task':
            self._dialogue = attrs.get('dialog')
        elif name == 'turn':
            self._turn_no = int(attrs.get('number'))
        elif name == 'utterance':
            self._full_line = []
            self._da_line_len = 0
            self._da_count = 0
        elif name == 'text' and attrs.get('type') == self.text_type:
            self._full_line = []
            self._whole_line = []
            self._catch_full_line = True
        elif name == 'dialogue_act':
            self._write_full_line = True
            self._da_count += 1
            self._da_attrs = attrs.copy()
        elif name == 'parametrized_act' and attrs.get('type') == self.text_type:
            self._eat_tag = True

        if not self._eat_tag:
            XMLFilterBase.startElement(self, name, attrs)

    def createWords(self, chars):
        # Split into words
        words = chars.split()
        # Remove words like [station] (named entities tags)
        words = [w for w in words if not w.startswith('[')]
        return words

    def characters(self, chars):
        words = self.createWords(chars)
        if self._catch_full_line:
            self._full_line.extend(words)
            self._whole_line.extend(words)
        if self._write_full_line:
            self._da_line_len += len(words)
        if not self._eat_tag:
            XMLFilterBase.characters(self, chars)
    
    def endElement(self, name):
        if not self._eat_tag:
            XMLFilterBase.endElement(self, name)

        if name == 'text' and self._catch_full_line:
            self._catch_full_line = False
        elif name == 'dialogue_act' and self._write_full_line:
            self._write_full_line = False
            if len(self._full_line) < self._da_line_len:
                self._whole_line.append("... (missing)")
                self.errorCallback()
            line = self._full_line[:self._da_line_len]
            del self._full_line[:self._da_line_len]
            self._da_line_len = 0
            line = u' '.join(line)

            writer = self.getContentHandler()
            writer.characters('\n' + ' '*self.TAG_INDENT)
            attrs = {'type': self.text_type}
            attrs.update(self._da_attrs)
            writer.startElement('parametrized_act', attrs)
            writer.characters('\n' + ' '*self.CHAR_INDENT)
            writer.characters(line)
            writer.characters('\n' + ' '*self.TAG_INDENT)
            writer.endElement('parametrized_act')
        elif name == 'utterance':
            if self._full_line and self._da_count != 0:
                self.errorCallback()
        elif name == 'parametrized_act':
            self._eat_tag = False

    def errorCallback(self):
        if self._error_callback is not None:
            dialogue = getattr(self, '_dialogue', None)
            turn_no = getattr(self, '_turn_no', None)
            line = ' '.join(self._whole_line)
            self._error_callback(dialogue, turn_no, line)



class LineStack(list):
    def __init__(self, separator=None):
        super(LineStack, self).__init__()
        self.separator = separator
        self._line = []

    def addWord(self, item):
        self._line.append(item)
        self.addSeparator()

    def addSeparator(self):
        if self.separator is not None:
            self._line.append(self.separator)

    def removeSeparator(self):
        if self.separator is not None:
            while self._line and \
                  self._line[-1] == self.separator:
                del self._line[-1]

    def lineEnd(self):
        self.removeSeparator()
        if self._line:
            self.append(''.join(self._line))
        del self._line[:]

class DXMLParametrizer(ExScript):
    debugMain = True

    options = {
        'command': ExScript.CommandParam,
        'files': (Multiple, Required, String),
        'outdir': (Required, String),
        'prepare.sen_file': String,
        'prepare.fm_file': String,
        'prepare.fm_dir': String,
        'prepare.fm_dict': String,
        'prepare.ul_trans': Flag,
        'prepare.exp_file': String,
        'prepare.exp_dir': String,
        'parametrize.exp_file': OptionAlias,
        'unkwords.exp_file': OptionAlias,
        'unkwords.ul_trans': OptionAlias,
        'extractText.sen_file': OptionAlias,
    }

    posOpts = ['command', 'outdir', 'files', Ellipsis]

    optionsDoc = {
        'files': 'Input DXML files',
        'outdir': 'Directory, where generated files will be stored',
        'sen_file': 'Temporary file with sentences from DXML',
        'fm_dir': 'Directory with FMorph (Default: %r)' % FMORPH_DIR,
        'fm_dict': 'Lexicon used by FMorph, defaults to standard PDT 1.0 lexicon',
        'fm_file': 'Output file of FMorph',
        'ul_trans': 'Convert all words to uppercase before processing',
        'exp_dir': 'Directory with EXPTagger (Default: %r)' % EXPTAGGER_DIR,
        'exp_file': 'Output file of EXPTagger',
    }

    def main(self, files, outdir='.', **kwargs):
        self.files = files
        self.outdir = outdir
        try:
            os.mkdir(self.outdir)
        except OSError:
            self.logger.debug('Output dir exists: %r', self.outdir)
        self._cached_table = []

        super(DXMLParametrizer, self).main(**kwargs)

    def createFilterChain(self, filters):
        if not filters:
            raise ValueError('You must specify some filters')
        if not issequence(filters):
            filters = [filters]
        chain = []
        for f in filters:
            if chain:
                chain[-1].setContentHandler(f)
            chain.append(f)
        return chain[0], chain[-1]

    def loadTrueMorphology(self, exp_file):
        parser = PDTParser()
        self._cached_table = list(parser.parseFile(exp_file))

    def getTrueMorphology(self):
        if not self._cached_table:
            raise ValueError("Morphology not loaded, use loadTrueMorphology()")
        return self._cached_table

    def makeLemmaTable(self):
        table = LineStack(' ')

        for orig, (lemma, tag), other in self.getTrueMorphology():
            if orig == ';':
                table.lineEnd()
            elif lemma is not None:
                if tag[10] == 'N':
                    lemma = 'ne' + lemma
                table.addWord(lemma)
##########################################################################
#   This is the ability to parse symbols like * or _ in input PDT data   #
##########################################################################
#            else:
#                if orig is not None:
#                    table.addWord(orig)
#                else:
#                    table.removeSeparator()
        return table

    def makePOSTable(self):
        table = LineStack(' ')

        for orig, (lemma, tag), other in self.getTrueMorphology():
            if orig == ';':
                table.lineEnd()
            elif tag is not None:
                table.addWord(tag)
        return table

    def reducePOSTag(self, tag):
        ret = []
        # ret.append(tag[0]) # POS
        # ret.append(tag[1]) # SUBPOS
        # ret.append(tag[2]) # GENDER
        # ret.append(tag[3]) # NUMBER
        ret.append(tag[4]) # CASE
        # ret.append(tag[5]) # POSSGENDER
        # ret.append(tag[6]) # POSSNUMBER
        ret.append(tag[7]) # PERSON
        # ret.append(tag[8]) # TENSE
        # ret.append(tag[9]) # GRADE
        # ret.append(tag[10]) # NEGATION
        return ''.join(ret)

    def makeHackedTable(self):
        table = LineStack(' ')

        for orig, (lemma, tag), other in self.getTrueMorphology():
            if orig == ';':
                table.lineEnd()
            elif orig is not None and orig not in '*_':
                if tag is not None and tag[0] == 'C':
                    orig = 'cislovka'
                table.addWord(orig)
        return table

    def filter(self, filters):
        in_handler, out_handler = self.createFilterChain(filters)

        for fn in self.files:
            ofn = path_translate(fn, self.outdir)
            self.logger.info('Processing: %s ---> %s', fn, ofn)
            ofw = file(ofn, 'wb')
            try:
                writer = XMLGenerator(ofw, 'utf-8')
                out_handler.setContentHandler(writer)
                sax.parse(fn, in_handler)
            finally:
                ofw.close()

    def prepareTable(self, sen_file, encoding=None, line_end=';', ul_trans=False):
        """Create file (see sen_file) to be analyzed using FMAnalyze.pl .
        """
        if encoding is None:
            encoding = PDT_ENCODING

        filter = SentenceFilter('normalized')
        for fn in self.files:
            ofn = path_translate(fn, self.outdir)
            self.logger.info('Getting text from %s', fn)
            sax.parse(fn, filter)

        fw = file(sen_file, 'w')
        try:
            for sen in filter.sentences:
                if ul_trans:
                    sen = sen.upper()
                print >> fw, '%s%s' % (sen.encode(encoding), line_end)
        finally:
            fw.close()

    @ExScript.command
    def all(self):
        """Execute `prepare` and `parametrize` commands
        """
        self.invokeCommand('prepare')
        self.invokeCommand('parametrize')

    @ExScript.command
    def prepare(self, sen_file='sen_file',
            fm_dir=FMORPH_DIR, fm_file='fm_file', fm_dict=None,
            exp_dir=EXPTAGGER_DIR, exp_file='exp_file', ul_trans=False):
        """Run FMorph and EXPTagger to obtain exp_file used in `parametrize` command
        """
        sen_file = path_mkoutpath(sen_file, self.outdir)
        fm_file = path_mkoutpath(fm_file, self.outdir)
        exp_file = path_mkoutpath(exp_file, self.outdir)

        self.prepareTable(sen_file, ul_trans=ul_trans)

        analyzer = FMAnalyzer(fm_dir, fm_dict)
        analyzer.analyzeFileToFile(sen_file, fm_file)

        tagger = EXPTagger(exp_dir)
        tagger.analyzeFileToFile(fm_file, exp_file)

    @ExScript.command
    def extractText(self, sen_file):
        """Extract text from DXML files and store it into sen_file
        """
        sen_file = path_mkoutpath(sen_file, self.outdir)
        self.prepareTable(sen_file, line_end='', ul_trans=ul_trans)

    @ExScript.command
    def unkwords(self, fm_file='fm_file', ul_trans=False):
        """Extract and print unknown words (with X-------------- tag)
        """
        fm_file = path_mkoutpath(fm_file, self.outdir)

        self.loadTrueMorphology(fm_file)

        unk = set()
        for orig, unique, other in self.getTrueMorphology():
            if orig is not None:
                for lemma, tags in other:
                    for tag in tags:
                        if tag[0] == 'X':
                            if ul_trans:
                                orig = orig.lower()
                            unk.add(orig)
        unk = sorted(unk)
        fw = sys.stdout
        fw.write('\n'.join(unk).encode('utf-8'))

    @ExScript.command
    def parametrize(self, exp_file='exp_file'):
        """Create lemma, POS and RPOS (Reduced POS) parametrization
        """
        exp_file = path_mkoutpath(exp_file, self.outdir)

        self.loadTrueMorphology(exp_file)
        
        lemma_table = self.makeLemmaTable()
        pos_table = self.makePOSTable()
        filters = [TaggingFilter('lemmatized', lemma_table, 'normalized'),
                   TaggingFilter('pos_tagged', pos_table, 'lemmatized')]

        self.filter(filters)

    @ExScript.command
    def fill_da(self):
        """Fill words from parametrized <text> tags into <dialogue_act> tags
        """
        def errorCallback(dialogue, turn_no, line):
            self.logger.error("<dialogue_act> doesn't match it's <text>; "
                              "dialogue=%s, turn=%s", dialogue, turn_no)
            self.logger.info("Unmatched <text>: %s", line)
        filters = [DAFiller('pos_tagged'),
                   DAFiller('lemmatized', error_callback=errorCallback),
                  ]
        self.filter(filters)

def main():
    script = DXMLParametrizer()
    script.run()

if __name__ == '__main__':
    main()
