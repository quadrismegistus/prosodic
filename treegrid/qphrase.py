import sys,pyparse,os

try:
	ifn=sys.argv[1]
except:
	ifn='/Users/ryan/Projects/kode/prosodic/corpora/stanfordparsed/'
	#exit("[usage]: qgrid.py [xml_filename_of_stanford_corenlp_parser_output]")


#ld=pyparse.parse2grid(fn,ldlim=10)


Phrases={}

for fn in os.listdir(ifn):
	if not fn.endswith('.xml'): continue
	print ">> phrase-collecting:",fn
	phrases=pyparse.parse2phrase(os.path.join(ifn,fn))
	for phrase in phrases:
		d={}
		if not len(phrase): continue
		for k in phrase[0]:
			d[k]=[]

		for phraseSlot in phrase:
			for k in phraseSlot:
				#if len(d[k])==0 or d[k][-1]!=phraseSlot[k]:
				d[k]+=[phraseSlot[k]]

		for k in d:
			d[k]=tuple(d[k])

		words=d['word']
		if len(words)<2: continue
		del d['word']

		print d
		print words
		print
		PhraseToken=pyparse.PhraseToken(**d)

		try:
			Phrases[words].addToken(PhraseToken)
		except KeyError:
			Phrases[words]=pyparse.PhraseType(words)
			Phrases[words].addToken(PhraseToken)
	
print ">> loaded",len(Phrases),"phrases"
import pickle

if ifn.endswith(os.path.sep): ifn=ifn[:-1]


ofn=ifn.split(os.path.sep)[-1]+'.pickle'
pickle.dump(Phrases,open(ofn,'wb'))
print ">> saved:",ofn