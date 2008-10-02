from svc.utils import linrange, linspace

#settings['DATA_REDUCTION']=6

prepareData(env=env)
train(env=env)
forcealignTrn(env=env)
smooth(env=env)
scale(env=env)
print decodeHldt()
print decodeTst()

#fsmconvert()
moveResults(True)
