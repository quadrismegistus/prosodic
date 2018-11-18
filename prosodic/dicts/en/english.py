#encoding=utf-8
import sys,codecs,os,subprocess
from ipa import sampa2ipa
import pyphen

Pyphen = None

DIR_ROOT=os.path.split(globals()['__file__'])[0]
CMU_DICT_FN=os.path.join(DIR_ROOT,'english.tsv')
CMU_DICT={}

CACHE_DICT_FN=os.path.join(DIR_ROOT,'english.tts-cache.tsv')
CACHE_DICT_F=None




def load_cmu(fn=CMU_DICT_FN,config={}):
	global CMU_DICT
	fns=[fn]
	if config.get('en_TTS_cache',False):
		fns+=[CACHE_DICT_FN]

	for fn in fns:
		#print '>> loading words from:',fn
		if os.path.exists(fn):
			with codecs.open(fn,encoding='utf-8') as f:
				for ln in f:
					ln=ln.strip()
					if not ln or ln.count('\t')!=1: continue
					word,ipa=ln.split('\t')[:2]
					word=word.strip()
					ipa=ipa.strip().split()[0]
					if not word in CMU_DICT: CMU_DICT[word]=[]
					CMU_DICT[word]+=[ipa]

def write_to_cache(token,ipa):
	tokenl=token.lower()
	global CACHE_DICT_F
	if not CACHE_DICT_F:
		CACHE_DICT_F=codecs.open(CACHE_DICT_FN,'a',encoding='utf-8')

	CACHE_DICT_F.write(tokenl+'\t'+ipa+'\n')
	if not tokenl in CMU_DICT:
		CMU_DICT[tokenl]=[]
	CMU_DICT[tokenl]+=[ipa]



def get(token,config={},toprint=False):
	# If not CMU loaded
	global CMU_DICT
	if not CMU_DICT: load_cmu(config=config)

	# First try CMU
	tokenl=word_l=token.lower()
	ipas = CMU_DICT.get(tokenl,[])

	# First see if this is a contraction
	if not ipas:
		for contr,add_ipa in [("'d","d")]: # no longer doing ("'s","z")-- too simple
			if word_l.endswith(contr):
				word_l_unc = word_l[:-2]
				# if the uncontracted in the dictionary
				if word_l_unc in CMU_DICT:
					for wipa in CMU_DICT[word_l_unc]:
						wipa+=add_ipa
						ipas+=[wipa]

	# Otherwise use TTS
	if not ipas:
		TTS_ENGINE=config.get('en_TTS_ENGINE','')
		if TTS_ENGINE=='espeak':
			ipa=espeak2ipa(token)
			cmu=espeak2cmu(ipa)
			cmu_sylls = syllabify_cmu(cmu)
			if toprint: print ipa
			if toprint: print cmu
			if toprint: print cmu_sylls
			ipa = cmusylls2ipa(cmu_sylls)
			if toprint: print ipa
		elif TTS_ENGINE=='openmary':
			ipa=openmary2ipa(token)
		else:
			return None
		ipas=[ipa]

		if config.get('en_TTS_cache',False):
			for ipa in ipas:
				write_to_cache(token,ipa)


	## Syllabify the orthography if possible
	results = []
	iselision=[]
	for ipa in ipas:
		num_sylls=ipa.count('.')+1
		sylls_text = syllabify_orth(token,num_sylls=num_sylls)
		res = (ipa, sylls_text)
		if not res in results:
			results+=[res]
			iselision+=[False]


		if config.get('add_elided_pronunciations',0):
			for ipa2 in add_elisions(ipa):
				num_sylls2=ipa2.count('.')+1
				sylls_text2 = syllabify_orth(token,num_sylls=num_sylls2)
				res = (ipa2, sylls_text2)
				if not res in results:
					results+=[res]
					iselision+=[True]

	toreturn = [(a,b,{'is_elision':c}) for ((a,b),c) in zip(results,iselision)]

	# Return the results to the dictionary
	return toreturn

def add_elisions(_ipa):
	"""
	Add alternative pronunciations: those that have elided syllables
	"""
	replace={}

	# -OWER
	# e.g. tower, hour, bower, etc
	replace[u'aʊ.ɛː']=u'aʊr'


	# -INOUS
	# e.g. ominous, etc
	replace[u'ə.nəs']=u'nəs'

	# -EROUS
	# e.g. ponderous, adventurous
	replace[u'ɛː.əs']=u'rəs'

	# -IA-
	# e.g. plutonian, indian, assyrian, idea, etc
	replace[u'iː.ə']=u'jə'
	# -IOUS
	# e.g. studious, tedious, etc
	#replace[u'iː.əs']=u'iːəs'


	# -IER
	# e.g. happier
	replace[u'iː.ɛː']=u'ɪr'

	# -ERING
	# e.g. scattering, wondering, watering
	replace[u'ɛː.ɪŋ']=u'rɪŋ'

	# -ERY
	# e.g. memory
	# QUESTIONABLE
	#replace[u'ɛː.iː']=u'riː'

	# -ENING
	# e.g. opening
	replace[u'ə.nɪŋ']=u'nɪŋ'

	# -ENER
	# e.g. gardener
	replace[u'ə.nɛː']=u'nɛː'

	# -EL- (-ELLER, -ELLING, -ELLY)
	# e.g. traveller, dangling, gravelly
	# QUESTIONABLE
	#replace[u'ə.l']=u'l'

	# -IRE-
	# e.g. fire, fiery, attire, hired
	replace[u'ɪ.ɛː']=u'ɪr'

	# -EL, -UAL
	# e.g. jewel
	replace[u'uː.əl']=u'uːl'

	# -EVN
	# e.g. heaven, seven
	replace[u'ɛ.vən']=u'ɛvn'

	# -IOUS, -EER
	# e.g. sincerest, dear, incommodiously
	# QUESTIONABLE
	#replace[u'.ʌ.']=u'ʌ.'
	replace[u'eɪ.ʌ']=u'eɪʌ'

	new=[_ipa]
	for k,v in replace.items():
		if k in _ipa:
			new+=[_ipa.replace(k,v)]
	return new





def espeak2ipa(token):
	CMD='espeak -q -x '+token.replace("'","\\'").replace('"','\\"')
	#print CMD
	try:
		# @HACK FOR MPI
		#for k in os.environ.keys():
		#	if k.startswith('OMPI_') or k.startswith('PMIX_'):
		#		del os.environ[k]
		##

		res=subprocess.check_output(CMD.split()).strip()
		#print '>> espeak = ',[res]
		return res
	except (OSError,subprocess.CalledProcessError) as e:
		#print "!!",e
		return None

def tts2ipa(token,TTS_ENGINE=None):
	if TTS_ENGINE=='espeak':
		return espeak2ipa(token)
	elif TTS_ENGINE=='openmary':
		return openmary2ipa(token)
	else:
		#raise Exception("No TTS engine specified. Please select 'espeak' or 'openmary' in config.txt.")
		return None

def espeak2cmu(tok):
	import lexconvert
	return lexconvert.convert(tok,'espeak','cmu')

def ipa2cmu(tok):
	import lexconvert
	return lexconvert.convert(tok,'unicode-ipa','cmu')

def cmu2ipa(tok):
	import lexconvert
	res=lexconvert.convert(tok,'cmu','unicode-ipa')

	## BUG FIXES
	if tok.endswith(' T') and not res.endswith('t'): res=res+'t'
	return res

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


def syllabify_orth_with_hyphenate(token,num_sylls=None):
	from hyphenate import hyphenate_word
	l=hyphenate_word(token)
	if not num_sylls or len(l)==num_sylls:
		return l
	return []

def syllabify_orth_with_pyphen(token,num_sylls=None):
	global Pyphen
	if not Pyphen: Pyphen=pyphen.Pyphen(lang='en_US')
	sylls = Pyphen.inserted(token,hyphen='||||').split('||||')
	if len(sylls)==num_sylls: return sylls
	return []

def syllabify_orth(token,num_sylls=None):
	return syllabify_orth_with_pyphen(token,num_sylls=num_sylls)





### OPEN MARY

def openmary2ipa(word):
	import urllib2
	try:
		wordxml=openmary(word)
	except urllib2.URLError:
		return None
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
