from svc.utils import linrange, linspace

#settings['DATA_REDUCTION']=6
settings['ONLY_ONE_TOP_ROOT_CONCEPT']=1

prepareData(env=env)
train(env=env)
forcealignTrn(env=env)
smooth(env=env)
scale(env=env)
print decodeHldt()
print decodeTst()

#fsmconvert()
moveResults(True)
