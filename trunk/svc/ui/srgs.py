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

import sys
import codecs
from svc.map import SymMap
from svc.utils import ADict
import os
import re
try:
    from xml.etree.ElementTree import parse, ElementTree, XML as ETreeXML, SubElement, Element
except ImportError:
    from elementtree.ElementTree import parse, ElementTree, XML as ETreeXML, SubElement, Element
from math import log10
import urllib
import urlparse
import fnmatch

GARBAGE_WORD = '__garbage__'
GARBAGE_WEIGHT = 0.1

ZERO_EPS = 1e-10

def UniValueError(string):
    if os.name == 'nt':
        string = string.encode('cp1250')
    else:
        string = string.encode('utf-8')
    return ValueError(string)

class FSM(dict):
    #__slots__ = ['s_0', 's_end', '_FSM__remap_idx']

    eps = 'eps'
    epsEdge = (eps,)

    def __init__(self, *args, **kwargs):
        super(FSM, self).__init__(*args, **kwargs)
        self.s_0 = None
        self.s_end = []
        self.__remap_idx = 0

    def copy(self):
        ret = self.__class__()
        for k, v in self.iteritems():
            ret[k] = v
        ret.s_0 = self.s_0
        ret.s_end = self.s_end.copy()
        return ret

    def states(self):
        """Returns set of nodes
        """
        ret = set()
        for f, t in self:
            ret.add(f)
            ret.add(t)
        ret.add(self.s_0)
        ret |= set(self.s_end)
        return ret

    def __remap(self, states, mapping, i):
        if i in mapping:
            return mapping[i]
        old_i = i
        while i in states:
            i = self.__remap_idx
            self.__remap_idx += 1
        states.add(i)
        mapping[old_i] = i
        return i

    def embed(self, fsm):
        """Embeds `fsm` into this fsm

        Returns remapping of start and end states
        """
        my_states = self.states()
        mapping = {}
        s_0_new = self.__remap(my_states, mapping, fsm.s_0)
        for (s0, s1), attrs in fsm.items():
            s0_new = self.__remap(my_states, mapping, s0)
            s1_new = self.__remap(my_states, mapping, s1)
            self[s0_new, s1_new] = attrs
        s_end_new = set(self.__remap(my_states, mapping, i) for i in fsm.s_end)
        return s_0_new, s_end_new

    @classmethod
    def epsbypass(cls, fsm, prob):
        ret = cls()
        ret.s_0 = 0
        s_1, ret.s_end = ret.embed(fsm)
        if prob is not None:
            ret[0, s_1] = cls.epsEdge + (1-prob, )
        else:
            ret[0, s_1] = cls.epsEdge
        for i in ret.s_end:
            if prob is not None:
                ret[0, i] = cls.epsEdge + (prob, )
            else:
                ret[0, i] = cls.epsEdge
        return ret

    @classmethod
    def seriall(cls, fsms):
        if not fsms:
            ret = cls()
            ret.s_0 = 0
            ret.s_end = set([0])
        else:
            ret = cls()
            ret.s_0, ret.s_end = ret.embedseriall(fsms)
            return ret

    def embedseriall(self, fsms):
        """Embeds all arguments into this fsm and joins them serially

        Returns remapping of start and end states
        """
        head = None
        tail = None
        for fsm in fsms:
            join = None
            my_states = self.states()
            mapping = {}
            s_0_new = self.__remap(my_states, mapping, fsm.s_0)
            if head is None:
                head = s_0_new

            if tail:
                #if len(tail) > 1:
                   for i in tail:
                       self[i,s_0_new] = self.epsEdge
                #else:
                #    join = (list(tail)[0], s_0_new)

            for (s0, s1), attrs in fsm.items():
                s0_new = self.__remap(my_states, mapping, s0)
                s1_new = self.__remap(my_states, mapping, s1)
                self[s0_new, s1_new] = attrs
            s_end_new = set(self.__remap(my_states, mapping, i) for i in fsm.s_end)
            tail = s_end_new
            if join:
                self.joinstates(join)

        return head, tail

    @classmethod
    def parallel(cls, fsms, weights=None, open=False):
        ret = cls()
        ret.s_0, ret.s_end = ret.embedparallel(fsms, weights=weights, open=open)
        return ret

    def embedparallel(self, fsms, weights=None, open=False):
        """Embeds all arguments into this fsm and joins them serially

        Returns remapping of start and end states
        """
        if weights is None:
            weights = [None] * len(fsms)
        heads = []
        tails = []
        for fsm, w in zip(fsms, weights):
            join = None
            my_states = self.states()
            mapping = {}
            s_0_new = self.__remap(my_states, mapping, fsm.s_0)
            heads.append((s_0_new, w))

            for (s0, s1), attrs in fsm.items():
                s0_new = self.__remap(my_states, mapping, s0)
                s1_new = self.__remap(my_states, mapping, s1)
                self[s0_new, s1_new] = attrs

            s_end_new = set(self.__remap(my_states, mapping, i) for i in fsm.s_end)

            for i in s_end_new:
                tails.append(i)

        head = self.newnode()
        tail = self.newnode()

        for i, w in heads:
            if w is not None:
                self[head,i] = self.epsEdge + (w, )
            else:
                self[head,i] = self.epsEdge

        if not open:
            for i in tails:
                self[i,tail] = self.epsEdge
            return head, [tail]
        else:
            return head, tails

    @classmethod
    def _convertFromText(cls, map, line):
        if len(line) == 1:
            symbol = line[0]
            weight = None
        elif len(line) == 2:
            symbol, weight = line
        else:
            raise ValueError("More items on line: %s" % ' '.join(line))

        symbol = map.inverse[int(symbol)]
        if weight is not None:
            weight = float(weight)
            return (symbol, weight)
        else:
            return symbol,

    @classmethod
    def _convertToText(cls, map, edge):
        if len(edge) == 0:
            symbol = cls.eps
            symbol = map.add(symbol)
            return '%d' % (symbol,)
        elif len(edge) == 1:
            symbol = edge[0]
            symbol = map.add(symbol)
            return '%d' % (symbol,)
        elif len(edge) == 2:
            symbol, weight = edge
            symbol = map.add(symbol)
            return '%d\t%e' % (symbol, weight)
        else:
            raise ValueError("Edge has more attributes than needed: %r", edge)

    @classmethod
    def _readMaps(cls, fsm_fn, encoding='utf-8'):
        map_fn = os.path.splitext(fsm_fn)[0]+'.isym'
        map = SymMap.readFromFile(map_fn, encoding=encoding)
        return map

    @classmethod
    def _emptyMaps(cls):
        map = SymMap()
        map[cls.eps] = 0
        return map

    @classmethod
    def _writeMaps(cls, fsm_fn, map, encoding='utf-8'):
        map_fn = os.path.splitext(fsm_fn)[0]+'.isym'
        map.writeToFile(map_fn, encoding=encoding)

    @classmethod
    def readFromFile(cls, fn, encoding='utf-8'):
        maps = cls._readMaps(fn, encoding)

        self = cls()
        self.s_end = set()

        fr = file(fn, 'ru')
        for idx, line in enumerate(fr):
            items = line.split()
            if len(items) == 1:
                self.s_end.add(int(items[0]))
                continue
            else:
                s_1, s_2 = items[:2]
                edge = cls._convertFromText(maps, items[2:])

            s_1 = int(s_1)
            s_2 = int(s_2)
            
            if self.s_0 is None:
                self.s_0 = s_1

            self[s_1, s_2] = edge
        fr.close()

        return self

    def writeToFile(self, fn, encoding='utf-8', callback=None):
        maps = self._emptyMaps()

        fw = file(fn, 'wu')

        def writeEdge(edge):
            states, attrs = edge
            attrs = self._convertToText(maps, attrs)
            print >> fw, '%d\t%d\t%s' % (states[0], states[1], attrs)

        def writeEnds(states):
            for i in states:
                print >> fw, unicode(i)

        try:
            edge_0 = None
            for edge in sorted(self.iteritems()):
                if edge[0][0] == self.s_0:
                    edge_0 = edge
                    break
            else:
                raise ValueError("No edge from s_0")

            writeEdge(edge_0)

            for edge in sorted(self.iteritems()):
                if edge == edge_0:
                    continue
                writeEdge(edge)

            writeEnds(self.s_end)
        finally:
            fw.close()

        if callback is not None:
            maps = callback(maps)

        self._writeMaps(fn, maps, encoding)

    def joinstates(self, states):
        print states
        if len(states) == 1:
            return self.s0

        states = list(states)
        s0 = states.pop(0)
        map = dict((k, s0) for k in states)
        pairs = []
        for (i, j), attrs in self.iteritems():
            i = map.get(i,i)
            j = map.get(j,j)
            pairs.append(((i,j), attrs))
        self.clear()
        for (i, j), attrs in pairs:
            self[i,j] = attrs
        self.s_0 = map.get(self.s_0,self.s_0)
        self.s_end = [map.get(i,i) for i in self.s_end]

        return s0

    def newnode(self):
        while True:
            i = self.__remap_idx
            self.__remap_idx += 1
            if i not in self.states():
                break
        return i

    def edgesFrom(self, node):
        for (s1, s2), value in self.iteritems():
            if s1 == node:
                yield s2, value

    def edgesFromDict(self):
        ret = {}
        for (s1, s2), value in self.iteritems():
            if s1 not in ret:
                ret[s1] = []
            ret[s1].append( (s2, value) )
        return ret

    def edgesTo(self, node):
        for (s1, s2), value in self.iteritems():
            if s2 == node:
                yield s1, value

    def edgesToDict(self):
        ret = {}
        for (s2, s1), value in self.iteritems():
            if s1 not in ret:
                ret[s1] = []
            ret[s1].append( (s2, value) )
        return ret


    def smrRealToTropical(self):
        def op(f):
            if f is not None:
                return -log10(f)
            else:
                return None
        return self.arith(op)

    def smrTropicalToReal(self):
        def op(f):
            if f is not None:
                return 10**(-f)
            else:
                return None
        return self.arith(op)

    def edgeProb(self, s1, s2):
        attrs = self[s1, s2]
        n_attrs = len(attrs)
        if n_attrs == 0:
            return None
        elif n_attrs == 1:
            return None
        else:
            return attrs[1]

    def setEdgeProb(self, s1, s2, prob):
        attrs = self[s1, s2]
        n_attrs = len(attrs)
        if prob is not None:
            if n_attrs == 0:
                new = (self.eps, prob)
            else:
                new = (attrs[0], prob)
        else:
            if n_attrs == 0:
                new = ()
            else:
                new = (attrs[0],)
        self[s1, s2] = new

    def arith(self, op):
        ret = self.__class__()
        ret.s_0 = self.s_0
        ret.s_end = set(self.s_end)
        for (s1, s2), attrs in self.iteritems():
            ret[s1, s2] = attrs
            prob = ret.edgeProb(s1, s2)
            prob = op(prob)
            ret.setEdgeProb(s1, s2, prob)
        return ret

    def estimateWeights(self):
        ret = self.ordered()
        states = sorted(ret.states())

        e_from = ret.edgesFromDict()
        e_to = ret.edgesToDict()

        fw = {}
        fw[states[0]] = 1
        for to_node in states[1:]:
            fw[to_node] = sum(fw[from_node] for (from_node, foo) in e_to[to_node])

        bw = {}
        for end_state in ret.s_end:
            bw[end_state] = 1
            states.remove(end_state)
        for from_node in states[::-1]:
            bw[from_node] = sum(bw[to_node] for (to_node, foo) in e_from[from_node])

        counts = {}
        for i in states:
            counts[i] = fw[i] * bw[i]

        for (from_node, to_node) in ret.keys():
            ret.setEdgeProb(from_node, to_node, bw[to_node]/float(bw[from_node]))

        return ret


    
    def ordered(self):
        order = []
        stack = [self.s_0]
        edges_from = self.edgesFromDict()
        edges_to = self.edgesToDict()
        removed = set()
        while stack:
            current = stack.pop(0)
            order.append(current)

            for node, attrs in edges_from.get(current, []):
                if (current, node) in removed:
                    continue
                removed.add((current, node))

                for node2, attrs in edges_to.get(node, []):
                    if (node2, node) not in removed:
                        break
                else:
                    stack.append(node)

        if self.states() - set(order):
            raise ValueError("Graph is not acyclic")

        mapping = dict((i[1], i[0]) for i in enumerate(order))

        ret = self.__class__()
        for (f_node, t_node), attrs in self.iteritems():
            f_node = mapping[f_node]
            t_node = mapping[t_node]
            ret[f_node, t_node] = attrs
        ret.s_0 = mapping[self.s_0]
        ret.s_end = set(mapping[i] for i in self.s_end)

        return ret


class FST(FSM):
    epsEdge = (FSM.eps, FSM.eps)

    def project(self, side='in'):
        ret = FSM()
        ret.s_0 = self.s_0
        ret.s_end = list(self.s_end)
        for states, attrs in self.iteritems():
            if len(attrs) == 0:
                attrs = ()
            elif len(attrs) >= 2:
                if side == 'in':
                    attrs = (attrs[0],) + attrs[2:]
                else:
                    attrs = (attrs[1],) + attrs[2:]
            else:
                raise ValueError("Bad edge format: %s" % attrs)
            ret[states] = attrs
        return ret

    @classmethod
    def _convertFromText(cls, (imap, omap), line):
        if len(line) == 2:
            isymbol, osymbol = line
            weight = None
        elif len(line) == 3:
            isymbol, osymbol, weight = line
        else:
            raise ValueError("More items on line: %s" % ' '.join(line))

        isymbol = imap.inverse[int(isymbol)]
        osymbol = omap.inverse[int(osymbol)]
        if weight is not None:
            weight = float(weight)
            return (isymbol, osymbol, weight)
        else:
            return (isymbol, osymbol)

    @classmethod
    def _convertToText(cls, (imap, omap), edge):
        if len(edge) == 0:
            isymbol = osymbol = self.eps
            isymbol = imap.add(symbol)
            osymbol = omap.add(symbol)
            return '%d\t%d' % (isymbol, osymbol)
        elif len(edge) == 1:
            raise ValueError("Edge has less attributes than needed: %r" % edge)
        elif len(edge) == 2:
            isymbol, osymbol = edge
            isymbol = imap.add(isymbol)
            osymbol = omap.add(osymbol)
            return '%d\t%d' % (isymbol, osymbol)
        elif len(edge) == 3:
            isymbol, osymbol, weight = edge
            isymbol = imap.add(isymbol)
            osymbol = omap.add(osymbol)
            return '%d\t%d\t%e' % (isymbol, osymbol, weight)
        else:
            raise ValueError("Edge has more attributes than needed: %r" % edge)

    @classmethod
    def _readMaps(cls, fsm_fn, encoding='utf-8'):
        imap_fn = os.path.splitext(fsm_fn)[0]+'.isym'
        imap = SymMap.readFromFile(imap_fn, encoding=encoding)

        omap_fn = os.path.splitext(fsm_fn)[0]+'.osym'
        omap = SymMap.readFromFile(omap_fn, encoding=encoding)
        return imap, omap

    @classmethod
    def _emptyMaps(cls):
        imap = SymMap()
        imap[cls.eps] = 0
        omap = SymMap()
        omap[cls.eps] = 0
        return imap, omap

    @classmethod
    def _writeMaps(cls, fsm_fn, (imap, omap), encoding='utf-8'):
        imap_fn = os.path.splitext(fsm_fn)[0]+'.isym'
        imap.writeToFile(imap_fn, encoding=encoding)

        omap_fn = os.path.splitext(fsm_fn)[0]+'.osym'
        omap.writeToFile(omap_fn, encoding=encoding)

    def edgeProb(self, s1, s2):
        attrs = self[s1, s2]
        n_attrs = len(attrs)
        if n_attrs == 0:
            return None
        elif n_attrs == 1:
            raise ValueError("Malformed edge attributes: %s" % attrs)
        elif n_attrs == 2:
            return None
        else:
            return attrs[2]

    def setEdgeProb(self, s1, s2, prob):
        attrs = self[s1, s2]
        n_attrs = len(attrs)
        if prob is not None:
            if n_attrs == 0:
                new = (self.eps, self.eps, prob)
            elif n_attrs == 1:
                raise ValueError("Malformed edge attributes: %s" % attrs)
            else:
                new = (attrs[0], attrs[1], prob)
        else:
            if n_attrs == 0:
                new = (self.eps, self.eps)
            elif n_attrs == 1:
                raise ValueError("Malformed edge attributes: %s" % attrs)
            else:
                new = (attrs[0], attrs[1])
        self[s1, s2] = new



class ABNFToXML(object):
    FLAGS = re.DOTALL | re.UNICODE

    def __init__(self, abnf):
        self.abnf = abnf
        self._checkABNF()
        self._recodeABNF()
        self._removeComments()

    def _checkABNF(self):
        head = self.abnf.splitlines()[0]
        try:
            h1, h2, h3 = head.split()
        except ValueError:
            raise UniValueError('This is not ABNF header: "%s"' % head)
        if h1 != '#ABNF' \
        or h2 != '1.0' \
        or not h3.endswith(';'):
            raise UniValueError('This is not ABNF header: "%s"' % head)
        self.abnf = re.sub(r'^#ABNF.*\n', '', self.abnf)
        self.encoding = h3[:-1].strip()

    def _recodeABNF(self):
        self.abnf = self.abnf.decode(self.encoding)

    def _removeComments(self):
        obj = re.compile(r'(?ms)(//.*?$|/\*.*?\*/)', self.FLAGS)
        self.abnf = obj.sub('', self.abnf)

    def _iterClauses(self):
        in_quotes = False
        start = 0
        for idx, i in enumerate(self.abnf):
            if i == '"':
                in_quotes = not in_quotes
            if in_quotes:
                continue
            if i == ';':
                clause = self.abnf[start:idx].strip()
                if clause:
                    yield clause
                start = idx+1

    def findMatching(self, idx, clause):
        match = {}
        match['('] = ')'
        match['['] = ']'
        match['<'] = '>'
        match['{'] = '}'
        par = clause[idx]
        if par not in match:
            return idx
        par2 = match[par]
        balance = 0
        for i, chr in enumerate(clause[idx:]):
            if chr == par:
                balance += 1
            if chr == par2:
                balance -= 1
                if balance == 0:
                    return idx+i
        return -1
    
    def _checkMatching(self, clause, rule_name):
        pars = "([<{"
        for checking in pars:
            start = 0
            while True:
                idx1 = clause.find(checking, start)
                if idx1 == -1:
                    break
                start = idx1+1
                idx2 = self.findMatching(idx1, clause)
                if idx2 == -1:
                    raise UniValueError('Unbalanced parenthesis %r in rule "%s": "... %s"' % (checking, rule_name, clause[idx1:]))

    def _clauseType(self, clause):
        if re.match(r'^\s*(private|public)?\s*\$\w*\s*=', clause, self.FLAGS):
            return 'ruleDef'
        else:
            return 'other'

    def _parseRuleDef(self, clause):
        match = re.match(r'^\s*(?:private|public)?\s*\$(\w*)\s*=(.*)$', clause, self.FLAGS)
        rule_name = match.group(1)
        rule_content = match.group(2)
        return rule_name, rule_content

    def _stripPars(self, content):
        content = content.strip()
        while True:
            if content.startswith('(') and self.findMatching(0, content) == len(content)-1:
                content = content[1:-1]
            else:
                break
        return content

    def _splitVariants(self, content):
        content = self._stripPars(content)

        variants = []

        has_variant = False
        i = 0
        var_start = 0
        while i < len(content):
            cur = content[i]
            if cur == '|':
                c_variant = content[var_start:i]
                var_start = i+1
                variants.append(c_variant)
            if cur in "([<{":
                matching = self.findMatching(i, content)
                if matching == -1:
                    raise ValueError("Parenthesis doesn't match!")
                i = matching + 1
            else:
                i += 1
        else:
            c_variant = content[var_start:]
            variants.append(c_variant)
        return variants

    def _parseRuleRef(self, content):
        c = re.compile(r'\$(\w*)', self.FLAGS)
        def sub_fun(match):
            g1 = match.group(1)
            if g1 not in ['NULL', 'VOID', 'GARBAGE', 'GARBAGE1']:
                return '<ruleref uri="#%s"/>' % g1
            else:
                return '<ruleref special="%s"/>' % g1
        return c.sub(sub_fun, content)

    def _parseParenthesis(self, content):
        while True:
            i = content.find('(')
            if i == -1:
                break
            j = self.findMatching(i, content)
            if j == -1:
                raise ValueError("Parenthesis doesn't match!")

            content = content[:i] + self._parseRuleContent(content[i:j+1]) + content[j+1:]
        return content

    def _parseWeigths(self, variants):
        weights = []
        ret = []
        for i in variants:
            m = re.match('^\s*(/(.*?)/)?(.*)', i, self.FLAGS)
            w = m.group(2)
            rest = m.group(3)
            weights.append(w)
            ret.append(rest)
        return weights, ret

    def _findTokenToRepeat(self, idx, string):
        head = string[:idx].rstrip()
        if head[-1] == ')':
            balance = 0
            for i in reversed(range(len(head))):
                if head[i] == ')':
                    balance += 1
                elif head[i] == '(':
                    balance -= 1
                if balance == 0:
                    return i
            else:
                raise UniValueError("Unbalanced parenthesis in: %u" % string)
        else:
            m = re.match(r'^.*[>\s|/}](.*?)$', head, self.FLAGS)
            if m is None:
                return 0
            else:
                return m.span(1)[0]

    def _replaceRepeats(self, string):
        debug = False

        old_string = string
        if debug: print string

        string = string.replace('[', '(')
        string = string.replace(']', ')<0-1>')
        if debug: print string

        start = 0
        while True:
            idx2 = string.find('<', start)
            if idx2 == -1:
                break
            start = idx2+1
            idx1 = self._findTokenToRepeat(idx2, string)
            string = string[:idx1]+'<'+string[idx1:idx2]+'['+string[idx2+1:]
        if debug: print string

        string = string.replace('<', '[').replace('>', ']]')
        if debug: print string

        while True:
            idx1 = string.find('[')
            if idx1 == -1:
                break
            idx2 = self.findMatching(idx1, string)
            if idx2 == -1:
                raise UniValueError("Bad repeat: %u" % old_string)
            idx3 = string.rfind('[', idx1, idx2)

            repeat_par = string[idx3+1:idx2-1]

            m = re.match(r'(.*?)\s*(/\s*(.+?)\s*/)?\s*$', repeat_par, self.FLAGS)
                         
            repeat_prob = m.group(3)
            if repeat_prob:
                repeat = 'repeat="%s" repeat-prob="%s"' % (m.group(1), m.group(3))
            else:
                repeat = 'repeat="%s"' % (m.group(1), )

            to_repeat = string[idx1+1:idx3]

            string = string[:idx1]+'<item %s>' % (repeat,)+to_repeat+'</item>'+string[idx2+1:]

        if debug: print string
        if debug: print '-'* 40
        return string

    def _parseRuleContent(self, content):
        variants = self._splitVariants(content)

        weights, variants = self._parseWeigths(variants)

        if len(variants) != 1:
            variants = [self._parseRuleContent(v) for v in variants]
            variants_xml = []
            for w, i in zip(weights, variants):
                if w is not None:
                    variants_xml.append('<item weight="%s">%s</item>' % (w, i))
                else:
                    variants_xml.append('<item>%s</item>' % i)
            variants_xml = '\n'.join(variants_xml)
            
            return '<one-of>\n%s\n</one-of>' % variants_xml
        else:
            single = variants[0]
            single = self._parseRuleRef(single)
            single = self._parseParenthesis(single)
            if single != content:
                ret = self._parseRuleContent(single)
            else:
                ret = variants[0]
            if weights[0] is not None:
                return '<item weight="%s">%s</item>' % (weights[0], ret)
            else:
                return ret

    def _xmlEscapeAmp(self, string):
        return string.replace('&', '&amp;')

    def _xmlEscapeAll(self, string):
        string = re.sub('&(?!amp;)', '&amp;', string)
        return string.replace('<', '&lt;').replace('>', '&gt;')

    def _substQuotes(self, content):
        i = 0
        ret_map = {}
        while True:
            def replacer(match):
                n_quot = 1
                while True:
                    ret = "%s%d%s" % ("'" * n_quot, i, "'" * n_quot)
                    if ret not in content:
                        break
                    else:
                        n_quot += 1
                ret_map[ret] = match.group(0)
                return ret

            (content, changed) = re.subn('".*?"', replacer, content, 1)
            if not changed:
                break
            else:
                i += 1
        return content, ret_map

    def _renewQuotes(self, content, mapping):
        for old, new in mapping.iteritems():
            new = self._xmlEscapeAll(new)
            content = content.replace(old, new)
        return content

    def _substTags(self, string):
        map = {}
        i = 0
        while True:
            idx1 = string.find('{')
            if idx1 == -1:
                break
            idx2 = self.findMatching(idx1, string)
            if idx2 == -1:
                raise UniValueError("Unbalanced tag parenthesis: %s" % string)
            
            new = '_tag_%d_/tag_'%i
            old = string[idx1+1:idx2]
            map[new] = old
            string = string[:idx1]+new+string[idx2+1:]
            i += 1
        return string, map

    def _renewTags(self, content, mapping):
        for old, new in mapping.iteritems():
            new = '<tag>'+self._xmlEscapeAll(new)+'</tag>'
            content = content.replace(old, new)
        return content

    def convert(self):
        rules = []
        root_node = None
        for clause in self._iterClauses():
            ctype = self._clauseType(clause)
            if ctype == 'ruleDef':
                clause, map = self._substQuotes(clause)
                clause, tmap = self._substTags(clause)

                rname, rcontent = self._parseRuleDef(clause)
                self._checkMatching(rcontent, rname)
                rcontent = self._xmlEscapeAmp(rcontent)
                rcontent = self._replaceRepeats(rcontent)

                rcontent = self._parseRuleContent(rcontent)

                rcontent = self._renewTags(rcontent, tmap)
                rcontent = self._renewQuotes(rcontent, map)
                node = '''<rule id="%s">
%s
</rule>'''
                node = node % (rname, rcontent)
                rules.append(node)
            else:
                match = re.match(r'^root\s*\$(\w*)\s*$', clause, self.FLAGS)
                if match:
                    root_node = match.group(1)

        if root_node is None:
            raise ValueError("No root rule specified")

        xml = '''<?xml version="1.0" encoding="%s"?>

<!DOCTYPE grammar PUBLIC "-//W3C//DTD GRAMMAR 1.0//EN"
                  "http://www.w3.org/TR/speech-grammar/grammar.dtd">
 
<grammar xmlns="http://www.w3.org/2001/06/grammar" version="1.0" root="%s">

%s

</grammar>
'''
        rules = '\n\n'.join(rules)
        xml = xml % (self.encoding, root_node, rules)
        return xml.encode(self.encoding)
        

class FSMProcessor(object):
    def __init__(self, fsm):
        self.fsm = fsm

    def normalizedEdgesFrom(self, node):
        lst = ADict()

        for new_node, edge in self.fsm.edgesFrom(node):
            isym = edge[0]
            osym = edge[1]
            if len(edge) == 2:
                weight = 1
            else:
                weight = edge[2]

            lst[new_node, isym, osym] += weight

        lst_sum = float(lst.sum())
        lst_sum = 1
        for (new_node, isym, osym), weight in lst.iteritems():
            weight /= lst_sum
            yield new_node, isym, osym, weight

    def processFromNode(self, node, items):
        if not items:
            if node in self.fsm.s_end:
                yield 1.0, [], []
            else:
                yield 1.0, None, None
            head = None
            tail = items
        else:
            head = items[0]
            tail = items[1:]

        garbage_stack = []
        something = False

        for new_node, isym, osym, weight in self.normalizedEdgesFrom(node):
            if head == isym:
                for w, inputs, outputs in self.processFromNode(new_node, tail):
                    if inputs is not None and outputs is not None:
                        inputs = [head] + inputs
                        outputs = [osym] + outputs
                    else:
                        inputs = outputs = None
                    yield weight*w, inputs, outputs
                    something = True
            elif isym == self.fsm.eps:
                for w, inputs, outputs in self.processFromNode(new_node, items):
                    if inputs is not None and outputs is not None:
                        inputs = [isym] + inputs
                        outputs = [osym] + outputs
                    else:
                        inputs = outputs = None
                    yield weight*w, inputs, outputs
                    something = True
            elif isym == GARBAGE_WORD:
                garbage_stack.append( (new_node, isym, osym, weight) )

        if not something and head is not None:
            for new_node, isym, osym, weight in garbage_stack:
                for w, inputs, outputs in self.processFromNode(new_node, tail):
                    if inputs is not None and outputs is not None:
                        inputs = [head] + inputs
                        outputs = [osym] + outputs
                    else:
                        inputs = outputs = None
                    yield weight*w, inputs, outputs

    def process(self, items, best=False):
        parses = []
        is_incomplete = False
        for w, inputs, outputs in self.processFromNode(self.fsm.s_0, items):
            if inputs is not None and outputs is not None:
                parses.append( (w, inputs, outputs) )
            else:
                is_incomplete = True

        if parses and is_incomplete:
            is_incomplete = False

        results = []
        for (w, inputs, outputs) in parses:
            stack = [[]]
            for i, o in zip(inputs, outputs):
                if i != self.fsm.eps:
                    stack[-1].append(i)
                if o != self.fsm.eps:
                    if o.startswith('#START-') and o.endswith('#'):
                        rule_name = unicode(o[7:-1])
                        nested = [rule_name]
                        stack[-1].append(nested)
                        stack.append(nested)
                    elif o.startswith('#END-') and o.endswith('#'):
                        del stack[-1]
                    else:
                        o = u'{%s}' % o
                        stack[-1].append(o)
            results.append(stack[-1][0])

        if is_incomplete:
            results.append([u'#INCOMPLETE#']+items)

        return results


class XMLRuleConvertor(object):
    def __init__(self, etree, sourceEncoding,
            xmlns='http://www.w3.org/2001/06/grammar', forceRule=None,
            urlBase=None, trackRules=False, urlCache=None, debug=False):
        self.fileName = '-'
        self.etree = etree
        self._xmlns = xmlns
        self.fsmClass = FST
        self.forceRule = forceRule
        self.sourceEncoding = sourceEncoding
        self.urlBase = urlBase
        self.maxRepeat = None
        self.estimateList = []
        self.trackRules = trackRules
        self._fsmCache = {}
        self.debug = debug
        if urlCache is None:
            self._urlCache = {}
        else:
            self._urlCache = urlCache

    @classmethod
    def createFromFile(cls, fn, *args, **kwargs):
        """Creates convertor from file `fn`
        """
        etree = parse(fn)
        enc = cls._sourceEncoding(fn)
        ret = cls(etree, enc, *args, **kwargs)
        ret.fileName = fn
        return ret

    @classmethod
    def createFromString(cls, s, *args, **kwargs):
        """Creates convertor from string `s`
        """
        from StringIO import StringIO
        obj = StringIO(s)
        etree = parse(obj)
        enc = cls._sourceEncoding(obj)
        return cls(etree, enc, *args, **kwargs)

    @classmethod
    def createFromURL(cls, url, noAutoBase=False, *args, **kwargs):
        from urlparse import urlparse, urlunparse
        scheme, netloc, path, parameters, query, fragment = urlparse(url)
        path = os.path.split(path)[0]
        urlBase = urlunparse((scheme, netloc, path, '', '', ''))
        fr = urllib.urlopen(url)
        content = fr.read()
        fr.close()
        if not noAutoBase:
            return cls.createFromString(content, urlBase=urlBase, *args, **kwargs)
        else:
            return cls.createFromString(content, *args, **kwargs)


    @classmethod
    def _sourceEncoding(cls, fn_or_obj):
        if hasattr(fn_or_obj, 'readline'):
            fn_or_obj.seek(0)
            string = fn_or_obj.readline()
        else:
            fr = file(fn_or_obj)
            string = fr.readline()
            fr.close()
        match = re.match(r'<\?xml.*?encoding="(.*?)".*?\?>', string)
        if match:
            return match.group(1)
        else:
            return 'utf-8'

    def setMaxRepeat(self, r):
        self.maxRepeat = r

    def setEstimateList(self, l):
        self.estimateList = list(l)

    def setTrackRules(self, r):
        self.trackRules = r

    def convertToFSM(self, level=50, skipping=False):
        """Converts whole source file into FSM
        """
        main_rule = self.mainRule()
        if main_rule is None:
            raise ValueError("This grammar doesn't have root rule.")
        fsm = self._FSMForRule(main_rule, level=level)
        if not skipping:
            return fsm
        else:
            s_0 = fsm.newnode()
            fsm[s_0, fsm.s_0] = fsm.epsEdge(fsm.eps, fsm.eps)
            fsm[s_0, s_0] = (fsm.eps, '__skip__', )
            fsm.s_0 = s_0

            s_1 = fsm.newnode()
            fsm[s_1, s_1] = (fsm.eps, '__skip__', )
            for i in fsm.s_end:
                fsm[i, s_0] = (fsm.eps, '__repeat__', )
                fsm[i, s_1] = (fsm.eps, fsm.eps)

            fsm.s_end = set([s_0, s_1])
            return fsm

    def mainRule(self):
        """Returns main rule of source file
        """
        if self.forceRule is None:
            return self.etree.getroot().get('root')
        else:
            return self.forceRule

    def _findRuleElement(self, rule_id):
        ret = []
        for element in self.etree.findall(self.tag('rule')):
            if element.get('id') == rule_id:
                ret.append(element)
        if len(ret) > 1:
            raise UniValueError('Multiple rules with same id: "%s"' % rule_id)
        elif len(ret) == 0:
            raise UniValueError('No rule with id: "%s"' % rule_id)
        return ret[0]

    def tag(self, tag):
        if self._xmlns is not None:
            return '{%s}%s' % (self._xmlns, tag)
        else:
            return tag

    def ruleInEstimateList(self, rule_id):
        to_match = self.fileName + '#' + rule_id
        for g in self.estimateList:
            if fnmatch.fnmatchcase(to_match, g):
                return True
        return False

    def _FSMForRule(self, rule_id, level):
        """Finds `rule_id` in underlying reprezentation and converts it into FSM

        Returns list of edges
        """
        if level <= 0:
            return None
        if rule_id in self._fsmCache:
            return self._fsmCache[rule_id]
        elem = self._findRuleElement(rule_id)
        fsm = self._FSMForElement(elem, level)
        if self.ruleInEstimateList(rule_id):
            fsm = fsm.estimateWeights()
        self._fsmCache[rule_id] = fsm
        return fsm

    def _FSMForElement(self, element, level):
        stack = []
        for t, e in self._iterElement(element):
            fsm = None

            if t == 'text':
                fsm = self._FSMForText(e)
            elif t == 'one-of':
                fsm = self._FSMForOneOf(e, level)
            elif t == 'item':
                fsm = self._FSMForElement(e, level)
            elif t == 'ruleref':
                special = e.get('special')
                if special is not None:
                    fsm = self._FSMForSpecialRule(special)
                else:
                    uri = e.get('uri')
                    if not uri:
                        raise ValueError("Reference with no URI")

                    parts = uri.split('#')
                    if len(parts) == 1:
                        base = parts[0]
                        fragment = None
                    elif len(parts) == 2:
                        base, fragment = parts
                        if not base: base = None
                        if not fragment: fragment = None
                    else:
                        raise ValueError("Multiple fragments in URI: %r" % uri)

                    if base is not None:
                        base = urlparse.urljoin(self.urlBase, base)

                    if base is not None:
                        if self.debug: print 'Loading file: %s' % base
                    if fragment is not None:
                        if self.debug: print 'Parsing rule: %s' % fragment

                    if base is None:
                        creator = self
                    else:
                        if base in self._urlCache:
                            creator = self._urlCache[base]
                        else:
                            if self.debug: print 'Creating creator for %s' % base
                            creator = self.createFromURL(base,
                                    xmlns=self._xmlns,
                                    forceRule=self.forceRule,
                                    urlBase=self.urlBase, noAutoBase=True,
                                    urlCache=self._urlCache,
                                    debug=self.debug)
                            creator.setMaxRepeat(self.maxRepeat)
                            creator.setEstimateList(self.estimateList)
                            creator.setTrackRules(self.trackRules)
                            self._urlCache[base] = creator

                    if fragment is None:
                        mainRule = creator.mainRule()
                        if mainRule is None:
                            raise ValueError("External grammar '%s' doesn't specify root rule" % base)
                        fsm = creator._FSMForRule(mainRule, level-1)
                    else:
                        fsm = creator._FSMForRule(fragment, level-1)
            elif t == 'tag':
                text = [e.text]
                for i in e:
                    text.append(i.tail)
                text = [i for i in text if i is not None]
                if text:
                    text = ' '.join(text)
                    fsm = self._FSMForTag(text)

            if fsm is not None:
                stack.append(fsm)

        ret = self.fsmClass.seriall(stack)

        repeat = element.get('repeat')
        repeat_prob = element.get('repeat-prob')
        if repeat_prob is not None:
            repeat_prob = float(repeat_prob)
        if repeat is not None:
            ret = self._FSMRepeat(repeat, ret, repeat_prob)

        return ret

    def _FSMRepeat(self, repeat, ret, repeat_prob):
        if repeat_prob is not None:
            bypass_prob = 1-repeat_prob
        else:
            bypass_prob = None

        if '-' not in repeat:
            count = int(repeat)
            rep = [count]
            inf = False
        else:
            low, high = repeat.split('-')
            low = int(low)
            if high:
                high = int(high)
                inf = False
            else:
                if self.maxRepeat is None:
                    high = low
                    inf = True
                else:
                    high = self.maxRepeat
                    inf = False
            rep = range(low, high+1)

        if 0 in rep:
            rep.remove(0)
            zero = True
        else:
            zero = False

        if rep:
            head = self.fsmClass.seriall( (ret,)*min(rep) )
            n = max(rep)-min(rep)
        else:
            head = self.fsmClass()
            head.s_0 = 0
            head.s_end = set([0])
            n = 0

        if n > 0:
            next_tail = ret
            while n > 0:
                tail = self.fsmClass.epsbypass(next_tail, bypass_prob)
                next_tail = self.fsmClass.seriall((ret, tail))
                n -= 1
            fsm = self.fsmClass.seriall((head, tail))
        elif not inf:
            fsm = head
        elif inf:
            tail = self.fsmClass()
            tail.s_0 = 0
            s_1, s_end = tail.embed(ret)
            if repeat_prob is not None:
                tail[tail.s_0, s_1] = (tail.eps, tail.eps, repeat_prob)
            else:
                tail[tail.s_0, s_1] = (tail.eps, tail.eps)
            for i in s_end:
                tail[i, tail.s_0] = (tail.eps, tail.eps)

            new_end = tail.newnode()
            if repeat_prob is not None:
                tail[tail.s_0,new_end] = (tail.eps, tail.eps, 1-repeat_prob)
            else:
                tail[tail.s_0,new_end] = (tail.eps, tail.eps)
            tail.s_end = set([new_end])
            fsm = self.fsmClass.seriall((head, tail))

        if zero and not inf:
            fsm = self.fsmClass.epsbypass(fsm, bypass_prob)

        return fsm


    def _iterElement(self, element):
        if self.trackRules and element.tag == self.tag('rule'):
            tag = Element(self.tag('tag'))
            tag.text = '#START-%s#' % element.get('id')
            yield ('tag', tag)
            
        t = element.text
        if t is not None:
            t = t.strip()
            if t:
                yield ('text', t)
        for i in element:
            if i.tag == self.tag('one-of'):
                yield ('one-of', i)
            elif i.tag == self.tag('item'):
                yield ('item', i)
            elif i.tag == self.tag('ruleref'):
                yield ('ruleref', i)
            elif i.tag == self.tag('tag'):
                yield ('tag', i)
            t = i.tail
            if t is not None:
                t = t.strip()
                if t:
                    yield ('text', t)

        if self.trackRules and element.tag == self.tag('rule'):
            tag = Element(self.tag('tag'))
            tag.text = '#END-%s#' % element.get('id')
            yield ('tag', tag)

    def _FSMForText(self, text):
        fsm = self.fsmClass()
        for idx, text in enumerate(self._splitText(text)):
            fsm[idx,idx+1] = (text, fsm.eps)
        fsm.s_0 = 0
        fsm.s_end = [idx+1]
        return fsm

    def _splitText(self, text):
        ret = []
        for i in re.finditer(r'([^\s]+|".*?")(\s+|$)', text):
            ret.append(i.group(1))
        return ret

    def _FSMForOneOf(self, element, level):
        stack = []
        weights = []
        for item in element.findall(self.tag('item')):
            fsm = self._FSMForElement(item, level)
            if fsm is not None:
                stack.append(fsm)
            w = item.get('weight')
            if w is not None:
                w = float(w)
            weights.append(w)

        ret = self.fsmClass.parallel(stack, weights, open=False)
        return ret

    def _FSMForTag(self, tag):
        fsm = self.fsmClass()
        #for idx, text in enumerate(self._splitText(tag)):
        #    fsm[idx,idx+1] = (fsm.eps, text)
        # fsm.s_0 = 0
        # fsm.s_end = [idx+1]
        fsm[0,1] = (fsm.eps, tag)
        fsm.s_0 = 0
        fsm.s_end = [1]
        return fsm

    def _FSMForSpecialRule(self, special):
        if special == 'NULL':
            return None
        elif special == 'VOID':
            fsm = self.fsmClass()
            fsm.s_0 = 0
            fsm.s_end = set([1])
            return fsm
        elif special == 'GARBAGE':
            fsm = self.fsmClass()
            fsm.s_0 = 0
            fsm.s_end = set([1])
            fsm[0, 0] = (GARBAGE_WORD, fsm.eps, GARBAGE_WEIGHT)
            fsm[0, 1] = (fsm.eps, fsm.eps)
            return fsm
        elif special == 'GARBAGE1':
            fsm = self.fsmClass()
            fsm.s_0 = 0
            fsm.s_end = set([2])
            fsm[0, 1] = (GARBAGE_WORD, fsm.eps, GARBAGE_WEIGHT)
            fsm[1, 1] = (GARBAGE_WORD, fsm.eps, GARBAGE_WEIGHT)
            fsm[1, 2] = (fsm.eps, fsm.eps)
            return fsm

