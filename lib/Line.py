from entity import being
from entity import entity
class Line(entity):
	def __init__(self):
		self.parent=False
		self.children=[]
		self.feats={}
		self.featpaths={}
		self.finished = False
		
		self.__parses={}
		self.__bestparse={}
	
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
			itms=self.__bestparse.items()
			if not len(itms): return
			for mtr,parses in itms:
				return parses
		
		try:
			return self.__bestparse[meter]
		except KeyError:
			return
	
	
	def finish(self):
		if not hasattr(self,'finished') or not self.finished:
			"""print "finishing... " + str(self)
			for word in self.words():
				print word, word.origin
			print"""
			
			self.finished = True
			if not hasattr(self,'broken'):
				self.broken=False
			
			## if no words
			if len(self.children) == 0:
				self.broken=True
			
			if not self.broken:
				## if word broken, self broken
				for words in self.children:
					if type(words)==type([]):
						for word in words:
							if word.isBroken():
								self.broken=True
					else:
						if words.isBroken():
							self.broken=True
							
			#if not self.broken:
			#	print self
			#self.pointsofcomparison=[]
			
	
	
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