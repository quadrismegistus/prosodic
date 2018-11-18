import sys,glob,os,time,codecs
#print '>> importing prosodic...'

#dir_prosodic=sys.path[0]
dir_prosodic=os.path.split(globals()['__file__'])[0]
sys.path.insert(0,dir_prosodic)

dir_mtree=os.path.join(dir_prosodic,'metricaltree')
sys.path.append(dir_mtree)

## import necessary objects
#toprintconfig=__name__=='__main__'
toprintconfig=False

def loadConfigPy(toprint=True,dir_prosodic=None,config=None):
	import imp
	settings={'constraints':[]}
	if not dir_prosodic: dir_prosodic=sys.path[0]

	config=config if config else imp.load_source('config', os.path.join(dir_prosodic,'config.py'))

	vnames = [x for x in dir(config) if not x.startswith('_')]

	for vname in vnames:
		vval=getattr(config,vname)
		if vname=='Cs':
			for k,v in vval.items():
				cname=k+'/'+str(v)
				settings['constraints']+=[cname]
		else:
			settings[vname]=vval


	if toprint:
		print ">> loaded settings:"
		for k,v in sorted(settings.items()):
			if type(v) == list:
				print '\t',k
				for x in v:
					print '\t\t',x
			else:
				print '\t',k,'\t',v

	#settings['constraints']=" ".join(settings['constraints'])
	#settings['meters']=loadMeters()

	return settings

config=loadConfigPy(toprint=toprintconfig,dir_prosodic=dir_prosodic)
#config['meters']=loadMeters()


from prosodic import *
