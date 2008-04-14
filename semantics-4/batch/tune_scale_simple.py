from svc.utils import linrange, linspace

SCALE_PUSHPOP = 1.5
SCALE_PUSHPOP_RANGE = 2.5
SCALE_PUSHPOP_STEP  = 0.1

SCALE_CONCEPT12 = SCALE_PUSHPOP
SCALE_CONCEPT12_RANGE = SCALE_PUSHPOP_RANGE
SCALE_CONCEPT12_STEP  = SCALE_PUSHPOP_STEP

if not 'noall' in argv:
    all()

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

params = Grid(params)

value, tuned_params = params.tune(tune_scale, logger=logger)

params.writeCSV('build/tune_scale_simple.csv')

env.update(tuned_params)

scale()
decodeHldt()
decodeTst()
