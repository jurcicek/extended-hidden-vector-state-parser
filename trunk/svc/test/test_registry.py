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

from svc.registry import *

class RegistryTest(unittest.TestCase):
	def testChildMethod(self):
		root = Registry()
		ch1 = Registry()
		ch2 = Registry()
		self.assertEqual(root.getParent(), None)
		self.assertEqual(ch1.getParent(), None)
		self.assertEqual(ch2.getParent(), None)

		root.addChild(ch1)
		ch1.addChild(ch2)
		self.assertEqual(root.getParent(), None)
		self.assertEqual(ch1.getParent(), root)
		self.assertEqual(ch2.getParent(), ch1)
		self.assertEqual(ch2.getPath(), [root, ch1, ch2])

		self.assertRaises(
				ValueError,
				ch2.addChild, ch2
		)

		self.assertRaises(
				ValueError,
				ch2.addChild, root
		)

		root.addChild(ch2)
		self.assertEqual(root.getParent(), None)
		self.assertEqual(ch1.getParent(), root)
		self.assertEqual(ch2.getParent(), root)

		root.delChild(ch1)
		root.delChild(ch2)
		self.assertEqual(root.getParent(), None)
		self.assertEqual(ch1.getParent(), None)
		self.assertEqual(ch2.getParent(), None)

	def testNames(self):
		root = Registry()
		ch1 = Registry()
		ch2 = Registry()
		ch3 = Registry()

		root.child1 = ch1
		root.child2 = ch2
		root.child1.child3 = ch3

		self.assertEqual(root.getPath(), [root])
		self.assertEqual(root.getFullName(), '<anon>')
		self.assertEqual(ch1.getFullName(), '<anon>.child1')
		self.assertEqual(ch2.getFullName(), '<anon>.child2')
		self.assertEqual(ch3.getFullName(), '<anon>.child1.child3')

		self.assertEqual(root.getParent(), None)
		self.assertEqual(ch1.getParent(), root)
		self.assertEqual(ch2.getParent(), root)
		self.assertEqual(ch3.getParent(), ch1)

		del root.child1.child3
		del root.child1
		del root.child2
		self.assertEqual(root.getParent(), None)
		self.assertEqual(ch1.getParent(), None)
		self.assertEqual(ch2.getParent(), None)
		self.assertEqual(ch3.getParent(), None)
	
	def testDecorator(self):
		root = Registry()
		root.child = Registry()

		@register(root)
		def f1(obj): return obj

		@register(root.child)
		def f2(obj): return obj

		@register(root)
		def f3(obj): return obj

		self.assertEqual(root, [f1, f3])
		self.assertEqual(root.child, [f2])
	
	def testObservers_Sequent(self):
		class NumberObserver(object):
			def __init__(self, number):
				self._number = number

			def getNumber(self):
				return self._number

		obj1 = NumberObserver(1)
		obj2 = NumberObserver(2)
		obj3 = NumberObserver(3)

		NumberRegistry = Registry()
		NumberRegistry.createSequent('getNumber')
		NumberRegistry.createSequent('getSum', reduce=sum, obs_name='getNumber')

		NumberRegistry[:] = [obj1, obj2, obj3]

		self.assertEqual([1, 2, 3], NumberRegistry.getNumber())
		self.assertEqual(1+2+3, NumberRegistry.getSum())

		NumberRegistry.remove(obj1)

		self.assertEqual([2, 3], NumberRegistry.getNumber())
		self.assertEqual(2+3, NumberRegistry.getSum())
	
	def testObservers_DirectSequent(self):
		NumberRegistry = Registry()
		NumberRegistry.createDirectSequent('getNumber')
		NumberRegistry.createDirectSequent('getSum', reduce=sum)

		@register(NumberRegistry)
		def f1(): return 1

		@register(NumberRegistry)
		def f2(): return 2

		@register(NumberRegistry)
		def f3(): return 3

		self.assertEqual([1, 2, 3], NumberRegistry.getNumber())
		self.assertEqual(1+2+3, NumberRegistry.getSum())

		NumberRegistry.remove(f1)

		self.assertEqual([2, 3], NumberRegistry.getNumber())
		self.assertEqual(2+3, NumberRegistry.getSum())

	def testObservers_Queries(self):
		class FileHandler(object):
			def getHandler(self, string):
				if string.startswith('file:'):
					return self
			def getPath(self, string):
				return string[5:]

		class FTPHandler(object):
			def getHandler(self, string):
				if string.startswith('ftp:'):
					return self
			def getPath(self, string):
				return string[4:]

		protocols = Registry()
		protocols.createQuery('getHandler')

		h_file = FileHandler()
		h_ftp = FTPHandler()
		protocols.extend([h_file, h_ftp])

		self.assertEqual(protocols.getHandler('file:/usr/share'), h_file)
		self.assertEqual(protocols.getHandler('ftp:/pub/linux'), h_ftp)
	
	def testObservers_Chain(self):
		class Number(object):
			def __init__(self, n):
				self._n = n

			def mul(self, value):
				return self._n * value

		numbers = Registry()
		numbers.createChain('factorial', obs_name='mul')
		numbers.createChain('mul')
		numbers[:] = [Number(i) for i in range(1, 6)]
		
		self.assertEqual(120, numbers.factorial(1))
		self.assertEqual(240, numbers.mul(2))
	
	def testObservers_DirectChain(self):
		def mul2(value):
			return value*2

		numbers = Registry()
		numbers.createDirectChain('mul2')
		numbers[:] = [mul2]*5

		self.assertEqual(32, numbers.mul2(1))

	
if __name__ == '__main__':
	unittest.main()
