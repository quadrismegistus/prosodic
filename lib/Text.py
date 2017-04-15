# -*- coding: UTF-8 -*-
from __future__ import division
import sys,re,os,codecs,time

from Stanza import Stanza
from Line import Line
from Word import Word
from entity import entity,being
from tools import *
from operator import itemgetter
from ipa import sampa2ipa
#import prosodic



class Text(entity):
	def __init__(self,filename,lang=None,meter=None,printout=None,limWord=False,linebreak=None,use_dict=True,fix_phons_novowel=True,stress_ambiguity=True): #',;:.?!()[]{}<>'
		## set language and other essential attributes
		import prosodic
		self.lang=self.set_lang(filename) if not lang else lang
		self.dict=prosodic.dict[self.lang]
		self.featpaths={}
		self.__parses={}
		self.__bestparses={}
		self.__boundParses={}
		self.__parsed_ents={}
		self.phrasebreak_punct = unicode(",;:.?!()[]{}<>")
		self.phrasebreak=prosodic.config['linebreak'].strip()
		self.limWord = limWord
		self.isFromFile = False
		self.feats = {}
		self.children = []
		self.isUnicode=True
		self.use_dict=use_dict
		self.fix_phons_novowel=fix_phons_novowel
		self.stress_ambiguity=stress_ambiguity
		self.dir_prosodic=prosodic.dir_prosodic
		self.dir_results=prosodic.dir_results
		self.config=prosodic.config
		self.meter=self.config['meters'][meter] if meter and meter in self.config['meters'] else None
		#self.meterd={]}



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
			print '>> loading text:',self.name
			file=codecs.open(filename,encoding='utf-8',errors='replace')
			#self.init_text(file)
			#if prosodic.config['use_open_mary']:
			#	self.init_run_mary(file.read())
			#else:
			self.isFromFile=True
			self.init_text(file)
		elif '</maryxml>' in filename:
			self.name='OpenMary'
			print '>> loading text:',self.name
			self.filename=filename
			self.isFromFile=False
			self.init_mary(filename)
		else:
			lines = filename.split('\n')
			self.name = noPunc(lines[0].lower())[:25].strip().replace(' ','-')
			#print '>> loading text:',self.name
			self.filename = lines[0].replace(' ','_')[:100]+'.txt'
			#self.init_text(lines)
			#if prosodic.config['use_open_mary']:
			#	self.init_run_mary(filename)
			#else:
			self.isFromFile=False
			self.init_text(lines)

		## clean
		self.children = [stanza for stanza in self.children if not stanza.empty()]
		for stanza in self.children: stanza.children = [line for line in stanza.children if not line.empty()]


	def set_lang(self,filename):
		filename=os.path.basename(filename)
		import prosodic
		if filename[2]=="." and (filename[0:2] in prosodic.dict):
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



	def stats_lines(self,meter=None,all_parses=False,viols=True):
		#parses = self.allParses(meter=meter) if all_parses else [[parse] for parse in self.bestParses(meter=meter)]
		meter=self.get_meter(meter)
		constraint_names = [c.name_weight for c in meter.constraints]
		header = ['line', 'parse', 'meter', 'num_sylls', 'num_parses', 'num_viols', 'score_viols'] + constraint_names

		def _writegen():
			for line in self.lines():
				dx={'text':self.name, 'line':str(line), 'header':header}
				bp=line.bestParse(meter)
				ap=line.allParses(meter)
				dx['parse']=bp.posString(viols=viols) if bp else ''
				dx['meter']=bp.str_meter() if bp else ''
				dx['num_parses']=len(ap)
				dx['num_viols'] = bp.totalCount if bp else ''
				dx['score_viols'] = bp.score() if bp else ''
				dx['num_sylls']=bp.num_sylls if bp else ''
				#dx['meter']=meter.id
				#if bp:
				#for c,v in bp.constraintScores.items():
				for c in meter.constraints:
					dx[c.name_weight]=bp.constraintScores[c] if bp and c in bp.constraintScores else ''
				yield dx

		name=self.name.replace('.txt','')
		ofn=os.path.join(self.dir_results, 'stats','texts',name, name+'.lines.'+('meter='+meter.id if meter else 'unknown')+'.csv')
		if not os.path.exists(os.path.split(ofn)[0]): os.makedirs(os.path.split(ofn)[0])
		for dx in writegengen(ofn, _writegen):
			yield dx
		print '>> saved:',ofn

	def stats_lines_ot(self,meter=None,all_parses=False,viols=True):
		#parses = self.allParses(meter=meter) if all_parses else [[parse] for parse in self.bestParses(meter=meter)]
		meter=self.get_meter(meter)
		constraint_names = [str(c) for c in meter.constraints]
		header = ['line', 'parse', 'meter', 'num_viols', 'score_viols'] + constraint_names

		def _writegen():
			for line in self.lines():

				#bp=line.bestParse(meter)
				ap=line.allParses(meter)
				if all_parses: ap+=line.boundParses(meter)

				for pi,parse in enumerate(ap):
					dx={'line':str(line) if not pi else ''}
					dx['text']=self.name
					dx['header']=header
					dx['parse']=parse.posString(viols=viols)
					#dx['2_obs']='1'
					dx['score_viols'] = parse.score()
					dx['num_viols'] = parse.totalCount
					dx['meter']=parse.str_meter()
					for c in meter.constraints:
						dx[str(c)]=parse.constraintCounts[c] if parse and c in parse.constraintScores and parse.constraintScores[c] else ''
					yield dx

		name=self.name.replace('.txt','')
		ofn=os.path.join(self.dir_results, 'stats','texts',name, name+'.lines_ot.'+('meter='+meter.id if meter else 'unknown')+'.csv')
		if not os.path.exists(os.path.split(ofn)[0]): os.makedirs(os.path.split(ofn)[0])
		for dx in writegengen(ofn, _writegen):
			yield dx
		print '>> saved:',ofn


	def stats_positions(self,meter=None,all_parses=False):

		"""Produce statistics from the parser"""

		"""Positions
		All feats of slots
		All constraint violations


		"""
		parses = self.allParses(meter=meter) if all_parses else [[parse] for parse in self.bestParses(meter=meter)]

		dx={}
		for parselist in parses:

			for parse in parselist:
				if not parse: continue
				slot_i=0
				for pos in parse.positions:
					for slot in pos.slots:
						slot_i+=1

						feat_dicts = [slot.feats, pos.constraintScores, pos.feats]
						for feat_dict in feat_dicts:
							for k,v in feat_dict.items():
								dk = (slot_i,str(k))
								if not dk in dx: dx[dk]=[]
								dx[dk]+=[v]


		def _writegen():
			for ((slot_i,k),l) in sorted(dx.items()):
				l2=[]
				for x in l:
					if type(x)==bool:
						x=1 if x else 0
					elif type(x)==type(None):
						x=0
					elif type(x) in [str,unicode]:
						continue
					else:
						x=float(x)
					if x>1: x=1
					l2+=[x]
				#print k, l2
				#try:
				if not l2: continue

				avg=sum(l2) / float(len(l2))
				count=sum(l2)
				chances=len(l2)
				#except TypeError:
				#	continue

				odx={'slot_num':slot_i, 'statistic':k, 'average':avg, 'count':count, 'chances':chances, 'text':self.name}
				odx['header']=['slot_num', 'statistic','count','chances','average']
				#print odx
				yield odx

		name=self.name.replace('.txt','')
		ofn=os.path.join(self.dir_results, 'stats','texts',name, name+'.positions.csv')
		#print ofn
		if not os.path.exists(os.path.split(ofn)[0]): os.makedirs(os.path.split(ofn)[0])
		for dx in writegengen(ofn, _writegen):
			yield dx
		print '>> saved:',ofn
		#for

	def stats(self,meter=None,all_parses=False,funcs=['stats_lines','stats_lines_ot','stats_positions']):
		for funcname in funcs:
			func=getattr(self,funcname)
			for dx in func(meter=meter,all_parses=all_parses):
				yield dx



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
		from Meter import Meter,genDefault,parse_ent
		meter=self.get_meter(meter)

		if self.isFromFile: print '>> parsing',self.name,'with meter:',meter.id
		self.meter=meter

		self.__parses[meter.id]=[]
		self.__bestparses[meter.id]=[]
		self.__boundParses[meter.id]=[]
		self.__parsed_ents[meter.id]=[]

		init=self
		if not hasattr(init,'meter_stats'):
			init.meter_stats={'lines':{},'positions':{},'texts':{}, '_ot':{},'_constraints':{}}
		if not hasattr(init,'bestparses'):
			init.bestparses=[]

		init.meter=meter
		init.meter_stats['_constraints']=sorted(init.meter.constraints)
		init.ckeys="\t".join(sorted([str(x) for x in init.meter.constraints]))

		ents=self.ents(arbiter)
		smax=self.config.get('line_maxsylls',100)
		smin=self.config.get('line_minsylls',0)
		#print '>> # of lines to parse:',len(ents)
		ents = [e for e in ents if e.num_syll >= smin and e.num_syll<=smax]
		#print '>> # of lines to parse after applying min/max line settings:',len(ents)

		self.scansion_prepare(meter=meter,conscious=True)



		numents=len(ents)
		now=time.time()
		clock_snum=0
		for ei,ent in enumerate(ents):
			clock_snum+=ent.num_syll
			if ei and not ei%100:
				nownow=time.time()
				print '>> parsing line #',ei,'of',numents,'lines','[',round(float(clock_snum/(nownow-now)),2),'syllables/second',']'
				now=nownow
				clock_snum=0
			ent.parse(meter,init=init)
			self.__parses[meter.id].append( ent.allParses(meter) )
			self.__bestparses[meter.id].append( ent.bestParse(meter) )
			self.__boundParses[meter.id].append( ent.boundParses(meter) )
			self.__parsed_ents[meter.id].append(ent)
			ent.scansion(meter=meter,conscious=True)

		if being.config['print_to_screen']: print

		#self.scansion_prepare(conscious=True)
		#self.scansion(meter=meter,conscious=True)

	def iparse2line(self,i,meter=None):
		meter=self.get_meter(meter)
		return self.__parsed_ents[meter.id][i]

	#@property
	def isParsed(self):
		#return (not False in [bool(_poemline.isParsed()) for _poemline in self.lines()])
		return bool(hasattr(self,'_Text__bestparses') and self.__bestparses)


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
		meter=self.get_meter(meter)
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

	def allParses(self,meter=None,include_bounded=False,one_per_meter=True):
		"""Return a list of lists of parses."""

		meter=self.get_meter(meter)
		try:
			parses=self.__parses[meter.id]

			if one_per_meter:
				toreturn=[]
				for _parses in parses:
					sofar=set()
					_parses2=[]
					for _p in _parses:
						_pm=_p.str_meter()
						if not _pm in sofar:
							sofar|={_pm}
							if _p.isBounded and _p.boundedBy.str_meter() == _pm:
								pass
							else:
								_parses2+=[_p]
					toreturn+=[_parses2]
				parses=toreturn

			if include_bounded:
				boundedParses=self.boundParses(meter)
				return [bp+boundp for bp,boundp in zip(toreturn,boundedParses)]
			else:
				return parses

		except (KeyError,IndexError) as e:
			return []


	def get_meter(self,meter=None):
		if not meter:
			if self.meter:
				meter=self.meter
			elif hasattr(self,'_Text__bestparses') and self.__bestparses:
				return self.get_meter(sorted(self.__bestparses.keys())[0])
			else:
				import Meter
				meter=Meter.genDefault()
				#print '>> no meter specified. defaulting to this meter:'
				#print meter
		elif type(meter) in [str,unicode]:
			meter= self.config['meters'][meter]
		else:
			pass

		return meter

	def report(self,meter=None,include_bounded=False):
		#return #super(Text,self).report(meter=meter if meter else self.meter)
		meter=self.get_meter(meter)
		return entity.report(self, meter=meter,include_bounded=include_bounded)


	def bestParses(self,meter=None):
		"""Return a list of the best parse per line."""
		meter=self.get_meter(meter)
		try:
			return self.__bestparses[meter.id]
		except (KeyError,IndexError) as e:
			return []

	def boundParses(self,meter=None,include_stressbounds=False):
		"""Return a list of the best parse per line."""
		meter=self.get_meter(meter)
		try:
			toreturn=[]
			for _parses in self.__boundParses[meter.id]:
				sofar=set()
				_parses2=[]
				for _p in _parses:
					_pm=_p.str_meter()
					if not _pm in sofar:
						if _p.isBounded and _p.boundedBy.str_meter() == _pm:
							pass
						else:
							sofar|={_pm}
							_parses2+=[_p]
				toreturn+=[_parses2]
			return toreturn

		except (KeyError,IndexError) as e:
			return [[]]

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

	def __repr__(self):
		return "<Text."+str(self.name)+"> ("+str(len(self.words()))+" words)"
