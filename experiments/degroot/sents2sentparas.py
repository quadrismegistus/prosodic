sentfolder='/Lab/Projects/sentence/sents'
sentparafolder='/Lab/Projects/sentence/sentparas'

import os,pytxt
for sentfn in os.listdir(sentfolder):
	sentfnfn=os.path.join(sentfolder,sentfn)
	f=open(sentfnfn)
	t=f.read()
	f.close()
	
	x=[]
	
	for sentence in t.split('\n'):
		x+=[sentence+'\n']
	
	ofn=os.path.join(sentparafolder,sentfn)
	pytxt.write(ofn,'\n'.join(x),toprint=True)