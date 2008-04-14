import os.path
from scipy import zeros, Float, equal, alltrue
from svc.egg import PythonEgg
from svc.utils import issequence, cartezian, iterslice
from fnmatch import fnmatchcase
from copy import deepcopy
import subprocess

GmtkFloat = Float
_LEAF = -1

class WordFile(file):
    """Class for reading file wordwise
    """
    def __init__(self, *args):
        super(WordFile, self).__init__(*args)
        self._stack = []

    def readWords(self):
        while not self._stack:
            line = self.readline()
            if not line:
                break
            line = line.split('%', 1)[0]
            self._stack.extend(line.split())
            while self._stack:
                yield self._stack.pop(0)


class ProbTable(PythonEgg):
    def __init__(self, scard, pcard):
        super(ProbTable, self).__init__()
        if not issequence(scard):
            scard = [scard]
        if not issequence(pcard):
            pcard = [pcard]
        self._nvars = len(scard)
        self._npars = len(pcard)
        self._cvars = tuple(scard)
        self._cpars = tuple(pcard)
        self._table = self._initTable(scard, pcard)

    def __eq__(self, other):
        for attr in ('_cvars', '_cpars', '_eqTables'):
            if not hasattr(other, attr):
                return NotImplemented

        return (self._cvars == other._cvars) and \
               (self._cpars == other._cpars) and \
               self._eqTables(other)

    def _initTable(self, scard, pcard):
        raise TypeError('Abstract method called')

    def _eqTables(self, other):
        raise TypeError('Abstract method called')

    def getTable(self):
        return self._table

    def _convertSlices(self, item):
        var = []
        cond = []
        cur = var
        if not issequence(item):
            item = [item]
        for i in item:
            if isinstance(i, slice):
                if cur is cond:
                    raise ValueError("Malformed probability index")
                if i.step is not None:
                    raise ValueError("Malformed probability index")
                if i.start is not None:
                    var.append(i.start)
                if i.stop is None:
                    raise ValueError("Malformed probability index")
                else:
                    cond.append(i.stop)
                cur = cond
            else:
                cur.append(i)
        return tuple(var), tuple(cond)

    def _getMassFunction(self, parents):
        raise TypeError('Abstract method called')

    def _createMassFunction(self, parents):
        raise TypeError('Abstract method called')

    def _delMassFunction(self, parents):
        raise TypeError('Abstract method called')

    def __getitem__(self, item):
        var, cond = self._convertSlices(item)
        mf = self._getMassFunction(cond)
        if len(var) > 1:
            return mf[var]
        elif len(var) == 1:
            return mf[var[0]]
        else:
            return mf

    def __setitem__(self, item, value):
        var, cond = self._convertSlices(item)
        mf = self._createMassFunction(cond)
        if len(var) > 1:
            mf[var] = value
        elif len(var) == 1:
            mf[var[0]] = value
        else:
            raise IndexError('Bad index into mass function: %r' % var)

    def __delitem__(self, item):
        var, cond = self._convertSlices(item)
        if len(var) > 0:
            raise IndexError('You can delete only whole mass function, eg. [:2, 1, 3]')
        self._delMassFunction(cond)

    def getParentCards(self):
        return self._cpars

    def getSelfCards(self):
        return self._cvars

    def getPossibleParents(self):
        raise TypeError('Abstract method called')

class DenseTable(ProbTable):
    def _initTable(self, scard, pcard):
        return zeros(pcard+scard, GmtkFloat)

    def _getMassFunction(self, parents):
        if len(parents) != self._npars:
            raise ValueError('Invalid count of parents')
        return self._table[parents]

    def _eqTables(self, other):
        return alltrue(alltrue(equal(self._table, other._table)))

    _createMassFunction = _getMassFunction

    def getPossibleParents(self):
        keys = [range(i) for i in self.parentCards]
        return cartezian(*keys)


class _Object(PythonEgg):
    def __init__(self, parent, name, *args):
        super(_Object, self).__init__(*args)
        self.name = name
        self.parent = parent
        self.parent[self.__class__] = self

    def __repr__(self):
        return '<%s object, name %r>' % (self.__class__.__name__, self.name)

    @classmethod
    def readFromFile(cls, parent, stream):
        raise TypeError('Abstract method called')

    def writeToFile(self, stream):
        raise TypeError('Abstract method called')

    def setName(self, name):
        self._name = name

    def getName(self):
        return self._name

    def setParent(self, parent):
        self._parent = parent

    def getParent(self):
        return self._parent

class Collection(_Object, list):
    @classmethod
    def readFromFile(cls, parent, stream):
        name = stream.readWord()
        coll = cls(parent, name)

        n_obj = stream.readInt()
        for i in range(n_obj):
            coll.append(stream.readWord())
        return coll

    def writeToFile(self, stream):
        stream.writelnWord(self.name)
        stream.writelnInt(len(self))
        for i in self:
            stream.writelnWord(i)

    def __eq__(self, other):
        return list(self) == list(other)


class TreeLeaf(object):
    def __init__(self, expression):
        if isinstance(expression, int):
            self.eval = False
            self.expression = expression
            self.sexpression = str(expression)
        elif expression[0] == '{' and expression[-1] == '}':
            self.sexpression = expression
            expression = expression[1:-1].replace('!', ' not ')
            expression = expression.replace('&&', ' and ')
            expression = 'int(%s)' % expression.replace('||', ' or ')
            self.eval = True
            self.expression = compile(expression, '', 'eval')
        else:
            self.sexpression = expression
            self.eval = False
            self.expression = int(expression)

    def __call__(self, parents):
        if self.eval:
            ns = {}
            for i, value in enumerate(parents):
                ns['p%d' % i] = value
            return eval(self.expression, ns)
        else:
            return self.expression

    def __eq__(self, other):
        if not hasattr(other, 'expression'):
            return NotImplemented
        return self.expression == other.expression

    @classmethod
    def readFromFile(cls, stream):
        total = stream.readWord()
        if total[0] == '{':
            while total[-1] != '}':
                total += stream.readWord()
        return cls(total)

    def writeToFile(self, stream, indent=''):
        stream.writeWord(self.sexpression)

class TreeBranch(object):
    def __init__(self, parent_id, default=0):
        super(TreeBranch, self).__init__()
        self.parentId = parent_id
        self._questions = []
        self.default = default

    def __eq__(self, other):
        for attr in ('parentId', '_questions', 'default'):
            if not hasattr(other, attr):
                return NotImplemented
        return (self.parentId == other.parentId) and (self._questions == other._questions) and (self.default == other.default)

    def isLeaf(self):
        return self.parentId == _LEAF

    def vanish(self):
        while True:
            if self.isLeaf():
                return
            if len(self._questions) == 0:
                self.parentId = self.default.parentId
                self._questions = self.default._questions
                self.default = self.default.default
            else:
                break
        for q, branch in self._questions:
            branch.vanish()
        self.default.vanish()

    def __contains__(self, item):
        for quest, subtree in self._questions:
            if quest == item:
                return True
        else:
            return False

    def __getitem__(self, item):
        if isinstance(item, (long, int)):
            for quest, subtree in self._questions:
                if quest == item:
                    return subtree
            else:
                return self.default
        else:
            raise TypeError('Bad index')

    def __setitem__(self, item, value):
        if isinstance(item, (long, int)):
            for i, (quest, subtree) in enumerate(self._questions):
                if quest == item:
                    break
            else:
                self._questions.append([item, None])
                i = len(self._questions)-1
            self._questions[i][1] = value
        else:
            raise TypeError('Bad index')

    def __delitem__(self, item):
        if isinstance(item, (long, int)):
            for i, (quest, subtree) in enumerate(self._questions):
                if quest == item:
                    break
            else:
                raise ValueError("Tree hasn't branch for %r" % item)
            del self._questions[i]
        else:
            raise TypeError('Bad index')

    @classmethod
    def readFromFile(cls, stream):
        parent_id = stream.readInt()
        branch = cls(parent_id)
        if parent_id == _LEAF:
            branch.default = TreeLeaf.readFromFile(stream)
            return branch
        else:
            n_quest = stream.readInt()
            questions = []
            for i in range(n_quest-1):
                questions.append(stream.readInt())
            #
            question = stream.readWord()
            if question != 'default':
                raise ValueError('Expected string "default", not %r' % question)
            #
            for q in questions:
                answer = cls.readFromFile(stream)
                branch[q] = answer
            branch.default = cls.readFromFile(stream)
            return branch

    def writeToFile(self, stream, indent=''):
        if indent:
            stream.writeWord(indent)
        stream.writeInt(self.parentId)
        if self.isLeaf():
            self.default.writeToFile(stream)
            stream.writeNewLine()
        else:
            stream.writeInt(len(self._questions)+1)
            for q, c in self._questions:
                stream.writeWord(q)
            stream.writelnWord('default')
            for q, c in self._questions:
                c.writeToFile(stream, indent+'    ')
            self.default.writeToFile(stream, indent+'    ')

class DT(_Object):
    NullTree = TreeBranch(_LEAF, TreeLeaf(0))

    def __init__(self, parent, name, parentCount, tree):
        self._tree = deepcopy(tree)
        self._parentCount = parentCount
        super(DT, self).__init__(parent, name)

    def __eq__(self, other):
        for attr in ('_parentCount', '_tree'):
            if not hasattr(other, attr):
                return NotImplemented
        return (self._parentCount == other._parentCount) and (self._tree == other._tree)

    def getTree(self):
        return self._tree

    def getParentCount(self):
        return self._parentCount

    @classmethod
    def readFromFile(cls, parent, stream):
        name = stream.readWord()
        w = stream.readWord()
        try:
            parentCount = int(w)
            per_utterance = False
        except ValueError:
            per_utterance = True

        if not per_utterance:
            tree = TreeBranch.readFromFile(stream)
            return cls(parent, name, parentCount, tree)
        else:
            return DTs(parent, w)

    def writeToFile(self, stream):
        stream.writelnWord(self.name)
        stream.writelnInt(self.parentCount)
        self.tree.writeToFile(stream)

    def __getitem__(self, item):
        return self.answer(item)

    def answer(self, values):
        if len(values) != self.parentCount:
            raise ValueError('You must supply %d values' % self.parentCount)
        tree = self.tree
        while True:
            if tree.isLeaf():
                return tree.default(values)
            else:
                tree = tree[values[tree.parentId]]

    def __setitem__(self, item, value):
        self.store(item, value)

    def store(self, parents, value):
        if len(parents) != self.parentCount:
            raise ValueError('You must supply %d values' % self.parentCount)

        p_indexes = range(len(parents))

        if not isinstance(value, TreeLeaf):
            value = TreeLeaf(value)
        tree = self.tree
        while True:
            if tree.isLeaf():
                if p_indexes:
                    # Start branching in leaf, create new default branch as
                    # copy of this leaf
                    tree.default = deepcopy(tree)
                    tree.parentId = p_indexes.pop(0)
                    continue
                else:
                    # Overwrite stored value
                    tree.default = value
                    break
            else:
                p_id = tree.parentId
                p_val = parents[p_id]
                if p_val in tree:
                    # Descent in tree
                    tree = tree[p_val]
                    if p_id in p_indexes:
                        p_indexes.remove(p_id)
                else:
                    if p_indexes:
                        # Insert new subtree
                        new_p_id = p_indexes.pop(0)
                        new_default = deepcopy(tree.default)
                        new_tree = TreeBranch(new_p_id, new_default)
                        tree[p_val] = new_tree
                        tree = new_tree
                    else:
                        # Make leaf
                        tree[p_val] = TreeBranch(_LEAF, value)
                        break

    def __delitem__(self, item):
        self.delete(item)

    def delete(self, values):
        if len(values) != self.parentCount:
            raise ValueError('You must supply %d values' % self.parentCount)
        tree = self.tree
        old_tree = None
        while True:
            if tree.isLeaf():
                if old_tree is not None:
                    val = values[old_tree.parentId]
                    del old_tree[val]
                    old_tree.vanish()
                    break
                else:
                    raise ValueError("Cannot delete value in default branch of tree")
            else:
                val = values[tree.parentId]
                if val in tree:
                    tree, old_tree = tree[val], tree
                else:
                    tree = tree[val]
                    old_tree = None

class DTs(_Object):
    def __init__(self, parent, name):
        gmtk_name = os.path.basename(name).replace('.', '_')
        super(DTs, self).__init__(parent, gmtk_name)
        self._trees = []
        self.setDtsFilename(name)

    def __eq__(self, other):
        if not hasattr(other, '_trees'):
            return NotImplemented
        return (self._trees == other._trees)

    def getDtsFilename(self):
        return self._dtsFilename

    def setDtsFilename(self, name):
        self._dtsFilename = name
        self.readTrees()

    def writeToFile(self, stream):
        stream.writelnWord(self.name)

    def getTrees(self):
        return self._trees

    def discardTrees(self):
        trees = self.trees
        parent = self.parent
        while trees:
            t = trees.pop()
            del parent[DT, t.name]

    def readTrees(self):
        self.discardTrees()
        trees = self.trees
        io = self.parent.preprocessFile(self.dtsFilename)
        nobj = io.readInt()
        for i in range(nobj):
            ri = io.readInt()
            if i != ri:
                raise ValueError('Invalid object index, read %d, expected %d' % (ri, i))
            trees.append(DT.readFromFile(self.parent, io))
        io.close()


class _PMF(_Object):
    def __init__(self, parent, name, cardinality):
        super(_PMF, self).__init__(parent, name)
        self._initTable(cardinality)

    def _initTable(self, cardinality):
        raise TypeError('Abstract method called')

    def getCardinality(self):
        return len(self)

class DPMF(_PMF, list):
    def _initTable(self, cardinality):
        self[:] = [0] * cardinality

    @classmethod
    def readFromFile(cls, parent, stream):
        name = stream.readWord()
        cardinality = stream.readInt()
        dpmf = cls(parent, name, cardinality)

        for i in range(cardinality):
            dpmf[i] = stream.readFloat()
        return dpmf

    def writeToFile(self, stream):
        stream.writelnWord(self.name)
        stream.writelnInt(self.cardinality)
        for i in self:
            stream.writeFloat(i)
        stream.writeNewLine()

class SPMF(_PMF):
    def __init__(self, parent, name, cardinality, dpmfName):
        super(SPMF, self).__init__(parent, name, cardinality)
        self._dpmfName = dpmfName
        self._ptrs = {}

    def __eq__(self, other):
        for attr in ('_dpmfName', '_ptrs'):
            if not hasattr(other, attr):
                return NotImplemented
        return (self._dpmfName == other._dpmfName) and (self._ptrs == other._ptrs)

    def _initTable(self, cardinality):
        self._cardinality = cardinality

    def getDpmf(self):
        return self.parent[DPMF, self.dpmfName]

    def getDpmfName(self):
        return self._dpmfName

    def getPtrs(self):
        return self._ptrs

    def __len__(self):
        return self._cardinality

    def __getitem__(self, item):
        dpmf = self.dpmf
        ptrs = self._ptrs
        l = len(self)
        if isinstance(item, (int, long)):
            if item < 0:
                item += l
            if not (0 <= item < l):
                raise IndexError('Index out of range')
            if item in ptrs:
                return dpmf[ptrs[item]]
            else:
                return 0.0
        else:
            raise TypeError('Bad index')

    def __setitem__(self, item, value):
        dpmf = self.dpmf
        ptrs = self._ptrs
        l = len(self)
        if isinstance(item, (int, long)):
            if item < 0:
                item += l
            if not (0 <= item < l):
                raise IndexError('Index out of range')
            if item in ptrs:
                dpmf[ptrs[item]] = value
            else:
                new_index = len(dpmf)
                ptrs[item] = new_index
                dpmf.append(value)
        else:
            raise TypeError('Bad index')

    def __delitem__(self, item):
        dpmf = self.dpmf
        ptrs = self._ptrs
        l = len(self)
        if isinstance(item, (int, long)):
            if item < 0:
                item += l
            if not (0 <= item < l):
                raise IndexError('Index out of range')
            if item in ptrs:
                ref = ptrs[item]
                del ptrs[item]
                del dpmf[ref]
                for key, value in ptrs.items():
                    if value > ref:
                        ptrs[key] = value-1
            else:
                pass
        else:
            raise TypeError('Bad index')

    @classmethod
    def readFromFile(cls, parent, stream):
        name = stream.readWord()
        cardinality = stream.readInt()

        ptrs = {}
        length = stream.readInt()
        for i in range(length):
            ptr = stream.readInt()
            ptrs[ptr] = i

        dpmfName = stream.readWord()
        spmf = cls(parent, name, cardinality, dpmfName)
        spmf.ptrs.update(ptrs)

        return spmf

    def writeToFile(self, stream):
        stream.writelnWord(self.name)
        stream.writelnInt(self.cardinality)

        t = [y[0] for y in sorted(self._ptrs.items(), key=lambda x: x[1])]

        stream.writelnInt(len(t))
        for n in t:
            stream.writeInt(n)
        stream.writeNewLine()
        stream.writelnWord(self.dpmfName)


class _CPT(_Object, ProbTable):
    def __init__(self, parent, name, parent_cards, self_card):
        super(_CPT, self).__init__(parent, name, [self_card], parent_cards)

    def getSelfCard(self):
        cards = self.selfCards
        assert len(cards) == 1
        return cards[0]

class DCPT(_CPT, DenseTable):
    @classmethod
    def readFromFile(cls, parent, stream):
        name = stream.readWord()
        n_parents = stream.readInt()
        parent_cards = []
        total = 1
        for i in range(n_parents):
            card = stream.readInt()
            parent_cards.append(card)
            total *= card
        self_card = stream.readInt()
        total *= self_card

        dcpt = cls(parent, name, parent_cards, self_card)

        t = dcpt.table.flat
        for i in range(total):
            t[i] = stream.readFloat()

        return dcpt

    def writeToFile(self, stream):
        stream.writelnWord(self.name)
        stream.writeInt(len(self.parentCards))
        for c in self.parentCards:
            stream.writeInt(c)
        stream.writeNewLine()
        self_card = self.selfCard
        stream.writelnInt(self_card)
        for i, val in enumerate(self.table.flat):
            if i > 0 and i % self_card == 0:
                stream.writeNewLine()
            stream.writeFloat(val)
        else:
            stream.writeNewLine()

class SCPT(_CPT):
    def __init__(self, parent, name, parent_cards, self_card, dt_name, coll_name):
        super(SCPT, self).__init__(parent, name, parent_cards, self_card)
        self._dtName = dt_name
        self._collName = coll_name

    def __eq__(self, other):
        return (super(SCPT, self).__eq__(other)) and \
               (self._dtName == other._dtName) and \
               (self._collName == other._collName)

    def _initTable(self, scard, pcard):
        return None

    def _eqTables(self, other):
        for attr in ('_dtName', '_collName'):
            if not hasattr(other, attr):
                return NotImplemented
        return (self._dtName == other._dtName) and \
               (self._collName == other._collName)

    def getDtName(self):
        return self._dtName

    def getDt(self):
        return self.parent[DT, self.dtName]

    def getCollName(self):
        return self._collName

    def getColl(self):
        return self.parent[Collection, self.collName]

    @classmethod
    def readFromFile(cls, parent, stream):
        name = stream.readWord()
        n_parents = stream.readInt()
        parent_cards = []
        for i in range(n_parents):
            card = stream.readInt()
            parent_cards.append(card)
        self_card = stream.readInt()

        dtName = stream.readWord()
        collName = stream.readWord()

        scpt = cls(parent, name, parent_cards, self_card, dtName, collName)

        return scpt

    def writeToFile(self, stream):
        stream.writelnWord(self.name)
        stream.writeInt(len(self.parentCards))
        for c in self.parentCards:
            stream.writeInt(c)
        stream.writeNewLine()
        stream.writelnInt(self.selfCard)
        stream.writelnWord(self.dtName)
        stream.writelnWord(self.collName)

    @classmethod
    def create(cls, parent, name, parent_cards, self_card):
        collection = Collection(parent, name)
        collection.append(name+'00000')
        null_dpmf = DPMF(parent, name+'00000', self_card)
        null_spmf = SPMF(parent, name+'00000', self_card, name+'00000')
        dt = DT(parent, name, len(parent_cards), DT.NullTree)
        return cls(parent, name, parent_cards, self_card, name, name)

    def _getMassFunction(self, parents):
        index = self.dt[parents]
        spmf = self.parent[SPMF, self.coll[index]]
        return spmf

    def newMassFunction(self):
        """Create new SPMF (and its DPMF) and register it in collection

        :Returns:
            Tuple (index, spmf), where `index` is index in Collection and spmf
            is created function.
        """
        index = len(self.coll)
        new_name = '%s%05d' % (self.name, index)
        dpmf = DPMF(self.parent, new_name, 0)
        spmf = SPMF(self.parent, new_name, self.selfCard, dpmf.name)
        self.coll.append(new_name)
        return index, spmf

    def _createMassFunction(self, parents):
        tree_value = self.dt[parents]
        if tree_value != 0:
            return self._getMassFunction(parents)
        else:
            index, spmf = self.newMassFunction()
            self.dt[parents] = index
            return spmf

    def _delMassFunction(self, parents):
        del self.dt[parents]

class DetCPT(_CPT):
    def __init__(self, parent, name, parent_cards, self_card, dt_name):
        super(DetCPT, self).__init__(parent, name, parent_cards, self_card)
        self._dtName = dt_name

    def _eqTables(self, other):
        if not hasattr(other, '_dtName'):
            return NotImplemented
        return (self._dtName == other._dtName) 

    def getDtName(self):
        return self._dtName

    def getDt(self):
        return self.parent[DT, self.dtName]

    def _initTable(self, scard, pcard):
        return None

    @classmethod
    def readFromFile(cls, parent, stream):
        name = stream.readWord()
        n_parents = stream.readInt()
        parent_cards = []
        for i in range(n_parents):
            card = stream.readInt()
            parent_cards.append(card)
        self_card = stream.readInt()

        dtName = stream.readWord()

        detcpt = cls(parent, name, parent_cards, self_card, dtName)

        return detcpt

    def writeToFile(self, stream):
        stream.writelnWord(self.name)
        stream.writeInt(len(self.parentCards))
        for c in self.parentCards:
            stream.writeInt(c)
        stream.writeNewLine()
        stream.writelnInt(self.selfCard)
        stream.writelnWord(self.dtName)

class Workspace(PythonEgg):
    knownObjects = {
            'NAME_COLLECTION': Collection,
            'DT': DT,
            'DPMF': DPMF,
            'SPMF': SPMF,
            'DENSE_CPT': DCPT,
            'SPARSE_CPT': SCPT,
            'DETERMINISTIC_CPT': DetCPT,
            '____DTs': DTs,
    }

    def __init__(self, cppOptions=None):
        super(Workspace, self).__init__()
        self._objects = dict((name, {}) for name in self.knownTypes)
        self._cpp = Preprocessor(cppOptions=cppOptions)

    def getKnownTypes(self):
        return self.knownObjects.values()

    def getObjects(self):
        return self._objects

    def preprocessFile(self, fn):
        return WorkspaceIO(self._cpp.openFile(fn))

    def readMasterFile(self, mstr):
        IN_FILE = '_IN_FILE'
        INLINE = 'inline'
        ASCII = 'ascii'
        mstr_io = self.preprocessFile(mstr)
        while True:
            try:
                command = mstr_io.readWord()
            except IOError:
                break
            if not command.endswith(IN_FILE):
                raise ValueError('Invalid master file command: %s' % command)
            type_name = command[:-len(IN_FILE)]
            obj_type = self.knownObjects[type_name]
            fn = mstr_io.readWord()
            if fn == INLINE:
                self.readFromIO(obj_type, mstr_io)
            else:
                format = mstr_io.readWord()
                if format != ASCII:
                    raise ValueError('Format of %r not supported: %s' % (fn, format))
                file_io = self.preprocessFile(fn)
                self.readFromIO(obj_type, file_io)

    def readFromIO(self, obj_type, io):
        nobj = io.readInt()
        for i in range(nobj):
            ri = io.readInt()
            if i != ri:
                raise ValueError('Invalid object index, read %d, expected %d' % (ri, i))
            obj = obj_type.readFromFile(self, io)

    def readFromFile(self, obj_type, filename):
        f = self.preprocessFile(filename)
        try:
            self.readFromIO(obj_type, f)
        finally:
            f.close()

    def writeToIO(self, obj_type, io):
        items = sorted(self[obj_type].items())
        io.writeInt(len(items))
        io.writeNewLine()
        io.writeNewLine()
        for i, (name, obj) in enumerate(items):
            io.writeInt(i)
            obj.writeToFile(io)
            io.writeNewLine()

    def writeToFile(self, obj_type, filename):
        f = WorkspaceIO.withFile(filename, 'w')
        try:
            self.writeToIO(obj_type, f)
        finally:
            f.close()

    def __contains__(self, (obj_type, name)):
        return name in self._objects[obj_type]

    def __getitem__(self, item):
        if not issequence(item):
            item = [item]
        if len(item) == 1:
            return self._objects[item[0]]
        elif len(item) == 2:
            return self._objects[item[0]][item[1]]
        else:
            raise IndexError('Invalid index: %r' % item)

    def __setitem__(self, obj_type, value):
        name = value.name
        if (obj_type, name) in self:
            raise ValueError('There is already %s object %r' % (obj_type.__name__, name))
        self._objects[obj_type][name] = value

    def __delitem__(self, (obj_type, name)):
        obj = self._objects[obj_type][name]
        del self._objects[obj_type][name]
        obj.parent = None

    def getObjLike(self, obj_type, mask):
        objs = self.objects[obj_type]
        ret = []
        for name, obj in objs.iteritems():
            if fnmatchcase(name, mask):
                ret.append(obj)
        return ret
    
    def delObjLike(self, obj_type, mask):
        objs = self.objects[obj_type]
        to_del = []
        for name, obj in objs.iteritems():
            if fnmatchcase(name, mask):
                to_del.append(name)
        for name in to_del:
            del self[obj_type, name]


class Preprocessor(PythonEgg):
    def __init__(self, cppOptions=None):
        super(Preprocessor, self).__init__()
        if cppOptions is None:
            cppOptions = []
        self.cppOptions = cppOptions

    def createProcess(self, fn):
        p = subprocess.Popen(['cpp'] + self.cppOptions + ['-P', fn], stdout=subprocess.PIPE)
        return p

    def openFile(self, fn):
        p = self.createProcess(fn)
        return p.stdout


class WorkspaceIO(PythonEgg):
    def __init__(self, fobj):
        super(WorkspaceIO, self).__init__()
        self._file = fobj
        self._stack = []
        self._ws = False

    @classmethod
    def withFile(cls, *args, **kwargs):
        f = file(*args, **kwargs)
        return cls(f)

    def getFile(self):
        return self._file

    def readWord(self):
        while not self._stack:
            line = self._file.readline()
            if not line:
                raise IOError('End of file')
            line = line.split('%', 1)[0]
            self._stack.extend(line.split())
        return self._stack.pop(0)

    def readInt(self):
        return int(self.readWord())

    def readFloat(self):
        return float(self.readWord())

    def writeWord(self, w):
        if self._ws:
            self._file.write(' ')
        self._file.write('%s' % w)
        self._ws = True

    def writelnWord(self, w):
        self.writeWord(w)
        self.writeNewLine()

    def writeInt(self, i):
        if self._ws:
            self._file.write(' ')
        self._file.write('%d' % i)
        self._ws = True

    def writelnInt(self, w):
        self.writeInt(w)
        self.writeNewLine()

    def writeFloat(self, f):
        if self._ws:
            self._file.write(' ')
        self._file.write('%f' % f)
        self._ws = True

    def writelnFloat(self, w):
        self.writeFloat(w)
        self.writeNewLine()

    def writeNewLine(self):
        self._file.write('\n')
        self._ws = False

    def close(self):
        self._file.close()
