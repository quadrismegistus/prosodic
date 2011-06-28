from __future__ import division
import sys,clash,prosodic as p,rpyd2
p.config['print_to_screen']=0
c=p.Corpus(sys.argv[1])


def numclashes_aslist(ent,stressval=1.0):
	clashes=[]
	a=None
	for b in ent.syllables():
		if not a:
			a=b
			continue
		clashes+=[a.feature('prom.stress')==stressval and b.feature('prom.stress')==stressval]
		a=b
	return clashes

ld=[]
for t in c.texts():
	vl=t.validlines()
	tname=str(len(vl)).zfill(4)+'l_'+t.name
	for l in vl:
		cl=numclashes_aslist(l)
		for i in range(len(cl)):
			
			d={}
			d['text']=tname
			d['percent_pos']=i/len(cl)
			d['pos']=i
			d['clash']=int(cl[i])
			ld.append(d)
			
	
r=rpyd2.RpyD2(ld)
#r.save('qclash.rpickle')

# r=rpyd2.load('qclash.rpickle')


r.plot(x='percent_pos',y='clash',group='text',smooth=True,col='text',point=False,se=True)
r.plot(x='pos',y='clash',group='text',smooth=True,col='text',point=False,se=True)