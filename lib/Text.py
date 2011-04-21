from __future__ import division
import sys,re,os,codecs


from Stanza import Stanza
from Line import Line
from Word import Word
from entity import entity,being
from tools import *
from operator import itemgetter


class Text(entity):
	def __init__(self,filename,lang=None,printout=None,limWord=False,linebreak=None): #',;:.?!()[]{}<>'
		## import prosodic to access global features
		import prosodic

		## load/write-load text
		if os.path.exists(filename):
			self.filename = filename
			self.name = filename.split("/").pop().strip()
		else:
			fn=os.path.join(sys.path[0],'.directinput.txt')
			write(fn,filename.replace('//','\n\n').replace('/','\n'))
			self.filename=fn
			filename=fn
			self.name = '_directinput_'

		## set language
		if lang==None:
			if self.name[2]=="." and (self.name[0:2] in prosodic.dict):
				lang=self.name[0:2]
			elif prosodic.lang:
				lang=prosodic.lang
			else:
				lang=choose(prosodic.languages,"in what language is '"+self.name+"' written?")
				if not lang:
					lang=prosodic.languages[0]
					print "!! language choice not recognized. defaulting to: "+lang
				else:
					lang=lang.pop()
		try:
			self.dict=prosodic.dict[lang]
		except KeyError:
			lang0=lang
			lang=prosodic.languages[0]
			print "!! language "+lang0+" not recognized. defaulting to: "+lang
			self.dict=prosodic.dict[lang]
		self.lang=lang
		
		
		## create atomistic features
		self.featpaths={}
		self.__parses={}
		self.__bestparses={}
		self.phrasebreak_punct = unicode(",;:.?!()[]{}<>")
		self.phrasebreak=prosodic.config['linebreak'].strip()
		
		
		#if printout==None: printout=being.printout
		
		if self.phrasebreak=='line':
			pass
		elif self.phrasebreak.startswith("line"):
			self.phrasebreak_punct=unicode(self.phrasebreak.replace("line",""))
			self.phrasebreak='both'
		else:
			self.phrasebreak_punct=unicode(self.phrasebreak)
		
		
		self.limWord = limWord
		self.feats = {}
		
		#if being.omms:
		self.om("## loading Text " + self.name + "...")
		#else:
		#	print "## loading Text " + self.name + "..."
		
		
		
		## parent/children
		self.children = []

		## open file, objects
		#try:
		# 	file = codecs.open(filename,encoding='utf-8')
		# 	for ln in file:
		# 		pass
		# 	self.isUnicode=True
		#except UnicodeDecodeError:
		# 	file=codecs.open(filename,'r',encoding=c)
		# 	self.isUnicode=False
		file=codecs.open(filename,encoding='utf-8',errors='replace')
		self.isUnicode=True
			
		
		## create first stanza,line 
		stanza = self.newchild()
		stanza.parent=self
		line = stanza.newchild()	# returns a new Line, the child of Stanza
		line.parent=stanza
		numwords = 0
		recentpunct=True
		
		## [loop] lines
		for ln in file:
			#print ln
			## check limWord
			if(limWord):
				if(numwords>limWord):
					break
	
			# split into words
			if self.isUnicode:
				toks = re.findall('[^\s+-]+',ln.strip(),flags=re.UNICODE)
			else:
				toks = re.findall('[^\s+-]+',ln.strip())
			numtoks=len(toks)
			
			
			## if no words, mark stanza/para end
			if (not ln.strip()) or (numtoks < 1):
				# if Stanza not empty, start a new one
				if not stanza.empty():
					stanza.finish()
					stanza = self.newchild()
					stanza.parent=self
					continue
			
			## resolve contractions
			"""for toknum in range(numtoks):
				if not toknum: continue
				tok=toks[toknum]
				if tok=="'":
					if toknum<(numtoks-2) and toknum>0:
						if tok: toks[toknum-1]+=tok
						if toks[toknum+1]: toks[toknum-1]+=toks[toknum+1]
						toks[toknum]=""
						toks[toknum+1]=""
			"""
	
			## [loop] words
			for toknum in range(numtoks):
				tok=toks[toknum]
				
				## check if really a word
				if not tok: continue
				tok=tok.strip()
				if not tok: continue
				(tok,punct) = gleanPunc(tok)				
				
				# check if new stanza/line necessary 
				if stanza.finished:
					stanza = self.newchild()
					stanza.parent=self
				if line.finished:
					line = stanza.newchild()
					line.parent=stanza
				
				newwords=self.dict.get(tok)
				
				line.newchild(newwords)
				numwords+=1
				
				if prosodic.config['print_to_screen']:
					self.om(str(numwords).zfill(6)+"\t"+str(newwords[0].output_minform()))
				
				if punct and len(line.children):
					if self.phrasebreak != 'line':
						if (self.phrasebreak_punct.find(punct) > -1):
							line.finish()
					continue
				
			## if line-based breaks, end line
			if (self.phrasebreak == 'both') or (self.phrasebreak == 'line'):
				line.finish()
	
	## def parse
	def parse(self,meter=None,arbiter='Line'):
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
	
	def scansion(self,meter=None,conscious=False):
		if not meter:
			try:
				meter=self.__bestparses.keys()[0]
			except:
				return
		
		self.scansion_prepare(meter=meter,conscious=conscious)
		for line in self.lines():
			line.scansion(meter=meter,conscious=conscious)
		
	
	
	def allParses(self,meter=None):
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
                stanza=Stanza()
                #stanza.parent=self
		return stanza
	
	def validlines(self):
		return [ln for ln in self.lines() if (not ln.isBroken() and not ln.ignoreMe)]
	
	def stats(self):
		o="\t"+makeminlength(" ",16)+"\t#tokens\t#types\t\t%typ/tok\n"
		dict=self.dict
		stats=self.getStats()
		
		for k,v in sorted(stats.items(),key=itemgetter(0)):
			numtok=v[0]
			numtyp=v[1]
			typovertok=v[2]
			
			o+="\t"+makeminlength(str(k),16)+"\t"+str(numtok)+"\t"+str(numtyp)+"\t"+str(typovertok)+"\n"
			
		return o
	
	def __repr__(self):
		return str(self.name)