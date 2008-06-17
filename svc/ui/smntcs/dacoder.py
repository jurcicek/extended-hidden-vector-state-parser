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
from svc.ui.smntcs import fsm

class DacoderFSM(fsm.FSM):
    def __init__(self, fsm_dir):
        parts = {
            'name': 'dacoder',
            'in_maps': ['dacoder.isym'],
            'out_map': 'dacoder.osym',
            'parts': ['dacoder1.fsm', 'dacoder2.fsm'],
        }
        super(DacoderFSM, self).__init__(fsm_dir, parts, nbest=1)

    def mapInput(self, input):
        map = self.in_maps[0]
        _user_ = map['_user_']
        _operator_ = map['_operator_']
        _unseen_ = map['_unseen_']
        _empty_ = map['_empty_']

        input = [j.split() for j in input.split(';')]

        ret = []
        for j, da in enumerate(input):
            spkr = [_operator_, _user_][j%2]
            ret.append( (spkr, None) )
            for i in da:
                sym = map.get(i, _unseen_)
                ret.append( (sym, i) )
            ret.append( (_empty_, None) )
        return ret

    def mapOutput(self, output, orig_input):
        ret = []
        for item in output:
            iindex, osym, weight = item
            if osym != 0:
                osym = self.out_map[osym]
                ret.append(osym)
        return ret

class SegmentorFSM(fsm.FSM):
    def __init__(self, fsm_dir):
        parts = {
            'name': 'hvsseg',
            'in_maps': ['hvsseg.isym1'],
            'out_map': 'dacoder.fsm.osym',
            'parts': ['hvsseg.fsm', 'dacoder.fsm', 'dialogue_act.fsm'],
        }
        super(SegmentorFSM, self).__init__(fsm_dir, parts, nbest=3)

    def mapInput(self, input):
        map = self.in_maps[0]

        _unseen_ = map['_unseen_']
        _empty_ = map['_empty_']

        ret = []
        for i in input.split():
            sym = map.get(i, _unseen_)
            ret.append( (sym, i) )
        ret.append( (_empty_, None) )

        return ret

    def mapOutput(self, output, orig_input):
        ret = []
        for item in output:
            iindex, osym, weight = item
            if osym != 0:
                osym = self.out_map[osym]
                ret.append(osym)
        return ret


class Dacoder(Script):
    options = {
        'model_dir': (Required, String),
    }

    posOpts = ['model_dir']

    def main(self, model_dir):
        fsm = SegmentorFSM(model_dir)
        while True:
            i = unicode(raw_input(), 'latin2')
            #print fsm.mapInput(i)
            print fsm.processInput(i)
