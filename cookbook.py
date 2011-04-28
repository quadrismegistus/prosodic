from __future__ import division

## functions

def is_ntV(word):
	phonemes = word.phonemes()
	if phonemes[-3:-1] != [p.Phoneme("n"), p.Phoneme("t")]:
		return False
	return phonemes[-1].feature("syll")

def typtok(ent,enttype='Phoneme'):
	group=ent.ents(enttype)
	return len(set(group))/len(group)


def numclashes(ent,stressval=1.0):
	clashes=0
	a=None
	for b in ent.syllables():
		if not a:
			a=b
			continue
		if a.feature('prom.stress')==stressval and b.feature('prom.stress')==stressval:
			clashes+=1
		a=b
	return clashes


def getLD(ents):
	ld=[]
	i=0
	for t in ents:
		i+=1
		d={}
		d['name']=str(i).zfill(4)+'.'+str(t)
		d['typtok_word']=typtok(t,'Word')
		d['typtok_syll']=typtok(t,'Syllable')
		d['typtok_ons']=typtok(t,'Onset')
		d['typtok_rime']=typtok(t,'Rime')
		d['clash_persyll']=numclashes(t,stressval=1.0)/len(t.syllables())
		d['lapse_persyll']=numclashes(t,stressval=0.0)/len(t.syllables())
		d['heavy']=len(t.feature('+prom.weight',True)) / len(t.feature('prom.weight',True))
		d['light']=len(t.feature('+prom.stress',True)) / len(t.feature('prom.stress',True))
		ld.append(d)
	return ld

def getCatLD(ent):
	ld=[]
	i=0
	for syll in ent.syllables():
		d={}
		d['stress']=str(syll.str_stress())
		d['weight']=str(syll.str_weight())
		d['shape']=str(syll.getShape())
		ld.append(d)
	return ld




if __name__ == '__main__':
	## main
	import prosodic as p
	p.config['print_to_screen']=0
		
	c=p.Corpus('corpora/corptest')
		
	for t in c.texts():
		print "\n"
		print t
		
		print "    Word typ/tok ratio =", typtok(t,'Word')
		print "    Syllable typ/tok ratio =", typtok(t,'Syllable')
		print "    Onset typ/tok ratio =", typtok(t,'Onset')
		print "    Rime typ/tok ratio =", typtok(t,'Rime')
		
		print "    # of Clashes / # of Syllables =", numclashes(t,stressval=1.0)/len(t.syllables())
		print "    # of Lapses / # of Syllables =", numclashes(t,stressval=0.0)/len(t.syllables())
		print "    % of syllables being Heavy =", len(t.feature('+prom.weight',True)) / len(t.feature('prom.weight',True))
		print "    % of syllables being Stressed =", len(t.feature('+prom.stress',True)) / len(t.feature('prom.stress',True))
		
		feats=['+high','+front','+low','+back']
		#feats+=['-high','-front','-low','-back']
		for x in feats:
			for y in feats:
				if y>=x: continue	# strings sort alphabetically; this avoids duplication of data
				print "    % of "+x+" and "+y+" vowels =",
				print len( [ z for z in t.feature(x,True) if z.feature(y) ] ) / len ( t.feature('+syll',True) )
		
		
	
	
	"""
	print ">> printing all -ntV words..."
	nta = [word for word in t.words() if is_ntV(word)]
	print nta
	
	print ">> counting stress clashes per line..."
	for line in t.validlines():
		print numclashes(line),"\t",line       # print clashes, tab, line
	
	"""