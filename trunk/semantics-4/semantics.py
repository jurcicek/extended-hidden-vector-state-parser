#!/usr/bin/env python2.4
# -*- coding: iso-8859-2 -*-

import re
import sys

from svc.utils import cartezian as _cartezianProduct, strnumber, strcomma
from svc.scripting.externals import *
from svc.ui.cdc.treedist import TreeDistScript
from svc.map import SymMap
from svc.osutils import mkdirp
from StringIO import StringIO
import commands

class Grid(PythonEgg, dict):
    def __init__(self, *args, **kwargs):
        super(Grid, self).__init__(*args, **kwargs)
        self._criterion = []

    @classmethod
    def cartezianGrid(cls, *args, **kwargs):
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

            old_crit = self.oldCriterion(new_values)
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

    def oldCriterion(self, values):
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
        lengths = [len(i) for i in self.values()]
        if not sum(lengths) == lengths[0]*len(lengths):
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

GOLD_MLF = {
    'fa_trn': 'data/trn/semantics.mlf',
    'fa_hldt': 'data/hldt/semantics.mlf',
    'fa_tst': 'data/tst/semantics.mlf',
    'dcd_hldt': 'data/hldt/semantics.mlf',
    'dcd_tst': 'data/tst/semantics.mlf',
}

HYP_MLF = {
    'fa_trn': 'fa/trn/semantics.mlf',
    'fa_hldt': 'fa/hldt/semantics.mlf',
    'fa_tst': 'fa/tst/semantics.mlf',
    'dcd_hldt': 'dcd/hldt/semantics.mlf',
    'dcd_tst': 'dcd/tst/semantics.mlf',
}

REQ_RESULTS = [
    ('source', 'Operation'),
    ('cAcc', 'Concept Accuracy'),
    ('cCorr', 'Concept Correctness'),
    ('uCorr', 'Utterance Correctness'),
    ('sActAcc', 'CUED Speech Act Accuracy'),
    ('iP', 'CUED Item Precision'),
    ('iR', 'CUED Item Recall'),
    ('iF', 'CUED Item F-measure'),
    ('brF', 'Bracket F-measure'),
    ('brR', 'Bracket Recall'),
    ('brP', 'Bracket Precision'),
]


class SemanticsMain(ExternalScript):
    externalMethodDirs = ['bin/semantics']

    externalMethods = {
        'deleteTmpData': ExScript.command,
        'makeDirs': ExScript.command,
        'setCommonParams': ExScript.command,
        'copyXMLData': ExecNoStdout,
        'genInputMaps': ExecNoStdout,
        'genInputs': ExecNoStdout,
        'genHiddenObservation': ExecNoStdout,
        'genEndOfUtteranceObservation': ExecNoStdout,
        'initSemanticModel': ExecNoStdout,
        'initLexicalModel': ExecNoStdout,
        'triangulate': ExScript.command,
        'trainModel': ExScript.command,
        'forcealignTrn': ExecNoStdout,
        'smoothModel': ExScript.command,
        'scaleModel': ExScript.command,
        'scaleModelFaligner': ExScript.command,
        'decodeHldt': ExecNoStdout,
        'decodeTst': ExecNoStdout,
        'moveResults': ExecNoStdout,
        'fsmcompile': ExecNoStdout,
        'confuse': ExecNoStdout,
        'makeDaDecoder': ExScript.command,
        'fsmcompileDacoder': ExecNoStdout,
    }

    options = {
        'command': ExScript.CommandParam, 
        'runbatch.script': (Required, String),
        'runbatch.argv': (Multiple, String),
        '__premain__.variable': (Multiple, String),
        '__premain__.cfgfile': (Multiple, String),
        'storeEnv.settingsfn': String,
        'parametrizeXML.dataset': (Required, String),
    }

    settingsFiles = ['settings', 'settings.path']

    posOpts = ['command', {'runbatch': ['script', 'argv', Ellipsis],
                           'all':      ['variable', Ellipsis],
                           'storeEnv': ['settingsfn'],
                           'parametrizeXML': ['dataset'],
                          }]

    shortOpts = {
            's': 'variable'
    }

    Grid = Grid

    def getSymbolStats(self, env={}):
        env = dict(env)
        ret = {}
        stats_fn = os.path.join(self.settings['MAP_DIR'], 'symbol.stats')
        fr = file(stats_fn)
        try:
            for line in fr:
                orig_line = line
                line = line.strip()
                if not line:
                    continue
                line = line.split('#', 1)[0]
                try:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                except ValueError:
                    self.logger.warning("Bad line in symbol.stats: %r" % orig_line)
                    continue
                try:
                    ret[key] = eval(value)
                except:
                    self.logger.warning("Bad line in symbol.stats: %r" % orig_line)
            return ret
        finally:
            fr.close()

    def printSymbolStats(self, stats=None, env={}):
        env = dict(env)
        if stats == None:
            stats = self.getSymbolStats(env=env)
        self.logger.info('OOV rate per symbol:')
        self.logger.info('===================:')
        self.logger.info('    S1: %.2f%%' % (stats['s1_oov'] * 100. ,))
        self.logger.info('    S2: %.2f%%' % (stats['s2_oov'] * 100. ,))
        self.logger.info('    S3: %.2f%%' % (stats['s3_oov'] * 100. ,))

    @ExScript.command
    def prepareData(self, env={}):
        env = dict(env)
        self.makeDirs(env=env)
        self.deleteTmpData(env=env)
        self.setCommonParams(env=env)
        if int(self.settings['CONFUSE']):
            self.confuse(env=env)
            env['DATA_DIR'] = self.settings['CONFUSE_DATA_DIR']
        self.copyXMLData(env=env)
        self.genInputMaps(env=env)
        self.printSymbolStats(env=env)
        self.genInputs(env=env)
        self.genHiddenObservation(env=env)
        self.genEndOfUtteranceObservation(env=env)
        self.initSemanticModel(env=env)
        self.initLexicalModel(env=env)

    @ExScript.command
    def train(self, env={}):
        env = dict(env)
        self.triangulate(env=env)
        self.trainModel(env=env)

    @ExScript.command
    def forcealignTrn(self, *args, **kwargs):
        super(SemanticsMain, self).forcealignTrn(*args, **kwargs)
        return self.evaluateResults('fa_trn')

    @ExScript.command
    def smooth(self, *args, **kwargs):
        self.smoothModel(*args, **kwargs)

    @ExScript.command
    def scale(self, *args, **kwargs):
        self.scaleModel(*args, **kwargs)

    @ExScript.command
    def scaleFaligner(self, *args, **kwargs):
        self.scaleModelFaligner(*args, **kwargs)

    @ExScript.command
    def decodeHldt(self, *args, **kwargs):
        super(SemanticsMain, self).decodeHldt(*args, **kwargs)
        return self.evaluateResults('dcd_hldt')

    @ExScript.command
    def decodeTst(self, *args, **kwargs):
        super(SemanticsMain, self).decodeTst(*args, **kwargs)
        return self.evaluateResults('dcd_tst')

    @ExScript.command
    def moveResults(self, keep=False, env={}):
        env = dict(env)
        super(SemanticsMain, self).moveResults(int(keep), env=env)

    @ExScript.command
    def parametrizeXML(self, dataset):
        if dataset == 'fa_trn':
            var_name = 'FA_TRN'
            var_name2 = 'DATA_XML_TRN'
        elif dataset == 'dcd_hldt':
            var_name = 'DCD_HLDT'
            var_name2 = 'DATA_XML_HLDT'
        elif dataset == 'dcd_tst':
            var_name = 'DCD_TST'
            var_name2 = 'DATA_XML_TST'
        else:
            raise ValueError("Unknown dataset: %s" % dataset)
        dir_name = self.settings[var_name]
        in_dir = self.settings[var_name2]
        mlf_name = os.path.join(dir_name, 'semantics.mlf.smntcs')
        out_dir = os.path.join(dir_name, 'xml')
        try:
            os.makedirs(out_dir)
        except OSError:
            pass
        self.logger.info("Generating output XMLs for: %s", dataset)
        os.system('./pdttools.py mlfparametrize %s %s %s --target-type %s' % (mlf_name, in_dir, out_dir, dataset))


    @ExScript.command
    def storeEnv(self, settingsfn=None, info={}, results={}):
        if settingsfn is None:
            ext = os.environ.get('EXPERIMENT_NAME', '')
            if ext:
                ext = '.' + ext
            settingsfn = os.path.join(self.settings['BUILD_DIR'], 'settings'+ext)
        info = dict(info)
        info['Experiment name'] = os.environ.get('EXPERIMENT_NAME', '< Unknown >')
        info['Build directory'] = self.settings['BUILD_DIR']

        if 'cAcc' in results:
            info['Results:  cAcc(hldt)'] = '%.2f%%' % results['cAcc']
        if 'uCorr' in results:
            info['Results: uCorr(hldt)'] = '%.2f%%' % results['uCorr']

        argv = []
        for i in sys.argv:
            if re.search(r'\s', i):
                argv.append('"%s"' % i)
            else:
                argv.append(i)
        info['Command line'] = ' '.join(argv)

        return super(SemanticsMain, self).storeEnv(settingsfn, info)

    @ExScript.command
    def faligner(self, moveResults=True, env={}):
        env = dict(env)
        self.prepareData(env=env)
        self.train(env=env)
        self.scaleFaligner(env=env)
        self.forcealignTrn(env=env)

        if self.settings['MAKE_XML'] == '1':
            self.parametrizeXML('fa_trn')

        results = {}
        self.storeEnv(results=results)
        if moveResults:
            self.moveResults(int(self.debugMain), env=env)

    @ExScript.command
    def all(self, moveResults=True, noDcd=False, env={}):
        env = dict(env)
        self.prepareData(env=env)
        self.train(env=env)
        self.forcealignTrn(env=env)
        self.smooth(env=env)
        self.scale(env=env)

        results = {}
        if not noDcd:
            results = self.decodeHldt(env=env)
            self.decodeTst(env=env)     

        if self.settings['MAKE_XML'] == '1':
            self.parametrizeXML('fa_trn')
            self.parametrizeXML('dcd_hldt')
            self.parametrizeXML('dcd_tst')

        self.storeEnv(results=results)
        if moveResults:
            self.moveResults(int(self.debugMain), env=env)

    @ExScript.command
    def runbatch(self, script, argv=[]):
        """Run Semantics script

        Semantics scripts are written in Python language. Filename of this
        script is given at command line. Positional arguments given after
        script file are passed inside the script using 'argv' variable. For
        script examples look into 'batch' directory of Semantics distribution.
        """
        ns_g = {'smntcs': self, 'argv': argv}
        ns_l = {}
        for name in dir(self):
            try:
                ns_g[name] = getattr(self, name)
            except AttributeError:
                pass
        ns_g['env'] = self.settings

        if script == '-':
            script = sys.stdin
        else:
            script = file(script, 'r')

        try:
            exec script in ns_g, ns_l
        finally:
            script.close()

    def evaluateResults(self, gold_mlf, hyp_mlf=None):
        if gold_mlf in GOLD_MLF:
            key = gold_mlf
            build_dir = self.settings['BUILD_DIR']
            gold_mlf = os.path.join(build_dir, GOLD_MLF[key])
            hyp_mlf = os.path.join(build_dir, HYP_MLF[key])
        elif hyp_mlf is None:
            raise ValueError('If you use path for `gold_mlf`, you must supply `hyp_mlf`')

        only = self.settings.get('SRESULTS_ONLY', None)
        skip = self.settings.get('SRESULTS_SKIP', None)

        output = StringIO()
        td = TreeDistScript()
        results = td.sresults((gold_mlf, hyp_mlf), fw=output, only=only, skip=skip)
        
        cued = commands.getoutput(self.externalMethodDirs[0]+'/cuedSemScore -d '+hyp_mlf+'.cued '+gold_mlf+'.cued')
##        self.logger.info('CUED SemScore.pl: %s', cued)

        cued = cued.split()
        try:
            results['sActAcc'] = float(cued[0])
            results['iP'] = float(cued[1])
            results['iR'] = float(cued[2])
            results['iF'] = float(cued[3])
        except ValueError:
            results['sActAcc'] = 0.0
            results['iP'] = 0.0
            results['iR'] = 0.0
            results['iF'] = 0.0
        
        self.printResults(results)
        
        return results

    def printResults(self, results):
        self.logger.info('Results:')
        self.logger.info('========')
        for key, title in REQ_RESULTS:
            if key not in results:
                continue

            value = results[key]
            try:
                value = '%6.2f' % value
            except TypeError:
                pass
            self.logger.info('    %-25s : %-10s', title, value)


    def premain(self, cfgfile=[], variable=[], *args, **kwargs):
        ret = super(SemanticsMain, self).premain(*args, **kwargs)
        for fn in cfgfile:
            self.sourceEnv(fn)
        for v in variable:
            try:
                name, value = v.split('=', 1)
            except ValueError:
                raise ValueError("Bad varible (%s), must have the form: VARNAME=value" % v)
            self.settings[name] = value
        return ret

    @ExScript.command
    def fsmconvert(self, pteMapFn=None):
        sys.path.append('src')
        import fsm
        from svc.ui import gmtk

        max_states = int(self.settings['FSM_STATES'])
        cutoff_sym = float(self.settings['FSM_CUTOFF_SYM'])
        cutoff_trans = float(self.settings['FSM_CUTOFF_TRANS'])

        self.setCommonParams()
        FSM_DIR = self.settings['FSM_DIR']
        mkdirp(FSM_DIR)

        conceptMapFn = self.settings['CONCEPT_MAP']
        self.logger.debug("Reading concept map: %s", conceptMapFn)
        conceptMap = SymMap.readFromFile(conceptMapFn, format=(int, unicode)).inverse
        del conceptMap['_SINK_']
        #conceptMap = SymMap((k, v) for (k, v) in conceptMap.iteritems() if k in '_EMPTY_ GREETING DEPARTURE'.split())
        #conceptMap = SymMap((k, v) for (k, v) in conceptMap.iteritems() if k in '_EMPTY_ GREETING'.split())

        dataset_fn = os.path.join(FSM_DIR, 'datasets')
        dataset_fw = file(dataset_fn, 'w')
        sMaps = []
        for ds in [1, 2, 3]:
            ds_value = self.settings['S%d_DATASET' % ds]
            if ds_value != 'off':
                mapFn = self.settings['S%d_MAP'% ds]
                self.logger.debug("Reading s%d map: %s", ds, mapFn)
                map = SymMap.readFromFile(mapFn, format=(int, unicode)).inverse
                #map = SymMap((k, v) for (k, v) in map.iteritems() if k in u'dobrý den kdy jede _empty_ _unseen_'.split())
                sMaps.append(map)
            else:
                self.logger.debug("Dataset s%d is turned off", ds)
                sMaps.append(None)
            dataset_fw.write(ds_value + '\n')
        dataset_fw.close()

        if pteMapFn is not None:
            self.logger.debug("Reading pte map: %s", pteMapFn)
            pteMap = SymMap.readFromFile(pteMapFn, format=(unicode, int))
        else:
            pteMap = {}
        pteSymbols = pteMap.keys()
        
        mstr = os.path.join(self.settings['MSTR_DCD_DIR'], 'in.mstr')
        cppOptions = self.settings['CPP_OPTIONS'].split()
        workspace = gmtk.Workspace(cppOptions=cppOptions, readDTS=False)
        self.logger.info('Reading master file: %s', mstr)
        workspace.readMasterFile(mstr)

        self.logger.info('Creating FSM from arcs')

        self.logger.info('Total number of concepts: %d', len(conceptMap))
        #self.logger.info('Total number of symbols: %d', len(s1Map))

        stateGenerator = fsm.FSMGenerator(workspace, conceptMap, sMaps,
                                    cutoff_sym, cutoff_trans, max_states,
                                    pteSymbols=pteSymbols,
                                    logger=self.logger)
        stateGenerator.writeFSMRepeater(os.path.join(FSM_DIR, 'hvsrepeater.txt'))
        stateGenerator.writeFSMPadder(os.path.join(FSM_DIR, 'hvspadder.txt'))
        stateGenerator.writeFSM(os.path.join(FSM_DIR, 'hvsparser_pad.txt'))

        stateGenerator.stateMap.writeToFile(os.path.join(FSM_DIR, 'state.map'))
        stateGenerator.osymMap.writeToFile(os.path.join(FSM_DIR, 'osym.map'))
        for i, map in enumerate(stateGenerator.isymMaps):
            map.writeToFile(os.path.join(FSM_DIR, 'isym%d.map' % (i+1, )))
        stateGenerator.ipteMap.writeToFile(os.path.join(FSM_DIR, 'pte.map'))

        self.fsmcompile()

    @ExScript.command
    def dadecoder(self, env={}):
        env = dict(env)
        self.makeDirs(env=env)
        self.deleteTmpData(env=env)
        self.setCommonParams(env=env)
        if int(self.settings['CONFUSE']):
            self.confuse(env=env)
            env['DATA_DIR'] = self.settings['CONFUSE_DATA_DIR']
        self.copyXMLData(env=env)
        self.makeDaDecoder(env=env)
        self.fsmcompileDacoder(env=env)

def __main__():
    s = SemanticsMain()
    s.run()

if __name__ == '__main__':
    __main__()
