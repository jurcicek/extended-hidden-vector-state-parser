import sys
import os

from svc.scripting import *
from xml import sax
from xml.sax.handler import ContentHandler
from xml.sax.saxutils import XMLFilterBase, XMLGenerator

DUMMY_CONCEPT = '_DUMMY_'

def path_basename_noext(path):
    path = os.path.basename(path)
    return os.path.splitext(path)[0]


class SemanticsFilter(PythonEgg, ContentHandler):
    def __init__(self):
        self._content_serial = []
        self._content = {}
        self._content_turns = {}
        self._turn = []
        self._turn_no = None
        self._speaker = None

    def startElement(self, name, attrs):
        if name == 'utterance':
            self._speaker = attrs.get('speaker')
        elif name == 'dialogue_act':
            speaker = self._speaker
            semantics = attrs.get('semantics').strip()
            if semantics:
                if speaker not in self._content:
                    self._content[speaker] = []
                self._content[speaker].append(semantics)
                self._content_serial.append((speaker, semantics))
                self._turn.append(semantics)
        elif name == 'turn':
            self._turn_no = int(attrs.get('number', '0'))
            self._turn = []
    
    def endElement(self, name):
        if name == 'turn':
            turn_no = self._turn_no
            speaker = self._speaker
            if self._turn:
                semantics = ', '.join(self._turn)
            else:
                semantics = DUMMY_CONCEPT
            if turn_no not in self._content_turns:
                self._content_turns[turn_no] = {}
            self._content_turns[turn_no] = (speaker, semantics)
    
    def getSemanticContent(self):
        return self._content

    def getSemanticContentSerial(self):
        return self._content_serial

    def getSemanticContentTurns(self):
        return self._content_turns


class DXML2MLF(ExScript):
    options = {
        'command': ExScript.CommandParam,
        'dlg_spkrs.files': (Required, Multiple, String),
        'turns.files': OptionAlias,
    }

    posOpts = ['command', 'files', Ellipsis]

    debugMain = False

    @ExScript.command
    def dlg_spkrs(self, files):
        fw = sys.stdout

        fw.write("#!MLF!#\n")
        for fn in files:
            handler = SemanticsFilter()
            sax.parse(fn, handler)
            for speaker, semantics in handler.semanticContent.iteritems():
                fn_base = path_basename_noext(fn)
                fw.write('"%s~%s"\n' % (fn_base, speaker))
                fw.write(', '.join(semantics) + '\n')
                fw.write('.\n')

    @ExScript.command
    def turns(self, files):
        fw = sys.stdout

        fw.write("#!MLF!#\n")
        for fn in files:
            handler = SemanticsFilter()
            sax.parse(fn, handler)
            for turn_no, (speaker, semantics) in handler.semanticContentTurns.iteritems():
                fn_base = path_basename_noext(fn)
                fw.write('"%s-%05d-%s"\n' % (fn_base, turn_no, speaker))
                fw.write(semantics + '\n')
                fw.write('.\n')

def main():
    script = DXML2MLF()
    script.run()

if __name__ == '__main__':
    main()
