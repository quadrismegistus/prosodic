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


if __name__ == '__main__':
	## main
	import prosodic as p
	p.config['print_to_screen']=0
	
	
	#t=p.Text('have you reckoned a thousand acres much?')
	#t=p.Text('corpora/corppoetry_fi/fi.koskenniemi.txt',lang='fi')
	#t=p.Text('corpora/leavesofgrass/1855.whitman.leavesofgrass.txt')
	#t=p.Text('corpora/corppoetry_en/en.shakespeare.txt')
	
	
	
	
	texts=[]
	texts.append(p.Text('corpora/corppoetry_en/en.shakespeare.txt'))
	texts.append(p.Text('corpora/corppoetry_en/en.whitman.txt'))
	texts.append(p.Text('corpora/corppoetry_en/en.yeats.early.txt'))
	texts.append(p.Text('corpora/corppoetry_en/en.yeats.late.txt'))
	texts.append(p.Text('corpora/corpprose/en.speech.gettysburg.txt'))
	texts.append(p.Text('corpora/corpprose/en.speech.bush.txt'))
	texts.append(p.Text('corpora/corpprose/en.speech.obama.txt'))
	texts.append(p.Text('corpora/corpprose/en.prose.nyt.txt'))
	texts.append(p.Text('corpora/corpprose/en.prose.blog.google.txt'))
	texts.append(p.Text('corpora/corpprose/en.academic.linguistics.txt'))
	texts.append(p.Text('corpora/corpprose/en.academic.literature.txt'))
	
	
	for t in texts:
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