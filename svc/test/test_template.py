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

