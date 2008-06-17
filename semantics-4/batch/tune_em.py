import os

def tune_em(**env):
    settings.update(env)
    all(noDcd=True, moveResults=False)
    res = decodeHldt()
    return res['cAcc'], res['uCorr']

params = {
    'TRAIN_EM_ITERS': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
}
params = Grid.cartezianGrid(params)

value, tuned_params = params.tune(tune_em, logger=logger)

params.writeCSV(os.path.join(env['BUILD_DIR'], 'tune_scale.csv'))

env.update(tuned_params)

all()
