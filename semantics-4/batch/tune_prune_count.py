import os

def tune_prune(percentage):
    PRUNE = percentage 
    settings['S1_PRUNE_COUNT'] = settings['S2_PRUNE_COUNT'] = settings['S3_PRUNE_COUNT'] = PRUNE
    all(noDcd=True, moveResults=False)
    res = decodeHldt()
    return res['cAcc'], res['uCorr']

if 'test' in argv:
    params = {
        'percentage': [-0.1, -0.5],
    }
    settings['TRAIN_EM_ITERS'] = 1
    settings['DATA_REDUCTION'] = 5
else:
    params = {
        'percentage': [-0.01, -0.025, -0.05, -0.075, -0.10, -0.15, -0.2, -0.3, -0.4, -0.5, -0.6, -0.7, -0.8, -0.9],
    }
params = Grid.cartezianGrid(params)

value, tuned_params = params.tune(tune_prune, logger=logger)

params.writeCSV(os.path.join(env['BUILD_DIR'], 'tune_prune_count.csv'))

settings['S1_PRUNE_COUNT'] = settings['S2_PRUNE_COUNT'] = settings['S3_PRUNE_COUNT'] = tuned_params['percentage']

all()
