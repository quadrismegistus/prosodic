# coding=utf-8

from finnish_annotator import make_annotation
#from tools import get_class


stress2stroke = {0:'',1:"'",2:"`"}

orth2phon = {}

## vowels
orth2phon['a']=['ɑ']
orth2phon['aa']=['ɑː']
orth2phon['e']=['e']
orth2phon['ee']=['eː']
orth2phon['i']=['i']
orth2phon['ii']=['iː']
orth2phon['o']=['o']
orth2phon['oo']=['oː']
orth2phon['u']=['ʊ']
orth2phon['uu']=['uː']
orth2phon['y']=['y']
orth2phon['yy']=['yː']
orth2phon['ä']=['æ']
orth2phon['ää']=['æː']
orth2phon['ö']=['ø']
orth2phon['öö']=['øː']
orth2phon['å']=orth2phon['o']

## dipthongs
orth2phon['ai']=orth2phon['a']+orth2phon['i']
orth2phon['ei']=orth2phon['e']+orth2phon['i']
orth2phon['oi']=orth2phon['o']+orth2phon['i']
orth2phon['äi']=orth2phon['ä']+orth2phon['i']
orth2phon['öi']=orth2phon['ö']+orth2phon['i']
orth2phon['au']=orth2phon['a']+orth2phon['u']
orth2phon['eu']=orth2phon['e']+orth2phon['u']
orth2phon['ou']=orth2phon['o']+orth2phon['u']
orth2phon['ey']=orth2phon['e']+orth2phon['y']
orth2phon['äy']=orth2phon['ä']+orth2phon['y']
orth2phon['öy']=orth2phon['ö']+orth2phon['y']
orth2phon['ui']=orth2phon['u']+orth2phon['i']
orth2phon['yi']=orth2phon['y']+orth2phon['i']
orth2phon['iu']=orth2phon['i']+orth2phon['u']
orth2phon['iy']=orth2phon['i']+orth2phon['y']
orth2phon['ie']=orth2phon['i']+orth2phon['e']
orth2phon['uo']=orth2phon['u']+orth2phon['o']
orth2phon['yö']=orth2phon['y']+orth2phon['ö']

## consonants
orth2phon['b']=['b']
orth2phon['c']=['k']
orth2phon['d']=['d']
orth2phon['f']=['f']
orth2phon['g']=['g']
orth2phon['h']=['h']
orth2phon['j']=['j']
orth2phon['k']=['k']
orth2phon['l']=['l']
orth2phon['m']=['m']
orth2phon['n']=['n']
orth2phon['p']=['p']
orth2phon['r']=['r']
orth2phon['s']=['s']
orth2phon['t']=['t']
orth2phon['v']=['v']
orth2phon['z']=['z']
orth2phon['w']=orth2phon['v']
orth2phon['x']=orth2phon['z']	#wrong
orth2phon['q']=orth2phon['k']

ipa2x=dict([("".join(v), k) for (k, v) in orth2phon.items()])







def get(token,config={}):
	token=token.strip()


	Annotation = make_annotation(token)
	syllables=[]
	wordbroken=False

	for ij in range(len(Annotation.syllables)):
		try:
			sylldat=Annotation.split_sylls[ij]
		except IndexError:
			sylldat=["","",""]

		syllStr=""
		onsetStr=sylldat[0].strip().replace("'","").lower()
		nucleusStr=sylldat[1].strip().replace("'","").lower()
		codaStr=sylldat[2].strip().replace("'","").lower()

		for x in [onsetStr,nucleusStr,codaStr]:
			x=x.strip()
			if not x: continue
			if (not x in orth2phon):
				for y in x:
					y=y.strip()
					if not y: continue
					if (not y in orth2phon):
						#print "<error> no orth2phon mapping for letter: ["+str(y)+"]"
						wordbroken=True
					else:
						syllStr+="".join(orth2phon[y])
			else:
				syllStr+="".join(orth2phon[x])

		syllables.append(syllStr)

	words=[]

	sylls_text=[]
	for syll in Annotation.syllables:
		sylls_text.append(syll.lower())

	for stress in Annotation.stresses:
		words.append((".".join([stress2stroke[stress[i]]+syllables[i] for i in range(len(syllables))]),sylls_text,{'broken':wordbroken}))	


	return words
