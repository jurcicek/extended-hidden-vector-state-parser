from svc.egg import PythonEgg
from warnings import warn as _warn
from svc.utils import cartezian as _cartezianProduct, strnumber, strcomma

class Grid(PythonEgg, dict):
    def __init__(self, *args, **kwargs):
        super(Grid, self).__init__(*args, **kwargs)
        self._criterion = []

    @classmethod
    def cartezianGrid(cls, *args, **kwargs):
        _warn("Use cartezian() instead of cartezianGrid()", DeprecationWarning, 2)
        return cls.cartezian(*args, **kwargs)

    @classmethod
    def cartezian(cls, *args, **kwargs):
        """Construct tuning grid from required parameter values (Cartesian product)

        It will construct tuning grid from `grid` parameter. `grid` is a
        dictionary with parameter names as keys and required values of this
        parameter as values. Resulting tuning grid is constructed as Cartesian
        product of parameter values.
        """
        grid = dict(*args, **kwargs).items()
        grid_keys = [k for k, v in grid]
        grid_values = [v for k, v in grid]
        grid_values = _cartezianProduct(*grid_values)
        ret = cls((k, []) for k in grid_keys)
        for item in grid_values:
            for key, value in zip(grid_keys, item):
                ret[key].append(value)
        ret._criterion = [None] * len(grid_values)
        return ret
    
    def _getKeysValues(self):
        self.validate()
        grid = self.items()
        grid_keys = [k for k, v in grid]
        grid_values = zip(*[v for k, v in grid])
        return grid_keys, grid_values

    def _logDict(self, logger, header, d):
        logger.info(header)
        logger.info("="*len(header))
        for key, val in d.iteritems():
            logger.info("    %s: %s", key, strnumber(val))

    def _logTable(self, logger):
        keys, values = self._getKeysValues()
        crit = self._criterion

        logger.debug("Criterion values for different values of parameters:")
        logger.debug("====================================================")
        logger.debug("                     %s", strcomma(keys))
        for cval, values in zip(crit, values):
            logger.debug("    %14s : %s", cval, strcomma(values))

    def _logTuned(self, logger, tuned_crit, tuned_values):
        t = dict(tuned_values)
        t['criterion value'] = tuned_crit
        self._logDict(logger, 'Tuned parameters:', t)

    def optimum(self, type=max):
        keys, values = self._getKeysValues()
        crit = self._criterion
        opt_index = crit.index(type(crit))
        opt_value = values[opt_index]
        crit_value = crit[opt_index]
        ret_value = {}
        for parameter, val in zip(keys, opt_value):
            ret_value[parameter] = val

        return crit_value, ret_value

    def tune(self, tune_func, logger=None, type=max):
        """Tune values of parameters

        Items in tuning grid are iteratively passed to `tune_func` and return
        value of this function is used as criterion value.

        It returns optimal value of criterion and points with associated
        criterion value. If `points` is not None, it is used as default
        dictionary for returned points. Points is a dictionary with parameter
        values as keys and criterion value as values. There is a special key
        'header' containing names of parameters.
        """
        grid_keys, grid_values = self._getKeysValues()
        crit = self._criterion

        for i, values in enumerate(grid_values):
            new_values = dict(zip(grid_keys, values))

            old_crit = self.tunedValueFor(new_values)
            if old_crit is not None:
                crit[i] = old_crit
                continue

            if logger is not None:
                self._logDict(logger, 'Setting values of parameters:', new_values)
            crit[i] = tune_func(**new_values)
            if logger is not None:
                logger.info("Criterion value: %s", strnumber(crit[i]))
                logger.info("\n")

        tuned_crit, tuned_values = self.optimum(type)

        if logger is not None:
            self._logTable(logger)
            self._logTuned(logger, tuned_crit, tuned_values)

        return tuned_crit, tuned_values

    def tunedValueFor(self, values):
        grid_keys, grid_values = self._getKeysValues()
        if set(grid_keys) != set(values.keys()):
            return None

        new_values = tuple(values[key] for key in grid_keys)
        try:
            i = grid_values.index(new_values)
            return self._criterion[i]
        except ValueError:
            return None

    def isTuned(self):
        crit = self._criterion
        return None not in crit

    def validate(self):
        first_len = None
        for i in self.values():
            if first_len is None:
                first_len = len(i)
            if len(i) != first_len:
                raise ValueError("Grid is not valid, lengths of items doesn't match")

    def writeCSV(self, fn):
        import csv
        fw = file(fn, 'wb')
        try:
            writer = csv.writer(fw)
            keys, values = self._getKeysValues()
            if not values:
                raise ValueError("Grid is empty")
            if self.isTuned():
                # TODO: Improve tuned/nontuned mixture
                crit = self._criterion
                if issequence(crit[0]):
                    n_crit = len(crit[0])
                else:
                    crit = [(i,) for i in crit]
                    n_crit = 1
                crit_hdr = ['crit%d' % i for i in range(1, n_crit+1)]
            else:
                crit = [() for i in values]
                crit_hdr = []

            writer.writerow(keys + crit_hdr)

            for var_values, crit_values in zip(values, crit):
                writer.writerow(var_values + crit_values)
        finally:
            fw.close()

    def extend(self, grid):
        if set(self.keys()) ^ set(grid.keys()):
            raise ValueError("Grid cannot be extended: keys missmatched")
        grid.validate()
        for k in self.keys():
            self[k].extend(grid[k])
        self._criterion.extend(grid._criterion)

    @classmethod
    def join(cls, *grids):
        keys = {}
        for g in grids:
            for k in g.iterkeys():
                if k not in keys:
                    keys[k] = 0
                keys[k] += 1
        for k, v in keys.iteritems():
            if v > 1:
                raise ValueError("Grids cannot be joined, they shares some keys: %s" % k)
        
        kv = [g._getKeysValues() for g in grids]
        keys = [i[0] for i in kv]
        values = [i[1] for i in kv]

        new_keys = []
        [new_keys.extend(i) for i in keys]

        new_values = []
        values = _cartezianProduct(*values)
        for i in values:
            value = []
            for j in i:
                value.extend(j)
            new_values.append(value)

        d = {}
        for value in new_values:
            for k, v in zip(new_keys, value):
                if k not in d:
                    d[k] = []
                d[k].append(v)

        return cls(d)
    
    def __repr__(self):
        r = super(Grid, self).__repr__()
        return '%s(%s)' % (self.__class__.__name__, r)
