from __future__ import division
import sys,re,os,codecs

from Stanza import Stanza
from Line import Line
from Word import Word
from entity import entity,being
from tools import *
from operator import itemgetter
#import prosodic

def openmary(line):
	import re, urlparse, pytxt

	def urlEncodeNonAscii(b):
		return re.sub('[\x80-\xFF]', lambda c: '%%%02x' % ord(c.group(0)), b)

	def iriToUri(iri):
		parts= urlparse.urlparse(iri)
		return urlparse.urlunparse(
			part.encode('idna') if parti==1 else urlEncodeNonAscii(part.encode('utf-8'))
			for parti, part in enumerate(parts)
		)

	import urllib2,pytxt
	#line=pytxt.ascii(line).replace(' ','+')
	line=line.replace(' ','+')
	link=u'http://localhost:59125/process?INPUT_TEXT={0}&INPUT_TYPE=TEXT&OUTPUT_TYPE=ALLOPHONES&LOCALE=en_US'.format(line)
	f=urllib2.urlopen(iriToUri(link))
	t=f.read()
	f.close()
	
	### OPEN MARY CLEANING OPERATIONS
	import bs4
	xml=bs4.BeautifulSoup(t)
	
	## fix word string problem
	for word in xml.find_all('t'): word['token']=word.text.strip()

	## CONTRACTION FIX
	for para in xml.find_all('p'):
		for phrase in para.find_all('phrase'):
			wordlist=[word for word in phrase.find_all('t') if len(list(word.find_all('syllable')))]
			for word1,word2 in pytxt.bigrams(wordlist):
				w2text=word2.text.strip().lower()
				if w2text.startswith("'"):
					phones2add=word2.find_all('syllable')[-1]['ph'].strip()
					word1.find_all('syllable')[-1]['ph']+=' '+phones2add
					word1['token']+=w2text
					word2.decompose()
	
	t=xml.prettify()
	#####
	
	return t

class Text(entity):
	def __init__(self,filename,lang=None,printout=None,limWord=False,linebreak=None): #',;:.?!()[]{}<>'
		## set language and other essential attributes
		import prosodic
		self.lang=self.set_lang(filename) if not lang else lang
		self.dict=prosodic.dict[self.lang]
		self.featpaths={}
		self.__parses={}
		self.__bestparses={}
		self.phrasebreak_punct = unicode(",;:.?!()[]{}<>")
		self.phrasebreak=prosodic.config['linebreak'].strip()
		self.limWord = limWord
		self.feats = {}
		self.children = []
		self.isUnicode=True
		
		## phrasebreak features
		if self.phrasebreak=='line':
			pass
		elif self.phrasebreak.startswith("line"):
			self.phrasebreak_punct=unicode(self.phrasebreak.replace("line",""))
			self.phrasebreak='both'
		else:
			self.phrasebreak_punct=unicode(self.phrasebreak)
		
		## load/write-load text
		if os.path.exists(filename) and filename!='.':
			self.filename = filename
			self.name = filename.split("/").pop().strip()
			file=codecs.open(filename,encoding='utf-8',errors='replace')
			self.init_text(file)
			#self.init_run_mary(file)
		elif '</maryxml>' in filename:
			self.name='OpenMary'
			self.filename=filename
			self.init_mary(filename)
		else:
			lines = filename.split('\n')
			self.name = lines[0]
			self.filename = lines[0].replace(' ','_')[:100]+'.txt'
			#self.init_text(lines)
			self.init_run_mary(filename)
		
		## clean
		self.children = [stanza for stanza in self.children if not stanza.empty()]
		for stanza in self.children: stanza.children = [line for line in stanza.children if not line.empty()]
		

	def set_lang(self,filename):
		import prosodic
		if filename[1:2]=="." and (filename[0:2] in prosodic.dict):
			lang=filename[0:2]
		elif prosodic.lang:
			lang=prosodic.lang
		else:
			lang=choose(prosodic.languages,"in what language is '"+self.name+"' written?")
			if not lang:
				lang=prosodic.languages[0]
				print "!! language choice not recognized. defaulting to: "+lang
			else:
				lang=lang.pop()

		if not lang in prosodic.dict:
			lang0=lang
			lang=prosodic.languages[0]
			print "!! language "+lang0+" not recognized. defaulting to: "+lang

		return lang
		
	def init_run_mary(self,text):
		import lexconvert,bs4
		numwords = 0
		stanza=self.newchild()
		line=stanza.newchild()
		
		for stanzatext in text.split('\n\n'):
			stanzatext=stanzatext.strip()
			if not stanzatext: continue
			
			for linetext in stanzatext.split('\n'):
				linetext=linetext.strip()
				if not linetext: continue
				
				wordlist=linetext.split()
				for i,word in enumerate(wordlist):
					p0,word,p1=gleanPunc2(word)
					if p0 and not line.empty(): line.finish()
					if not word: continue
					
					if stanza.finished: stanza = self.newchild()
					if line.finished: line = stanza.newchild()
					
					if self.dict.has(word):
						words=self.dict.get(word)
						for w in words: w.origin='cmu'
					else:
						## make word from openmary
						wordxml=bs4.BeautifulSoup(openmary(word))
						sylls=[]
						for syll in wordxml.find_all('syllable'):
							syllstr="'" if syll.get('stress',None) else ""
							syllstr+=lexconvert.convert(syll['ph'],'x-sampa','unicode-ipa')
							sylls+=[syllstr]

						from Phoneme import Phoneme
						if len(sylls)>1 and not True in [Phoneme(phon).isVowel() for phon in sylls[0]]:
							sylls=[sylls[0]+sylls[1]]+ (sylls[2:] if len(sylls)>2 else [])

						pronounc='.'.join(sylls)
						words=[ self.dict.make((pronounc,[]), word) ]
						for w in words: w.origin='openmary'
					
					line.newchild(words)
					if p1 and not line.empty(): line.finish()
					numwords+=1
				
				if not line.empty(): line.finish()
			if not line.empty(): line.finish()
			if not stanza.empty(): stanza.finish()			
		
		
		
	def init_mary(self,xml):
		import lexconvert,bs4
		xml=bs4.BeautifulSoup(xml)
		numwords = 0
		stanza=self.newchild()
		line=stanza.newchild()
		
		
		for para in xml.find_all('p'):
			for phrase in para.find_all('phrase'):
				
				for word in phrase.find_all('t'):
					if stanza.finished: stanza = self.newchild()
					if line.finished: line = stanza.newchild()
					wordstr=word['token']
					if not word.get('ph',None): continue
					if self.dict.has(wordstr):
						words=self.dict.get(wordstr)
						for w in words: w.origin='cmu'
						#print ">>",wordstr,words
					else:
						#print "??",wordstr
						## make word from openmary
						sylls=[]
						for syll in word.find_all('syllable'):
							syllstr="'" if syll.get('stress',None) else ""
							syllstr+=lexconvert.convert(syll['ph'],'x-sampa','unicode-ipa')
							sylls+=[syllstr]
						
						from Phoneme import Phoneme
						if len(sylls)>1 and not True in [Phoneme(phon).isVowel() for phon in sylls[0]]:
							sylls=[sylls[0]+sylls[1]]+ (sylls[2:] if len(sylls)>2 else [])
						
						
						pronounc='.'.join(sylls)
						words=[ self.dict.make((pronounc,[]), wordstr) ]
						for w in words: w.origin='openmary'
					
					line.newchild(words)
					numwords+=1
				if not line.empty(): line.finish()
			if not line.empty(): line.finish()
			if not stanza.empty(): stanza.finish()
				
			
				
		
		
		
	
	def init_text(self,lines_or_file):
		## create first stanza,line 
		stanza = self.newchild()
		line = stanza.newchild()	# returns a new Line, the child of Stanza
		numwords = 0
		recentpunct=True
		import prosodic
		tokenizer=prosodic.config['tokenizer'].replace('\\\\','\\')
		
		## [loop] lines
		for ln in lines_or_file:
			ln=ln.strip()
			if self.limWord and numwords>limWord: break
			
			# split into words			
			toks = re.findall(tokenizer,ln.strip(),flags=re.UNICODE) if self.isUnicode else re.findall(tokenizer,ln.strip())
			toks = [tok.strip() for tok in toks if tok.strip()]
			numtoks=len(toks)
			
			## if no words, mark stanza/para end
			if (not ln or numtoks < 1):
				if not stanza.empty():
					stanza.finish()
				continue
	
			## [loop] words
			for toknum,tok in enumerate(toks):
				(tok,punct) = gleanPunc(tok)
				
				if stanza.finished: stanza = self.newchild()
				if line.finished: line = stanza.newchild()
				
				newwords=self.dict.get(tok)
				line.newchild(newwords)
				numwords+=1
				
				self.om(str(numwords).zfill(6)+"\t"+str(newwords[0].output_minform()))
				
				if punct and len(line.children) and self.phrasebreak != 'line':
					if (self.phrasebreak_punct.find(punct) > -1):
						line.finish()
			
			## if line-based breaks, end line
			if (self.phrasebreak == 'both') or (self.phrasebreak == 'line'):
				line.finish()
		
	
	
	
	## def parse
	def parse(self,meter=None,arbiter='Line'):
		"""Parse this text metrically."""
		
		if not meter:
			from Meter import Meter,genDefault
			meter = genDefault()
		
		self.__parses[meter]=[]
		self.__bestparses[meter]=[]
		ents=self.ents(arbiter)
		for ent in ents:
			ent.parse(meter)
			self.__parses[meter].append( ent.allParses(meter) )
			self.__bestparses[meter].append( ent.bestParse(meter) )
	
		#self.scansion_prepare(conscious=True)
		self.scansion(meter=meter,conscious=True)
	
	@property
	def isParsed(self):
		return (not False in [bool(_poemline.isParsed()) for _poemline in self.lines()])
	
	@property
	def numSyllables(self):
		if self.isParsed:
			num_syll=0
			for bp in self.bestParses():
				for pos in bp.positions:
					num_syll+=len(pos.slots)
		else:
			num_syll=len(self.syllables())
		return num_syll
	
	def scansion(self,meter=None,conscious=False):
		"""Print out the parses and their violations in scansion format."""
		
		if not meter:
			try:
				meter=self.__bestparses.keys()[0]
			except:
				return
		
		self.scansion_prepare(meter=meter,conscious=conscious)
		for line in self.lines():
			try:
				line.scansion(meter=meter,conscious=conscious)
			except AttributeError:
				print "!!! Line skipped [Unknown word]:"
				print line
				print line.words()
				print
	
	
	def allParses(self,meter=None):
		"""Return a list of lists of parses."""
		
		if not meter:
			itms=self.__parses.items()
			if not len(itms): return []
			for mtr,parses in itms:
				return parses
		
		try:
			return self.__parses[meter]
		except KeyError:
			return []
	
	
	def bestParses(self,meter=None):
		"""Return a list of the best parse per line."""
		
		if not meter:
			itms=self.__bestparses.items()
			if not len(itms): return []
			for mtr,parses in itms:
				return parses
		
		try:
			return self.__bestparses[meter]
		except KeyError:
			return []

	
				
	
	## children	
	def givebirth(self):
		"""Return an empty Stanza."""
		
                stanza=Stanza()
                #stanza.parent=self
		return stanza
	
	def validlines(self):
		"""Return all lines within which Prosodic understood all words."""
		
		return [ln for ln in self.lines() if (not ln.isBroken() and not ln.ignoreMe)]
	
	#def stats(self):
	#	o="\t"+makeminlength(" ",16)+"\t#tokens\t#types\t\t%typ/tok\n"
	#	dict=self.dict
	#	stats=self.getStats()
	#	
	#	for k,v in sorted(stats.items(),key=itemgetter(0)):
	#		numtok=v[0]
	#		numtyp=v[1]
	#		typovertok=v[2]
	#		
	#		o+="\t"+makeminlength(str(k),16)+"\t"+str(numtok)+"\t"+str(numtyp)+"\t"+str(typovertok)+"\n"
	#		
	#	return o
	
	def __repr__(self):
		return "<Text."+str(self.name)+"> ("+str(len(self.words()))+" words)"