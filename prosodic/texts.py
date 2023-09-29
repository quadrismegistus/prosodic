from .imports import *


class Text(entity):
	sep: str = ''
	child_type: str = 'Stanza'

	def __init__(self,
			txt: str = '',
			filename: str = '',
			lang: Optional[str] = None,
			parent: Optional[entity] = None,
			children: Optional[list] = None,
			**kwargs
			):
		logger.trace(f'{self.__class__.__name__}({txt}, {filename}, {lang})')

		if not txt and not filename and not children:
			raise Exception('must provide either txt, filename, or children objects')

		self._txt = get_txt(txt,filename)
		self.fn = filename

		if self.__class__.__name__ == 'Text':
			self.lang=lang if lang else (detect_lang(self._txt) if self._txt else '??')
		
		self.parent = parent
		self.children = [] if children is None else children
		self.attrs = kwargs
		self._init = False
		self.init()


	
	def init(self):
		if self._init: return self
		self._init=True
		from .lines import Stanza, Line
		from .words import Word
		logger.trace(self.__class__.__name__)


		df = self.df_tokens = pd.DataFrame(tokenize_sentwords_iter(self.txt))
		text_stanzas = []
		for stanza_i,stanza_df in df.groupby('stanza_i'):
			stanza_d = {k:v for k,v in dict(stanza_df.iloc[0]).items() if k.split('_')[0] not in {'word','line'}}
			stanza_lines = []
			for line_i,line_df in stanza_df.groupby('line_i'):
				line_words = []
				line_d = {k:v for k,v in dict(line_df.iloc[0]).items() if k.split('_')[0] not in {'word'}}
				for i,word_row in line_df.iterrows():
					word_d=dict(word_row)
					word_d['word_lang'] = self.lang
					token = word_row.word_str
					wordforms = self.lang_obj.get(token)
					print(wordforms)
					word = Word(token, children=wordforms, **word_d)
					print(word.children)
					line_words.append(word)
				line = Line(children=line_words, **line_d)
				for word in line_words: word.parent = line
				stanza_lines.append(line)
			stanza = Stanza(children=stanza_lines, parent=self, **stanza_d)
			for line in stanza_lines: line.parent = stanza
			text_stanzas.append(stanza)
		self.children = text_stanzas
		return self

	def __repr__(self):
		attrstr=' '.join(f'{k}={v.strip() if type(v)==str else v}' for k,v in self.attrs.items())
		attrstr=f' [{attrstr}]' if attrstr else ''
		return f'({self.__class__.__name__}: {self.txt.strip()}){attrstr}'



	@property
	def txt(self):
		logger.trace(self.__class__.__name__)
		if self._txt: txt = self._txt
		elif self.children: txt=self.sep.join(child.txt for child in self.children)
		return clean_text(txt)

	@cached_property
	def lang_obj(self):
		logger.trace(self.__class__.__name__)
		from .langs import English
		if self.lang=='en': return English()



# 	def init_text(self,lines_or_file):
# 		## create first stanza,line
# 		stanza = self.newchild()
# 		stanza.num=stanza_num=1
# 		line = stanza.newchild()	# returns a new Line, the child of Stanza
# 		line.num=line_num=1
# 		numwords = 0
# 		recentpunct=True
# 		import prosodic
# 		tokenizer=prosodic.config['tokenizer'].replace('\\\\','\\')

# 		## [loop] lines
# 		for ln in lines_or_file:
# 			if REPLACE_DASHES:
# 				for dash in DASHES:
# 					ln=ln.replace(dash,' '+dash+' ')
# 			ln=ln.strip()
# 			#print ln,type(ln)
# 			if self.limWord and numwords>self.limWord: break

# 			# split into words
# 			#print self.isUnicode
# 			toks = re.findall(tokenizer,ln.strip(),flags=re.UNICODE) if self.isUnicode else re.findall(tokenizer,ln.strip())
# 			#print toks
# 			#print tokenizer
# 			toks = [tok.strip() for tok in toks if tok.strip()]
# 			numtoks=len(toks)

# 			## if no words, mark stanza/para end
# 			if (not ln or numtoks < 1):
# 				if not stanza.empty():
# 					stanza.finish()
# 				continue

# 			## [loop] words
# 			for toknum,tok in enumerate(toks):
# 				#(tok,punct) = gleanPunc(tok)
# 				(punct0,tok,punct) = gleanPunc2(tok)

# 				if stanza.finished:
# 					stanza = self.newchild()
# 					stanza.num = stanza_num = stanza_num+1
# 				if line.finished:
# 					line = stanza.newchild()
# 					line.num = line_num = line_num+1

# 				if punct0:
# 					wordtok=WordToken([],token=punct0,is_punct=True, line = line)
# 					line.newchild(wordtok)

# 				if tok:
# 					newwords=self.dict.get(tok,stress_ambiguity=self.stress_ambiguity)
# 					wordtok = WordToken(newwords,token=tok,is_punct=False, line = line)
# 					line.newchild(wordtok)
# 					numwords+=1

# 					self.om(str(numwords).zfill(6)+"\t"+str(newwords[0].output_minform()))

# 				if punct:
# 					wordtok=WordToken([],token=punct,is_punct=True, line = line)
# 					line.newchild(wordtok)

# 				if punct and len(line.children) and self.phrasebreak != 'line':
# 					if (self.phrasebreak_punct.find(punct) > -1):
# 						line.finish()

# 			## if line-based breaks, end line
# 			if (self.phrasebreak == 'both') or (self.phrasebreak == 'line'):
# 				line.finish()

# 		if self.config.get('parse_using_metrical_tree',False) and self.lang=='en':
# 			import time
# 			then=time.time()
# 			print('>> parsing text using MetricalTree (because "parse_using_metrical_tree" setting activated in config.py)...')
# 			try:
# 				self.parse_mtree()
# 			except ImportError as e:
# 				print('!! text not parsed because python module missing:',str(e).split()[-1])
# 				print('!! to install, run: pip install',str(e).split()[-1])
# 				print('!! if you don\'t have pip installed, run this script: <https://bootstrap.pypa.io/get-pip.py>')
# 				print()
# 			except LookupError as e:
# 				emsg=str(e)

# 				if "Resource" in emsg and "punkt" in emsg and "not found" in emsg:
# 					print('!! text not parsed because NLTK missing needed data: punkt')
# 					print('!! to install, run: python -c "import nltk; nltk.download(\'punkt\')"')
# 					print()
# 				elif 'stanford-parser.jar' in emsg:
# 					import prosodic
# 					print('!! text not parsed because Stanford NLP Parser not installed')
# 					print('!! to install, run:\n!!    prosodic install stanford_parser')
# 					# print('!! if that doesn\'t work:')
# 					# print('!! \t1) download: http://nlp.stanford.edu/software/stanford-parser-full-2015-04-20.zip')
# 					# print('!! \t2) unzip it')
# 					# print('!! \t3) move the unzipped directory to:',self.dir_nlp_data+'/Stanford Library/stanford-parser-full-2015-04-20/')
# 					print()
# 				else:
# 					print('!! text not parsed for unknown reason!')
# 					print('!! error message received:')
# 					print(emsg)
# 					print()
# 			except AssertionError:
# 				print("This is a bug in PROSODIC that is Ryan Heuser's fault. [Bug ID: Assertion_MTree]")
# 				print("Please kindly report it to: https://github.com/quadrismegistus/prosodic/issues")
# 				print()
# 			except Exception as e:
# 				emsg=str(e)
# 				print('!! text not parsed for unknown reason!')
# 				print('!! error message received:')
# 				print(emsg)
# 				print()
# 			#"""
# 			now=time.time()
# 			print('>> done:',round(now-then,2),'seconds')

# 	def parse_mtree(self):
# 		if self.lang!='en': raise Exception("MetricalTree parsing only works currently for English text.")

# 		import metricaltree as mtree
# 		mtree.set_paths(self.dir_nlp_data)

# 		wordtoks = self.wordtokens()
# 		toks = [wtok.token for wtok in wordtoks]

# 		pauses = mtree.pause_splitter_tokens(toks)

# 		#sents = [sent for pause in pauses for sent in pause]
# 		sents=[]
# 		for pause in pauses:
# 			sents.extend(mtree.split_sentences_from_tokens(pause))
# 		parser = mtree.return_parser(self.dir_nlp_data)
# 		trees = list(parser.lex_parse_sents(sents, verbose=False))
# 		stats = parser.get_stats(trees,arto=True,format_pandas=False)
# 		assert len(stats)==len(wordtoks)

# 		sents = []
# 		sent = []
# 		sent_id=None
# 		for wTok,wStat in zip(wordtoks,stats):
# 			if sent_id!=wStat['sidx']:
# 				sent_id=wStat['sidx']
# 				if sent: sents+=[sent]
# 				sent=[]

# 			sent+=[wTok]
# 			#for k,v in wStat.items():
# 			#	setattr(wTok,k,v)
# 			if not hasattr(wTok,'feats'): wTok.feats={}
# 			for k,v in list(wStat.items()):
# 				if k in mtree.INFO_DO_NOT_STORE: continue
# 				wTok.feats[k]=v

# 		if sent: sents+=[sent]
# 		assert len(sents) == len(trees)

# 		from Sentence import Sentence
# 		for sent,tree in zip(sents,trees):
# 			sentobj = Sentence(sent, tree)
# 			self._sentences+=[sentobj]

# 		# create a normalized stress per line
# 		import numpy as np
# 		for line in self.lines():
# 			wtoks = line.children

# 			# norm mean
# 			stresses = [wtok.feats['norm_mean'] for wtok in wtoks if not np.isnan(wtok.feats['norm_mean'])]
# 			max_stress = float(max(stresses))
# 			min_stress = float(min(stresses))
# 			for wtok in wtoks:
# 				wtok.feats['norm_mean_line']=(wtok.feats['norm_mean']-min_stress)/(max_stress-min_stress) if max_stress else np.nan

# 			# mean
# 			stresses = [wtok.feats['mean'] for wtok in wtoks if not np.isnan(wtok.feats['mean'])]
# 			min_stress = float(min(stresses))
# 			diff = 1.0 - min_stress
# 			for wtok in wtoks:
# 				wtok.feats['mean_line']=wtok.feats['mean'] + diff




# 	def grid(self,nspace=10):
# 		return '\n\n'.join(sent.grid(nspace=nspace) for sent in self.sentences())

# 	def clear_parses(self):
# 		self.__parses={}
# 		self.__bestparses={}
# 		self.__boundParses={}
# 		self.__parsed_ents={}

# 	def iparse(self,meter=None,num_processes=1,arbiter='Line',line_lim=None,toprint=True):
# 		"""Parse this text metrically, yielding it line by line."""
# 		from Meter import Meter,genDefault,parse_ent,parse_ent_mp
# 		import multiprocessing as mp
# 		meter=self.get_meter(meter)

# 		# set internal attributes
# 		self.__parses[meter.id]=[]
# 		self.__bestparses[meter.id]=[]
# 		self.__boundParses[meter.id]=[]
# 		self.__parsed_ents[meter.id]=[]

# 		lines = self.lines()
# 		lines=lines[:line_lim]
# 		numlines = len(lines)

# 		init=self
# 		ents=self.ents(arbiter)
# 		smax=self.config.get('line_maxsylls',100)
# 		smin=self.config.get('line_minsylls',0)
# 		#print '>> # of lines to parse:',len(ents)
# 		ents = [e for e in ents if e.num_syll >= smin and e.num_syll<=smax]
# 		#print '>> # of lines to parse after applying min/max line settings:',len(ents)

# 		self.scansion_prepare(meter=meter,conscious=toprint)

# 		numents=len(ents)

# 		#pool=mp.Pool(1)
# 		objects = [(ent,meter,init,toprint) for ent in ents]

# 		if num_processes>1:
# 			print('!! MULTIPROCESSING PARSING IS NOT WORKING YET !!')
# 			pool = mp.Pool(num_processes)
# 			jobs = [pool.apply_async(parse_ent_mp,(x,)) for x in objects]
# 			for j in jobs:
# 				print(j.get())
# 				yield j.get()
# 		else:
# 			now=time.time()
# 			clock_snum=0
# 			# for ei,ent in enumerate(pool.imap(parse_ent_mp,objects)):
# 			for ei,objectx in enumerate(tqdm(objects)):
# 				clock_snum+=objectx[0].num_syll
# 				if ei and not ei%100:
# 					nownow=time.time()
# 					if being.config['print_to_screen']:
# 						print('>> parsing line #',ei,'of',numents,'lines','[',round(float(clock_snum/(nownow-now)),2),'syllables/second',']')
# 					now=nownow
# 					clock_snum=0

# 				yield parse_ent_mp(objectx)

# 		if being.config['print_to_screen']:
# 			print('\n\n>> parsing complete in:',time.time()-now,'seconds')


# 	def parse(self,meter=None,arbiter='Line',line_lim=None):
# 		list(self.iparse(meter=meter,arbiter=arbiter,line_lim=line_lim))

# 	## def parse
# 	def parse1(self,meter=None,arbiter='Line'):
# 		"""@DEPRECATED
# 		Parse this text metrically."""
# 		from Meter import Meter,genDefault,parse_ent
# 		meter=self.get_meter(meter)

# 		if self.isFromFile: print('>> parsing',self.name,'with meter:',meter.id)
# 		self.meter=meter

# 		self.__parses[meter.id]=[]
# 		self.__bestparses[meter.id]=[]
# 		self.__boundParses[meter.id]=[]
# 		self.__parsed_ents[meter.id]=[]

# 		init=self
# 		"""
# 		if not hasattr(init,'meter_stats'):
# 			init.meter_stats={'lines':{},'positions':{},'texts':{}, '_ot':{},'_constraints':{}}
# 		if not hasattr(init,'bestparses'):
# 			init.bestparses=[]

# 		init.meter=meter
# 		init.meter_stats['_constraints']=sorted(init.meter.constraints)
# 		init.ckeys="\t".join(sorted([str(x) for x in init.meter.constraints]))
# 		"""

# 		ents=self.ents(arbiter)
# 		smax=self.config.get('line_maxsylls',100)
# 		smin=self.config.get('line_minsylls',0)
# 		#print '>> # of lines to parse:',len(ents)
# 		ents = [e for e in ents if e.num_syll >= smin and e.num_syll<=smax]
# 		#print '>> # of lines to parse after applying min/max line settings:',len(ents)

# 		self.scansion_prepare(meter=meter,conscious=True)



# 		numents=len(ents)
# 		now=time.time()
# 		clock_snum=0
# 		for ei,ent in enumerate(ents):
# 			clock_snum+=ent.num_syll
# 			if ei and not ei%100:
# 				nownow=time.time()
# 				print('>> parsing line #',ei,'of',numents,'lines','[',round(float(clock_snum/(nownow-now)),2),'syllables/second',']')
# 				now=nownow
# 				clock_snum=0
# 			ent.parse(meter,init=init)
# 			self.__parses[meter.id].append( ent.allParses(meter) )
# 			self.__bestparses[meter.id].append( ent.bestParse(meter) )
# 			self.__boundParses[meter.id].append( ent.boundParses(meter) )
# 			self.__parsed_ents[meter.id].append(ent)
# 			ent.scansion(meter=meter,conscious=True)

# 		if being.config['print_to_screen']: print()

# 		#self.scansion_prepare(conscious=True)
# 		#self.scansion(meter=meter,conscious=True)

# 	def iparse2line(self,i,meter=None):
# 		meter=self.get_meter(meter)
# 		return self.__parsed_ents[meter.id][i]

# 	#@property
# 	def isParsed(self):
# 		#return (not False in [bool(_poemline.isParsed()) for _poemline in self.lines()])
# 		return bool(hasattr(self,'_Text__bestparses') and self.__bestparses)


# 	@property
# 	def numSyllables(self):
# 		if self.isParsed:
# 			num_syll=0
# 			for bp in self.bestParses():
# 				for pos in bp.positions:
# 					num_syll+=len(pos.slots)
# 		else:
# 			num_syll=len(self.syllables())
# 		return num_syll

# 	def scansion(self,meter=None,conscious=True):
# 		"""Print out the parses and their violations in scansion format."""
# 		meter=self.get_meter(meter)
# 		self.scansion_prepare(meter=meter,conscious=conscious)
# 		for line in self.lines():
# 			try:
# 				line.scansion(meter=meter,conscious=conscious)
# 			except AttributeError:
# 				print("!!! Line skipped [Unknown word]:")
# 				print(line)
# 				print(line.words())
# 				print()

# 	def allParsesByLine(self,meter=None):
# 		parses=self.allParses(meter=meter)
# 		for parse_product in product(*parses):
# 			yield parse_product

# 	def allParses(self,meter=None,include_bounded=False,one_per_meter=True):
# 		"""Return a list of lists of parses."""

# 		meter=self.get_meter(meter)
# 		try:
# 			parses=self.__parses[meter.id]

# 			if one_per_meter:
# 				toreturn=[]
# 				for _parses in parses:
# 					sofar=set()
# 					_parses2=[]
# 					for _p in _parses:
# 						_pm=_p.str_meter()
# 						if not _pm in sofar:
# 							sofar|={_pm}
# 							if _p.isBounded and _p.boundedBy.str_meter() == _pm:
# 								pass
# 							else:
# 								_parses2+=[_p]
# 					toreturn+=[_parses2]
# 				parses=toreturn

# 			if include_bounded:
# 				boundedParses=self.boundParses(meter)
# 				return [bp+boundp for bp,boundp in zip(toreturn,boundedParses)]
# 			else:
# 				return parses

# 		except (KeyError,IndexError) as e:
# 			return []


# 	def get_meter(self,meter=None):
# 		if not meter:
# 			if self.meter:
# 				meter=self.meter
# 			elif hasattr(self,'_Text__bestparses') and self.__bestparses:
# 				return self.get_meter(sorted(self.__bestparses.keys())[0])
# 			else:
# 				import Meter
# 				meter=Meter.genDefault()
# 				#print '>> no meter specified. defaulting to this meter:'
# 				#print meter
# 		elif type(meter) in [str,str]:
# 			meter= self.config['meters'][meter]
# 		else:
# 			pass

# 		if not meter.id in self.config['meters']: self.config['meters'][meter.id]=meter
# 		return meter

# 	def report(self,meter=None,include_bounded=False,reverse=True):
# 		#return #super(Text,self).report(meter=meter if meter else self.meter)
# 		meter=self.get_meter(meter)
# 		return entity.report(self, meter=meter,include_bounded=include_bounded,reverse=reverse)


# 	def bestParses(self,meter=None):
# 		"""Return a list of the best parse per line."""
# 		meter=self.get_meter(meter)
# 		try:
# 			return self.__bestparses[meter.id]
# 		except (KeyError,IndexError) as e:
# 			return []

# 	def boundParses(self,meter=None,include_stressbounds=False):
# 		"""Return a list of the best parse per line."""
# 		meter=self.get_meter(meter)
# 		try:
# 			toreturn=[]
# 			for _parses in self.__boundParses[meter.id]:
# 				sofar=set()
# 				_parses2=[]
# 				for _p in _parses:
# 					_pm=_p.str_meter()
# 					if not _pm in sofar:
# 						if _p.isBounded and _p.boundedBy.str_meter() == _pm:
# 							pass
# 						else:
# 							sofar|={_pm}
# 							_parses2+=[_p]
# 				toreturn+=[_parses2]
# 			return toreturn

# 		except (KeyError,IndexError) as e:
# 			return [[]]

# 	def viol_words(self):
# 		bp=self.bestParses()
# 		if not bp: return ''
# 		constraintd={}
# 		for parse in bp:
# 			for mpos in parse.positions:
# 				viold=False
# 				words=set([slot.word.token for slot in mpos.slots])
# 				for ck,cv in list(mpos.constraintScores.items()):
# 					if not cv: continue
# 					ckk=ck.name.replace('.','_')
# 					if not ckk in constraintd: constraintd[ckk]=set()
# 					constraintd[ckk]|=words
# 		for k in constraintd:
# 			constraintd[k]=list(constraintd[k])

# 		return constraintd

# 	def parsed_words(self):
# 		bp=self.bestParses()
# 		if not bp: return []

# 		wordNow=None
# 		words=[]
# 		for parse in bp:
# 			for mpos in parse.positions:
# 				for mslot in mpos.slots:
# 					word=mslot.i_word
# 					if wordNow is word: continue
# 					words+=[word]
# 					wordNow=word
# 		return words


# 	def parse_strs(self,text=True,viols=True,text_poly=False):
# 		for parses in self.allParsesByLine():
# 			yield self.parse_str(text=text,viols=viols,text_poly=text_poly,parses=parses)

# 	def parse_str(self,text=True,viols=True,text_poly=False,parses=False):
# 		bp=self.bestParses() if not parses else parses
# 		if not bp: return ''
# 		all_strs=[]
# 		letters=['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R']
# 		for parse in bp:
# 			parse_strs=[]
# 			for mpos in parse.positions:
# 				viold=False
# 				for ck,cv in list(mpos.constraintScores.items()):
# 					if cv:
# 						viold=True
# 						break

# 				if text_poly:
# 					word_pos=[slot.wordpos[0] for slot in mpos.slots]
# 					mpos_letters=[letters[pos-1] for pos in word_pos]
# 					if not mpos.isStrong: mpos_letters=[letter.lower() for letter in mpos_letters]
# 					mpos_str='.'.join(mpos_letters)

# 				elif not text:
# 					mpos_str=mpos.mstr
# 				else:
# 					mpos_str=mpos.token


# 				if viols and viold: mpos_str+='*'

# 				parse_strs+=[mpos_str]
# 			all_strs+=['|'.join(parse_strs)]
# 		return '||'.join(all_strs)

# 	@property
# 	def numBeats(self):
# 		parse_str=self.parse_str(text=False,viols=False)
# 		s_feet=[x for x in parse_str.split('|') if x.startswith('s')]
# 		return len(s_feet)


# 	@property
# 	def constraintd(self):
# 		return self.constraintViolations(self,normalize=True)


# 	def constraintViolations(self,normalize=False,use_weights=False):
# 		bp=self.bestParses()
# 		viold={}
# 		if not bp: return {}
# 		mstrs=[]
# 		for parse in bp:
# 			for mpos in parse.positions:
# 				for ck,cv in list(mpos.constraintScores.items()):
# 					ck=ck.name
# 					if not ck in viold: viold[ck]=[]
# 					val = (cv if not use_weights else 1) if cv else 0
# 					viold[ck]+=[val]

# 		for ck in viold:
# 			lv=viold[ck]
# 			viold[ck]=sum(lv)/float(len(lv)) if normalize else sum(lv)

# 		return viold

# 	@property
# 	def ambiguity(self):
# 		ap=self.allParses()
# 		line_numparses=[]
# 		line_parselen=0
# 		if not ap: return 0
# 		for parselist in ap:
# 			numparses=len(parselist)
# 			line_numparses+=[numparses]

# 		import operator
# 		ambigx=reduce(operator.mul, line_numparses, 1)
# 		return ambigx


# 	def get_parses(self, meter):
# 		return self.__parses[meter.id]

# 	## children
# 	def givebirth(self):
# 		"""Return an empty Stanza."""
# 		stanza=Stanza()
# 		return stanza

# 	def validlines(self):
# 		"""Return all lines within which Prosodic understood all words."""

# 		return [ln for ln in self.lines() if (not ln.isBroken() and not ln.ignoreMe)]

# 	# def __repr__(self):
# 		# return "<Text."+str(self.name)+"> ("+str(len(self.words()))+" words)"








# class Corpus(entity):

# 	def __init__(self,corpusRoot,lang=None,printout=None,corpusFiles="*.txt",phrasebreak=',;:.?!()[]{}<>',limWord=None):
# 		import prosodic
# 		## entity-shared attribtues

# 		self.lang=prosodic.config['lang'] if not lang else lang
# 		self.dict=prosodic.dict[self.lang]
# 		self.parent=False
# 		#self.foldername=corpusRoot.split("/").pop().strip()
# 		self.children=[]	# texts
# 		self.feats = {}
# 		self.featpaths={}
# 		self.finished = False
# 		self.config=prosodic.config
# 		self.meter=None
# 		if printout==None: printout=being.printout

# 		## corpus attributes
# 		self.corpusRoot = corpusRoot
# 		self.corpusFiles = corpusFiles
# 		self.name=os.path.split(os.path.abspath(self.corpusRoot))[-1]
# 		self.foldername=self.name
# 		self.dir_results = prosodic.dir_results

# 		## language may be **, ie, determinable by the first two character of the textfile ("en" for english, "fi" for finnish, etc)
# 		if not lang:
# 			lang=being.lang
# 		self.lang = lang

# 		## [loop] through filenames
# 		for filename in glob.glob(os.path.join(corpusRoot, corpusFiles)):
# 			## create and adopt the text
# 			newtext = Text(filename,printout=printout)
# 			self.newchild(newtext)	# append Text to children


# 	def parse(self,meter=None,arbiter='Line'):
# 		if not meter and self.meter: meter=self.meter
# 		for text in self.children:
# 			text.parse(meter=meter,arbiter=arbiter)
# 			if not meter: self.meter=meter=text.meter

# 	def report(self,meter=None,include_bounded=False):
# 		for text in self.children:
# 			print()
# 			print('>> text:',text.name)
# 			text.report(meter=meter,include_bounded=include_bounded)

# 	def scansion(self,meter=None):
# 		for text in self.children:
# 			print('>> text:',text.name)
# 			text.scansion(meter=meter)
# 			print()

# 	def get_meter(self,meter=None):
# 		if not meter:
# 			child=self.children[0] if self.children else None
# 			if self.meter:
# 				meter=self.meter
# 			elif child and hasattr(child,'_Text__bestparses') and child.__bestparses:
# 				return self.get_meter(sorted(child.__bestparses.keys())[0])
# 			else:
# 				import Meter
# 				meter=Meter.genDefault()
# 		elif type(meter) in [str,str]:
# 			meter= self.config['meters'][meter]
# 		else:
# 			pass

# 		return meter

# 	def stats(self,meter=None,all_parses=False,funcs=['stats_lines','stats_lines_ot','stats_positions']):
# 		for funcname in funcs:
# 			func=getattr(self,funcname)
# 			for dx in func(meter=meter,all_parses=all_parses):
# 				yield dx


# 	def stats_lines(self,meter=None,all_parses=False):
# 		meter=self.get_meter(meter)

# 		def _writegen():
# 			for text in self.children:
# 				for dx in text.stats_lines(meter=meter):
# 					dx['header']=['text']+dx['header']
# 					yield dx

# 		ofn=os.path.join(self.dir_results, 'stats','corpora',self.name, self.name+'.lines.'+('meter='+meter.id if meter else 'unknown')+'.csv')
# 		if not os.path.exists(os.path.split(ofn)[0]): os.makedirs(os.path.split(ofn)[0])
# 		for dx in writegengen(ofn, _writegen): yield dx
# 		print('>> saved:',ofn)

# 	def isParsed(self):
# 		#return (not False in [bool(_poemline.isParsed()) for _poemline in self.lines()])
# 		return not (False in [child.isParsed() for child in self.children])

# 	def stats_lines_ot(self,meter=None,all_parses=False):
# 		meter=self.get_meter(meter)

# 		def _writegen():
# 			for text in self.children:
# 				for dx in text.stats_lines_ot(meter=meter):
# 					#dx['text']=text.name
# 					#dx['corpus']=self.name
# 					dx['header']=['text']+dx['header']
# 					yield dx

# 		ofn=os.path.join(self.dir_results, 'stats','corpora',self.name, self.name+'.lines_ot.'+('meter='+meter.id if meter else 'unknown')+'.csv')
# 		if not os.path.exists(os.path.split(ofn)[0]): os.makedirs(os.path.split(ofn)[0])
# 		for dx in writegengen(ofn, _writegen): yield dx
# 		print('>> saved:',ofn)

# 	def grid(self,nspace=10):
# 		grid=[]
# 		for text in self.children:
# 			textgrid=text.grid(nspace=nspace)
# 			if textgrid:
# 				grid+=['## TEXT: '+text.name+'\n\n'+textgrid]
# 		return '\n\n\n'.join(grid)


# 	def stats_positions(self,meter=None,all_parses=False):

# 		def _writegen():
# 			for text in self.children:
# 				for dx in text.stats_positions(meter=meter,all_parses=all_parses):
# 					#dx['text']=text.name
# 					#dx['corpus']=self.name
# 					dx['header']=['text']+dx['header']
# 					yield dx

# 		ofn=os.path.join(self.dir_results, 'stats','corpora',self.name, self.name+'.positions.csv')
# 		if not os.path.exists(os.path.split(ofn)[0]): os.makedirs(os.path.split(ofn)[0])
# 		for dx in writegengen(ofn, _writegen): yield dx
# 		print('>> saved:',ofn)

# 	def sentences(self):
# 		return [sent for text in self.children for sent in text.sentences()]




class Subtext(Text):
	def init(self):
		self._init=True