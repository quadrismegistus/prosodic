# -*- coding: UTF-8 -*-
from __future__ import division
import sys,re,os,codecs,time

from Stanza import Stanza
from Line import Line
from Word import Word
from WordToken import WordToken
from entity import entity,being
from tools import *
from operator import itemgetter
#import prosodic

DASHES=['--',u'–',u'—','-']
REPLACE_DASHES = True


class Text(entity):
	def __init__(self,filename=None,lang=None,meter=None,printout=None,limWord=False,linebreak=None,use_dict=True,fix_phons_novowel=True,stress_ambiguity=True): #',;:.?!()[]{}<>'
		## set language and other essential attributes
		import prosodic

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
		self.dir_mtree = prosodic.dir_mtree
		self.config=prosodic.config
		self.meter=self.config['meters'][meter] if meter and meter in self.config['meters'] else None
		self._sentences=[]
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
		if not filename:
			self.name = '[undefined]'
			self.isFromFile = False
			self.lang=self.set_lang(filename) if not lang else lang
			self.dict=prosodic.dict[self.lang]
		elif os.path.exists(filename) and filename!='.':
		#if False:
			self.filename = filename
			self.name = filename.split("/").pop().strip()
			print '>> loading text:',self.name
			file=codecs.open(filename,encoding='utf-8',errors='replace')
			self.isFromFile=True
			self.lang=self.set_lang(filename) if not lang else lang
			self.dict=prosodic.dict[self.lang]
			self.init_text(file)
		else:
			txt=filename
			if type(txt)!=unicode: txt=txt.decode('utf-8',errors='replace')
			lines = txt.split('\n')
			self.name = noPunc(lines[0].lower())[:25].strip().replace(' ','-')
			#print '>> loading text:',self.name
			self.filename = lines[0].replace(' ','_')[:100]+'.txt'
			#self.init_text(lines)
			self.isFromFile=False
			self.lang=self.set_lang(filename) if not lang else lang
			self.dict=prosodic.dict[self.lang]
			self.init_text(lines)


		## clean
		self.children = [stanza for stanza in self.children if not stanza.empty()]
		for stanza in self.children: stanza.children = [line for line in stanza.children if not line.empty()]

	def sentences(self):
		return self._sentences

	def set_lang(self,filename):
		if not filename: return 'en'
		filename=os.path.basename(filename)
		import prosodic
		if self.isFromFile and len(filename)>2 and filename[2]=="." and (filename[0:2] in prosodic.dict):
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



	def stats_lines(self,meter=None,all_parses=False,viols=True, save=True):
		#parses = self.allParses(meter=meter) if all_parses else [[parse] for parse in self.bestParses(meter=meter)]
		meter=self.get_meter(meter)
		constraint_names = [c.name_weight for c in meter.constraints]
		header = ['line', 'parse', 'meter', 'num_sylls', 'num_parses', 'num_viols', 'score_viols'] + constraint_names

		def _writegen():
			for line in self.lines():
				dx={'text':self.name, 'line':unicode(line), 'header':header}
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
		for dx in writegengen(ofn, _writegen, save=save):
			yield dx
		if save: print '>> saved:',ofn

	def stats_lines_ot_header(self,meter=None):
		meter=self.get_meter(meter)
		constraint_names = [str(c) for c in meter.constraints]
		header = ['line', 'parse', 'meter', 'num_viols', 'score_viols'] + constraint_names + ['num_line','num_stanza']
		return header

	def stats_lines_ot(self,meter=None,all_parses=False,viols=True,save=True):
		#parses = self.allParses(meter=meter) if all_parses else [[parse] for parse in self.bestParses(meter=meter)]
		meter=self.get_meter(meter)
		header=self.stats_lines_ot_header(meter)

		def _writegen():
			for line in self.lines():

				#bp=line.bestParse(meter)
				ap=line.allParses(meter)
				if all_parses: ap+=line.boundParses(meter)

				for pi,parse in enumerate(ap):
					dx={'line':unicode(line) if not pi else ''}
					dx['text']=self.name
					dx['header']=header
					dx['parse']=parse.posString(viols=viols)
					#dx['2_obs']='1'
					dx['score_viols'] = parse.score()
					dx['num_line']=line.num
					dx['num_stanza']=line.parent.num
					dx['num_viols'] = parse.totalCount
					dx['meter']=parse.str_meter()
					for c in meter.constraints:
						dx[str(c)]=parse.constraintCounts[c] if parse and c in parse.constraintScores and parse.constraintScores[c] else ''
					yield dx

		name=self.name.replace('.txt','')
		ofn=os.path.join(self.dir_results, 'stats','texts',name, name+'.lines_ot.'+('meter='+meter.id if meter else 'unknown')+'.csv')
		if not os.path.exists(os.path.split(ofn)[0]): os.makedirs(os.path.split(ofn)[0])
		for dx in writegengen(ofn, _writegen,save=save):
			if not save: del dx['header']
			yield dx
		if save: print '>> saved:',ofn

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

	def save_stats(self):
		for dx in self.stats():
			pass

	def stats(self,meter=None,all_parses=False,funcs=['stats_lines','stats_lines_ot','stats_positions']):
		for funcname in funcs:
			func=getattr(self,funcname)
			for dx in func(meter=meter,all_parses=all_parses):
				yield dx



	def init_text(self,lines_or_file):
		## create first stanza,line
		stanza = self.newchild()
		stanza.num=stanza_num=1
		line = stanza.newchild()	# returns a new Line, the child of Stanza
		line.num=line_num=1
		numwords = 0
		recentpunct=True
		import prosodic
		tokenizer=prosodic.config['tokenizer'].replace('\\\\','\\')

		## [loop] lines
		for ln in lines_or_file:
			if REPLACE_DASHES:
				for dash in DASHES:
					ln=ln.replace(dash,u' '+dash+' ')


			ln=ln.strip()
			#print ln,type(ln)
			if self.limWord and numwords>self.limWord: break

			# split into words
			#print self.isUnicode
			toks = re.findall(tokenizer,ln.strip(),flags=re.UNICODE) if self.isUnicode else re.findall(tokenizer,ln.strip())
			#print toks
			#print tokenizer
			toks = [tok.strip() for tok in toks if tok.strip()]
			numtoks=len(toks)

			## if no words, mark stanza/para end
			if (not ln or numtoks < 1):
				if not stanza.empty():
					stanza.finish()
				continue

			## [loop] words
			for toknum,tok in enumerate(toks):
				#(tok,punct) = gleanPunc(tok)
				(punct0,tok,punct) = gleanPunc2(tok)

				if stanza.finished:
					stanza = self.newchild()
					stanza.num = stanza_num = stanza_num+1
				if line.finished:
					line = stanza.newchild()
					line.num = line_num = line_num+1

				if punct0:
					wordtok=WordToken([],token=punct0,is_punct=True, line = line)
					line.newchild(wordtok)

				if tok:
					newwords=self.dict.get(tok,stress_ambiguity=self.stress_ambiguity)
					wordtok = WordToken(newwords,token=tok,is_punct=False, line = line)
					line.newchild(wordtok)
					numwords+=1

					self.om(str(numwords).zfill(6)+"\t"+str(newwords[0].output_minform()))

				if punct:
					wordtok=WordToken([],token=punct,is_punct=True, line = line)
					line.newchild(wordtok)

				if punct and len(line.children) and self.phrasebreak != 'line':
					if (self.phrasebreak_punct.find(punct) > -1):
						line.finish()

			## if line-based breaks, end line
			if (self.phrasebreak == 'both') or (self.phrasebreak == 'line'):
				line.finish()

		if self.config.get('parse_using_metrical_tree',False) and self.lang=='en':
			import time
			then=time.time()
			print '>> parsing text using MetricalTree (because "parse_using_metrical_tree" setting activated in config.py)...'
			try:
				self.parse_mtree()
			except ImportError as e:
				print '!! text not parsed because python module missing:',str(e).split()[-1]
				print '!! to install, run: pip install',str(e).split()[-1]
				print '!! if you don\'t have pip installed, run this script: <https://bootstrap.pypa.io/get-pip.py>'
				print
			except LookupError as e:
				emsg=str(e)
				#print '!! ERROR:',emsg
				#print '!!'

				if "Resource" in emsg and "punkt" in emsg and "not found" in emsg:
					print '!! text not parsed with metricaltree because NLTK missing needed data: punkt'
					print '!! to install, run: python -c "import nltk; nltk.download(\'punkt\')"'
					print
				elif 'stanford-parser.jar' in emsg:
					import prosodic
					print '!! text not parsed with metricaltree because Stanford NLP Parser not installed'
					print '!! to install, run: python -c "import prosodic; prosodic.install_stanford_parser()"'
					#print '!!'
					#print '!! if that doesn\'t work:'
					#print '!! \t1) download: http://nlp.stanford.edu/software/stanford-parser-full-2015-04-20.zip'
					#print '!! \t2) unzip it'
					#print '!! \t3) move the unzipped directory to:',self.dir_mtree+'/StanfordLibrary/stanford-parser-full-2015-04-20/'
					print
				else:
					print '!! text not parsed with metricaltree for unknown reason!'
					print '!! error message received:'
					print emsg
					print
			except AssertionError:
				print "This is a bug in PROSODIC that is Ryan Heuser's fault. [Bug ID: Assertion_MTree]"
				print "Please kindly report it to: https://github.com/quadrismegistus/prosodic/issues"
				print
			except Exception as e:
				emsg=str(e)
				print '!! text not parsed for unknown reason!'
				print '!! error message received:'
				print emsg
				print
			#"""
			now=time.time()
			print '>> done:',round(now-then,2),'seconds'

	def parse_mtree(self):
		if self.lang!='en': raise Exception("MetricalTree parsing only works currently for English text.")

		import metricaltree as mtree
		mtree.set_paths(self.dir_mtree)

		wordtoks = self.wordtokens()
		toks = [wtok.token for wtok in wordtoks]

		pauses = mtree.pause_splitter_tokens(toks)

		#sents = [sent for pause in pauses for sent in pause]
		sents=[]
		for pause in pauses:
			sents.extend(mtree.split_sentences_from_tokens(pause))
		parser = mtree.return_parser(self.dir_mtree)
		trees = list(parser.lex_parse_sents(sents, verbose=False))
		stats = parser.get_stats(trees,arto=True,format_pandas=False)
		assert len(stats)==len(wordtoks)

		sents = []
		sent = []
		sent_id=None
		for wTok,wStat in zip(wordtoks,stats):
			if sent_id!=wStat['sidx']:
				sent_id=wStat['sidx']
				if sent: sents+=[sent]
				sent=[]

			sent+=[wTok]
			#for k,v in wStat.items():
			#	setattr(wTok,k,v)
			if not hasattr(wTok,'feats'): wTok.feats={}
			for k,v in wStat.items():
				if k in mtree.INFO_DO_NOT_STORE: continue
				wTok.feats[k]=v

		if sent: sents+=[sent]
		assert len(sents) == len(trees)

		from Sentence import Sentence
		for sent,tree in zip(sents,trees):
			sentobj = Sentence(sent, tree)
			self._sentences+=[sentobj]

		# create a normalized stress per line
		import numpy as np
		for line in self.lines():
			wtoks = line.children

			# norm mean
			stresses = [wtok.feats['norm_mean'] for wtok in wtoks if not np.isnan(wtok.feats['norm_mean'])]
			max_stress = float(max(stresses))
			min_stress = float(min(stresses))
			for wtok in wtoks:
				wtok.feats['norm_mean_line']=(wtok.feats['norm_mean']-min_stress)/(max_stress-min_stress) if max_stress else np.nan

			# mean
			stresses = [wtok.feats['mean'] for wtok in wtoks if not np.isnan(wtok.feats['mean'])]
			min_stress = float(min(stresses))
			diff = 1.0 - min_stress
			for wtok in wtoks:
				wtok.feats['mean_line']=wtok.feats['mean'] + diff




	def grid(self,nspace=10):
		return '\n\n'.join(sent.grid(nspace=nspace) for sent in self.sentences())

	def clear_parses(self):
		self.__parses={}
		self.__bestparses={}
		self.__boundParses={}
		self.__parsed_ents={}

	def iparse(self,meter=None,num_processes=1,arbiter='Line',line_lim=None):
		"""Parse this text metrically, yielding it line by line."""
		from Meter import Meter,genDefault,parse_ent,parse_ent_mp
		import multiprocessing as mp
		meter=self.get_meter(meter)

		# set internal attributes
		self.__parses[meter.id]=[]
		self.__bestparses[meter.id]=[]
		self.__boundParses[meter.id]=[]
		self.__parsed_ents[meter.id]=[]

		lines = self.lines()
		lines=lines[:line_lim]
		numlines = len(lines)

		init=self
		ents=self.ents(arbiter)
		smax=self.config.get('line_maxsylls',100)
		smin=self.config.get('line_minsylls',0)
		#print '>> # of lines to parse:',len(ents)
		ents = [e for e in ents if e.num_syll >= smin and e.num_syll<=smax]
		#print '>> # of lines to parse after applying min/max line settings:',len(ents)

		self.scansion_prepare(meter=meter,conscious=True)

		numents=len(ents)

		#pool=mp.Pool(1)
		toprint=self.config['print_to_screen']
		objects = [(ent,meter,init,False) for ent in ents]

		if num_processes>1:
			print '!! MULTIPROCESSING PARSING IS NOT WORKING YET !!'
			pool = mp.Pool(num_processes)
			jobs = [pool.apply_async(parse_ent_mp,(x,)) for x in objects]
			for j in jobs:
				print j.get()
				yield j.get()
		else:
			now=time.time()
			clock_snum=0
			#for ei,ent in enumerate(pool.imap(parse_ent_mp,objects)):
			for ei,objectx in enumerate(objects):
				clock_snum+=ent.num_syll
				if ei and not ei%100:
					nownow=time.time()
					if self.config['print_to_screen']:
						print '>> parsing line #',ei,'of',numents,'lines','[',round(float(clock_snum/(nownow-now)),2),'syllables/second',']'
					now=nownow
					clock_snum=0

				yield parse_ent_mp(objectx)

		if self.config['print_to_screen']:
			print '>> parsing complete in:',time.time()-now,'seconds'


	def parse(self,meter=None,arbiter='Line',line_lim=None):
		list(self.iparse(meter=meter,arbiter=arbiter,line_lim=line_lim))

	## def parse
	def parse1(self,meter=None,arbiter='Line'):
		"""@DEPRECATED
		Parse this text metrically."""
		from Meter import Meter,genDefault,parse_ent
		meter=self.get_meter(meter)

		if self.isFromFile: print '>> parsing',self.name,'with meter:',meter.id
		self.meter=meter

		self.__parses[meter.id]=[]
		self.__bestparses[meter.id]=[]
		self.__boundParses[meter.id]=[]
		self.__parsed_ents[meter.id]=[]

		init=self
		"""
		if not hasattr(init,'meter_stats'):
			init.meter_stats={'lines':{},'positions':{},'texts':{}, '_ot':{},'_constraints':{}}
		if not hasattr(init,'bestparses'):
			init.bestparses=[]

		init.meter=meter
		init.meter_stats['_constraints']=sorted(init.meter.constraints)
		init.ckeys="\t".join(sorted([str(x) for x in init.meter.constraints]))
		"""

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

		if self.config['print_to_screen']: print

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

		if not meter.id in self.config['meters']: self.config['meters'][meter.id]=meter
		return meter

	def report(self,meter=None,include_bounded=False,reverse=True):
		#return #super(Text,self).report(meter=meter if meter else self.meter)
		meter=self.get_meter(meter)
		return entity.report(self,meter=meter,include_bounded=include_bounded,reverse=reverse)


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
					mpos_str=mpos.token


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


	def get_parses(self, meter):
		return self.__parses[meter.id]

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
		return "<Text."+unicode(self.name)+"> ("+str(len(self.words()))+" words)"
