import os

def tune_em(**env):
    all(env=env, noDcd=True, moveResults=False)
    res = decodeHldt(env=env)
    return res['cAcc'], res['uCorr']

params = {
    'CONFUSE_POWER': [ 1.25,  1.38,  1.48,  1.55,  1.62,  1.71,  1.81,  1.98,  2.30,  4.00],
#    'WORD_ACC':      [55.09, 59.79, 65.25, 69.97, 74.67, 80.02, 84.73, 90.02, 95.30, 99.89]
}

#export CONFUSE_POWER=3.5
# ACC 55.09 POWER=1.25  LMW=2.0 
# ACC 59.79 POWER=1.38  LMW=2.0 
# ACC 65.25 POWER=1.58  LMW=2.0 
# ACC 69.97 POWER=1.55  LMW=2.0 
# ACC 74.67 POWER=1.62  LMW=2.0 
# ACC 80.02 POWER=1.71  LMW=2.0 
# ACC 84.73 POWER=1.81  LMW=2.0 
# ACC 90.02 POWER=1.98  LMW=2.0 
# ACC 95.30 POWER=2.30  LMW=2.0 
# ACC 99.89 POWER=4.00  LMW=2.0 

params = Grid.cartezianGrid(params)

value, tuned_params = params.tune(tune_em, logger=logger)

params.writeCSV(os.path.join(env['BUILD_DIR'], 'tune_word_acc.csv'))

env.update(tuned_params)

all()
