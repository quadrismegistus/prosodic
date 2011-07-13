import sys,os,prosodic as p

try:
	ifn=sys.argv[1]
except:
	ifn='/Users/ryan/kode/prosodic/corpora/stanfordparsed/'
	#exit("[usage]: qgrid.py [xml_filename_of_stanford_corenlp_parser_output]")


from ZODB.DB import DB
from ZEO import ClientStorage
import transaction

addr = 'localhost', '/tmp/zeosocket'
storage = ClientStorage.ClientStorage(addr)
db = DB(storage)
connection = db.open()
root = connection.root()

print root.keys()



class PhraseToken(object):
	def __init__(self,**args):
		for k,v in args.items():
			setattr(self,k,v)



class PhraseType(object):
	def __init__(self,words,freq=None,**args):
		for k,v in args.items():
			setattr(self,k,v)
		self.words=words
		self.freq=freq
		self.tokens=[]

	def __str__(self):
		return " ".join(self.words)

	def addToken(self,token):
		self.tokens.append(token)

def parse2words(parsestr):
	return [x.replace(')','') for x in parsestr.split() if ')' in x]

class Sentence(object):
	def __init__(self,parsestr,pgraph=None):
		self.parsestr=parsestr
		self.token=' '.join(parse2words(parsestr))
		self.parsed=p.Line(self.token)
		self.broken=self.parsed.broken
		#self.len_word=len(self.parsed.words())
		#self.len_syll=len(self.parsed.syllables())
		self.tokens=[]
		self.pgraph=pgraph

class Paragraph(object):
	def __init__(self):
		self.tokens=[]
		self.sentences=[]



def parse2phrase(ifn,phrasetype='NP',embedlimit=2,shuffle=False,ldlim=None):
	ofn=os.path.basename(ifn)
	f=open(ifn)
	t=str(f.read())
	f.close()
	sents=t.split('<sentence ')

	if shuffle:
		import random
		random.shuffle(sents)

	sentnum=0
	phrases=[]
	phrase=[]
	ld=[]
	for sentence in sents[1:]:
		sentnum+=1
		if ldlim and sentnum>ldlim: break
		parse=sentence.split('<parse>')[1].split('</parse>')[0]

		tokens=[]
		for token in sentence.split('<word>')[1:]:
			token=token.split('</word>')[0]
			tokens+=[token]
		sentlen_word=len(tokens)
		#print parse
		pdat=parse.split()
		sentlen_paren=len(pdat)
		wordi=0
		pnumi=-1
		pstack=[]
		words=[]
		wordnodes=[]
		embedlevel=0

		for pnum in range(len(pdat)):
			p=pdat[pnum]
			pnumi+=1

			pnop=p.replace('(','').replace(')','')
			if not pytxt.noPunc(pnop): continue
			if pnop==phrasetype:
				#print "yes"
				embedlevel=0
				phrase=[]


			pnode=(pnumi,pnop)

			#print pnumi,wordi,pnop,p,embedlevel
			#print phrase

			if p.startswith('('):		# is tag	
				#G.edge[pstack[-1]][pnode]['isFinal']=False
				pstack.append(pnode)
				if embedlevel!=None: embedlevel+=1
			else:						# is word
				#G.edge[pstack[-1]][pnode]['isFinal']=True

				## get word stats
				word=p.replace(')','')
				word=word.lower()

				words+=[word]
				wordnodes+=[pnode]
				stresslevel=0
				wordi+=1

				if embedlevel!=None:
					if embedlevel<=embedlimit:
						phrase+=[ {'word':word, 'paren_num':pnumi+1, 'word_num':wordi+1, 'word_sentlen':sentlen_word, 'paren_sentlen':sentlen_paren} ]

				## go through tags in stack according to the number of tags which closed
				num_closing_paren=p.count(')')

				#print num_closing_paren,pstack
				for i in range(num_closing_paren):
					if embedlevel!=None: embedlevel-=1
					if len(pstack):
						pt=pstack.pop()

					#print pt
					#print pt
					if i==num_closing_paren-1:
						if num_closing_paren<=embedlimit and pt[1]==phrasetype:
						#if pt[1]==phrasetype:
							phrases+=[phrase]
							phrase=[]
							embedlevel=None

	return phrases











Phrases={}

for fn in os.listdir(ifn):
	if not fn.endswith('.xml'): continue
	print ">> phrase-collecting:",fn
	phrases=parse2phrase(os.path.join(ifn,fn))
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

		PhraseToken=PhraseToken(**d)

		try:
			Phrases[words].addToken(PhraseToken)
		except KeyError:
			Phrases[words]=PhraseType(words)
			Phrases[words].addToken(PhraseToken)
	
print ">> loaded",len(Phrases),"phrases"
import pickle

if ifn.endswith(os.path.sep): ifn=ifn[:-1]


ofn=ifn.split(os.path.sep)[-1]+'.pickle'
pickle.dump(Phrases,open(ofn,'wb'))
print ">> saved:",ofn