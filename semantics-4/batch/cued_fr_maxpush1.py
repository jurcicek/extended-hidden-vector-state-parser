from svc.utils import linrange, linspace

#settings['DATA_REDUCTION']=10
settings['MAX_PUSH']=1

prepareData(env=env)
train(env=env)
forcealignTrn(env=env)
smooth(env=env)
scale(env=env)
print decodeHldt()
print decodeTst()

#fsmconvert()
moveResults(True)
