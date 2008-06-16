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
import re
from svc.scripting import *
from svc.ui.gmtk import *

class GmtkDiff(Script):
    options = {
        'mstr1': (Required, String),
        'mstr2': (Required, String),
        'dir1': String,
        'dir2': String,
        't1': (Multiple, String),
        't2': (Multiple, String),
        'noeq': Flag,
    }

    posOpts = ['mstr1', 'mstr2']

    def transformDict(self, d, regex, subst):
        ret = {}
        regex = re.compile(regex)
        for name, obj in d.iteritems():
            name = regex.sub(subst, name)
            ret[name] = obj
        return ret

    def diffGmtkTypes(self, type_name, d1, d2, t1=[], t2=[], noeq=False):
        self.logger.debug('Making diff of type %s', type_name)
        for t in t1:
            d1 = self.transformDict(d1, *t)
        for t in t2:
            d2 = self.transformDict(d2, *t)

        d1_names = set(d1.keys())
        d2_names = set(d2.keys())
        in1 = d1_names - d2_names
        in2 = d2_names - d1_names
        inboth = d1_names & d2_names

        for i, missing in [(2, in1), (1, in2)]:
            for name in sorted(missing):
                print '%s %s is missing in %d' % (type_name, name, i)

        differs = set()
        if not noeq:
            for name in sorted(inboth):
                obj1 = d1[name]
                obj2 = d2[name]
                if not (obj1 == obj2):
                    differs.add(name)
                    print '%s %s differs' % (type_name, name)

        if not (in1 or in2 or differs):
            print '%s objects completely matches' % (type_name,)

    def diffWorkspaces(self, w1, w2, t1={}, t2={}, noeq=False):
        self.logger.info('Making diff between GMTK workspaces')
        for type_name, type in Workspace.knownObjects.iteritems():
            d1 = w1[type]
            d2 = w2[type]
            dt1 = t1.get(type_name, [])
            dt2 = t2.get(type_name, [])
            self.diffGmtkTypes(type_name, d1, d2, dt1, dt2, noeq)

    def createWorkspaceFromMSTR(self, mstr):
        w = Workspace()
        self.logger.info('Reading master file %r', mstr)
        w.readMasterFile(mstr)
        return w

    def createTransformDict(self, t):
        ret = dict((n, []) for n in Workspace.knownObjects)
        for t_line in t:
            type_name, regex, subst = t_line.split(':', 2)
            if type_name == '*':
                for type_name in Workspace.knownObjects:
                    ret[type_name].append((regex, subst))
            else:
                ret[type_name].append((regex, subst))
        return ret

    def main(self, mstr1, mstr2, dir1=None, dir2=None, t1=[], t2=[], noeq=False):
        t1 = self.createTransformDict(t1)
        t2 = self.createTransformDict(t2)

        cwd = os.getcwd()
        if dir1 is not None:
            self.logger.debug('Changing current directory to %r', dir1)
            os.chdir(dir1)
        w1 = self.createWorkspaceFromMSTR(mstr1)
        os.chdir(cwd)
        if dir2 is not None:
            self.logger.debug('Changing current directory to %r', dir2)
            os.chdir(dir2)
        w2 = self.createWorkspaceFromMSTR(mstr2)
        os.chdir(cwd)

        self.diffWorkspaces(w1, w2, t1, t2, noeq)


if __name__ == '__main__':
    s = GmtkDiff()
    s.run()
