# -*- coding: UTF-8 -*-
from __future__ import division
import sys,re,os,codecs

from Stanza import Stanza
from Line import Line
from Word import Word
from entity import entity,being
from tools import *
from operator import itemgetter
from ipa import sampa2ipa
#import prosodic



class Text(entity):
	def __init__(self,filename,lang=None,printout=None,limWord=False,linebreak=None,use_dict=True,fix_phons_novowel=True,stress_ambiguity=True): #',;:.?!()[]{}<>'
		## set language and other essential attributes
		import prosodic
		self.lang=self.set_lang(filename) if not lang else lang
		self.dict=prosodic.dict[self.lang]
		self.featpaths={}
		self.__parses={}
		self.__bestparses={}
		self.__parsed_ents={}
		self.phrasebreak_punct = unicode(",;:.?!()[]{}<>")
		self.phrasebreak=prosodic.config['linebreak'].strip()
		self.limWord = limWord
		self.feats = {}
		self.children = []
		self.isUnicode=True
		self.use_dict=use_dict
		self.fix_phons_novowel=fix_phons_novowel
		self.stress_ambiguity=stress_ambiguity
		
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
		#if False:
			self.filename = filename
			self.name = filename.split("/").pop().strip()
			file=codecs.open(filename,encoding='utf-8',errors='replace')
			#self.init_text(file)
			#if prosodic.config['use_open_mary']:
			#	self.init_run_mary(file.read())
			#else:
			self.init_text(file)
		elif '</maryxml>' in filename:
			self.name='OpenMary'
			self.filename=filename
			self.init_mary(filename)
		else:
			lines = filename.split('\n')
			self.name = noPunc(lines[0].lower())[:25].strip().replace(' ','-')
			self.filename = lines[0].replace(' ','_')[:100]+'.txt'
			#self.init_text(lines)
			#if prosodic.config['use_open_mary']:
			#	self.init_run_mary(filename)
			#else:
			self.init_text(lines)
		
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
		#print ">> init_run_mary..."
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
						words=self.dict.get(word,stress_ambiguity=self.stress_ambiguity)
						for w in words: w.origin='cmu'
					elif self.lang=='en':
						## make word from openmary
						wordxml=bs4.BeautifulSoup(openmary(word),'html.parser')
						sylls=[]
						for syll in wordxml.find_all('syllable'):
							syllstr="'" if syll.get('stress',None) else ""
							#print syll['ph']
							for ph in syll['ph'].split():
								syllstr+=sampa2ipa(ph)
							#print syllstr
							#print
							sylls+=[syllstr]

						from Phoneme import Phoneme
						if len(sylls)>1 and not True in [Phoneme(phon).isVowel() for phon in sylls[0]]:
							sylls=[sylls[0]+sylls[1]]+ (sylls[2:] if len(sylls)>2 else [])

						pronounc='.'.join(sylls)
						words=[ self.dict.make((pronounc,[]), word) ]
						for w in words: w.origin='openmary'
					else:
						words=self.dict.get(word,stress_ambiguity=self.stress_ambiguity)
					
					line.newchild(words)
					if self.phrasebreak!='line':
						if p1 and not line.empty(): line.finish()
					numwords+=1
				
				if not line.empty(): line.finish()
			if not line.empty(): line.finish()
			if not stanza.empty(): stanza.finish()			
		
		
		
	def init_mary(self,xml):
		import lexconvert,bs4
		xml=bs4.BeautifulSoup(xml,'html.parser')
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
					if self.dict.has(wordstr) and self.use_dict:
						#print "HAVE",wordstr
						words=self.dict.get(wordstr,stress_ambiguity=self.stress_ambiguity)
						for w in words: w.origin='cmu'
						#print ">>",wordstr,words
					else:
						#print "??",wordstr
						## make word from openmary
						sylls=[]
						for syll in word.find_all('syllable'):
							syllstr="'" if syll.get('stress',None) else ""

							for ph in syll('ph'):
								ph_str=ph['p']
								ph_ipa=sampa2ipa(ph_str)
								#print ph_str, ph_ipa
								syllstr+=ph_ipa

							#syllstr+=lexconvert.convert(syll['ph'],'sampa','unicode-ipa')
							#print syllstr, syll['ph']
							sylls+=[syllstr]
						
						#if self.fix_phons_novowel:
							from Phoneme import Phoneme
							#if len(sylls)>1 and not True in [Phoneme(phon).isVowel() for phon in sylls[0]]:
							if len(sylls)>1 and sylls[0]==u'ʃ':
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
			if self.limWord and numwords>self.limWord: break
			
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
				

				if tok:
					newwords=self.dict.get(tok,stress_ambiguity=self.stress_ambiguity)
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
			#print '>> no meter specified. defaulting to this meter:'
			#print meter
			pass
		else:
			#print '>> meter specified:'
			#print meter
			pass

		#print '>> Parsing with meter:',meter
		
		self.__parses[meter]=[]
		self.__bestparses[meter]=[]
		self.__parsed_ents[meter]=[]

		init=self
		if not hasattr(init,'meter_stats'): init.meter_stats={'lines':{},'positions':{},'texts':{}, '_ot':{},'_constraints':{}}
		if not hasattr(init,'bestparses'): init.bestparses=[]
		init.meter=meter
		init.meter_stats['_constraints']=sorted(init.meter.constraints)
		init.ckeys="\t".join(sorted([str(x) for x in init.meter.constraints]))

		ents=self.ents(arbiter)
		self.scansion_prepare(meter=meter,conscious=True)
		for ent in ents:
			ent.parse(meter,init=init)
			self.__parses[meter].append( ent.allParses(meter) )
			self.__bestparses[meter].append( ent.bestParse(meter) )
			self.__parsed_ents[meter].append(ent)
			ent.scansion(meter=meter,conscious=True)
	
		#self.scansion_prepare(conscious=True)
		#self.scansion(meter=meter,conscious=True)
	
	def iparse2line(self,i,meter=None):
		if not meter:
			meter=self.__parsed_ents.keys()[0]
		return self.__parsed_ents[meter][i]

	#@property
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
	
	def allParsesByLine(self,meter=None):
		parses=self.allParses(meter=meter)
		for parse_product in product(*parses):
			yield parse_product
	
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

	def viol_words(self):
		bp=self.bestParses()
		if not bp: return ''
		constraintd={}
		for parse in bp:
			for mpos in parse.positions:
				viold=False
				words=set([slot.word.token for slot in mpos.slots])
				for ck,cv in mpos.constraintScores.items():
					if not cv: continue
					ckk=ck.name.replace('.','_')
					if not ckk in constraintd: constraintd[ckk]=set()
					constraintd[ckk]|=words
		for k in constraintd:
			constraintd[k]=list(constraintd[k])
		
		return constraintd

	def parsed_words(self):
		bp=self.bestParses()
		if not bp: return []
		
		wordNow=None
		words=[]
		for parse in bp:
			for mpos in parse.positions:
				for mslot in mpos.slots:
					word=mslot.i_word
					if wordNow is word: continue
					words+=[word]
					wordNow=word
		return words


	def parse_strs(self,text=True,viols=True,text_poly=False):
		for parses in self.allParsesByLine():
			yield self.parse_str(text=text,viols=viols,text_poly=text_poly,parses=parses)

	def parse_str(self,text=True,viols=True,text_poly=False,parses=False):
		bp=self.bestParses() if not parses else parses
		if not bp: return ''
		all_strs=[]
		letters=['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R']
		for parse in bp:
			parse_strs=[]
			for mpos in parse.positions:
				viold=False
				for ck,cv in mpos.constraintScores.items():
					if cv:
						viold=True
						break

				if text_poly:
					word_pos=[slot.wordpos[0] for slot in mpos.slots]
					mpos_letters=[letters[pos-1] for pos in word_pos]
					if not mpos.isStrong: mpos_letters=[letter.lower() for letter in mpos_letters]
					mpos_str='.'.join(mpos_letters)

				elif not text:
					mpos_str=mpos.mstr
				else:
					mpos_str=repr(mpos)
				

				if viols and viold: mpos_str+='*'

				parse_strs+=[mpos_str]
			all_strs+=['|'.join(parse_strs)]
		return '||'.join(all_strs)

	@property
	def numBeats(self):
		parse_str=self.parse_str(text=False,viols=False)
		s_feet=[x for x in parse_str.split('|') if x.startswith('s')]
		return len(s_feet)

	
	@property
	def constraintd(self):
		return self.constraintViolations(self,normalize=True)

	
	def constraintViolations(self,normalize=False,use_weights=False):
		bp=self.bestParses()
		viold={}
		if not bp: return {}
		mstrs=[]
		for parse in bp:
			for mpos in parse.positions:
				for ck,cv in mpos.constraintScores.items():
					ck=ck.name
					if not ck in viold: viold[ck]=[]
					val = (cv if not use_weights else 1) if cv else 0
					viold[ck]+=[val]
		
		for ck in viold:
			lv=viold[ck]
			viold[ck]=sum(lv)/float(len(lv)) if normalize else sum(lv)

		return viold

	@property
	def ambiguity(self):
		ap=self.allParses()
		line_numparses=[]
		line_parselen=0
		if not ap: return 0
		for parselist in ap:
			numparses=len(parselist)
			line_numparses+=[numparses]
		
		import operator
		ambigx=reduce(operator.mul, line_numparses, 1)
		return ambigx

				
	
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