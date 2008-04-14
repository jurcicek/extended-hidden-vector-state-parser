#!/usr/bin/env python2.4

from svc.scripting.externals import *
from svc.map import SymMap
import sys
import itertools
sys.path.append('src')
import input

SYM_empty = '_empty_'
SYM_unseen = '_unseen_'

class HVSParser(ExternalScript):
    externalMethodDirs = ['bin/hvsparser']

    externalMethods = {
        'fsmrawdecode': Generator,
    }

    options = {
        'encoding': String,
        'model_dir': (Required, String),
        'batch': Flag,
    }

    posOpts = ['model_dir']

    def parseLine(self, model_dir, lines, isymMaps, osymMap):
        nsyms = len(isymMaps)
        mapped = []
        input_lines = []
        for il in lines:
            s_mapped = []
            s_input_lines = []
            for sym_il, map in zip(il, isymMaps):
                _unseen_ = map[SYM_unseen]
                _empty_ = map[SYM_empty]

                sym_il = [w.lower() for w in sym_il]
                s_mapped.append([map.get(w, _unseen_) for w in sym_il])
                s_mapped[-1].append(_empty_)
                s_input_lines.append(sym_il)
                s_input_lines[-1].append(SYM_empty)

            for si in zip(*s_mapped):
                mapped.extend(si)
            for si in zip(*s_input_lines):
                input_lines.extend(si)

        lines = []
        for i, w in enumerate(mapped):
            lines.append('%d\t%d\t%d\t%d\n' % (i, i+1, i, w))
        lines.append('%d\n' % (i+1, ))

        dcd_total = []
        dcd = []
        for dcdline in self.fsmrawdecode(model_dir, stdin=lines):
            dcdsplit = dcdline.split()
            if len(dcdsplit) == 1:
                continue
            elif len(dcdsplit) == 5:
                foo1, foo2, w, stack, value = dcdsplit
            elif len(dcdsplit) == 4:
                foo1, foo2, w, stack = dcdsplit
                value = 0
            else:
                raise ValueError("Bad output line from decoder: %r" % dcdline)
            w = int(w)
            if w % nsyms != 0:
                continue
            w = input_lines[w]
            stack = osymMap.inverse[int(stack)]
            to_append = ''
            if stack != '_':
                to_append += stack
            if w != SYM_empty:
                to_append += w
            dcd.append(to_append)
            if w == SYM_empty:
                dcd_total.append(' '.join(dcd))
                del dcd[:]

        return dcd_total

    def main(self, model_dir, encoding='iso-8859-2', batch=False):
        isymMaps = [SymMap.readFromFile(os.path.join(model_dir, 'isym1.map')),
                    SymMap.readFromFile(os.path.join(model_dir, 'isym2.map')),
                    SymMap.readFromFile(os.path.join(model_dir, 'isym3.map'))]

        osymMap = SymMap.readFromFile(os.path.join(model_dir, 'osym.map'))

        datasets_fn = os.path.join(model_dir, 'datasets')
        datasets_fr = file(datasets_fn, 'r')
        datasets = []
        for line in datasets_fr:
            datasets.append(line.strip())

        reader = input.StdInReader(encoding=encoding)
        if 'lemma' in datasets or 'pos' in datasets:
            reader = input.PDTReader('/opt/PDT-2.0/tools/machine-annotation', reader, online=not batch)
        generator = input.InputGenerator(reader, datasets, 'word')
        if not batch:
            for da_fn, da_id, da_semantics, da_txts in generator.readInputs():
                dcd = self.parseLine(model_dir, [da_txts], isymMaps, osymMap)
                if dcd:
                    print dcd[0].encode(encoding)
                else:
                    print line
        else:
            lines = []
            for da_fn, da_id, da_semantics, da_txts in generator.readInputs():
                lines.append(da_txts)
            dcd = self.parseLine(model_dir, lines, isymMaps, osymMap)
            for ol in dcd:
                print ol.encode(encoding)


if __name__ == '__main__':
    s = HVSParser()
    s.run()
