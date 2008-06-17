from svc.utils import linrange, linspace

def tune(**env):
    settings.update(env)
    all(noDcd=True, moveResults=False)
    res = decodeHldt()
    return res['cAcc'], res['uCorr']

if 'test' not in argv:
    params = {
        'TRAIN_DATA_REDUCTION': linrange(5,100,5),
    }
else:
    params = {
        'TRAIN_DATA_REDUCTION': [5, 10],
    }

params = Grid.cartezianGrid(params)

value, tuned_params = params.tune(tune, logger=logger)

params.writeCSV(os.path.join(env['BUILD_DIR'], 'tune_train_data_reduction.csv'))

settings.update(tuned_params)

all()

