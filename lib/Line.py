from entity import being
from entity import entity
class Line(entity):
	def __init__(self,linestr=None,lang=None):
		self.parent=False
		self.children=[]
		self.feats={}
		self.featpaths={}
		self.finished = False
	
		self.__parses={}
		self.__bestparse={}
		self.__bestparse_now=None
		
		if linestr and isinstance(linestr,basestring):
			import prosodic
			if lang==None: lang=prosodic.lang
			self.children=[ prosodic.dict[lang].get(w) for w in linestr.strip().split() if w ]
			self.finish()
	
	def str_meter(self):
		return self.bestParse().str_meter()
	
	def parse(self,meter=None):
		if not meter:
			from Meter import Meter,genDefault
			meter = genDefault()

		words=self.ents(cls='Word',flattenList=False)
		numSyll=0
		if not words: return None
		for word in words:
			if type(word)==type([]):
				for wrd in word:
					if wrd.isBroken():
						#print wrd
						return None
				numSyll+=word[0].getNumSyll()
			else:
				if word.isBroken():
					return None
				numSyll+=word.getNumSyll()
		
		self.__parses[meter]=meter.parse(words,numSyll)
		try:
			self.__bestparse[meter]=self.__parses[meter][0]
		except KeyError:
			self.__bestparse[meter]=None
	
	def scansion(self,meter=None,conscious=False):
		bp=self.bestParse(meter)
		if type(bp)==type(None): return
		lowestScore=bp.score()
		from tools import makeminlength
		self.om("\t".join( [ str(x) for x in [makeminlength(str(self),being.linelen), makeminlength(str(bp), being.linelen),len(self.allParses(meter)),lowestScore,bp.str_ot()] ] ),conscious=conscious)
	
	
	def allParses(self,meter=None):
		if not meter:
			itms=self.__parses.items()
			if not len(itms): return
			for mtr,parses in itms:
				return parses

		try:
			return self.__parses[meter]
		except KeyError:
			return None
		
	def bestParse(self,meter=None):
		if not meter:
			if not self.__bestparse_now:
				itms=self.__bestparse.items()
				if not len(itms): return
				for mtr,parse in itms:
					self.__bestparse_now=parse
					break
			return self.__bestparse_now
		
		try:
			return self.__bestparse[meter]
		except KeyError:
			return
	
	
	def finish(self):
		if not hasattr(self,'finished') or not self.finished:
			#print "finishing... " + str(self)
			self.finished = True
			if not hasattr(self,'broken'):
				self.broken=False
			
			## if no words
			if len(self.children) == 0:
				self.broken=True
			

			## if word broken, self broken
			for words in self.children:
				if words[0].isBroken():
					self.broken=True
					break
			else:
				self.broken=False
			
			# resolve lapses if possible
			if not self.broken:
				self.resolveLapses()
	
	def resolveLapses(self):
		words = self.words()
		num_recent_unstressed = 0
		for i, word in enumerate(words):
			for syll in word.syllables():
				if syll.feature('prom.stress'):
					num_recent_unstressed = 0
				else:
					num_recent_unstressed += 1
					if num_recent_unstressed > 2:
						if i > 0 and len(words[i-1].syllables()) == 1:
							self.children[i-1] = self.children[i-1][:]
							self.children[i-1].reverse()
							num_recent_unstressed = 1
	
	def __repr__(self):
		return " ".join([child[0].getToken() for child in self.children])


	def str_wordbound(self):
		o=[]
		for words in self.children:
			e=""
			for x in words[0].children:
				e+="X"
			o.append(e)
		return "#".join(o)
	
	def str_weight(self):
		o=[]
		for words in self.children:
			o.append("".join(x.str_weight() for x in words[0].children))
		return "".join(o)
	
	def str_stress(self):
		o=[]
		for words in self.children:
			o.append("".join(x.str_stress() for x in words[0].children))
		return "".join(o)


	#def __eq__(self,other):
	#	if (not hasattr(being,'pointsofcomparison') or not being.pointsofcomparison):
	#		return object.__eq__(self,other)
	#	else:
	#		print
	#		print
	#		print
	#		print self
	#		print other
	#		
	#		for poc in being.pointsofcomparison:
	#			a=getattr(self,poc)()
	#			b=getattr(other,poc)()
	#			
	#			print
	#			print a
	#			print b
	#							
	#			if a!=b:
	#				return False
	#		return True