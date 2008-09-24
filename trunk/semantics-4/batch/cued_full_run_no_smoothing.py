from svc.utils import linrange, linspace

#settings['DATA_REDUCTION']=6

# Set whether the smootnig is perfomed
# '-n' - no smoothing
# ''   - smoothing
settings['WORD_NO_SMOOTHING']='-n'
settings['CONCEPT1_NO_SMOOTHING']='-n'

prepareData(env=env)
train(env=env)
forcealignTrn(env=env)
smooth(env=env)
scale(env=env)
print decodeHldt()
print decodeTst()

#fsmconvert()
moveResults(True)
