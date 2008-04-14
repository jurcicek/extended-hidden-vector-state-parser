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
    'DATA_REDUCTION': linrange(5,100,5),
}

params = Grid(params)

value, tuned_params = params.tune(tune, logger=logger)

params.writeCSV('build/tune_data_reduction.csv')

env.update(tuned_params)

all()

