# Script name      : tune_scale.py
# Semantics version: semantics-4
# Description      : Tento skript umoznuje ladeni scaling faktoru
#                    SCALE_CONCEPT12 a SCALE_PUSHPOP. Vychozi hodnoty jsou
#                    brany ze souboru settings, vychozi rozsah je +-0.6 a krok
#                    0.2. Pro otestovani predat na prikazove radce retezec
#                    "test", pro postupne zjemnovani mrizky za kazde zjemneni
#                    pridat "refine", neni-li treba spoustet proceduru all,
#                    predejte "noall". Skript zapise do souboru
#                    'tune_scale.csv' hodnoty kriterii pro dany beh.
import os
from svc.utils import linrange, linspace

if not 'noall' in argv and 'test' not in argv:
    all(moveResults=False)

def tune_scale(**env):
    eps = 1e-6
    if env['SCALE_CONCEPT12'] < 1.0-eps or env['SCALE_PUSHPOP'] < 1.0-eps:
        logger.info("Scaling factor is less than 1.0")
        return 0.
    if 'test' not in argv:
        scale(env=env)
        res = decodeHldt()
#        return res['cAcc'], res['uCorr']
       return res['sActAcc'], res['iF'], res['iP'], res['iR']
    else:
        # V pripade testovani je ztratova funkce maximalni (rovna 1) v bodech
        # 1.83, 1.97
        global SCALE_CONCEPT12, SCALE_PUSHPOP
        return 1 - (env['SCALE_CONCEPT12']-1.83)**2 \
                 - (env['SCALE_PUSHPOP']-1.97)**2

n_iters = argv.count('refine')+1

SCALE_PUSHPOP = float(env['SCALE_PUSHPOP'])
SCALE_PUSHPOP_RANGE = +-0.6
SCALE_PUSHPOP_STEP  =   0.2

SCALE_CONCEPT12 = float(env['SCALE_CONCEPT12'])
SCALE_CONCEPT12_RANGE = +-0.6
SCALE_CONCEPT12_STEP  =   0.2

for i in range(n_iters):
    logger.info("_" * 80)
    logger.info('')
    logger.info("Setting tuning steps:")
    logger.info("=====================")
    logger.info("   SCALE_CONCEPT12_STEP: %.2f" % SCALE_CONCEPT12_STEP)
    logger.info("   SCALE_PUSHPOP_STEP  : %.2f" % SCALE_PUSHPOP_STEP)
    logger.info("_" * 80)
    logger.info('')
    logger.info('')

    params = {
        'SCALE_PUSHPOP': linrange(SCALE_PUSHPOP, SCALE_PUSHPOP_RANGE, SCALE_PUSHPOP_STEP),
        'SCALE_CONCEPT12': linrange(SCALE_CONCEPT12, SCALE_CONCEPT12_RANGE, SCALE_CONCEPT12_STEP),
    }

    params = Grid.cartezianGrid(params)

    value, tuned_params = params.tune(tune_scale, logger=logger)

    if i == 0:
        fn = 'tune_cued_scale.csv'
    else:
        fn = 'tune_cued_scale%d.csv' % (i+1, )
    params.writeCSV(os.path.join(env['BUILD_DIR'], fn))

    SCALE_CONCEPT12 = tuned_params['SCALE_CONCEPT12']
    SCALE_CONCEPT12_RANGE = +-SCALE_CONCEPT12_STEP
    SCALE_CONCEPT12_STEP /= 2

    SCALE_PUSHPOP = tuned_params['SCALE_PUSHPOP']
    SCALE_PUSHPOP_RANGE = +-SCALE_PUSHPOP_STEP
    SCALE_PUSHPOP_STEP /= 2

env.update(tuned_params)

if 'test' not in argv:
    scale()
    decodeHldt()
    decodeTst()

    moveResults()
