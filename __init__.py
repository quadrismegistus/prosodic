import sys,glob,os,time,codecs
#print '>> importing prosodic...'

#dir_prosodic=sys.path[0]
dir_prosodic=os.path.split(globals()['__file__'])[0]
sys.path.insert(0,dir_prosodic)

dir_imports=os.path.join(dir_prosodic,'lib')
sys.path.append(dir_imports)

dir_mtree=os.path.join(dir_prosodic,'metricaltree')
sys.path.append(dir_mtree)

## import necessary objects
#toprintconfig=__name__=='__main__'
toprintconfig=False
from tools import *
config=loadConfigPy(toprint=toprintconfig,dir_prosodic=dir_prosodic)
config['meters']=loadMeters()


from prosodic import *
