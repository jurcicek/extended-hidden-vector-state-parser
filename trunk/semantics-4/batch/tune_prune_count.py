import os

def tune_prune(percentage):
    PRUNE = percentage 
    env['S1_PRUNE_COUNT'] = env['S2_PRUNE_COUNT'] = env['S3_PRUNE_COUNT'] = PRUNE
    all(noDcd=True, moveResults=False)
    res = decodeHldt()
    return res['cAcc'], res['uCorr']

params = {
    'percentage': [-0.01, -0.025, -0.05, -0.075, -0.10, -0.125, -0.15, -0.175],
}
params = Grid.cartezianGrid(params)

value, tuned_params = params.tune(tune_prune, logger=logger)

params.writeCSV(os.path.join(env['BUILD_DIR'], 'tune_prune_count.csv'))

env['S1_PRUNE_COUNT'] = env['S2_PRUNE_COUNT'] = env['S3_PRUNE_COUNT'] = tuned_params['percentage']

all()
