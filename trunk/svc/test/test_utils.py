import unittest

from svc.utils import *

class UtilTest(unittest.TestCase):
    def testSyms(self):
        Foo = sym('Foo')
        self.assert_(Foo == 'Foo', 'sym not equal to string')
        self.assert_(Foo == Foo, 'sym not equal to sym')
        self.assert_('Foo' == Foo, 'string not equal to sym')
        self.assert_(
                hash('Foo') == hash(Foo),
                'hashes of sym and string are not equal'
        )
    
    def testIsStr(self):
        self.assert_(isstr('abc'))
        self.assert_(isstr(u'abc'))
        self.assert_(not isstr(123))

    def testIsSequence(self):
        s1 = 'string'
        s2 = ['list']
        s3 = ['tuple']
        s4 = {'dictionary': 1}
        s5 = 1 # integer
        self.assert_(not issequence(s1))
        self.assert_(issequence(s2))
        self.assert_(issequence(s3))
        self.assert_(issequence(s4))
        self.assert_(not issequence(s5))

    def testSeqIntoDict(self):
        format = ['foo', 'bar', Ellipsis, 'baz']
        s1 = [1, 2, 3, 4, 5]
        self.assertEqual(seqIntoDict(s1, format), {'foo': 1, 'bar': [2, 3, 4], 'baz': 5})
        s2 = [1, 2, 3, 4]
        self.assertEqual(seqIntoDict(s2, format), {'foo': 1, 'bar': [2, 3], 'baz': 4})
        s3 = [1, 2, 3]
        self.assertEqual(seqIntoDict(s3, format), {'foo': 1, 'bar': [2], 'baz': 3})
        s4 = [1, 2]
        self.assertEqual(seqIntoDict(s4, format), {'foo': 1, 'baz': 2})
        s5 = [1]
        self.assertEqual(seqIntoDict(s5, format), {'foo': 1 })
        s6 = []
        self.assertEqual(seqIntoDict(s6, format), {})
        format = ['foo', Ellipsis, 'bar', Ellipsis]
        self.assertRaises(ValueError, seqIntoDict, s1, format)
        format = [Ellipsis, 'bar']
        self.assertRaises(ValueError, seqIntoDict, s1, format)
        format = [Ellipsis]
        self.assertRaises(ValueError, seqIntoDict, s1, format)

        format = []
        self.assertEqual(seqIntoDict(s1, format), {})


if __name__ == '__main__':
    unittest.main()

