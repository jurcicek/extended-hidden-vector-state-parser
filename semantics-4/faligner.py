#!/usr/bin/env python2.4

from svc.scripting.externals import *
from svc.ui.cdc.treedist import TreeDistScript
from StringIO import StringIO

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
    ('brF', 'Bracket F-measure'),
    ('brR', 'Bracket Recall'),
    ('brP', 'Bracket Precision'),
]

class FAligner(ExternalScript):
    externalMethodDirs = ['bin/faligner']

    externalMethods = {
        'deleteTmpData': ExScript.command,
        'makeDirs': ExScript.command,
        'setCommonParams': ExScript.command,
        'copyXMLData': OmitStdout,
        'genInputMaps': OmitStdout,
        'genInputs': OmitStdout,
        'genHiddenObservation': OmitStdout,
        'genEndOfUtteranceObservation': OmitStdout,
        'initSemanticModel': OmitStdout,
        'initLexicalModel': OmitStdout,
        'triangulate': ExScript.command,
        'trainModel': ExScript.command,
        'scaleModel': ExScript.command,
        'forcealignTrn': OmitStdout,
    }

    options = {
        'command': ExScript.CommandParam, 
        '__premain__.cfgfile': (Multiple, String),
    }

    settingsFiles = ['settings.path', 'settings']

    posOpts = ['command']

    @ExScript.command
    def prepareData(self, env={}):
        self.deleteTmpData(env=env)
        self.makeDirs(env=env)
        self.setCommonParams(env=env)
        self.copyXMLData(env=env)
        self.genInputMaps(env=env)
        self.genInputs(env=env)
        self.genHiddenObservation(env=env)
        self.genEndOfUtteranceObservation(env=env)
        self.initSemanticModel(env=env)
        self.initLexicalModel(env=env)

    @ExScript.command
    def train(self, env={}):
        self.triangulate(env=env)
        self.trainModel(env=env)

    @ExScript.command
    def scale(self, *args, **kwargs):
        self.scaleModel(*args, **kwargs)

    @ExScript.command
    def forcealignTrn(self, *args, **kwargs):
        super(FAligner, self).forcealignTrn(*args, **kwargs)
        return self.evaluateResults('fa_trn')

    @ExScript.command
    def all(self, env={}):
        self.prepareData(env=env)
        self.train(env=env)
        self.scale(env=env)
        self.forcealignTrn(env=env)

    def evaluateResults(self, gold_mlf, hyp_mlf=None):
        if gold_mlf in GOLD_MLF:
            key = gold_mlf
            build_dir = self.externalEnv['BUILD_DIR']
            gold_mlf = os.path.join(build_dir, GOLD_MLF[key])
            hyp_mlf = os.path.join(build_dir, HYP_MLF[key])
        elif hyp_mlf is None:
            raise ValueError('If you use path for `gold_mlf`, you must supply `hyp_mlf`')

        output = StringIO()
        td = TreeDistScript()
        results = td.sresults((gold_mlf, hyp_mlf), fw=output)
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

    def premain(self, cfgfile=[], *args, **kwargs):
        ret = super(FAligner, self).premain(*args, **kwargs)
        for fn in cfgfile:
            self.sourceEnv(fn)
        return ret

def __main__():
    s = FAligner()
    s.run()

if __name__ == '__main__':
    __main__()
