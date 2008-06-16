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

from svc.egg import *

class PythonEggTest(unittest.TestCase):
    def testProperties(self):
        class MyEgg(PythonEgg):
            def getValue(self): pass
            def setValue(self, v): pass

            def setBadValue(self, v, bad_arg): pass

            def getAnotherValue(self): pass
            def delAnotherValue(self): pass

            def isOTHER(self): pass

        self.assert_(hasattr(MyEgg, 'value'))
        self.assert_(hasattr(MyEgg, 'anotherValue'))
        self.assert_(hasattr(MyEgg, 'OTHER'))
        self.assert_(not hasattr(MyEgg, 'badValue'))

    def testProperties2(self):
        class MyEgg2(PythonEgg):
            def getValue(self):
                return self._value
            def setValue(self, v):
                self._value = v
                self.testValue = v
            def delValue(self):
                del self.testValue

        e = MyEgg2()
        e.value = 42
        self.assertEqual(e.value, 42)
        self.assertEqual(e.testValue, 42)
        del e.value
        self.assert_(not hasattr(e, 'testValue'))

    def testProperties3(self):
        class EggParent(PythonEgg):
            def setMyValue(self, v):
                self._value = v
        class EggChild(EggParent):
            def getMyValue(self):
                return self._value

        parent = EggParent()
        child = EggChild()

        parent.myValue = 42
        self.assertRaises(AttributeError, getattr, parent, 'myValue')
        child.myValue = 42
        self.assertEqual(child.myValue, 42)

    def testNameConversions(self):
        suffixes = ['Value', 'SomeValue', 'ASR', 'X']
        for s in suffixes:
            pname = MetaEgg._suffixToProperty(s)
            sname = MetaEgg._propertyToSuffix(pname)
            self.assertEqual(s, sname)


    def testMultiGetters(self):
        def newClass():
            class BadEgg(PythonEgg):
                def getValue(self): pass
                def isValue(self): pass

        self.assertRaises(ValueError, newClass)

    def testPrivateProperties(self):
        class MyEgg3(PythonEgg):
            def _getValue(self):
                return self.__value
            def _setValue(self, v):
                self.__value = v
                self.testValue = v
            def _delValue(self):
                del self.testValue

        e = MyEgg3()
        e._value = 42
        self.assertEqual(e._value, 42)
        self.assertEqual(e.testValue, 42)
        del e._value
        self.assert_(not hasattr(e, 'testValue'))

    def testMetaAttrs(self):
        def myrange(owner, *args, **kwargs):
            return range(*args, **kwargs)

        class MyEgg(PythonEgg):
            attr = MetaAttribute(myrange, 10)

        obj1 = MyEgg()
        obj2 = MyEgg()
        self.assertEqual(obj1.attr, range(10))
        self.assertEqual(obj2.attr, range(10))
        del obj1.attr[-1]
        self.assertEqual(obj1.attr, range(9))
        self.assertEqual(obj2.attr, range(10))

    def testAttributeClass(self):
        class MyEgg(PythonEgg):
            class double(AttributeClass):
                def getValue(self):
                    return self.owner.value * 2.
                def setValue(self, val):
                    self.owner.value = val / 2.
            def getValue(self):
                return self._value
            def setValue(self, val):
                self._value = val

        obj = MyEgg()

        obj.value = 2
        self.assertEqual(obj.value, 2)
        self.assertEqual(obj.double.value, 4)

        obj.double.value = 5
        self.assertEqual(obj.value, 2.5)
        self.assertEqual(obj.double.value, 5)




if __name__ == '__main__':
	unittest.main()
