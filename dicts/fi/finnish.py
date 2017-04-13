# coding=utf-8

from finnish_annotator import make_annotation
#from tools import get_class


stress2stroke = {0:'',1:"'",2:"`"}

orth2phon = {}

## vowels
orth2phon[u'a']=[u'ɑ']
orth2phon[u'aa']=[u'ɑː']
orth2phon[u'e']=[u'e']
orth2phon[u'ee']=[u'eː']
orth2phon[u'i']=[u'i']
orth2phon[u'ii']=[u'iː']
orth2phon[u'o']=[u'o']
orth2phon[u'oo']=[u'oː']
orth2phon[u'u']=[u'ʊ']
orth2phon[u'uu']=[u'uː']
orth2phon[u'y']=[u'y']
orth2phon[u'yy']=[u'yː']
orth2phon[u'ä']=[u'æ']
orth2phon[u'ää']=[u'æː']
orth2phon[u'ö']=[u'ø']
orth2phon[u'öö']=[u'øː']
orth2phon[u'å']=orth2phon[u'o']

## dipthongs
orth2phon[u'ai']=orth2phon[u'a']+orth2phon[u'i']
orth2phon[u'ei']=orth2phon[u'e']+orth2phon[u'i']
orth2phon[u'oi']=orth2phon[u'o']+orth2phon[u'i']
orth2phon[u'äi']=orth2phon[u'ä']+orth2phon[u'i']
orth2phon[u'öi']=orth2phon[u'ö']+orth2phon[u'i']
orth2phon[u'au']=orth2phon[u'a']+orth2phon[u'u']
orth2phon[u'eu']=orth2phon[u'e']+orth2phon[u'u']
orth2phon[u'ou']=orth2phon[u'o']+orth2phon[u'u']
orth2phon[u'ey']=orth2phon[u'e']+orth2phon[u'y']
orth2phon[u'äy']=orth2phon[u'ä']+orth2phon[u'y']
orth2phon[u'öy']=orth2phon[u'ö']+orth2phon[u'y']
orth2phon[u'ui']=orth2phon[u'u']+orth2phon[u'i']
orth2phon[u'yi']=orth2phon[u'y']+orth2phon[u'i']
orth2phon[u'iu']=orth2phon[u'i']+orth2phon[u'u']
orth2phon[u'iy']=orth2phon[u'i']+orth2phon[u'y']
orth2phon[u'ie']=orth2phon[u'i']+orth2phon[u'e']
orth2phon[u'uo']=orth2phon[u'u']+orth2phon[u'o']
orth2phon[u'yö']=orth2phon[u'y']+orth2phon[u'ö']

## consonants
orth2phon[u'b']=[u'b']
orth2phon[u'c']=[u'k']
orth2phon[u'd']=[u'd']
orth2phon[u'f']=[u'f']
orth2phon[u'g']=[u'g']
orth2phon[u'h']=[u'h']
orth2phon[u'j']=[u'j']
orth2phon[u'k']=[u'k']
orth2phon[u'l']=[u'l']
orth2phon[u'm']=[u'm']
orth2phon[u'n']=[u'n']
orth2phon[u'p']=[u'p']
orth2phon[u'r']=[u'r']
orth2phon[u's']=[u's']
orth2phon[u't']=[u't']
orth2phon[u'v']=[u'v']
orth2phon[u'z']=[u'z']
orth2phon[u'w']=orth2phon[u'v']
orth2phon[u'x']=orth2phon[u'z']	#wrong
orth2phon[u'q']=orth2phon[u'k']

ipa2x=dict([("".join(v), k) for (k, v) in orth2phon.iteritems()])







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
						syllStr+=u"".join(orth2phon[y])
			else:
				syllStr+=u"".join(orth2phon[x])

		syllables.append(syllStr)

	words=[]

	sylls_text=[]
	for syll in Annotation.syllables:
		sylls_text.append(syll.lower())

	for stress in Annotation.stresses:
		words.append((u".".join([stress2stroke[stress[i]]+syllables[i] for i in range(len(syllables))]),sylls_text,{'broken':wordbroken}))	


	return words
