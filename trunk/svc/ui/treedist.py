import re
import sys
import copy

from svc.egg import PythonEgg
from svc.utils import ADict

ROOT_CONCEPT = 'tree'

def string_matchpar(s, left=0, right=sys.maxint, pars='()'):
    """Return index of left-most opening and its matching right parenthesis

    :Parameters:
        - `s` - string to search
        - `left` - index where to start, defaults to 0
        - `right` - index where to end, defaults to `sys.maxint`
        - `pars` - 2-item sequence containing parentheses pair,
           defaults to `'()'`

    :Returns:
        2-tuple (`left_index`, `right_index`) where `left_index` is index of
        left opening parenthesis and `right_index` is index of matched closing
        parenthesis.

    :Raises ValueError:
        If parenthesis are not balanced.
    """
    left_par, right_par = pars
    s = s[left:right]
    start_index = end_index = s.find(left_par)
    par_count = 0
    for char in s[start_index:]:
        if char == left_par:
            par_count += 1
        if char == right_par:
            par_count -= 1
        if par_count == 0:
            break
        end_index += 1

    if par_count != 0:
        raise ValueError("Unbalanced paranthesis")
    
    start_index = left + start_index
    stop_index = left + end_index
    return start_index, stop_index

def string_minindex(s, args):
    """Return left-most index of one of items in `args`

    :Parameters:
        - `s` - string to search
        - `args` - strings to find using `s.find`

    :Returns:
        Index if left-most item in `s`

    :Raises ValueError:
        If no item is found
    """
    ret = []
    for what in args:
        index = s.find(what)
        if index != -1:
            ret.append(index)
    return min(ret)

class EditScript(list, PythonEgg):
    """Class representing edit script as result of `TreeDist.dist`

    This class can compute number of errors (insertions, deletions,
    substitutions), number of nodes in left and right trees and error
    statistics Acc and Corr.

    Edit script is list of 2-tuples in form:
        - `(a, a)` - matched item `a` in both trees
        - `(a, None)` - missing item `a` in the second tree, *deletion* error
        - `(None, b)` - missing item `b` in the first tree, *insertion* error
        - `(a, b)` - substitution of item `a` to item `b`, *substiotion* error

    :See:
        DartDist.dist, TreeDist.dist
    """
    def __init__(self, *args, **kwargs):
        super(EditScript, self).__init__(*args, **kwargs)
        self._cache = {}

    def getHDIS(self):
        """Return tuple (H, D, I, S) containing number of errors

        :Returns:
            - `H` - number of matched nodes
            - `D` - number of nodes in first tree but not in the second
            - `I` - number of nodes in second tree but not in the first
            - `S` - number of substitutions
        """
        if 'HDIS' in self._cache:
            return self._cache['HDIS']

        H = I = D = S = 0
        for a, b in self:
            if a == b:
                H += 1
            elif a == None:
                I += 1
            elif b == None:
                D += 1
            else:
                S += 1
        
        self._cache['HDIS'] = H, D, I, S
        return H, D, I, S

    def getHitMissFA(self):
        if 'HitMissFA' in self._cache:
            return self._cache['HitMissFA']

        hit = ADict()
        miss = ADict()
        fa = ADict()
        for a, b in self:
            if a == b:
                hit[a] += 1
            elif a == None:
                fa[b] += 1
            elif b == None:
                miss[a] += 1
            else:
                miss[a] += 1
                fa[b] += 1

        self._cache['HitMissFA'] = hit, miss, fa
        return hit, miss, fa

    def getNodes(self):
        """Return tuple (N, M) containing number of nodes

        :Returns:
            - `N` - number of nodes in first tree
            - `M` - number of nodes in second tree
        """
        if 'nodes' in self._cache:
            return self._cache['nodes']

        N = M = 0
        for a, b in self:
            if a is not None: N += 1
            if b is not None: M += 1

        self._cache['nodes'] = N, M
        return N, M

    def getNumConcepts(self):
        # XXX: Remove
        return self.getNodes()

    def getStatAcc(self):
        """Return Acc stat

        Acc is computed like Acc = (H - I) / N
        """
        if 'Acc' in self._cache:
            return self._cache['Acc']

        H, D, I, S = self.HDIS
        N = self.numConcepts[0]
        if N == 0:
            Acc = 0
        else:
            Acc = (H - I) / float(N)
        self._cache['Acc'] = Acc
        return Acc

    def getStatCorr(self):
        """Return Corr stat

        Corr is computed like Corr = H / N
        """
        if 'Corr' in self._cache:
            return self._cache['Corr']

        H, D, I, S = self.HDIS
        N = self.numConcepts[0]
        if N == 0:
            Corr = 0
        else:
            Corr = H / float(N)
        self._cache['Corr'] = Corr
        return Corr

    def getLeafScript(self):
        """Return EditScript instance with leafs only
        """
        def getLeafs((a, b)):
            if a is not None:
                a = a[-1]
            if b is not None:
                b = b[-1]
            return a, b
        return self.__class__(getLeafs(item) for item in self)

    def getAsString(self):
        """Convert to list of strings

        Conversion rules:
            - `(a, a)` = 'H(a, a)'
            - `(a, None)` = 'D(a)'
            - `(None, b)` = 'I(b)'
            - `(a, b)` = 'S(a, b)'
        """
        ret = []
        for a, b in self:
            if a == b:
                ret.append('H(%s, %s)' % (a, b))
            elif a == None:
                ret.append('I(%s)' % (b,))
            elif b == None:
                ret.append('D(%s)' % (a,))
            else:
                ret.append('S(%s, %s)' % (a, b))
        return ret

class DartString(tuple):
    """Class representing closed Euler path trough ordered tree

    If the DartString instance is created, edges without their mates will be
    ommited.
        
        >>> DartString('abccbdda')
        ('a', 'b', 'c', 'c', 'b', 'd', 'd', 'a')
        >>> DartString('abccbdd')
        ('b', 'c', 'c', 'b', 'd', 'd')
        >>> DartString('abccbd')
        ('b', 'c', 'c', 'b')
    """
    def __new__(self, l):
        stack = []
        stack_index = []
        l = list(l)
        for i, item in enumerate(l):
            if item not in stack:
                stack.insert(0, item)
                stack_index.insert(0, i)
            else:
                index = stack.index(item)
                del stack[index]
                del stack_index[index]
        for i in sorted(stack_index, reverse=True):
            del l[i]
        return tuple.__new__(self, l)

    def rightMatch(self, value):
        """Find indices of two mates `value` from right side of dart

        :Returns:
            2-tuple (`left`, `right`) representing indices with two mates with
            `value`
        """
        ret = []
        i = len(self)-1
        for item in reversed(self):
            if item == value:
                ret.insert(0, i)
            if len(ret) == 2:
                return tuple(ret)
            i -= 1
        else:
            raise ValueError("Item %r not in string")

    def leftMatch(self, value):
        """Find indices of two mates `value` from left side of dart

        :Returns:
            2-tuple (`left`, `right`) representing indices with two mates with
            `value`
        """
        ret = []
        i = 0
        for item in self:
            if item == value:
                ret.append(i)
            if len(ret) == 2:
                return tuple(ret)
            i += 1
        else:
            raise ValueError("Item %r not in string")

    def __getslice__(self, *args):
        ret = super(DartString, self).__getslice__(*args)
        return self.__class__(ret)

    def ommitLast(self):
        """Return dart string without last edge and its mate
        """
        return self[:-1]

    def lastPar(self):
        """Return "match" decomposition of dart

        If the dart has items 'bccbdffd', the decomposition contains
        three elements: s1 = 'bccb', s2 = 'ff' and last = 'd' such that:
            'bccbdffd' = s1 + last + s2 + last

            >>> x = DartString('bccbdffd')
            >>> x.lastPar()
            (('b', 'c', 'c', 'b'), ('f', 'f'), 'd')
        """
        if len(self) == 0:
            raise ValueError("String has not requested form")
        last = self[-1]
        start, end = self.rightMatch(last)
        s1 = self[:start]
        s2 = self[start+1:end]
        return s1, s2, last

    def firstPar(self):
        """Return "match" decomposition of dart

        If the dart has items 'bccbdffd', the decomposition contains
        three elements: s1 = 'cc', s2 = 'dffd' and first = 'b' such that:
            'bccbdffd' = first + s1 + first + s2

            >>> x = DartString('bccbdffd')
            >>> x.firstPar()
            (('c', 'c'), ('d', 'f', 'f', 'd'), 'b')
        """
        if len(self) == 0:
            raise ValueError("String has not requested form")
        first = self[0]
        start, end = self.leftMatch(first)
        s1 = self[start+1:end]
        s2 = self[end+1:]
        return s1, s2, first

    @classmethod
    def fromOrderedTree(cls, l):
        """Creates `DartString` from `OrderedTree`

        Items in `DartString` will be labels of nodes in OrderedTree.
        """
        # XXX: make it OrderedTree method
        total = set()
        counts = {}
        def preOrder(tree):
            ret = []
            if hasattr(tree, 'label'):
                label = tuple(tree.allParents)
                counts.setdefault(label, 0)
                counts[label] += 1
                label = (counts[label], ) + label
                ret.append(label)
                for child in tree:
                    ret.extend(preOrder(child))
                ret.append(label)
            else:
                ret.append(tree)
                ret.append(tree)
            return ret
        return cls(preOrder(l))
        
class OrderedTree(list, PythonEgg):
    """Ordered tree with node label and parent tree
    """
    def __init__(self, label=None, parent=None):
        super(OrderedTree, self).__init__()
        self.label = label
        self.parent = parent

    @classmethod
    def fromString(cls, source, _outer=True, parent=None, label=None):
        """Creates tree from string

        :Parameters:
            - `source` - source string in parenthesised form:
                
                DEPARTURE(FROM(STATION), TO(STATION))

            - `parent` - parent of resulting tree
            - `label` - label of resulting tree

        :Returns:
            Tree constructed by recursive call of `fromString`
        """
        tree = cls(parent=parent, label=label)

        while source:
            try:
                separator_index = string_minindex(source, ' ,(')
            except ValueError:
                separator_index = len(source)

            label = source[:separator_index].strip()
            if not label or label in ',()':
                source = source[1:]
                continue

            if separator_index < len(source):
                separator = source[separator_index]
            else:
                separator = None

            if separator == '(':
                par_left, par_right = string_matchpar(source, separator_index)
                children_source = source[par_left+1:par_right]
                separator_index = par_right
                tree.append(cls.fromString(children_source, parent=tree, label=label))
            else:
                tree.append(cls(label=label, parent=tree))
            source = source[separator_index+1:]

        return tree

    @classmethod
    def fromStateVector(cls, source, parent=None, label=None, _outer=True):
        """Create tree from state vector

        XXX: Make example
        """
        tree = cls(parent=parent, label=label)

        START_LABEL = ['UNIQUE VALUE']
        first_label = START_LABEL
        for item in source:
            label = item[0]
            child = item[1:]

            if first_label is START_LABEL:
                first_label = label
                children = []
                continue

            if label == first_label and len(child) > 0:
                children.append(child)
            else:
                tree.append(cls.fromStateVector(children, parent=tree, label=first_label, _outer=False))
                if len(child) > 0:
                    children = [child]
                else:
                    children = []
                first_label = label
        else:
            if first_label is not START_LABEL:
                tree.append(cls.fromStateVector(children, parent=tree, label=first_label, _outer=False))

        if _outer:
            tree[0].parent = None
            return tree[0]

        return tree

    def getAllParents(self):
        """Return tuple containing full path to this tree

        Full path consists of trees' labels.
        """
        parent = self
        ret = []
        while parent is not None:
            if hasattr(parent, 'label'):
                ret.insert(0, parent.label)
            else:
                ret.insert(0, None)
            parent = parent.parent
        return ret

    def getNumConcepts(self):
        """Return total number of concepts
        """
        # XXX: Use preOrder method
        ret = 1
        for child in self:
            if hasattr(child, 'getNumConcepts'):
                ret += child.getNumConcepts()
            else:
                ret += 1
        return ret

    def treeWithLabel(self, l):
        """Return first child tree with label `l`
        """
        for child in self:
            if getattr(child, 'label', None) == l:
                return child
        else:
            raise ValueError('No child with label %r' % (l,))

    def copy(self):
        """Return copy of Tree
        """
        return copy.deepcopy(self)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        # XXX: Make __strlabel__() method
        child_str = []
        for child in self:
            child_str.append(str(child))
        if child_str:
            child_str = ', '.join(child_str)
            return '%s(%s)' % (self.label, child_str)
        else:
            return str(self.label)

    def preOrder(self):
        """Return pre-order iterator of the tree
        """
        label = self.label
        yield label, self
        for child in self:
            if hasattr(child, 'preOrder'):
                for item in child.preOrder():
                    yield item
            else:
                yield child, child

    def preOrderStack(self, _stack=[]):
        _stack = _stack + [self]

        label = self.label
        yield label, self, _stack
        for child in self:
            if hasattr(child, 'preOrder'):
                for item in child.preOrderStack(_stack):
                    yield item
            else:
                yield child, child

    def postOrder(self):
        """Return post-order iterator of the tree
        """
        label = self.label
        for child in self:
            if hasattr(child, 'preOrder'):
                for item in child.preOrder():
                    yield item
            else:
                yield child, child
        yield label, self

    def postOrderStack(self, _stack=[]):
        _stack = _stack + [self]

        label = self.label
        for child in self:
            if hasattr(child, 'preOrder'):
                for item in child.postOrderStack(_stack):
                    yield item
            else:
                yield child, child
        yield label, self, _stack


    def getConceptCounts(self):
        """Return dictionary with counts of concepts used in tree
        """
        ret = {}
        for label, tree in self.preOrder():
            ret[label] = ret.get(label, 0) + 1
        return ret

class CommonOrderedTree(OrderedTree):
    """Instance used as result of CommonDist.commonTree

    Every node can have assigned set of labels
    """
    @classmethod
    def fromTree(cls, tree, parent=None):
        """Create CommonOrderedTree from OrderedTree instance
        """
        new = cls(label=frozenset((tree.label,)), parent=parent)
        for child in tree:
            if hasattr(child, 'label'):
                new.append(cls.fromTree(child, parent=new))
            else:
                new.append(child)
        return new

    @classmethod
    def fromEditScript(cls, script, append=False):
        """Create common tree from EditScript instance
        """
        vector = cls._clearEditScript(script, append=append)
        return cls.fromStateVector(vector)

    @classmethod
    def _clearEditScript1(cls, source, second=False):
        """Remove unmatched nodes from EditScript
        """
        PATH_START = ['UNIQUE VALUE']

        #source = source[:]
        i = 0
        while i < len(source):
            # Read left and right items
            a, b = source[i]
            if second:
                a, b = b, a

            if b is None and a is not None:
                j = i
                a_last = PATH_START
                a_last_len = 0
                while j < len(source):
                    a, b = source[j]
                    if second:
                        a, b = b, a

                    if a is None:
                        j += 1
                        continue

                    if a_last == PATH_START:
                        a_last = a
                        a_last_len = len(a)
                        j += 1
                        continue

                    if a[:a_last_len] == a_last and len(a) > a_last_len:
                        a = a[:a_last_len-1] + a[a_last_len:]
                    else:
                        break

                    if second:
                        a, b = b, a
                    source[j] = a, b
                    
                    j += 1
                del source[i]
                continue
            i += 1
        return source

    @classmethod
    def _clearEditScript(cls, source, append=False):
        """Remove unmatched nodes from editscript and create state vector of new tree
        """
        source = cls._clearEditScript1(source[:])
        source = cls._clearEditScript1(source, second=True)

        ret = []
        a2new = {(): ()}
        b2new = {(): ()}
        for a, b in source:
            a_path = a[:-1]
            a_elem = a[-1]
            b_path = b[:-1]
            b_elem = b[-1]
            #assert a_path == b_path
            a_path = a2new[a_path]
            b_path = b2new[b_path]

            if append:
                new_elem = a_elem | frozenset((b_elem,))
            else:
                new_elem = frozenset((a_elem, b_elem))
            new = a_path + (new_elem,)
            ret.append(new)
            a2new[a] = new
            b2new[b] = new
        return ret

    def getNumMatches(self):
        """Return number of exactly matched nodes

        Exactly matched node is node with only one possible label
        """
        ret = 0
        if len(self.label) == 1:
            ret += 1
        for child in self:
            if hasattr(child, 'getNumMatches'):
                ret += child.getNumMatches()
        return ret

    def __str__(self):
        child_str = []
        for child in self:
            child_str.append(str(child))
        try:
            len(self.label)
            label = ';'.join(self.label)
        except TypeError:
            label = str(self.label)
        if child_str:
            child_str = ', '.join(child_str)
            return '%s(%s)' % (label, child_str)
        else:
            return label



class DartDist(PythonEgg):
    """Class computing distance and alignment of two `DartString`

    Key methods are `dist` and `leafDist`.
    """
    def __init__(self):
        super(DartDist, self).__init__()
        self.clear()
        self._cache = {((),()): (0, [])}

    def clear(self):
        """Clear computing cache

        Already computed distances are cached.
        """
        #self._cache = {((),()): (0, [])}
        pass

    def costSubs(self, a, b):
        """Return cost of matching node `a` to node `b`
        """
        if a[-1] == b[-1]:
            return 0
        else:
            return 1

    def costDel(self, a):
        """Return cost of deletion of node `a`
        """
        return 1

    def costIns(self, a):
        """Return cost of insertion of node `a`
        """
        return 1

    def match(self, s, t):
        """Calculate cost of matching of dart string `s` and `t`

        :Returns:
            2-tuple (cost, edit_script)
        """
        try:
            s1, s2, s_first = s.firstPar()
            t1, t2, t_first = t.firstPar()
        except ValueError:
            return 10**10, []

        cost1, script1 = self._distDarts(s1, t1)
        cost3, script3 = self._distDarts(s2, t2)
        cost2 = self.costSubs(s_first, t_first)
        script2 = [(s_first, t_first)]
        return cost2+cost1+cost3, script2+script1+script3

    def _distDarts(self, s, t):
        """Calculate cost of alignment of dart strings `s` and `t`

        :Returns:
            2-tuple (cost, edit_script)
        """
        if (s,t) in self._cache:
            return self._cache[(s,t)]

        if s and t:
            cost, script = self.match(s, t)
        else:
            cost = 10**10
            script = []
        if t:
            t_cost1, t_script1 = self._distDarts(s, t[1:])
            t_cost2 = self.costIns(t[0])
            t_script2 = [(None, t[0])]
            t_cost = t_cost1 + t_cost2
            if t_cost < cost:
                cost = t_cost
                script = t_script2 + t_script1
        if s:
            s_cost1, s_script1 = self._distDarts(s[1:], t)
            s_cost2 = self.costDel(s[0])
            s_script2 = [(s[0], None)]
            s_cost = s_cost1 + s_cost2
            if s_cost < cost:
                cost = s_cost
                script = s_script2 + s_script1

        self._cache[(s,t)]=(cost, script)
        return cost, script

    def dist(self, s, t, clear=True):
        """Calculate cost of alignment of dart strings `s` and `t`

        It also returns corresponding editscript.
        """
        if clear:
            self.clear()
        dist, script = self._distDarts(s, t)
        return dist, EditScript(script)

    def fullDist(self, s, t):
        """Alias for dist(s, t)
        """
        return self.dist(s, t)

    def leafDist(self, s, t):
        """Make fullDist(s, t) and convert returned script into leaf script
        """
        dist, script = self.fullDist(s, t)
        return dist, script.leafScript

class TreeDist(DartDist):
    """Class computing distance and alignment of two `OrderedTree`

    Before calling `dist` method, input trees are converted into darts using
    `makeDart` method.
    """
    @classmethod
    def makeDart(self, tree):
        """Convert `tree` into `DartString`

        :See:
            DartString.fromOrderedTree
        """
        return DartString.fromOrderedTree(tree)

    def dist(self, s, t, clear=True):
        """Calculate cost of alignment of TREES `s` and `t`
        """
        s = self.makeDart(s)
        t = self.makeDart(t)
        dist, script = super(TreeDist, self).dist(s, t, clear=clear)
        new_script = EditScript()
        for a, b in script:
            if a is not None:
                a = a[1:]
            if b is not None:
                b = b[1:]
            new_script.append((a, b))
        return dist, new_script

class CommonDist(TreeDist):
    def dist(self, s, t, clear=True):
        """Calculate cost of alignment of dart strings `s` and `t`

        It also returns corresponding editscript. Before calculating, the first
        tree is converted into CommonOrderedTree instance.
        """
        if not isinstance(s, CommonOrderedTree):
            s = CommonOrderedTree.fromTree(s)
        return super(CommonDist, self).dist(s, t, clear)

    def costSubs(self, a, b):
        """Return cost of matching node `a` to node `b`
        """
        if b[-1] in a[-1]:
            return 0.01 * (len(b[-1])-1)
        else:
            return 1

    def commonTree(self, *trees):
        """Return instance of CommonOrderedTree

        Returned tree is common tree of all arguments. This tree is obtained
        from arguments by deleting some nodes. When aligning arguments with
        common tree, nodes will never be deleted from common tree. (The common
        tree is always included in every argument according to tree edit
        distance).
        """
        trees = list(trees)
        common = trees.pop(0)
        if not isinstance(common, CommonOrderedTree):
            common = CommonOrderedTree.fromTree(common)
        for tree in trees:
            edt = self.dist(common, tree)[1]
            common = CommonOrderedTree.fromEditScript(edt, append=True)
        return common

