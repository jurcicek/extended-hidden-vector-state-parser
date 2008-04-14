from svc.utils import linrange, linspace

def tune(**env):
    prepareData(env=env)
    train(env=env)
    forcealignTrn(env=env)
    smooth(env=env)
    scale(env=env)
    res = decodeHldt()
    return res['cAcc'], res['uCorr']

params = {
#    'TRAIN_EM_ITERS': [1, 2, 3, 4, 5, 6, 7, 8, 9],
    'TRAIN_EM_ITERS': [4, 5, 6, 7, 8, 9, 10],
}

params = Grid(params)

value, tuned_params = params.tune(tune, logger=logger)

params.writeCSV('build/tune_train_em_iters.csv')

env.update(tuned_params)

all()
