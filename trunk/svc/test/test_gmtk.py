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

import unittest
import os
import random

from svc.ui.gmtk import *
from svc.utils import cartezian

class DTTest(unittest.TestCase):
    V_LEN = 5
    V_N = 3

    def setUp(self):
        self.w = Workspace()

    def testCartezian(self):
        dt = DT(self.w, 'mydt', self.V_N, DT.NullTree)
        vects = [range(self.V_LEN) for i in range(self.V_N)]
        en = list(enumerate(cartezian(*vects)))
        for i, v in en:
            dt[v] = i

        for i, v in en:
            self.assertEqual(i, dt[v])

    def testDeletions(self):
        dt = DT(self.w, 'mydt', self.V_N, DT.NullTree)
        vects = [range(self.V_LEN) for i in range(self.V_N)]
        en = list(enumerate(cartezian(*vects)))
        for i, v in en:
            dt[v] = i

        random.shuffle(en)

        for i, v in en[:20]:
            del dt[v]

        for i, v in en[:20]:
            self.assertEqual(0, dt[v])

        for i, v in en[20:]:
            self.assertEqual(i, dt[v])

        dt.tree.vanish() 

        for i, v in en[:20]:
            self.assertEqual(0, dt[v])

        for i, v in en[20:]:
            self.assertEqual(i, dt[v])

    def testIO(self):
        dt = DT(self.w, 'mydt', self.V_N, DT.NullTree)
        vects = [range(self.V_LEN) for i in range(self.V_N)]
        en = list(enumerate(cartezian(*vects)))
        for i, v in en:
            dt[v] = i
        
        self.w.writeToFile(DT, 'gmtk/test.dt')
        del self.w[DT, 'mydt']
        self.w.readFromFile(DT, 'gmtk/test.dt')

        dt = self.w[DT, 'mydt']
        for i, v in en:
            self.assertEqual(i, dt[v])

        # os.remove('gmtk/test.dt')

        


if __name__ == '__main__':
	unittest.main()


