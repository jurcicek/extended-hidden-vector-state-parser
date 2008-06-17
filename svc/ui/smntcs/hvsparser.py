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

from subprocess import Popen, PIPE
from os.path import join as pjoin
import tempfile
import sys
import itertools

from svc.scripting import *
from svc.utils import ADict
from svc.map import SymMap
from svc.ui.mlf import MLF
from svc.ui.smntcs import input

SYM_empty = '_empty_'
SYM_unseen = '_unseen_'

IN_FILE = '%(i)s'
OUT_FILE = '%(o)s'

def pipeline(tmp_dir, fn, cmds, debug=False):
    counter = 0
    input_fn = fn
    for cmd in cmds:
        counter += 1
        output_fn = pjoin(tmp_dir, '%05d'%counter)

        if IN_FILE not in cmd:
            input = file(input_fn, 'rb')
        else:
            input = None
        if OUT_FILE not in cmd:
            output = file(output_fn, 'wb')
        else:
            output = None

        in_out = {'i': input_fn, 'o': output_fn}
        cmd = [i%in_out for i in cmd]

        #print 'cmd=%r, input_fn=%r, output_fn=%r' % (cmd, input_fn, output_fn)
        p = Popen(cmd, stdin=input, stdout=output)
        p.wait()

        if input is not None:
            input.close()
        if output is not None:
            output.close()

        if not debug:
            os.remove(input_fn)
        input_fn = output_fn
    return output_fn

def fsmrawdecode(model_dir, lines, debug=False):
    tmp_dir = tempfile.mkdtemp(prefix='hvsparser')
    cmds = [['fsmcompile', '-t', '-F', OUT_FILE],
            ['fsmcompose', '-F', OUT_FILE, IN_FILE, pjoin(model_dir, 'hvsparser.fsm')],
            ['fsmbestpath', '-n', '1', '-F', OUT_FILE, IN_FILE],
            ['fsmprint', IN_FILE],]
    input_fn = pjoin(tmp_dir, 'input')
    input = file(input_fn, 'wb')
    for line in lines:
        print >> input, line,
    input.close()
    output_fn = pipeline(tmp_dir, input_fn, cmds, debug=debug)
    output = file(output_fn, 'rb')
    for line in output:
        yield line
    output.close()
    if not debug:
        os.remove(output_fn)
        os.rmdir(tmp_dir)

class HVSParser(Script):
    options = {
        'encoding': String,
        'model_dir': (Required, String),
        'batch': Flag,
        'batch_size': Integer,
        'omit_leaves': Flag,
        'mlf': Flag,
        'ref_mlf': String,
        'xml_dir': String,
        'skip_empty': Flag,
        'input_chain': String,
        'no_underscores': Flag,
    }

    posOpts = ['model_dir']

    def fsmDecode(self, model_dir, lines):
        start = None
        heap = ADict(default=list)
        #for dcdline in self.fsmrawdecode(model_dir, stdin=lines):
        for dcdline in fsmrawdecode(model_dir, lines, debug=self.debugMain):
            dcdsplit = dcdline.split()
            if len(dcdsplit) == 1:
                continue
            elif len(dcdsplit) == 5:
                s1, s2, w, stack, weight = dcdsplit
            elif len(dcdsplit) == 4:
                s1, s2, w, stack = dcdsplit
                weight = 0.
            else:
                raise ValueError("Bad output line from decoder: %r" % dcdline)
            s1 = int(s1)
            s2 = int(s2)
            w = int(w)
            stack = int(stack)
            weight = float(weight)
            if start is None:
                start = s1
            heap[s1].append( (s2, w, stack, weight) )

        while heap[start]:
            new_state = start
            while new_state in heap:
                trans = heap[new_state].pop(0)
                if not heap[new_state]:
                    del heap[new_state]
                old_state = new_state
                new_state, w, stack, weight = trans
                yield w, stack, weight

    def parseLine(self, model_dir, lines, isymMaps, osymMap, omitLeaves=False):
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
            lines.append('%d\t%d\t%d\t%d\n' % (i, i+1, i+1, w))
        lines.append('%d\n' % (i+1, ))

        # print ''.join(lines)
        # print ' '.join(input_lines)

        dcd_total = [[]]
        dcd = []
        for w, stack, weight in self.fsmDecode(model_dir, lines):
            #print '%s:%s/%f' % (w, stack, weight)
            if stack != 0:
                stack = osymMap.inverse.get(stack, 'epsilon')
                if stack[0] == ')' and not omitLeaves:
                    del dcd_total[-1][-1]
                    dcd_total[-1].append(stack)
                    dcd_total[-1].append(' ')
                else:
                    dcd_total[-1].append(stack)
            if w != 0:
                w -= 1
                if w % nsyms != 0:
                    # Skip input symbols other than S1
                    continue
                w = input_lines[w]
                if w == SYM_empty:
                    if dcd_total[-1] and dcd_total[-1][-1] == ' ':
                        del dcd_total[-1][-1]
                    dcd_total[-1] = ''.join(dcd_total[-1])
                    dcd_total.append([])
                elif not omitLeaves:
                    dcd_total[-1].append(w)
                    dcd_total[-1].append(' ')
        if dcd_total[-1] == []:
            del dcd_total[-1]
        #print dcd_total
        return dcd_total

    def main(self, model_dir, encoding=None, batch=False, omit_leaves=False,
            mlf=False, xml_dir=None, ref_mlf=None, skip_empty=False,
            input_chain=None, batch_size=100, no_underscores=True):
        encoding = sys.stdout.encoding
        if encoding is None:
            if os.name == 'nt':
                encoding = 'cp1250'
            else:
                encoding = 'iso-8859-2'

        datasets_fn = pjoin(model_dir, 'datasets')
        datasets_fr = file(datasets_fn, 'r')
        datasets = []
        isymMaps = []
        for i, line in enumerate(datasets_fr):
            line = line.strip()
            datasets.append(line)
            if line != 'off':
                isymMaps.append(SymMap.readFromFile(pjoin(model_dir, 'isym%d.map'%(i+1,))))

        osymMap = SymMap.readFromFile(pjoin(model_dir, 'osym.map'))

        if 'signed' in datasets:
            da_type = 'signed'
        else:
            da_type = 'normalized'

        if xml_dir:
            reader = input.MultiReader([xml_dir], input.DXMLReader)
        else:
            reader = input.StdInReader(encoding=encoding, type=da_type)
            if 'lemma' in datasets or 'pos' in datasets:
                if os.name == 'nt':
                    raise RuntimeError("Datasets 'lemma' and 'pos' are unsupported on Windows")
                reader = input.PDTReader('/opt/PDT-2.0/tools/machine-annotation', reader, online=not batch)
        if input_chain is not None:
            reader = input.InputChain(input_chain, reader)
        generator = input.InputGenerator(reader, datasets, datasets[0], noUnderscores=no_underscores)
        hypMLF = MLF()
        refMLF = MLF()
        if not batch:
            for da_fn, da_id, da_semantics, da_txts in generator.readInputs():
                da_empty = not bool(da_semantics.strip())
                if (da_empty and skip_empty):
                    continue

                refMLF[da_id] = da_semantics+'\n'
                dcd = self.parseLine(model_dir, [da_txts], isymMaps, osymMap, omitLeaves=omit_leaves)
                if dcd:
                    if len(dcd) == 1:
                        hypMLF[da_id] = dcd[0].encode(encoding)+'\n'
                    else:
                        hypMLF[da_id] = ';'.join(dcd).encode(encoding)+'\n'
                else:
                    hypMLF[da_id] = line+'\n'
                if not mlf:
                    print hypMLF[da_id],
        else:
            all_processed = False
            inputs = generator.readInputs()
            while not all_processed:
                da_count = 0
                lines = []
                ids = []
                for da_fn, da_id, da_semantics, da_txts in inputs:
                    da_empty = not bool(da_semantics.strip())
                    if (da_empty and skip_empty):
                        continue

                    refMLF[da_id] = da_semantics+'\n'
                    lines.append(da_txts)
                    ids.append(da_id)
                    da_count += 1
                    if da_count >= batch_size:
                        break
                else:
                    all_processed = True

                dcd = self.parseLine(model_dir, lines, isymMaps, osymMap, omitLeaves=omit_leaves)
                for da_id, ol in zip(ids, dcd):
                    hypMLF[da_id] = ol.encode(encoding)+'\n'
                    if not mlf:
                        print hypMLF[da_id],
        if mlf:
            s = ''.join(hypMLF.toLines())
            print s

        if ref_mlf:
            refMLF.writeToFile(ref_mlf)


