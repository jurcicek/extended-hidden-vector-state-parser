from svc.utils import linrange, linspace

#settings['DATA_REDUCTION']=10
settings['SCALE_CONCEPT12']=1.0
settings['SCALE_PUSHPOP']=1.0
settings['INSERTION_PENALTY']=0.2

prepareData(env=env)
train(env=env)
forcealignTrn(env=env)
smooth(env=env)
scale(env=env)
print decodeHldt()
print decodeTst()

#fsmconvert()
moveResults(True)
