from entity import being
from entity import entity
from tools import *

class Line(entity):
	def __init__(self):
		self.parent=False
		self.children=[]
		self.feats={}
		self.featpaths={}
		self.finished = False
		
		self.__parses={}
		self.__bestparse={}
	
	def parse(self,meter=None,init=None):
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

		if init: self.store_stats(meter,init)


	def store_stats(self,meter,init):
		textname=init.getName()
		if not textname: textname=str(self).replace(" ","_")
		
		## store stats
		if (not textname in init.meter_stats['lines']):
			init.meter_stats['lines'][textname]={}
		if (not textname in init.meter_stats['positions']):
			init.meter_stats['positions'][textname]={}
		if (not textname in init.meter_stats['texts']):
			init.meter_stats['texts'][textname]={}
		if (not textname in init.meter_stats['_ot']):
			init.meter_stats['_ot'][textname]=makeminlength("line",being.linelen)+"\tmeter\t"+init.ckeys+"\n"
		
		parsedat=[]
		for k,v in sorted(self.__bestparse[meter].constraintScores.items()):
			if (not k in init.meter_stats['texts'][textname]):
				init.meter_stats['texts'][textname][k]=[]
			init.meter_stats['texts'][textname][k].append(v)
			
			#parsedat.append(v/len(self.__bestparse.positions))	#???
			parsedat.append(v)
			
		linekey=str(len(init.meter_stats['lines'][textname])+1).zfill(6)+"_"+str(self.__bestparse[meter].posString())
		init.meter_stats['lines'][textname][linekey]=parsedat
		
		## OT stats
		parses=self.__parses[meter]
		init.meter_stats['_ot'][textname]+=makeminlength(str(self),being.linelen)+"\t"+parses[0].str_ot()+"\n"
		if len(parses)>1:
			for parse in parses[1:]:
				init.meter_stats['_ot'][textname]+=makeminlength("",being.linelen)+"\t"+parse.str_ot()+"\n"
			
		
		
		for posn in range(len(self.__bestparse[meter].positions)):
			pos=self.__bestparse[meter].positions[posn]
			(posdat,ckeys)=pos.formatConstraints(normalize=True,getKeys=True)
			
			for cnum in range(len(ckeys)):
				if (not posn in init.meter_stats['positions'][textname]):
					init.meter_stats['positions'][textname][posn]={}
				if (not ckeys[cnum] in init.meter_stats['positions'][textname][posn]):
					init.meter_stats['positions'][textname][posn][ckeys[cnum]]=[]
				init.meter_stats['positions'][textname][posn][ckeys[cnum]].append(posdat[cnum])

	
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

	@property
	def txt(self):
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