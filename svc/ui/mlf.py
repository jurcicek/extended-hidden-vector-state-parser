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
import codecs

from svc.egg import PythonEgg
from svc.utils import issequence
from svc.ui.treedist import OrderedTree, ROOT_CONCEPT

class _ConceptLine(list):
    def __init__(self, separator):
        super(_ConceptLine, self).__init__()
        self._separator = separator

    def addSeparator(self):
        self.append(self._separator)

    def removeSeparator(self):
        while self and self[-1] == self._separator:
            del self[-1]

    def flushLine(self):
        self.removeSeparator()
        ret = ''.join(self)
        del self[:]
        return OrderedTree.fromString(ret, label=ROOT_CONCEPT)


class MLF(PythonEgg, dict):
    MLF_HEADER = '#!MLF!#'

    @classmethod
    def mapFromMLF(cls, contents):
        return contents

    def mapToMLF(self, value):
        return value

    @classmethod
    def readFromFile(cls, fn):
        fr = codecs.open(fn, 'r', 'utf-8')
        try:
            return cls.fromLines(fr)
        finally:
            fr.close()

    @classmethod
    def fromLines(cls, lines):
        forest = cls()
        it = iter(lines)

        header = it.next().strip()
        if header != cls.MLF_HEADER:
            raise ValueError("Not a MLF file, bad header")
        filename_line = True
        for line in it:
            if filename_line:
                filename_line = False
                filename = line.strip()[1:-1]
                filename = os.path.splitext(filename)[0]
                content_lines = []
                continue
            elif line[0] == '.':
                filename_line = True
                forest[filename] = cls.mapFromMLF(content_lines)
                del content_lines
                continue
            else:
                content_lines.append(line)
        return forest

    def writeToFile(self, fn):
        fw = codecs.open(fn, 'w', 'utf-8')
        try:
            for line in self.toLines():
                fw.write(line)
        finally:
            fw.close()

    def toLines(self):
        yield self.MLF_HEADER + '\n'
        for key in sorted(self):
            yield '"%s"\n' % key
            value = self[key]
            for line in self.mapToMLF(value):
                yield line
            yield '.\n'

class ConceptMLF(MLF):
    @classmethod
    def mapFromMLF(cls, contents):
        str = ' '.join(s.strip() for s in contents)
        return OrderedTree.fromString(str, label=ROOT_CONCEPT)

    def mapToMLF(self, value):
        return str(value)
