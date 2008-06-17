import os

def tune_word_acc(**env):
    settings.update(env)
    all(noDcd=True, moveResults=False)
    res = decodeHldt()
    return res['cAcc'], res['uCorr']

settings['CONFUSE']=1
settings['CONFUSE_NUM']=50
settings['CONFUSE_LMW']=2.0

for i in [1, 2, 3]:
    if settings['S%d_DATASET'%i] != 'off':
        settings['S%d_DATASET_DCD'%i] = 'conf_'+settings['S%d_DATASET'%i]
    else:
        settings['S%d_DATASET_DCD'%i] = 'off'
settings['ORIG_DATASETS_DCD']='conf_word,conf_lemma'

if 'train_true' not in argv:
    for i in [1, 2, 3]:
        if settings['S%d_DATASET'%i] != 'off':
            settings['S%d_DATASET'%i] = 'conf_'+settings['S%d_DATASET'%i]
    settings['ORIG_DATASETS']='conf_word,conf_lemma'

params = {
    'CONFUSE_POWER': [ 1.25,  1.38,  1.48,  1.55,  1.62,  1.71,  1.81,  1.98,  2.30,  4.00],
#   'WORD_ACC':      [55.09, 59.79, 65.25, 69.97, 74.67, 80.02, 84.73, 90.02, 95.30, 99.89]
}

params = Grid.cartezianGrid(params)

value, tuned_params = params.tune(tune_word_acc, logger=logger)

params.writeCSV(os.path.join(env['BUILD_DIR'], 'tune_word_acc.csv'))

settings.update(tuned_params)

all()
