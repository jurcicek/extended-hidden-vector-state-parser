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
import tempfile
from subprocess import Popen, PIPE
from os.path import join as pjoin

from svc.map import SymMap
from svc.egg import PythonEgg
from svc.utils import ADict

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

class FSM(PythonEgg):
    def __init__(self, fsm_dir, fsm_parts={}, nbest=1):
        super(FSM, self).__init__()
        self.fsm_dir = fsm_dir
        self.fsm_parts = fsm_parts
        self.in_maps = self.loadMaps(fsm_parts['in_maps'])
        self.nbest = nbest

        out_map = self.loadMaps([fsm_parts['out_map']])
        if len(out_map) != 1:
            raise ValueError("There must be exactly one output map")
        self.out_map = out_map[0].inverse
    
    def loadMaps(self, maps):
        ret = []
        for m in maps:
            fn = pjoin(self.fsm_dir, m)
            ret.append( SymMap.readFromFile(fn) )
        return ret

    def mapInput(self, input):
        raise ValueError("Unimplemented")

    def mapOutput(self, output, orig_input):
        raise ValueError("Unimplemented")

    def splitMapped(self, num_input):
        ret1 = []
        ret2 = []
        for num, sym in num_input:
            ret1.append(num)
            ret2.append(sym)
        return ret1, ret2

    def encodeInput(self, input):
        for state, sym in enumerate(input):
            yield '%d\t%d\t%d\t%d\n' % (state, state+1, state+1, sym)
        yield '%d\n' % (state+1, )

    def compose(self, input, debug=False):
        prefix = self.fsm_parts.get('name', 'fsm')
        fsms = [pjoin(self.fsm_dir, i) for i in self.fsm_parts['parts']]
        nbest = str(self.nbest)

        tmp_dir = tempfile.mkdtemp(prefix=prefix)
        cmds = [['fsmcompile', '-t', '-F', OUT_FILE],
                ['fsmcompose', '-F', OUT_FILE, IN_FILE] + fsms,
                ['fsmbestpath', '-n', nbest, '-F', OUT_FILE, IN_FILE],
                ['fsmprint', IN_FILE],]

        input_fn = pjoin(tmp_dir, 'input')
        input_fw = file(input_fn, 'wb')
        for line in input:
            print >> input_fw, line,
        input_fw.close()

        output_fn = pipeline(tmp_dir, input_fn, cmds, debug=debug)

        output = file(output_fn, 'rb')
        for line in output:
            yield line
        output.close()

        if not debug:
            os.remove(output_fn)
            os.rmdir(tmp_dir)
    
    def decodeOutput(self, outputs):
        start = None
        heap = ADict(default=list)
        for dcdline in outputs:
            dcdsplit = dcdline.split()
            if len(dcdsplit) == 1:
                continue
            elif len(dcdsplit) == 2:
                continue
            elif len(dcdsplit) == 5:
                s1, s2, isym, osym, weight = dcdsplit
            elif len(dcdsplit) == 4:
                s1, s2, isym, osym = dcdsplit
                weight = 0.
            else:
                raise ValueError("Bad output line from decoder: %r" % dcdline)
            s1 = int(s1)
            s2 = int(s2)

            isym = int(isym)
            osym = int(osym)
            weight = float(weight)

            if start is None:
                start = s1
            heap[s1].append( (s2, isym, osym, weight) )

        while heap[start]:
            new_state = start
            while new_state in heap:
                trans = heap[new_state].pop(0)
                if not heap[new_state]:
                    del heap[new_state]
                old_state = new_state
                new_state, isym, osym, weight = trans
                yield isym, osym, weight
            yield None

    def mapNBestOutput(self, num_output, orig_input):
        ret = []
        current = []
        for item in num_output:
            if item is None:
                current = self.mapOutput(current, orig_input)
                ret.append(current)
                current = []
                continue
            else:
                current.append(item)
        return ret

    def processInput(self, *args, **kwargs):
        map_input = self.mapInput(*args, **kwargs)

        num_input, orig_input = self.splitMapped(map_input)

        input_fsm = self.encodeInput(num_input)
        output_fsm = self.compose(input_fsm)
        num_output = self.decodeOutput(output_fsm)

        num_output = list(num_output)
        return self.mapNBestOutput(num_output, orig_input)
