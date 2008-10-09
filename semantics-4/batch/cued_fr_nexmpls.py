from svc.utils import linrange, linspace

#settings['DATA_REDUCTION']=6
settings['S1_NEGEX']=1
settings['S1_NEG_THRESHOLD']=10

prepareData(env=env)
train(env=env)
forcealignTrn(env=env)
smooth(env=env)
scale(env=env)
print decodeHldt()
print decodeTst()

#fsmconvert()
moveResults(True)
