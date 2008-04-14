#!/usr/bin/env python2.4

import sys
from svc.scripting import *

class PDTLower(Script):
    options = {
        'input': String,
        'output': String,
        'encoding': String,
    }
    posOpts = ['input', 'output']

    def main(self, input=None, output=None, encoding='iso-8859-2'):
        if input is None:
            input = sys.stdin
        else:
            input = file(input)
        if output is None:
            output = sys.stdout
        else:
            output = file(output)

        output.write('; Lowercase version of morphological lexicon\n')
        output.write(';\n')
        output.write('; Generated using script pdt_lower.py from semantics-4 distribution\n')
        output.write('; Author of pdt_lower.py: Jan Svec <honzas@kky.zcu.cz>\n')
        output.write(';\n')

        for line in input:
            line = line.decode(encoding)
            if line[0] == 'R':
                R, pname, root, lemma, other = line.split('|', 4)
                root = root.lower()
                lemma = lemma.lower()
                line = '|'.join([R, pname, root, lemma, other])
            line = line.encode(encoding)
            output.write(line)

        input.close()
        output.close()

if __name__ == '__main__':
    s = PDTLower()
    s.run()
