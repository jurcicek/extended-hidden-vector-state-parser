import os
from svc.utils import linrange, linspace

SCALE_PUSHPOP = float(env['SCALE_PUSHPOP'])
SCALE_PUSHPOP_RANGE = +-0.4
SCALE_PUSHPOP_STEP  =   0.2

SCALE_CONCEPT12 = float(env['SCALE_CONCEPT12'])
SCALE_CONCEPT12_RANGE = +-0.4
SCALE_CONCEPT12_STEP  =   0.2

if not 'noall' in argv:
    all(moveResults=False)

def tune_scale(**env):
    eps = 1e-6
    if env['SCALE_CONCEPT12'] < 1.0-eps or env['SCALE_PUSHPOP'] < 1.0-eps:
        logger.info("Scaling factor is less than 1.0")
        return 0.
    scale(env=env)
    res = decodeHldt()
    return res['cAcc'], res['uCorr']

params = {
    'SCALE_PUSHPOP': linrange(SCALE_PUSHPOP, SCALE_PUSHPOP_RANGE, SCALE_PUSHPOP_STEP),
    'SCALE_CONCEPT12': linrange(SCALE_CONCEPT12, SCALE_CONCEPT12_RANGE, SCALE_CONCEPT12_STEP),
}
params = Grid.cartezianGrid(params)

value, tuned_params = params.tune(tune_scale, logger=logger)

params.writeCSV(os.path.join(env['BUILD_DIR'], 'tune_scale.csv'))

env.update(tuned_params)

scale()
decodeHldt()
decodeTst()

moveResults()
