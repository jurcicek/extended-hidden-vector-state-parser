#!/usr/bin/env python2.4

import os.path
from glob import glob
from fnmatch import fnmatchcase
import codecs

from svc.scripting import *

from lexMap import LexMap
import gmtk

class WordFile(file):
    def __init__(self, *args):
        super(WordFile, self).__init__(*args)
        self._stack = []

    def readWords(self):
        while not self._stack:
            line = self.readline()
            if not line:
                break
            line = line.split('%', 1)[0]
            self._stack.extend(line.split())
            while self._stack:
                yield self._stack.pop(0)

class PrMassScaler(Script):
    options = {
        'inFile': (Required, String),
        'outFile': (Required, String),
        'job': (Multiple, String),
        'clear': (Multiple, String),
        'dpmf': Flag,
        'dcpt': Flag,
    }

    def readTables(self, inFile, dpmfs=False):
        fr = WordFile(inFile)
        f = fr.readWords()
        num = int(f.next())
        for i in range(num):
            index = int(f.next())
            if i != index:
                raise ValueError("Bad DCPT file %r" % inFile)
            name = f.next()
            if not dpmfs:
                nparents = int(f.next())
            else:
                nparents = 0
            parents = []
            total = 1
            for foo in range(nparents+1):
                pcard = int(f.next())
                parents.append(pcard)
                total *= pcard
            items = []
            for foo in range(total):
                value = float(f.next())
                items.append(value)
            yield name, (parents, items)

    def writeTables(self, outFile, tables, dpmfs=False):
        fw = WordFile(outFile, 'w')
        tables = list(tables)
        fw.write('%d\n\n' % len(tables))
        for i, (name, (parents, items)) in enumerate(tables):
            fw.write('%d\n' % i)
            fw.write('%s\n' % name)

            if not dpmfs:
                fw.write('%d\n' % (len(parents)-1))

            str_parents = ' '.join('%d' % p for p in parents)
            fw.write(str_parents + '\n')

            card = parents[-1]
            for i in xrange(0, len(items), card):
                line = ' '.join('%.3e' % f for f in items[i:i+card])
                fw.write(line + '\n')

    def distributeMass(self, table, into, coef):
        parents, items = table
        card = parents[-1]
        for i in xrange(0, len(items), card):
            line_sum = 0
            for j in range(0, card):
                if j != into:
                    value = items[i+j] ** coef
                    items[i+j] = value
                    line_sum += value
            items[i+into] = max(1 - line_sum, 0)

    def clearMass(self, table, indices):
        parents, items = table
        card = parents[-1]
        for i in xrange(0, len(items), card):
            line_sum = 0.
            for j in range(0, card):
                if j in indices:
                    items[i+j] = 0
                else:
                    line_sum += items[i+j]
            if line_sum != 0:
                for j in range(0, card):
                    if j not in indices:
                        items[i+j] /= line_sum
            else:
                if j in indices:
                    items[i+j] = 1. / len(indices)

    def doJob(self, job, source):
        template, factor, index = job.split(':', 2)
        factor = float(factor)
        if '@' in index:
            symbol, map = index.split('@', 1)
            map = LexMap().read(map)
            index = int(map[symbol])
        else:
            index = int(index)
        for dcpt_name, table in source:
            if fnmatchcase(dcpt_name, template):
                self.distributeMass(table, index, factor)
            yield dcpt_name, table

    def doClear(self, clear, source):
        template, indices = clear.split(':', 1)
        indices = set(int(i) for i in indices.split(','))
        for dcpt_name, table in source:
            if fnmatchcase(dcpt_name, template):
                self.clearMass(table, indices)
            yield dcpt_name, table

    def makeBatch(self, jobs, clears, source):
        for job in jobs:
            source = self.doJob(job, source)
        for clear in clears:
            source = self.doClear(clear, source)
        return source

    def main(self, inFile, outFile, job=['*:1.0:1'], clear=[], dpmf=False, dcpt=False):
        if not (dpmf or dcpt):
            self.logger.warn("Assuming DCPT tables")
            dcpt = True
        elif dpmf and dcpt:
            raise ValueError("Don't use both --dpmf and --dcpt options")
        dpmf = not dcpt

        tables = self.readTables(inFile, dpmfs=dpmf)
        tables = self.makeBatch(job, clear, tables)
        self.writeTables(outFile, tables, dpmfs=dpmf)


def main():
    script = PrMassScaler()
    script.run()

if __name__ == '__main__':
    main()
