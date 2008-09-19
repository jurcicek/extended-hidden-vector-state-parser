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

from svc.egg import PythonEgg
from svc.utils import ADict
import sys
import codecs
import math
from pprint import pprint

def log2(x):
    return math.log(x) / math.log(2)

def NGramIter(n, parent, start_seq=[]):
    if n == 0:
        for i in parent:
            yield ()
    else:
        start_seq = tuple(start_seq)
        it = iter(parent)
        while len(start_seq) < n-1:
            i = it.next()
            start_seq = start_seq + (i,)

        hist = tuple(start_seq)[len(start_seq)-n+1:]
        assert len(hist) == n-1, 'History size doesn\'t match'

        for i in it:
            current = hist + (i,)
            yield current
            hist = current[1:]

class Counts(ADict):
    def __init__(self, n):
        assert n >= 0, 'n must have been greeter than zero'
        super(Counts, self).__init__()
        self.n = n
        self._leftReduced = None
        self._rightReduced = None

    @classmethod
    def fromText(cls, n, txt):
        ret = cls(n)
        for line in txt:
            for ngram in NGramIter(n, line, ['<s>']*(n-1)):
                ret[ngram] += 1.
        return ret
    
    def reduceLeft(self):
        if self._leftReduced is not None:
            return self._leftReduced
        else:
            ret = self.__class__(self.n-1)
            for ngram, count in self.iteritems():
                ngram1 = ngram[1:]
                ret[ngram1] += count
            self._leftReduced = ret
            return ret

    def reduceRight(self):
        if self._rightReduced is not None:
            return self._rightReduced
        else:
            ret = self.__class__(self.n-1)
            for ngram, count in self.iteritems():
                ngram1 = ngram[:-1]
                ret[ngram1] += count
            self._rightReduced = ret
            return ret

EPS = 1e-5

class LM(PythonEgg):
    def __init__(self):
        super(LM, self).__init__()
        self._params = {}
        self._n1hist = set()

    def __getitem__(self, item):
        if item[1] in self._n1hist:
            return self._params.get(item, 0)
        else:
            return 1./646

    @classmethod
    def fromText(cls, n, txt):
        if n == 0:
            return UniformLM.fromText(n, txt)
        else:
            countsN = Counts.fromText(n, txt)
            return cls.fromCounts(countsN)

    @classmethod
    def fromCounts(cls, countsN):
        countsN1 = countsN.reduceRight()

        ret = cls()
        for ngram, count in countsN.iteritems():
            w = ngram[-1]
            hist = ngram[:-1]
            countH = countsN1[hist]
            ret._n1hist.add(hist)
            ret._params[w, hist] = count / countH

        ret._n = countsN.n
        return ret

    def crossEntropy(self, heldout):
        try:
            T = 0.
            H = 0.
            for line in heldout:
                for ngram in NGramIter(self._n, line, ['<s>']*(self._n-1)):
                    w = ngram[-1]
                    hist = ngram[:-1]
                    T += 1
                    H += -log2(self[w, hist])
            return H / T
        except OverflowError:
            return float('inf')

class UniformLM(LM):
    def __getitem__(self, item):
        return self._p

    @classmethod
    def fromText(cls, n, txt):
        if n != 0:
            raise ValueError("UniformLM must have n==0, not %r" % n)
        vocabulary = set()
        for line in txt:
            for token in line:
                vocabulary.add(token)
        ret = cls()
        ret._p = 1. / len(vocabulary)
        ret._vocab = vocabulary
        ret._n = 0
        return ret


class LinearLM(LM):
    def __getitem__(self, item):
        w = item[0]
        hist = item[1]
        ret = 0.
        for n, (model, lmbd) in enumerate(zip(self._models, self._params)):
            histN = hist[len(hist)-n+1:]
            ret += lmbd * model[w, histN]
        return ret

    def em(self, heldout, eps=EPS, debug=False):
        H_old = self.crossEntropy(heldout)
        if debug: print 'lambda_j =', self._params
        if debug: print 'H =', H_old
        i_num = 1
        while True:
            params_old = self._params
            # E-step
            cj = []
            for j, (model, lmbd) in enumerate(zip(self._models, self._params)):
                E = 0
                for line in heldout:
                    for ngram in NGramIter(self._n, line, ['<s>']*(self._n-1)):
                        wi = ngram[-1]
                        if j != 0:
                            hi = ngram[-j:-1]
                        else:
                            hi = ()
                        hi_f = ngram[:-1]
                        assert j == 0 or len(hi) == j-1, 'Bad history length'
                        E += (lmbd*model[wi, hi] / self[wi, hi_f])
                cj.append(E)
            if debug: print 'iter =', i_num
            if debug: print '  c(lambda_j) =', cj

            # M-step
            sum_cj = sum(cj)
            self._params = [c/sum_cj for c in cj]
            if debug: print '  lambda_j_new =', self._params

            H = self.crossEntropy(heldout)
            if debug: print '  H =', H

            # Iteration end
            if H_old - H < eps:
                break
            else:
                H_old = H
            i_num += 1


    @classmethod
    def fromText(cls, n, train, heldout, debug=False):
        ret = cls()
        ret._n = n
        counts = Counts.fromText(n, train)
        m = ret._models = [LM.fromCounts(counts)]
        while counts.n > 1:
            counts = counts.reduceLeft()
            m.insert(0, LM.fromCounts(counts))
        m.insert(0, UniformLM.fromText(0, train))
        ret._params = [1./(n+1.) for i in range(n+1)]
        ret.em(heldout, debug=debug)
        return ret

class BuckLinearLM(LM):
    def __getitem__(self, item):
        w = item[0]
        hist = item[1]
        bucket = self.getBucket(hist)
        ret = 0.
        for n, (model, lmbd) in enumerate(zip(self._models, self._params[bucket])):
            histN = hist[len(hist)-n+1:]
            ret += lmbd * model[w, histN]
        return ret

    def em(self, heldout, eps=EPS, debug=False):
        H_old = self.crossEntropy(heldout)
        if debug: print 'lambda_j ='
        if debug: pprint(self._params)
        if debug: print 'H =', H_old
        i_num = 1
        while True:
            params_old = self._params
            # E-step
            cj = [[0.]*len(self._models) for b in self._params]
            for line in heldout:
                for ngram in NGramIter(self._n, line, ['<s>']*(self._n-1)):
                    wi = ngram[-1]
                    hi_f = ngram[:-1]
                    bucket = self.getBucket(hi_f)
                    for j, model in enumerate(self._models):
                        if j != 0:
                            hi = ngram[-j:-1]
                        else:
                            hi = ()
                        assert j == 0 or len(hi) == j-1, 'Bad history length'
                        lmbd = self._params[bucket][j]
                        cj[bucket][j] += (lmbd*model[wi, hi] / self[wi, hi_f])
            if debug: print 'iter =', i_num

            # M-step
            for idx, c in enumerate(cj):
                sum_c = sum(c)
                if sum_c != 0:
                    self._params[idx] = [k/sum_c for k in c]
            if debug: print 'lambda_j_new ='
            if debug: pprint(self._params)

            H = self.crossEntropy(heldout)
            if debug: print 'H =', H
            if debug: print

            # Iteration end
            if H_old - H < eps:
                break
            else:
                H_old = H
            i_num += 1


    @classmethod
    def fromText(cls, n, n_buck, train, heldout, debug=False):
        ret = cls()
        ret._n = n
        ret._n_buck = n_buck
        ret._models = [LM.fromText(i, train) for i in range(n+1)]
        ret._buckets, ret._params = ret.makeBuckets(n_buck, heldout)
        ret.em(heldout, debug=debug)
        return ret

    def makeBuckets(self, n_buck, heldout):
        n = self._n
        counts = ADict()
        for line in heldout:
            for ngram in NGramIter(n, line, ['<s>']*(n-1)):
                hist = ngram[:-1]
                counts[hist] += 1.
        sum_hist = sum(counts.values())
        f_max = float(sum_hist) / float(n_buck)
        b = [set()]
        b_sum = 0.
        for hist, count in sorted(counts.iteritems(), key=lambda i: i[1], reverse=True):
            if count == 1:
                continue
            if b_sum + count > f_max:
                b.append(set())
                b_sum = 0.
            b[-1].add(hist)
            b_sum += count

        ret = {}
        params = []
        for idx, bucket in enumerate(b):
            params.append([1./(n+1.) for i in range(n+1)])
            for hist in bucket:
                ret[hist] = idx
        if n_buck != 1:
            params.append([1./(n+1.) for i in range(n+1)])
        return ret, params
    
    def getBucket(self, hist):
        return self._buckets.get(hist, -1)


class Tokenizer(PythonEgg):
    def __init__(self, txt):
        super(Tokenizer, self).__init__()
        self.txt = txt

    def __iter__(self):
        for line in self.txt.splitlines():
            line = line.strip()
            if line:
                yield line.split()

    @classmethod
    def fromFile(cls, fn):
        fr = codecs.open(fn, 'r', 'utf-8')
        txt = fr.read()
        fr.close()
        return cls(txt)
    

if __name__ == '__main__':
    train = Tokenizer.fromFile(sys.argv[1])
    #heldout = Tokenizer.fromFile(sys.argv[2])
    #llm4 = BuckLinearLM.fromText(3, 500, train, heldout, debug=True)
    #print lm._models
    #print lm._params
    c3 = Counts.fromText(3, train)
    c2 = Counts.fromText(2, train)
    c1 = Counts.fromText(1, train)
    c0 = Counts.fromText(0, train)
    print c0
    print c2 == c3.reduceLeft()
    print c1 == c2.reduceLeft()
    print c0 == c1.reduceLeft()
