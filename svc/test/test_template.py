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

from svc.template import *

class TemplateTest(unittest.TestCase):
    def testBackload(self):
        t = ExTemplate('Variables: v1=$v1, v2=$v2')
        res = t.backload('Variables: v1=10, v2=20')
        self.assertEqual(res, {'v1': '10', 'v2': '20'})
        res = t.backload('Variables: v1=10! v2=20')
        self.assertEqual(res, None)
        res = t.backload('Variables: v1=10, v2=20     ')
        self.assertEqual(res, {'v1': '10', 'v2': '20     '})

    def testPlacing(self):
        t = ExTemplate('[v1=$v1, v2=$v2]')
        res = t.backload('[v1=10, v2=20]')
        self.assertEqual(res, {'v1': '10', 'v2': '20'})

        t = ExTemplate('[v1=$v1, v2=$v2]', 'space')
        res1 = t.backload('[v1=10, v2=20]')
        res2 = t.backload('   [v1=10, v2=20]   ')
        self.assertEqual(res1, res2)
        res3 = t.backload('XXX[v1=10, v2=20]XXX')
        self.assertEqual(res3, None)

        t = ExTemplate('[v1=$v1, v2=$v2]', 'ignore')
        res1 = t.backload('[v1=10, v2=20]')
        res2 = t.backload('XXX[v1=10, v2=20]XXX')
        res3 = t.backload('   [v1=10, v2=20]   ')
        self.assertEqual(res1, res2)
        self.assertEqual(res3, res2)


if __name__ == '__main__':
	unittest.main()

