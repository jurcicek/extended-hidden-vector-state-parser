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

from svc.scripting import *
import sys
import subprocess
import re

class Preprocessor(PythonEgg):
    def __init__(self, cppOptions=None):
        super(Preprocessor, self).__init__()
        if cppOptions is None:
            cppOptions = []
        self.cppOptions = cppOptions

    def process(self, fr):
        p = subprocess.Popen(['cpp'] + self.cppOptions + ['-P'], stdin=fr, stdout=subprocess.PIPE)
        return p.stdout

class RuleSet(PythonEgg):
    def __init__(self, rules):
        super(RuleSet, self).__init__()
        self.rules = self.compileRules(rules)

    def compileRules(self, rules):
        return [(re.compile(i[0], re.UNICODE), i[1]) for i in rules]

    def applyn(self, text):
        total_count = 0
        while True:
            old_text = text
            for pattern, new in self.rules:
                text, count = pattern.subn(new, text)
                total_count += count
            if text == old_text:
                break
        return text, total_count

    def apply(self, text):
        return self.applyn(text)[0]


class RuleList(PythonEgg, list):
    ESCAPES = {
        r'\_': ' ',
        r'\t': '\t',
    }

    def applyn(self, text):
        total_count = 0
        for i in self:
            text, count = i.applyn(text)
            total_count += count
        return text, total_count

    def apply(self, text):
        return self.applyn(text)[0]

    @classmethod
    def parseRuleLine(cls, line):
        parts = line.split(':')
        parts = cls._joinEscapedParts(parts, ':')

        parts = [i.strip() for i in parts]
        parts = [cls._substituteEscapes(i) for i in parts]

        ret = []
        last = parts[-1]
        for i in parts[:-1]:
            ret.append( (i, last) )
        return ret

    @classmethod
    def _joinEscapedParts(cls, parts, chr):
        parts = list(parts)
        i = 0
        while i < len(parts):
            if parts[i] and parts[i][-1] == '\\':
                parts[i:i+2] = [parts[i][:-1] + chr + parts[i+1]]
            else:
                i += 1
        return parts

    @classmethod
    def _substituteEscapes(cls, s):
        for old, new in cls.ESCAPES.iteritems():
            s = s.replace(old, new)
        return s

    @classmethod
    def _cleanRules(cls, rules):
        ret = []
        for i1, i2 in rules:
            if not i1 and not i2:
                if not ret or ret[-1] is not None:
                    ret.append(None)
            else:
                ret.append( (i1, i2) )
        return ret

    @classmethod
    def createFromString(cls, s, ruleClass=RuleSet):
        rules = []
        for line in s.splitlines():
            rules.extend( cls.parseRuleLine(line) )
        return cls._createFromRules(rules, ruleClass)


    @classmethod
    def _createFromRules(cls, rules, ruleClass=RuleSet):
        rules = cls._cleanRules(rules)

        ret = cls()
        last_stop = 0
        for i, item in enumerate(rules):
            if item is None:
                ret.append( ruleClass(rules[last_stop:i]) )
                last_stop = i+1
        rest = rules[last_stop:]
        if rest:
            ret.append( ruleClass(rest) )
        return ret


    @classmethod
    def createFromFiles(cls, fns, encoding='utf-8', ruleClass=RuleSet):
        #cpp = Preprocessor()

        rules = []
        for fn in fns:
            fr = file(fn, 'r')
            try:
                #for line in cpp.process(fr):
                for line in fr:
                    line = unicode(line, encoding)
                    rules.extend( cls.parseRuleLine(line) )
            finally:
                fr.close()

        return cls._createFromRules(rules, ruleClass)


class ReTrans(Script):
    options = {
        'input': String,
        'output': String,
        'encoding': String,
        'batch': Flag,
        'files': (Required, Multiple, String),
    }

    shortOpts = {
        'i': 'input',
        'o': 'output',
        'b': 'batch',
        'e': 'encoding',
    }

    posOpts = ['files', Ellipsis]

    def process(self, rules, fr, fw, encoding):
        text = unicode(fr.read(), encoding)
        text = rules.apply(text)
        fw.write(text.encode(encoding))

    def main(self, files, input='-', output='-', encoding='utf-8', batch=False):
        rules = RuleList.createFromFiles(files, encoding)

        if not batch:
            if input == '-':
                input = sys.stdin
            else:
                input = file(input, 'r')

            if output == '-':
                output = sys.stdout
            else:
                output = file(output, 'w')

            self.process(rules, input, output, encoding)
            input.close()
            output.close()
        else:
            if not os.path.isdir(input):
                raise ValueError("Input directory %s doesn't exist" % input)

            if not os.path.isdir(output):
                raise ValueError("Output directory %s doesn't exist" % output)
            

            for fn in os.listdir(input):
                fni = os.path.join(input, fn)
                fr = file(fni, 'r')

                fno = os.path.join(output, fn)
                fw = file(fno, 'w')

                self.logger.info("Processing file %s into %s", fni, fno)

                self.process(rules, fr, fw, encoding)

                fr.close()
                fw.close()
            


if __name__ == '__main__':
    s = ReTrans()
    s.run()

