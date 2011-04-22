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



if __name__ == '__main__':
	## main
	import prosodic as p
	p.config['print_to_screen']=0
	
	#t=p.Text('have you reckoned a thousand acres much?')
	#t=p.Text('corpora/corppoetry_fi/fi.koskenniemi.txt',lang='fi')
	t=p.Text('corpora/leavesofgrass/1855.whitman.leavesofgrass.txt')
	#t=p.Text('corpora/corppoetry_en/en.shakespeare.txt')
	
	print ">> printing Word typ/tok ratio for text "+str(t)+":", typtok(t,'Word')
	print ">> printing Syllable typ/tok ratio for text "+str(t)+":", typtok(t,'Syllable')
	print ">> printing Onset typ/tok ratio for text "+str(t)+":", typtok(t,'Onset')
	print ">> printing Rime typ/tok ratio for text "+str(t)+":", typtok(t,'Rime')
	
	
	"""
	print ">> printing all heavy syllables..."
	print t.feature('+prom.weight',True)
	
	print ">> printing all -ntV words..."
	nta = [word for word in t.words() if is_ntV(word)]
	print nta
	
	
	print ">> counting stress clashes per line..."
	for line in t.validlines():
		linestress = "".join(word.stress for word in line.words())
		
		clashes=0
		#badclashes=linestress.count("PP")  # python's String.count(substr) is non-overlapping
		
		## to capture the overlapping clashes -- ie, PPP is 2 clashes ...
		a=None                        # create variable a, set to None
		for b in linestress:          # iterate over the letters of linestress (UPPU...) 
			if not a:             # true only just when loop begun
				a=b           # set a to b's initial position to linestress[0]
				continue      # skip to next iteration of b (linestress[1]) 
			
			if a=="P" and b=="P": # clash! 
				clashes+=1
			
			a=b                   # set a to 'former' b, so that a/former_b--next_b compared next
		
		print clashes,"\t",line       # print clashes, tab, line
	
	
	"""