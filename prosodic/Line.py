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
		self.__boundParses={}

	def parse(self,meter=None,init=None):
		#print '>> LINE PARSING',meter,init
		#if not meter:
		#	from Meter import Meter,genDefault
		#	meter = genDefault()

		"""
		words=self.ents(cls='Word',flattenList=False)
		#print words
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

		## PARSE
		self.__parses[meter.id],self.__boundParses[meter.id]=meter.parse(words,numSyll)
		####
		"""
		wordtoks=self.wordtokens(include_punct=False)
		#print words
		numSyll=0
		if not wordtoks: return None
		for wordtok in wordtoks:
			wordtok_words = wordtok.children
			if not wordtok_words or True in [word.isBroken() for word in wordtok_words]:
				return None
			numSyll+=wordtok_words[0].getNumSyll()

		## PARSE
		self.__parses[meter.id],self.__boundParses[meter.id]=meter.parse(wordtoks,numSyll)
		####


		self.__bestparse[meter.id]=None
		try:
			self.__bestparse[meter.id]=self.__parses[meter.id][0]
		except (KeyError,IndexError) as e:
			try:
				self.__bestparse[meter.id]=self.__boundParses[meter.id][0]
			except (KeyError,IndexError) as e:
				self.__bestparse[meter.id]=None


		## Re-sort words within wordtoken
		bp = self.__bestparse[meter.id]
		if bp: bp.set_wordtokens_to_best_word_options()



		#if init: self.store_stats(meter,init)


	"""def store_stats(self,meter,init):
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

		try:

			parsedat=[]
			for k,v in sorted(self.__bestparse[meter.id].constraintScores.items()):
				if (not k in init.meter_stats['texts'][textname]):
					init.meter_stats['texts'][textname][k]=[]
				init.meter_stats['texts'][textname][k].append(v)

				#parsedat.append(v/len(self.__bestparse.positions))	#???
				parsedat.append(v)

			linekey=str(len(init.meter_stats['lines'][textname])+1).zfill(6)+"_"+str(self.__bestparse[meter.id].posString())
			init.meter_stats['lines'][textname][linekey]=parsedat

			## OT stats
			parses=self.__parses[meter.id]
			init.meter_stats['_ot'][textname]+=makeminlength(str(self),being.linelen)+"\t"+parses[0].str_ot()+"\n"
			if len(parses)>1:
				for parse in parses[1:]:
					init.meter_stats['_ot'][textname]+=makeminlength("",being.linelen)+"\t"+parse.str_ot()+"\n"



			for posn in range(len(self.__bestparse[meter.id].positions)):
				pos=self.__bestparse[meter.id].positions[posn]
				(posdat,ckeys)=pos.formatConstraints(normalize=True,getKeys=True)

				for cnum in range(len(ckeys)):
					if (not posn in init.meter_stats['positions'][textname]):
						init.meter_stats['positions'][textname][posn]={}
					if (not ckeys[cnum] in init.meter_stats['positions'][textname][posn]):
						init.meter_stats['positions'][textname][posn][ckeys[cnum]]=[]
					init.meter_stats['positions'][textname][posn][ckeys[cnum]].append(posdat[cnum])
		except (IndexError,KeyError,AttributeError) as e:
			#print "!! no lines successfully parsed with any meter"
			pass
	"""


	def scansion(self,meter=None,conscious=False):
		bp=self.bestParse(meter)
		config=being.config
		#if not bp: return
		lowestScore=''
		str_ot=''
		count=''
		meterstr=''
		if bp:
			meterstr=bp.str_meter()
			str_ot=bp.str_ot()
			lowestScore=bp.score()
			count=bp.totalCount
		from tools import makeminlength
		print makeminlength(unicode(bp),60)
		data = [makeminlength(unicode(self),config['linelen']), makeminlength(unicode(bp) if bp else '', config['linelen']),meterstr,len(self.allParses(meter)),count,lowestScore,str_ot]
		data_unicode = [unicode(x) for x in data]
		self.om("\t".join( data_unicode ),conscious=conscious)


	def allParses(self,meter=None,one_per_meter=True):
		if not meter:
			itms=self.__parses.items()
			if not len(itms): return
			for mtr,parses in itms:
				return parses

		try:
			parses=self.__parses[meter.id]
			if one_per_meter:
				toreturn=[]
				sofar=set()
				for _p in parses:
					_pm=_p.str_meter()
					if not _pm in sofar:
						sofar|={_pm}
						if _p.isBounded and _p.boundedBy.str_meter() == _pm:
							pass
						else:
							toreturn+=[_p]
				parses=toreturn
			return parses
		except KeyError:
			return []

	def boundParses(self,meter=None):
		if not meter:
			itms=sorted(self.__boundParses.items())
			if not len(itms): return []
			for mtr,parses in itms:
				return parses

		try:
			return self.__boundParses[meter.id]
		except KeyError:
			return []

	def bestParse(self,meter=None):
		if not meter:
			itms=self.__bestparse.items()
			if not len(itms): return
			for mtr,parses in itms:
				return parses

		try:
			return self.__bestparse[meter.id]
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
				for words in self.words(flattenList=False):
					assert type(words)==list
					for word in words:
						if word.isBroken():
							self.broken=True




	def __repr__(self):
		return self.txt

	@property
	def txt(self):
		x=""
		for wordtok in self.wordtokens():
			if not wordtok.is_punct:
				x+=" "+wordtok.token
			else:
				x+=wordtok.token
		return x.strip()



	def str_wordbound(self):
		o=[]
		for word in self.words():
			e=""
			for x in word.children:
				e+="X"
			o.append(e)
		return "#".join(o)

	def str_weight(self,word_sep=""):
		o=[]
		for word in self.words():
			o.append("".join(x.str_weight() for x in word.children))
		return word_sep.join(o)

	def str_stress(self,word_sep=""):
		o=[]
		for word in self.words():
			o.append("".join(x.str_stress() for x in word.children))
		return word_sep.join(o)

	def str_sonority(self,word_sep=""):
		o=[]
		for word in self.words():
			o.append("".join(x.str_sonority() for x in word.children))
		return word_sep.join(o)



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
