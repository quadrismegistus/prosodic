from __future__ import division
import sys,clash,prosodic as p,rpyd2
p.config['print_to_screen']=0
c=p.Corpus(sys.argv[1])


def numclashes_aslist(ent,stressval=0.0):
	clashes=[]
	a=None
	for b in ent.syllables():
		if not a:
			a=b
			continue
		clashes+=[a.feature('prom.stress')==stressval and b.feature('prom.stress')==stressval]
		a=b
	return clashes

for t in c.texts():
	ld=[]
	dl_groups={}
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
			d['group']=str(d['percent_pos']*100).zfill(2)[:1]+'0'
			ld.append(d)
			
			if not d['group'] in dl_groups: dl_groups[d['group']]=[]
			dl_groups[d['group']]+=[d['clash']]
	
	ld2=[]
	meanline=[]
	for group,glist in sorted(dl_groups.items()):
		mean,std=rpyd2.mean_stdev(glist)
		meanline+=[mean]
		ld2.append({'group':group,'score':mean,'scoreType':'mean'})
		ld2.append({'group':group,'score':std,'scoreType':'stdev'})
	
	r=rpyd2.RpyD2(ld2)
	r.plot(fn=t.name,x='group',y='score',group='scoreType',smooth=True,col='scoreType',point=True,se=True)
	
	## correlate sentences to archetype, print sorted list
	#### TODO

exit()	
r=rpyd2.RpyD2(ld)
#r.save('qclash.rpickle')

# r=rpyd2.load('qclash.rpickle')

r.plot(x='percent_pos',y='clash',group='text',smooth=True,col='text',point=False,se=True)

r.plot(x='pos',y='clash',group='text',smooth=True,col='text',point=False,se=True)