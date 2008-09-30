from svc.utils import linrange, linspace

settings['ONLY_ONE_TOP_ROOT_CONCEPT']=1
settings['EXPERIMENT_NAME']='2008-09-29-17.53'
settings['BUILD_DIR']='build/'+settings['EXPERIMENT_NAME']

env.update(settings)

print decodeHldt(env=env)
print decodeTst(env=env)

#fsmconvert()
moveResults(True)
