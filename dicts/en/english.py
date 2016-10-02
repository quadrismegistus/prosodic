#encoding=utf-8
import sys,codecs,os,subprocess
from ipa import sampa2ipa


def get(token,config={}):
	TTS_ENGINE=config.get('en_TTS_ENGINE','')
	if TTS_ENGINE=='espeak':
		ipa=espeak2ipa(token)
		cmu=ipa2cmu(ipa)
		cmu_sylls = syllabify_cmu(cmu)
		ipa = cmusylls2ipa(cmu_sylls)
	elif TTS_ENGINE=='openmary':
		ipa=openmary2ipa(token)
	else:
		return None

	num_sylls=ipa.count('.')+1
	sylls_text = syllabify_orth(token,num_sylls=num_sylls)
	return [(ipa, sylls_text)]

def espeak2ipa(token):
	CMD='espeak -q --ipa '+token
	#print CMD
	return subprocess.check_output(CMD.split()).strip()

def tts2ipa(token,TTS_ENGINE=None):
	if TTS_ENGINE=='espeak':
		return espeak2ipa(token)
	elif TTS_ENGINE=='openmary':
		return openmary2ipa(token)
	else:
		#raise Exception("No TTS engine specified. Please select 'espeak' or 'openmary' in config.txt.")
		return None

def ipa2cmu(tok):
	import lexconvert
	return lexconvert.convert(tok,'unicode-ipa','cmu')

def cmu2ipa(tok):
	import lexconvert
	return lexconvert.convert(tok,'cmu','unicode-ipa')

def syllabify_cmu(cmu_token):
	import syllabify as sy
	cmu_token=cmu_token.replace(' 2','2').replace(' 1','1') # fix prim/sec stress markings for syllabify
	sylls = sy.syllabify(sy.English, cmu_token)
	#for x in sylls:
	#	print x
	return sylls

def cmusylls2ipa(sylls):
	new_cmu=[]
	for syl in sylls:
		stress, onset, nucleus, coda = syl
		"""if not stress:
			stress_str=""
		elif stress==1:
			stress_str="'"
			stress_str=str(stress)
		else:
			stress_str="`"
			stress_str=str(stress)
		"""
		if stress:
			nucleus = [nucleus[0]+" "+str(stress)] + nucleus[1:]

		_newcmu = " ".join(onset+nucleus+coda).strip().replace("  "," ")
		new_cmu+=[_newcmu]
	new_cmu =" 0 ".join(new_cmu)
	#print new_cmu

	## ipa
	ipa=cmu2ipa(new_cmu)
	#print ipa
	# clean
	ipa_sylls = ipa.split('.')
	for i,syl in enumerate(ipa_sylls):
		if u"ˈ" in syl:
			syl="'"+syl.replace(u"ˈ","")
		if u"ˌ" in syl:
			syl="`"+syl.replace(u"ˌ","")
		ipa_sylls[i]=syl
	ipa=".".join(ipa_sylls)
	#print ipa
	return ipa


def syllabify_orth(token,num_sylls=None):
	from hyphenate import hyphenate_word
	l=hyphenate_word(token)
	if not num_sylls or len(l)==num_sylls:
		return l
	return []





### OPEN MARY

def openmary2ipa(word):
	wordxml=openmary(word)
	sylls=[]
	for syll in wordxml.find_all('syllable'):
		syllstr="'" if syll.get('stress',None) else ""
		for ph in syll['ph'].split():
			syllstr+=sampa2ipa(ph)
		sylls+=[syllstr]

	from Phoneme import Phoneme
	if len(sylls)>1 and not True in [Phoneme(phon).isVowel() for phon in sylls[0]]:
		sylls=[sylls[0]+sylls[1]]+ (sylls[2:] if len(sylls)>2 else [])

	pronounc='.'.join(sylls)
	return pronounc

def openmary(line):
	import re, urlparse, urllib2

	try:
		from unidecode import unidecode
	except ImportError:
		raise Exception("""
			In order to use OpenMary, you need to install the unidecode python module. Run:
			pip install unidecode
			""")

	try:
		import bs4
	except ImportError:
		raise Exception("""
			In order to use OpenMary, you need to install the bs4 python module. Run:
			pip install bs4
			""")

	#print '>> openmary:',line
	line=line.replace("'","") # apostrophes seem to make openmary oversyllabify by a mile
	line=unidecode(line)
	#print '>> openmary:',line
	#print
	

	def urlEncodeNonAscii(b):
		return re.sub('[\x80-\xFF]', lambda c: '%%%02x' % ord(c.group(0)), b)

	def iriToUri(iri):
		parts= urlparse.urlparse(iri)
		return urlparse.urlunparse(
			part.encode('idna') if parti==1 else urlEncodeNonAscii(part.encode('utf-8'))
			for parti, part in enumerate(parts)
		)

	def bigrams(l):
		return ngram(l,2)

	def ngram(l,n=3):
		grams=[]
		gram=[]
		for x in l:
			gram.append(x)
			if len(gram)<n: continue
			g=tuple(gram)
			grams.append(g)
			gram.reverse()
			gram.pop()
			gram.reverse()
		return grams



	line=line.replace(' ','+')
	link=u'http://localhost:59125/process?INPUT_TEXT={0}&INPUT_TYPE=TEXT&OUTPUT_TYPE=ALLOPHONES&LOCALE=en_US'.format(line)
	f=urllib2.urlopen(iriToUri(link))
	t=f.read()
	f.close()
	
	### OPEN MARY CLEANING OPERATIONS
	xml=bs4.BeautifulSoup(t,'html.parser')
	
	## fix word string problem
	for word in xml.find_all('t'): word['token']=word.text.strip()

	## CONTRACTION FIX
	for para in xml.find_all('p'):
		for phrase in para.find_all('phrase'):
			wordlist=[word for word in phrase.find_all('t') if len(list(word.find_all('syllable')))]
			for word1,word2 in bigrams(wordlist):
				w2text=word2.text.strip().lower()
				if w2text.startswith("'"):
					phones2add=word2.find_all('syllable')[-1]['ph'].strip()
					word1.find_all('syllable')[-1]['ph']+=' '+phones2add
					word1['token']+=w2text
					word2.decompose()
	
	
	return xml

