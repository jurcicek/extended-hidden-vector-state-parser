import codecs
from svc.egg import PythonEgg

class HalfMap(PythonEgg, dict):
    def __init__(self, *args, **kwargs):
        super(HalfMap, self).__init__(*args, **kwargs)
        self.setindex(0)

    def newindex(self):
        v = set(self.itervalues())
        while self._index in v:
            self._index += 1
        return self._index

    def setindex(self, value):
        self._index = value

    def add(self, key):
        if key not in self:
            value = self.newindex()
            self[key] = value
            return value
        else:
            return self[key]

    @classmethod
    def readFromFile(cls, fn, encoding='utf-8', format=(unicode, int)):
        fr = codecs.open(fn, 'r', encoding)
        try:
            ret = cls()
            for line in fr:
                split = line.split()
                if len(split) == 0:
                    continue
                elif len(split) != 2:
                    raise ValueError("Bad line in file %r: %r" % (fn, line))
                key, value = split
                key = format[0](key)
                value = format[1](value)
                ret[key] = value
            return ret
        finally:
            fr.close()

    def writeToFile(self, fn, encoding='utf-8'):
        fw = codecs.open(fn, 'w', encoding)
        try:
            for k, v in sorted(self.items()):
                fw.write('%s\t%s\n' % (k, v))
        finally:
            fw.close()

_unique_value = ['unique_value']

class SymMap(HalfMap):
    def __init__(self, source=None, _inv=None):
        super(SymMap, self).__init__()
        if _inv is None:
            self.inverse = self.__class__(_inv=self)
        else:
            self.inverse = _inv
        if source is not None:
            i = 0
            for key, value in dict(source).iteritems():
                self[key] = value
                i += 1
            self.setindex(i)

    def clear(self, _inv=False):
        super(SymMap, self).clear()
        if not _inv:
            self.inverse.clear(_inv=True)

    def pop(self, *args):
        ret = super(SymMap, self).pop(*args)
        self.inverse.__delitem__(ret, _inv=True)
        return ret

    def popitem(self):
        key, value = super(SymMap, self).popitem()
        self.inverse.__delitem__(value, _inv=True)
        return key, value

    def setdefault(self, key, value=None):
        raise NotImplementedError("Method SymMap.setdefault() is not implemented")

    def __setitem__(self, key, value, _inv=False):
        # FIXME:
        #   x = SymMap([(1, 2), (2, 3), (3, 4), (4, 1)])
        #   x[1] = 3
        #   x == {1: 3, 3: 4, 4: 1}    ## Missing key 2
        if key in self:
            old_value = self[key]
            self.inverse.__delitem__(old_value, _inv=True)
        super(SymMap, self).__setitem__(key, value)
        if not _inv:
            self.inverse.__setitem__(value, key, _inv=True)

    def __delitem__(self, key, _inv=False):
        value = self[key]
        super(SymMap, self).__delitem__(key)
        if not _inv:
            self.inverse.__delitem__(value, _inv=True)

