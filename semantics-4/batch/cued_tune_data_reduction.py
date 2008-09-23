from svc.utils import linrange, linspace

def tune(**env):
    prepareData(env=env)
    train(env=env)
    forcealignTrn(env=env)
    smooth(env=env)
    scale(env=env)
    res = decodeHldt()
    return res['sActAcc'], res['iF']
#    return res['cAcc'], res['uCorr']

params = {
    'DATA_REDUCTION': linrange(10,100,10),
}

params = Grid.cartezianGrid(params)

value, tuned_params = params.tune(tune, logger=logger)

params.writeCSV(os.path.join(env['BUILD_DIR'], 'tune_data_reduction.csv'))

env.update(tuned_params)

# I know that all data are always the best
#all()
moveResults()