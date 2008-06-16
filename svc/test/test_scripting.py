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
from os.path import isfile

from svc.scripting import *
from svc.scripting import _OptionTree
from svc.scripting import extractors

class OptionManagerTest(unittest.TestCase):
    spec = {
        'int1': Integer,
        'int2': (Required, Integer),
        'int3': (Required, Multiple, Integer),
        'list': (ListOf, Integer, '+'),
        'str1': String,
        'str2': (Required, String),
        'str3': (Required, Multiple, String),
    }

    spec_ret = {
        'dir1': Integer,
        'dir2': String,
    }

    spec_val = {
        'int1': Integer,
        'int2': (Required, Integer),
        'int3': (Required, Multiple, Integer),
    }

    val = [
        ('int1', '1', 'source', 'desc'),
        ('int2', '2', 'source', 'desc'),
        ('int3', '3', 'source', 'desc'),
        ('int3', '6', 'source', 'desc'),
    ]

    spec_multi = {
        'int1': Integer,
        'int2': (JoinSources, Integer),
        'int3': (Multiple, Integer),
    }

    multi = [
        ('int1', '1', 'A', 'desc'),
        ('int2', '2', 'A', 'desc'),
        ('int2', '3', 'A', 'desc'),
        ('int3', '4', 'A', 'desc'),

        ('int2', '4', 'B', 'desc'),
        ('int3', '5', 'B', 'desc'),
        ('int3', '6', 'B', 'desc'),
    ]

    multi2 = [
        ('int1', '1', 'A', 'desc'),
        ('int2', '2', 'A', 'desc'),
        ('int2', '3', 'A', 'desc'),
        ('int3', '4', 'A', 'desc'),

        ('int2', 1.4, 'B', 'desc'),
        ('int3', 1.5, 'B', 'desc'),
        ('int3', 1.6, 'B', 'desc'),
    ]

    def testQueries(self):
        m = OptionManager(self.spec)
        self.assertEqual(
                set(['int1', 'int2', 'int3', 'list', 'str1', 'str2', 'str3']),
                m.options()
        )
        self.assertEqual(
                set(['int1', 'int2', 'int3', 'list', 'str1', 'str2', 'str3']),
                m.params()
        )
        self.assertEqual(
                set(['int2', 'int3', 'str2', 'str3']),
                m.optionsWithSpecifier(Required)
        )
        self.assertEqual(
                set(['int2', 'int3', 'str2', 'str3']),
                m.paramsWithSpecifier(Required)
        )
        self.assertEqual(
                set(['int1', 'list', 'str1']),
                m.optionsWithoutSpecifier(Required)
        )
        self.assertEqual(
                set(['int1', 'list', 'str1']),
                m.paramsWithoutSpecifier(Required)
        )
        self.assertEqual(
                set(['int3', 'str3']),
                m.optionsWithSpecifier(Multiple)
        )
        self.assertEqual(
                set(['int3', 'str3']),
                m.paramsWithSpecifier(Multiple)
        )
        self.assertEqual(
                set([Required, Multiple]),
                m.specifiers('str3')
        )
        self.assertEqual(
                (ListOf, [Integer, '+']),
                m.conversion('list')
        )
    
    def testValidate(self):
        m = OptionManager(self.spec_val)
        s = OptionStack(m)
        # Everything is allright
        values = self.val[:]
        s[:] = values
        self.assert_(s.validate())

        # Specifying more then 1 value to non-Multiple option
        values += [
            ('int2', '4', 'source', 'desc'),
        ]
        s[:] = values
        self.assertRaises(
                OptionError,
                s.validate,
        )
        del values[-1]

        # Unknown option in input
        values += [
            ('unknown', '4', 'source', 'desc'),
        ]
        s[:] = values
        self.assertRaises(
                OptionError,
                s.validate,
        )
        del values[0]
        del values[-1]

        # Everything is allright
        s[:] = values
        self.assert_(s.validate())
        values = [
            ('int2', '2', 'source', 'desc'),
            ('int3', '6', 'source', 'desc'),
        ]
        s[:] = values
        self.assert_(s.validate())
        del values[:]
        # Missing Required options
        s[:] = values
        self.assertRaises(
                OptionError,
                s.validate, 
        )

    def testConversion(self):
        m = OptionManager(self.spec_val)
        s = OptionStack(m)
        values = self.val[:]
        s[:] = values
        self.assertEqual(
                {'int1':1, 'int2':2, 'int3':[3,6]},
                s.getObjects(),
        )
        values.reverse()
        s[:] = values
        self.assertEqual(
                {'int1':1, 'int2':2, 'int3':[6,3]},
                s.getObjects(),
        )
        del values[0]
        s[:] = values
        self.assertEqual(
                {'int1':1, 'int2':2, 'int3':[3]},
                s.getObjects(),
        )

    def testConversionMultiSources(self):
        m = OptionManager(self.spec_multi)
        s = OptionStack(m)
        values = self.multi[:]
        s[:] = values
        self.assertEqual(
                {'int1':1, 'int2':[2,3,4], 'int3':[5,6]},
                s.getObjects(),
        )
        values += [
            ('int2', '5', 'C', 'desc'),
            ('int3', '7', 'C', 'desc'),
        ]
        s[:] = values
        self.assertEqual(
                {'int1':1, 'int2':[2,3,4,5], 'int3':[7]},
                s.getObjects(),
        )
    
    def testConversionObjects(self):
        m = OptionManager(self.spec_multi)
        s = OptionStack(m)
        values = self.multi2[:]
        s[:] = values
        self.assertEqual(
                {'int1':1, 'int2':[2,3,1.4], 'int3':[1.5,1.6]},
                s.getObjects(),
        )

class OptionManagerHierTest(unittest.TestCase):
    spec = {
        'int.int1': Integer,
        'int.int2': (Required, Integer),
        'int.int3': (Required, Multiple, Integer),
        'some.other.int': Integer,
        'list': (ListOf, Integer, '+'),
        'str.str1': String,
        'str.str2': (Required, String),
        'str.str3': (Required, Multiple, String),
    }

    spec_val = {
        'int.int1': Integer,
        'int.int2': (Multiple, Integer),
        'str.str1': String,
        'str.str2': (Multiple, String),
        'xxx.int1': (FullParam, Integer),
        'number': Float,
    }

    val = [
        ('int1', '1', 'A', '...'),
        ('int2', '1', 'A', '...'),
        ('int2', '2', 'A', '...'),
        ('int2', '3', 'A', '...'),
        ('str1', 'ABC', 'A', '...'),
        ('str2', 'XYZ', 'A', '...'),
        ('str2', 'OPQ', 'A', '...'),
        ('xxx_int1', '42', 'A', '...'),
        ('number', '3.14', 'A', '...'),
    ]

    spec_hier = {
        'a.b.a': String,
        'a.b.b': String,
        'a.c': String,
        'a.d': String,
        'x': String,
        'y': (Multiple, String),
        'z': String,
        'q.m': String,
        'q.n': String,
    }

    def testQueries(self):
        m = OptionManager(self.spec)
        self.assertEqual(
                set(['int', 'int1', 'int2', 'int3', 'list', 'str1', 'str2',
                    'str3']),
                m.options()
        )
        self.assertEqual(
                set(['some.other.int', 'int.int1', 'int.int2', 'int.int3',
                    'list', 'str.str1', 'str.str2', 'str.str3']),
                m.params()
        )
        self.assertEqual(
                set(['int2', 'int3', 'str2', 'str3']),
                m.optionsWithSpecifier(Required)
        )
        self.assertEqual(
                set(['int.int2', 'int.int3', 'str.str2', 'str.str3']),
                m.paramsWithSpecifier(Required)
        )
        self.assertEqual(
                set(['int', 'int1', 'list', 'str1']),
                m.optionsWithoutSpecifier(Required)
        )
        self.assertEqual(
                set(['some.other.int', 'int.int1', 'list', 'str.str1']),
                m.paramsWithoutSpecifier(Required)
        )
        self.assertEqual(
                set(['int3', 'str3']),
                m.optionsWithSpecifier(Multiple)
        )
        self.assertEqual(
                set(['int.int3', 'str.str3']),
                m.paramsWithSpecifier(Multiple)
        )
        self.assertEqual(
                set([Required, Multiple]),
                m.specifiers('str.str3')
        )
        self.assertEqual(
                (ListOf, [Integer, '+']),
                m.conversion('list')
        )

    def testFullParam(self):
        s = self.spec.copy()
        s['long.int3'] = (Required, Multiple, Integer)
        self.assertRaises(
                ValueError,
                OptionManager, s
        )
        s['long.int3'] = (FullParam, Required, Multiple, Integer)
        m = OptionManager(s)
        self.assertEqual(
                set(['int', 'int1', 'int2', 'int3', 'list', 'long_int3', 'str1', 'str2', 'str3']),
                m.options()
        )

    def testConversionObjects(self):
        m = OptionManager(self.spec_val)
        s = OptionStack(m)
        s[:] = self.val
        self.assertEqual(
                {'int': {'int1': 1, 'int2': [1, 2, 3]},
                 'str': {'str1': 'ABC', 'str2': ['XYZ', 'OPQ']},
                 'xxx': {'int1': 42},
                 'number': 3.14,
                },
                s.getObjects(),
        )

    def testParamHierarchy(self):
        m = OptionManager(self.spec_hier)
        self.assertEqual(
                set(['x', 'y', 'z']),
                m.paramsAbove(1),
        )
        self.assertEqual(
                m.params() - m.paramsAbove(1),
                m.paramsBelow(1),
        )
        self.assertEqual(
                set(['a.b.a', 'a.b.b', 'a.c', 'a.d']),
                m.paramsChildren('a'),
        )

class OptionManagerAliasTest(unittest.TestCase):
    spec = {
        'a': Integer,
        'b': Integer,
        'y.a': OptionAlias,
        'y.b': OptionAlias,
        'y.x.a': OptionAlias,
        'y.x.b': OptionAlias,
    }

    val = [
        ('a', '1', 'A', '...'),
        ('b', '2', 'A', '...'),
    ]

    def testQueries(self):
        m = OptionManager(self.spec)
        self.assertEqual(
            m.aliases,
            set(['y.a', 'y.b', 'y.x.a', 'y.x.b']),
        )
        self.assertEqual(
            m.options(),
            set(['a', 'b']),
        )
        self.assertEqual(
            m.params(),
            set(['a', 'b', 'y.a', 'y.b', 'y.x.a', 'y.x.b']),
        )
        self.assertEqual(
            m.optionToParam('a'),
            'a'
        )
        self.assertEqual(
            m.optionToAliases('a'),
            set(['a', 'y.a', 'y.x.a']),
        )
        self.assertEqual(
            m.paramToOption('y.x.a'),
            'a'
        )

    def testValues(self):
        m = OptionManager(self.spec)
        s = OptionStack(m)
        s[:] = self.val
        self.assertEqual(
                {'y': {'x': {'a': 1,
                             'b': 2,
                            },
                       'a': 1,
                       'b': 2,
                      },
                 'a': 1,
                 'b': 2,
                },
                s.getObjects()
        )
        s.disable(m.paramsChildren('y.x'))
        self.assertEqual(
                {'y': {'a': 1,
                       'b': 2,
                      },
                 'a': 1,
                 'b': 2,
                },
                s.getObjects()
        )
        s.disableAll()
        s.enable(['y.x.a', 'y.b'])
        self.assertEqual(
                {'y': {'x': {'a': 1}, 'b': 2}},
                s.getObjects()
        )

class OptionManagerPriorTest(unittest.TestCase):
    class Collector(object):
        value = []   # Initial collector value
        conv = int   # collector conversion function
        def collect(self, obj):
            self.value = self.value + [obj]
        def __call__(self, obj):
            obj = self.conv(obj)
            self.collect(obj)
            return obj

    def testPrior(self):
        Collector = self.Collector()
        spec = {
            'int1': (Multiple, Collector),
            'int2': (Multiple, Collector),
            'int3': (Prior, Multiple, Collector),
        }
        m = OptionManager(spec)
        s = OptionStack(m)
        s[:] = [
            ('int1', '1', 'xxx', 'yyy'),
            ('int2', '2', 'xxx', 'yyy'),
            ('int1', '3', 'xxx', 'yyy'),
            ('int2', '4', 'xxx', 'yyy'),
            ('int3', '5', 'xxx', 'yyy'),
            ('int2', '6', 'xxx', 'yyy'),
            ('int3', '7', 'xxx', 'yyy'),
            ('int1', '8', 'xxx', 'yyy'),
            ('int2', '9', 'xxx', 'yyy'),
        ]
        objects = s.getObjects()
        self.assertEqual(
                objects,
                {'int1': [1, 3, 8],
                 'int2': [2, 4, 6, 9],
                 'int3': [5, 7]
                }
        )
        self.assertEqual(
                Collector.value,
                # Values 5 and 7 are values with Prior option, therefore they
                # are at the beginning of the list
                [5, 7,    1, 2, 3, 4, 6, 8, 9]
        )

class OptionTreeTest(unittest.TestCase):
    def testTree1(self):
        t = _OptionTree(None)
        t['a'] = 1
        t['b'] = 2
        t['c'] = 3
        t['x.a'] = 10
        t['x.b'] = 20
        t['x.y.a'] = 100
        t['x.z.b'] = 200
        t['y.c'] = 30
        self.assertEqual(
                t.nested(),
                {'a': 1,
                 'b': 2,
                 'c': 3,
                 'x': {
                    'a': 10,
                    'b': 20,
                    'y': {'a': 100},
                    'z': {'b': 200},
                 },
                 'y': {'c': 30}
                }
        )
        del t['y.c']
        self.assertEqual(
                t.nested(),
                {'a': 1,
                 'b': 2,
                 'c': 3,
                 'x': {
                    'a': 10,
                    'b': 20,
                    'y': {'a': 100},
                    'z': {'b': 200},
                 },
                }
        )
        self.assertEqual(
                t.nested('x'),
                {'a': 10,
                 'b': 20,
                 'y': {'a': 100},
                 'z': {'b': 200},
                }
        )

    def testTree2(self):
        t = _OptionTree(None)
        t['a'] = 'BAD'
        t['a.b'] = 'BAD'
        t['a.b.c'] = 'OK'
        self.assertRaises(
                ValueError,
                t.nested
        )
        t = _OptionTree(None)
        t['a.b'] = 'BAD'
        t['a.b.c'] = 'OK'
        self.assertRaises(
                ValueError,
                t.nested
        )
        t = _OptionTree(None)
        t['a'] = 'BAD'
        t['a.b.c'] = 'OK'
        self.assertRaises(
                ValueError,
                t.nested
        )

class OptionStackTest(unittest.TestCase):
    spec_hier = {
        'a.b.a': (Required, Integer),
        'a.b.b': Integer,
        'a.c': (Required, Integer),
        'a.d': Integer,
        'x': (Required, Integer),
        'y': Integer,
        'z': Integer,
        'q.m': (Required, Integer),
        'q.n': (Multiple, Integer),
        'q.o': (Multiple, Integer),
    }

    val_hier = [
        ('a', '1', 'source', 'subsource'),
        ('b', '2', 'source', 'subsource'),
        ('c', '3', 'source', 'subsource'),
        ('d', '4', 'source', 'subsource'),
        ('x', '5', 'source', 'subsource'),
        ('y', '6', 'source', 'subsource'),
        ('z', '7', 'source', 'subsource'),
        ('m', '8', 'source', 'subsource'),
        ('n', '9', 'source', 'subsource'),
        ('n', '10', 'source', 'subsource'),
    ]

    val_dict_hier = {
        'a': '1',
        'b': '2',
        'c': '3',
        'd': '4',
        'x': '5',
        'y': '6',
        'z': '7',
        'm': '8',
        'n': ['9', '10'],
        'o': '11',
    }

    def testStack1(self):
        m = OptionManager(self.spec_hier)
        s = OptionStack(m)
        self.assertEqual(
                m.params(),
                s.enabled
        )
        s.disable(m.paramsBelow(1))
        self.assertEqual(
                set(['x', 'y', 'z']),
                s.enabled,
        )
        s.enable(m.paramsChildren('a.b'))
        self.assertEqual(
                set(['x', 'y', 'z', 'a.b.a', 'a.b.b']),
                s.enabled,
        )
        s.enable(m.paramsChildren('a'))
        self.assertEqual(
                set(['x', 'y', 'z', 'a.b.a', 'a.b.b', 'a.c', 'a.d']),
                s.enabled,
        )
        s.disableAll()
        self.assertEqual(
                set(),
                s.enabled,
        )
        s.enable(m.paramsAbove(2))
        self.assertEqual(
                set(['x', 'y', 'z', 'a.c', 'a.d', 'q.m', 'q.n', 'q.o']),
                s.enabled,
        )
        self.assertEqual(
                set(['a.b.a', 'a.b.b']),
                s.disabled,
        )
        # Unknown parameter
        self.assertRaises(
                OptionError,
                s.enable, 'unknown.option'
        )
        # Enable parameter tree which cannot be enabled
        self.assertRaises(
                OptionError,
                s.enable, 'a.b'
        )

    def testStack2(self):
        m = OptionManager(self.spec_hier)
        s = OptionStack(m)
        s[:] = self.val_hier
        s.disable(m.paramsBelow(1))
        self.assertEqual(
                {'x': 5, 'y': 6, 'z': 7},
                s.popObjects(),
        )
        self.assertEqual(
                {},
                s.popObjects(),
        )
        s.enable(m.paramsChildren('a'))
        self.assertEqual(
                {'a': {'b': {'a': 1, 'b': 2}, 'c': 3, 'd': 4}},
                s.popObjects(),
        )
        self.assertEqual(
                {},
                s.popObjects(),
        )
        # Enable already processed parameter
        s.enable(['a.b.a'])
        self.assertRaises(
                OptionError,
                s.popObjects,
        )
        s.disable(['a.b.a'])
        self.assertEqual(
                {},
                s.popObjects(),
        )
        s.enable(['x'])
        self.assertRaises(
                OptionError,
                s.popObjects,
        )
        # There are some items in s
        self.assert_(s)
        # Clear this items
        s.clear()
        # There is nothing
        self.assert_(not s)

    def testAddObjects(self):
        m = OptionManager(self.spec_hier)
        s = OptionStack(m)
        s[:] = self.val_hier
        self.assertEqual(
                {'a': {'b': {'a': 1, 
                             'b': 2},
                       'c': 3, 
                       'd': 4},
                 'q': {'m': 8,
                       'n': [9, 10]},
                 'x': 5,
                 'y': 6,
                 'z': 7,},
                s.popObjects()
        )

        self.assertEqual(0, len(s))

        s.enableAll()
        s.addObjects(self.val_dict_hier)
        self.assertEqual(
                {'a': {'b': {'a': 1, 
                             'b': 2},
                       'c': 3, 
                       'd': 4},
                 'q': {'m': 8,
                       'n': [9, 10],
                       'o': [11]},
                 'x': 5,
                 'y': 6,
                 'z': 7,},
                s.popObjects()
        )

class SimpleScriptTest(unittest.TestCase):
    class MyScript(SimpleScript):
        options = {
            'arg1': Integer,
            'arg2': (Multiple, Float),
        }
        def main(self, arg1=0, arg2=[]):
            self.arg1 = arg1
            self.arg2 = arg2
            return [x*arg1 for x in arg2]
        def createExtractors(self, **kwargs):
            self._extractors = [SimpleScriptTest.MyExtractor()]
    
    class MyExtractor(Extractor):
        def getSource(self):
            return self._source
        def setSource(self, source):
            self._source = source
        def getSourceName(self):
            return 'argv'
        def extract(self, state):
            state.extend([
                ('arg1', '11', 'argv', 'desc'),
                ('arg2', '22', 'argv', 'desc'),
                ('arg2', '23', 'argv', 'desc'),
            ])
        def setManager(self, manager):
            self._manager = manager

    def testScript(self):
        myscript = self.MyScript()
        myscript.run()
        self.assertEqual(myscript.arg1, 11)
        self.assertEqual(myscript.arg2, [22,23])
    
    def testSources(self):
        myscript = self.MyScript()
        sources = {'argv': 'foo1 foo2 foo3'}
        myscript.setSources(sources)
        self.assertEqual(
                sources,
                myscript.getSources()
        )
        sources2 = {'argv': 'x y z'}
        myscript.run(sources2)

        # SimpleScript.run(sources) restores previous sources
        self.assertEqual(
                sources,
                myscript.getSources()
        )

    def testExtractors(self):
        myscript = self.MyScript()
        for e in myscript.getExtractors():
            self.assertEqual(
                    myscript.getManager(),
                    e._manager
            )

class SimpleScriptTest2(unittest.TestCase):
    class MyScript(SimpleScript):
        options = {
            'option1': (Required, Integer),
            'option2': (Multiple, Integer),
            'option3': (EnvVar, JoinSources, Integer),
            'option4': (EnvVar, Integer),
        }

        shortOpts = {'o': 'option3'}
        posOpts = ['option1', 'option2', Ellipsis, 'option4']
        envPrefix = [None, 'SCRIPT_']

        def main(self, **kwargs):
            self.kwargs = kwargs

    def testScript1(self):
        s = self.MyScript()
        s.setSources({
            'argv': '1 2 3 4 5'.split(),
            'env': {},
        })
        s.run()
        self.assertEqual(
                {'option1': 1, 'option2': [2, 3, 4], 'option4': 5},
                s.kwargs,
        )

    def testScript2(self):
        s = self.MyScript()
        s.setSources({
            'argv': '-o 3 1 2 3 4 5'.split(),
            'env': {},
        })
        s.run()
        self.assertEqual(
                {'option1': 1, 'option2': [2, 3, 4], 'option3': [3], 'option4': 5},
                s.kwargs,
        )

    def testScript3(self):
        s = self.MyScript()
        s.setSources({
            'argv': '-o 3 1 2 3 4 5'.split(),
            'env': {'SCRIPT_OPTION3': '30:31', 'OPTION3': '50'},
        })
        s.run()
        self.assertEqual(
                {'option1': 1, 'option2': [2, 3, 4], 'option3': [50, 30, 31, 3], 'option4': 5},
                s.kwargs,
        )

    def testScript4(self):
        s = self.MyScript()
        s.setSources({
            'argv': '-o 3 1 2 3 4 5'.split(),
            'env': {'SCRIPT_OPTION3': '30:31', 'OPTION3': '50'},
            'pyfiles': 'pyfiles/myscript.py',
        })
        s.run()
        self.assertEqual(                                   #    vv ENVIRON  vv PYFILES vv CMDLINE
                {'option1': 1, 'option2': [2, 3, 4], 'option3': [50, 30, 31, 1000, 1001, 3], 'option4': 5},
                s.kwargs,
        )
        self.assertEqual(
                set(['pyfiles/myscript.py']),
                s.getExtractors()[1].getProcessedFiles()
        )

class ExScriptSimpleTest(unittest.TestCase):
    class MyScript(ExScript):
        options = {
            'command': ExScript.CommandParam,
            'opt1': Integer,
            'opt2': (JoinSources, Integer),
            'tree.opt3': (Multiple, Integer),
        }
        posOpts = ['command', Ellipsis]
        debugMain = True
        register = {}
        commands = []
        def main(self, command=[], **kwargs):
            self.register = self.register.copy()
            self.register.update(kwargs)
            return super(ExScriptSimpleTest.MyScript, self).main(command=command)
        def invokeCommand(self, command):
            self.commands = self.commands + [command]

    def testBadCommands(self):
        # You cannot use these parameters in ExScript
        bad_params = ['pyfile', 'logging.verbose_level', 'logging.verbose']
        orig_options = self.MyScript.options.copy()
        for param in bad_params:
            self.MyScript.options.update({param: String})
            self.assertRaises(
                    ValueError,
                    self.MyScript
            )
            self.MyScript.options = orig_options.copy()   # restore original options

    def testPyFiles(self):
        e = self.MyScript()
        e.sources = {
            'argv': '--pyfile=pyfiles/pyfile1.py --pyfile=pyfiles/pyfile2.py'.split()
        }
        e.run()
        self.assertEqual(
                set(['pyfiles/pyfile1.py', 'pyfiles/pyfile2.py']),
                e._extractor_pyfiles.processedFiles,
        )
        self.assertEqual(
                {'opt1': 201, 'tree': {'opt3': [203, 204]}, 'opt2': [102, 202]},
                e.register
        )

    def testCommands(self):
        e = self.MyScript()
        e.sources = {
            'argv': 'command1 command2 command3 command4'.split()
        }
        e.run()
        self.assertEqual(
                ['command1', 'command2', 'command3', 'command4'],
                e.commands,
        )

class ExScriptTest(unittest.TestCase):
    class MyScript(ExScript):
        options = {
            'command': ExScript.CommandParam,
            'cmd1.opt1': (Required, Integer),
            'cmd1.opt2': (JoinSources, Integer),
            'cmd2.opt3': (Multiple, Integer)
        }
        posOpts = ['command', {'cmd1': ['opt1', 'opt2'],
                               'cmd2': 'opt3'
                              }
                  ]
        debugMain = True

        @ExScript.command
        def cmd1(self, **kwargs):
            self.cmd1_args = kwargs

        @ExScript.command
        def cmd2(self, **kwargs):
            self.cmd2_args = kwargs

    def testCommands(self):
        e = self.MyScript()

        self.assertEqual(e.commandOption, 'command')

        e.sources = {
            'argv': '--pyfile=pyfiles/pyfile1.py --pyfile=pyfiles/pyfile2.py cmd1'.split()
        }
        e.run()
        self.assertEqual(
                {'opt1': 201, 'opt2': [102, 202]},
                e.cmd1_args,
        )

        # Set only another sources of the SAME instance as previous test
        e.sources = {
            'argv': '--pyfile=pyfiles/pyfile2.py cmd1'.split()
        }
        e.run()
        self.assertEqual(
                {'opt1': 201, 'opt2': [202]},
                e.cmd1_args,
        )

    def testInvokeCommands(self):
        e = self.MyScript()
        e.sources = {
            'argv': '--opt1=123 --opt2=234 --opt2=345 cmd1'.split()
        }
        e.createState()
        e.invokeCommand('cmd1')
        self.assertEqual(
                {'opt1': 123, 'opt2': [234, 345]},
                e.cmd1_args,
        )
        self.assertRaises(
                OptionError,
                e.invokeCommand, 'cmd1', opt3=[12345]
        )

        e.sources = {
            'argv': '--opt2=234'.split()
        }
        e.createState()
        self.assertRaises(
                OptionError,
                e.invokeCommand, 'cmd1'
        )
        e.invokeCommand('cmd1', opt1=123)
        self.assertEqual(
                {'opt1': 123, 'opt2': [234]},
                e.cmd1_args
        )

    def testUnknownCommand(self):
        e = self.MyScript()
        e.sources = {
            'argv': ['unknown_cmd']
        }
        self.assertRaises(
                ValueError,
                e.run,
        )

    def testCommandPosOptions(self):
        e = self.MyScript()
        self.assertEqual(e.cmdPosOpts, {'cmd1': ['opt1', 'opt2'], 'cmd2': 'opt3'})
        e.sources = {
            'argv': 'cmd1 123 234'.split()
        }
        e.run()

class ScriptTest(unittest.TestCase):
    class MyScript(Script):
        options = {
            'foo': (Multiple, String),
        }
        posOpts = ['foo', Ellipsis]
        debugMain = True

        def main(self, foo=[]):
            pass

    def testVerbosity(self):
        e = self.MyScript()
        e.sources = {
            'argv': '-vvv'.split()
        }
        e.run()
        self.assert_(0 < e.logger.getEffectiveLevel())
        e.sources = {
            'argv': '--verbose-level=DEBUG'.split()
        }
        e.run()
        self.assertEqual(logging.DEBUG, e.logger.getEffectiveLevel())
        e.sources = {
            'argv': '--verbose-level=UNKNOWN'.split()
        }
        self.assertRaises(
                ValueError,
                e.run
        )

class ExScriptAliasesTest(unittest.TestCase):
    class MyScript(ExScript):
        options = {
            'command': ExScript.CommandParam,
            'cmd1.int': Integer,
            'cmd1.files': (Required, Multiple, String),
            'cmd2.files': OptionAlias,
        }
        posOpts = ['command', Ellipsis]
        debugMain = True

        @ExScript.command
        def cmd1(self, **kwargs):
            self.cmd1_args = kwargs

        @ExScript.command
        def cmd2(self, **kwargs):
            self.cmd2_args = kwargs

    class MyScript2(MyScript):
        options = {
            'command': ExScript.CommandParam,
            'files': (Required, Multiple, String),
            'cmd1.int': Integer,
            'cmd1.files': OptionAlias,
            'cmd2.files': OptionAlias,
        }

        def main(self, files, **kwargs):
            self.main_args = {'files': files}
            return ExScript.main(self, **kwargs)

    def testSharedOptions(self):
        e = self.MyScript2()
        e.sources = {
            'argv': '--files=xxx --files=yyy --files=zzz --int=3 cmd1 cmd2'.split()
        }
        e.run()
        self.assertEqual(
                {'files': ['xxx', 'yyy', 'zzz']},
                e.main_args,
        )
        self.assertEqual(
                {'files': ['xxx', 'yyy', 'zzz'], 'int': 3},
                e.cmd1_args,
        )
        self.assertEqual(
                {'files': ['xxx', 'yyy', 'zzz']},
                e.cmd2_args,
        )

    def testSharedOptionsBetweenCommands(self):
        e = self.MyScript()
        e.sources = {
            'argv': '--files=xxx --files=yyy --files=zzz --int=3 cmd1 cmd2'.split()
        }
        e.run()
        self.assertEqual(
                {'files': ['xxx', 'yyy', 'zzz'], 'int': 3},
                e.cmd1_args,
        )
        self.assertEqual(
                {'files': ['xxx', 'yyy', 'zzz']},
                e.cmd2_args,
        )

class AllExtractorTest(unittest.TestCase):
    spec = {
        'arg1': (Required, Integer),
        'arg2': (Multiple, Integer),
        'arg3': Flag,
        'tree.arg4': Integer,
    }

    def testExtractors(self):
        m = OptionManager(self.spec)
        for cls in [extractors.CmdlineExtractor, extractors.PyFileExtractor,
                    extractors.EnvironExtractor]:
            e = cls()
            e.setManager(m)
            # Test setting of protected attribute _manager
            self.assertEqual(m, e._manager)
            # Test setting of source property to None in __init__()
            self.assertEqual(None, e.getSource())

class CmdlineExtractorTest(unittest.TestCase):
    short_opts = {
        'a': 'arg1',
        'b': 'arg2',
        'c': 'arg3',
    }

    spec = {
        'pos1': (Required, Integer),
        'pos2': Integer,
        'pos3': (Multiple, Integer),
        'tree.arg': Integer,
    }

    pos_opts = ['pos1', 'pos2', 'pos3', Ellipsis, 'arg']

    def testQueries(self):
        m = OptionManager(AllExtractorTest.spec)
        e = extractors.CmdlineExtractor(self.short_opts, self.pos_opts)
        e.setManager(m)
        self.assertEqual(
                set(['arg1', 'arg2', 'arg4']),
                e._optionsWithArg()
        )
        self.assertEqual(
                sorted('a:b:c'),
                sorted(e._getoptShort()),
        )
        self.assertEqual(
                sorted(['arg1=', 'arg2=', 'arg3', 'arg4=']),
                sorted(e._getoptLong())
        )
        self.assertEqual(
                'argv',
                e.getSourceName()
        )
    
    def testExtractionOptions(self):
        m = OptionManager(AllExtractorTest.spec)
        s = OptionStack(m)
        e = extractors.CmdlineExtractor(self.short_opts)
        e.setManager(m)
        source = ['--arg1=1', '--arg2=2', '--arg3']
        e.setSource(source)
        e.extract(s)
        self.assertEqual(
                {'arg1': 1, 'arg2': [2], 'arg3': True},
                s.getObjects(),
        )
        source = ['-a1', '-b2', '-c']
        e.setSource(source)
        s.clear()
        e.extract(s)
        self.assertEqual(
                {'arg1': 1, 'arg2': [2], 'arg3': True},
                s.getObjects(),
        )
        source = ['--arg1=1', '--arg2=2', '--arg2=3']
        e.setSource(source)
        s.clear()
        e.extract(s)
        self.assertEqual(
                {'arg1': 1, 'arg2': [2,3]},
                s.getObjects(),
        )
        source = ['-a1', '-b2', '-b3']
        e.setSource(source)
        s.clear()
        e.extract(s)
        self.assertEqual(
                {'arg1': 1, 'arg2': [2,3]},
                s.getObjects(),
        )
        # XXX: Why are the exceptions raised?
        source = ['--arg2=2', '--arg2=3']
        e.setSource(source)
        s.clear()
        e.extract(s)
        self.assertRaises(
                OptionError,
                s.getObjects,
        )
        source = ['--arg1=2', '-a3']
        e.setSource(source)
        s.clear()
        e.extract(s)
        self.assertRaises(
                OptionError,
                s.getObjects, 
        )
        
    def testExtractionPositional(self):
        m = OptionManager(self.spec)
        s = OptionStack(m)
        e = extractors.CmdlineExtractor(self.short_opts, self.pos_opts)
        e.setManager(m)
        source = ['1', '2', '3', '4', '5']
        e.setSource(source)
        e.extract(s)
        self.assertEqual(
                {'tree': {'arg': 5}, 'pos2': 2, 'pos3': [3, 4], 'pos1': 1},
                s.getObjects(),
        )
        source = ['1']
        e.setSource(source)
        s.clear()
        e.extract(s)
        self.assertEqual(
                {'pos1': 1},
                s.getObjects(),
        )
        source = []
        e.setSource(source)
        s.clear()
        e.extract(s)
        self.assertRaises(
                OptionError,
                s.getObjects,
        )

        e = extractors.CmdlineExtractor(pos_opts = ['pos3', Ellipsis, 'pos2', 'pos1', 'arg'])
        e.setManager(m)
        source = ['1', '2', '3', '4', '5']
        e.setSource(source)
        s.clear()
        e.extract(s)
        self.assertEqual(
                {'tree': {'arg': 5}, 'pos1': 4, 'pos2': 3, 'pos3': [1, 2]},
                s.getObjects(),
        )
        source = ['3', '4', '5']
        e.setSource(source)
        s.clear()
        e.extract(s)
        self.assertEqual(
                {'tree': {'arg': 5}, 'pos1': 4, 'pos2': 3},
                s.getObjects(),
        )
        source = ['4', '5']
        e.setSource(source)
        s.clear()
        e.extract(s)
        self.assertRaises(
                OptionError,
                s.getObjects,
        )
    
    def testBadSpecs(self):
        self.assertRaises(
                ValueError,
                extractors.CmdlineExtractor, pos_opts = [Ellipsis, 'bad1']
        )
        self.assertRaises(
                ValueError,
                extractors.CmdlineExtractor, pos_opts = ['bad1', Ellipsis, 'bad2', Ellipsis]
        )
        self.assertRaises(
                ValueError,
                extractors.CmdlineExtractor, pos_opts = ['bad', Ellipsis], short_opts = {'b': 'bad'}
        )
        self.assertRaises(
                ValueError,
                extractors.CmdlineExtractor, short_opts = {'bad': 'too_many_chars_for_shor_opt'}
        )

    def testUnderscores(self):
        spec = {
            'flag_option': Flag,
            'other_option': Integer,
        }
        short_opts = {'o': 'other_option'}
        m = OptionManager(spec)
        s = OptionStack(m)
        e = extractors.CmdlineExtractor(short_opts=short_opts)
        e.setManager(m)
        self.assertEqual(
                sorted(['flag-option', 'other-option=']),
                sorted(e._getoptLong()),
        )
        argv = '--flag-option --other-option=3 -o2'.split()
        e.setSource(argv)
        s.clear()
        e.extract(s)
        self.assertEqual(
                [('flag_option', 'true', 'argv', '--flag-option'),
                 ('other_option', '3', 'argv', '--other-option'),
                 ('other_option', '2', 'argv', '-o'),
                ],
                s,
        )

class PyFileExtractorTest(unittest.TestCase):
    files = ['pyfiles/pyfile1.py', 'pyfiles/pyfile2.py']
    badfiles = ['pyfiles/pyfile_e1.py', 'pyfiles/pyfile_e2.py', 'pyfiles/pyfile_e3.py']
    testglobals = ['pyfiles/pyfile_globals.py']

    spec = {
        'opt1': (Required, Integer),
        'opt2': (JoinSources, Integer),
        'tree.opt3': (Multiple, Integer),
    }

    def assertFilesExists(self, files):
        if not issequence(files):
            files = [files]
        for file in files:
            self.assert_(isfile(file), 'Non-existent file: %r' % file)

    def testExtraction(self):
        m = OptionManager(self.spec)
        s = OptionStack(m)
        e = extractors.PyFileExtractor()
        e.setManager(m)

        self.assertFilesExists(self.files)
        e.setSource(self.files)
        s.clear()
        e.extract(s)
        self.assertEqual(
                {'opt1': 201, 'opt2': [102, 202], 'tree': {'opt3': [203, 204]}},
                s.getObjects(),
        )

        for file in self.badfiles:
            self.assertFilesExists(file)
            e.setSource(file)
            s.clear()
            e.extract(s)
            self.assertRaises(
                    OptionError,
                    s.getObjects,
            )
    
    def testGlobals(self):
        globals = {'global1': 12, 'global2': 13}
        self.assertFilesExists(self.testglobals)
        m = OptionManager(self.spec)
        s = OptionStack(m)
        e = extractors.PyFileExtractor(globals)
        e.setManager(m)
        e.setSource(self.testglobals)
        s.clear()
        e.extract(s)
        self.assertEqual(
                {'opt1': 12*13},
                s.getObjects(),
        )

class EnvironTest(unittest.TestCase):
    spec = {
        'var1': (EnvVar, Integer),
        'var2': (EnvVar, Multiple, Integer),
        'tree.var3': (EnvVar, JoinSources, Multiple, Integer),
    }

    def testExtraction(self):
        m = OptionManager(self.spec)
        s = OptionStack(m)
        e = extractors.EnvironExtractor()
        e.setManager(m)

        e.setSource({'VAR1': '1', 'VAR2': '2'})
        e.extract(s)
        self.assertEqual(
                {'var1': 1, 'var2': [2]},
                s.getObjects(),
        )

        e.setSource({'VAR1': '1', 'VAR2': '2:3:4'})
        s.clear()
        e.extract(s)
        self.assertEqual(
                {'var1': 1, 'var2': [2, 3, 4]},
                s.getObjects(),
        )

        e.setEnvPrefix([None, 'MY_', 'YOUR_'])
        e.setSource({'VAR1': '1', 'MY_VAR1': '2', 'YOUR_VAR1': '3'})
        s.clear()
        e.extract(s)
        self.assertEqual(
                {'var1': 3},
                s.getObjects(),
        )

        e.setSource({'VAR3': '1', 'MY_VAR3': '2:3', 'YOUR_VAR3': '4:5'})
        s.clear()
        e.extract(s)
        self.assertEqual(
                {'tree': {'var3': [1,2,3,4,5]}},
                s.getObjects(),
        )

if __name__ == '__main__':
    unittest.main()
