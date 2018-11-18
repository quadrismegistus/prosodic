from tools import *
from copy import copy
import string
from entity import entity
import logging

# class representing the potential bounding relations between to parses
class Bounding:
	bounds = 0 # first parse harmonically bounds the second
	bounded = 1 # first parse is harmonically bounded by the second
	equal = 2 # the same constraint violation scores
	unequal = 3 # unequal scores; neither set of violations is a subset of the other


class Parse(entity):
	str2int = {'w':'1','s':'2'}
	#def __hash__(self):
	#	str = ""
	#	for x in self.meter:
	#		str+=Parse.str2int[x]
	#	return int(str)

	def __init__(self,meter,totalSlots):
		# set attrs
		self.positions = []
		self.meter = meter
		self.constraints = meter.constraints
		self.constraintScores = {}
		for constraint in self.constraints:
			self.constraintScores[constraint] = 0
		self.constraintNames = [c.name for c in self.constraints]
		self.numSlots = 0
		self.totalSlots = totalSlots
		self.isBounded = False
		self.boundedBy = None
		self.unmetrical = False
		self.comparisonNums = set()
		self.comparisonParses = []
		self.parseNum = 0
		self.totalScore = None
		self.pauseComparisons = False

	def __copy__(self):
		other = Parse(self.meter, self.totalSlots)
		other.numSlots = self.numSlots
		for pos in self.positions:
			other.positions.append(copy(pos))

		other.comparisonNums = copy(self.comparisonNums)
		for k,v in self.constraintScores.items():
			other.constraintScores[k]=copy(v)
		#other.constraintScores=self.constraintScores.copy()
		#print self.constraintScores
		#print other.constraintScores

		return other

	# return a list of all slots in the parse
	def slots(self,by_word=False):
		slots = []
		last_word_i=None
		for pos in self.positions:
			for slot in pos.slots:
				if not by_word:
					slots.append(slot)
				else:
					if last_word_i==None or last_word_i != slot.i_word:
						slots.append([])
					slots[-1].append(slot)
					last_word_i=slot.i_word
		return slots


	def str_meter(self,word_sep=""):
		str_meter=""
		wordTokNow=None
		for pos in self.positions:
			for slot in pos.slots:
				if word_sep and wordTokNow and slot.wordtoken != wordTokNow:
					str_meter+=word_sep
				wordTokNow=slot.wordtoken
				str_meter+=pos.meterVal
		return str_meter

	# add an extra slot to the parse
	# returns a list of the parse with a new position added and (if it exists) the parse with the last position extended
	def extend(self, slot):
		logging.debug('>> extending self (%s) with slot (%s)',self,slot)
		from MeterPosition import MeterPosition
		self.totalScore = None
		self.numSlots += 1

		extendedParses = [self]

		# positions containing just the slot

		sPos = MeterPosition(self.meter, 's')
		sPos.append(slot)
		wPos = MeterPosition(self.meter, 'w')
		wPos.append(slot)

		if len(self.positions) == 0:
			wParse = copy(self)
			self.positions.append(sPos)
			wParse.positions.append(wPos)
			extendedParses.append(wParse)

		else:
			lastPos = self.positions[-1]

			if lastPos.meterVal == 's':
				if len(lastPos.slots) < self.meter.maxS() and not slot.issplit:
					sParse = copy(self) # parse with extended final 's' position
					sParse.positions[-1].append(slot)
					extendedParses.append(sParse)
				self.positions.append(wPos)

			else:
				if len(lastPos.slots) < self.meter.maxW() and not slot.issplit:
					wParse = copy(self) # parse with extended final 'w' position
					wParse.positions[-1].append(slot)
					extendedParses.append(wParse)
				self.positions.append(sPos)

			# assign violation scores for the (completed) penultimate position

			## EXTRAMETRICAL?
			pos_i=len(self.positions)-2
			for constraint in self.constraints:
				vScore = constraint.violationScore(self.positions[-2], pos_i=pos_i,slot_i=self.numSlots-1,num_slots=self.totalSlots,all_positions=self.positions,parse=self)
				if vScore == "*":
					self.constraintScores[constraint] = "*"
				else:
					self.constraintScores[constraint] += vScore

		if self.numSlots == self.totalSlots:

			# assign violation scores for the (completed) ultimate position
			for parse in extendedParses:
				for constraint in self.constraints:
					vScore = constraint.violationScore(parse.positions[-1], pos_i=len(parse.positions)-1,slot_i=self.numSlots-1,num_slots=self.totalSlots,all_positions=parse.positions,parse=parse)
					if vScore == "*":
						parse.constraintScores[constraint] = "*"
					else:
						parse.constraintScores[constraint] += vScore

		logging.debug('>> self extended to be (%s) with extendedParses (%s)',self,extendedParses)
		return extendedParses

	def getErrorCount(self):
		return self.score()

	def getErrorCountN(self):
		return self.getErrorCount() / len(self.positions)

	def formatConstraints(self,normalize=True,getKeys=False):
		vals=[]
		keys=[]
		for k,v in sorted(self.constraintScores.items()):
			if normalize:
				#vals.append(v/len(self.positions))
				if bool(v):
					vals.append(1)
				else:
					vals.append(0)
			else:
				vals.append(v)

			if getKeys:
				keys.append(k)
				#keys[k]=len(vals)-1
		if getKeys:
			return (vals,keys)
		else:
			return vals

	@property
	def totalCount(self):
		return sum(self.constraintCounts.values())

	@property
	def constraintCounts(self):
		#return dict((c,int(self.constraintScores[c] / c.weight)) for c in self.constraintScores)
		cc={}
		for constraint in self.constraints:
			cn=0
			for pos in self.positions:
				if pos.constraintScores[constraint]:
					cn+=1
			cc[constraint]=cn
		return cc

	@property
	def num_sylls(self):
		return sum(len(pos.slots) for pos in self.positions)

	def score(self):
		#if self.totalScore == None:
		score = 0
		for constraint, value in self.constraintScores.items():
			if value == "*":
				self.totalScore = "*"
				return self.totalScore
			score += value
		self.totalScore = score

		return int(self.totalScore) if int(self.totalScore) == self.totalScore else self.totalScore

	def __cmp__(self, other):
		## @TODO: parameterize this: break ties by favoring the more binary parse
		x,y=self.score(),other.score()
		if x<y: return -1
		if x>y: return 1

		# Break tie
		return 0
		xs=self.str_meter()
		ys=other.str_meter()
		return cmp(xs.count('ww')+xs.count('ss'), ys.count('ww')+ys.count('ss'))
		# if x==y:
		#
		# return cmp(self.score(), other.score())

	def posString(self,viols=False):		# eg NE|ver|CAME|poi|SON|from|SO|sweet|A|place
		output = []
		for pos in self.positions:
			x=unicode(pos)
			if viols and pos.has_viol: x+='*'
			output.append(x)
		return string.join(output, '|')

	def posString2(self,viols=False):
		last_word = None
		output=''
		for pos in self.positions:
			for slot in pos.slots:
				slotstr=slot.token.upper() if pos.meterVal=='s' else slot.token.lower()
				if last_word != slot.wordtoken:
					output+=' '+slotstr
					last_word=slot.wordtoken
				else:
					output+='.'+slotstr
		return output.strip()

	def str_stress(self):		# eg NE|ver|CAME|poi|SON|from|SO|sweet|A|place
		output = []
		for pos in self.positions:
			slotx=[]
			for slot in pos.slots:
				if not slot.feats['prom.stress']:
					slotx.append('U')
				elif slot.feats['prom.stress']==1:
					slotx.append('P')
				else:
					slotx.append('S')
			output+=[''.join(slotx)]
		return string.join(output, '|')

	def words(self):
		last_word = None
		words=[]
		for slot in self.slots():
			slot_word=slot.word
			slot_wordtoken=slot.wordtoken
			if last_word != slot_wordtoken:
				words+=[slot_word]
				last_word=slot_wordtoken
		return words

	def wordtokens(self):
		last_word = None
		words=[]
		for slot in self.slots():
			slot_word=slot.wordtoken
			if last_word != slot_word:
				words+=[slot_word]
				last_word=slot_word
		return words

	def set_wordtokens_to_best_word_options(self):
		for wordtok,wordobj in zip(self.wordtokens(),self.words()):
			wordtok.set_as_best_word_option(wordobj)



	def __repr__(self):
		return self.posString()
		#return "["+str(self.getErrorCount()) + "] " + self.getUpDownString()

	def __repr2__(self):
		return str(self.getErrorCount())

	def str_ot(self):
		ot=[]
		#ot+=[self.str_meter()]
		#for k,v in sorted(self.constraintScores.items()):
		for c in self.constraints:
			v=self.constraintScores[c]
			ot+=[str(v) if int(v)!=float(v) else str(int(v))]
		return "\t".join(ot)

	def __report__(self,proms=False):
		o = ""
		i=0

		for pos in self.positions:
			unitlist = ""
			factlist = ""
			for unit in pos.slots:
				unitlist += self.u2s(unit.token) + " "
				#factlist += unit.stress + unit.weight + " "
			unitlist = unitlist[:-1]
			#factlist = factlist[:-1]
			unitlist = makeminlength(unitlist,10)

			if proms:
				feats = ""
				for unit in pos.slots:
					for k,v in unit.feats.items():
						if (not "prom." in k): continue
						if v:
							feats += "[+" + str(k) + "] "
						else:
							feats += "[-" + str(k) + "] "
					feats += '\t'
				feats = feats.strip()

			viols = ""
			for k,v in pos.constraintScores.items():
				if v:
					viols+=str(k)
			viols = viols.strip()
			if proms:
				viols = makeminlength(viols,60)

			if pos.meterVal == "s":
				unitlist = unitlist.upper()
			else:
				unitlist = unitlist.lower()

			i+=1
			o+=str(i) +'\t'+ pos.meterVal2 + '\t' + unitlist + '\t' + viols
			if proms:
				o+=feats + '\n'
			else:
				o+='\n'
		return o[:-1]

	def isIambic(self):
		if len(self.positions) < 2:
			return None
		else:
			return self.positions[0].meterVal == 'w' and self.positions[1].meterVal == 's'

	# return true if two parses can be compared for harmonic bounding
	def canCompare(self, parse):

		isTrue = (self.numSlots == self.totalSlots) or ((self.positions[-1].meterVal == parse.positions[-1].meterVal) and (len(self.positions[-1].slots) == len(parse.positions[-1].slots)))
		if isTrue:
			logging.debug('Parse1: %s\nLastMeterVal1: %s\nLastNumSlots1: %s\n--can compare-->\nParse2: %s\nLastMeterVal2: %s\nLastNumSlots2: %s',self,self.positions[-1].meterVal,len(self.positions[-1].slots),parse,parse.positions[-1].meterVal,len(parse.positions[-1].slots))
		return isTrue
		#return (self.numSlots == self.totalSlots)
		#return False

	def violations(self,boolean=False):
		if not boolean:
			return self.constraintScores
		else:
			return [(k,(v>0)) for (k,v) in self.constraintScores.items()]

	@property
	def violated(self):
		viold=[]
		for c,viol in self.constraintScores.items():
			if viol:
				viold+=[c]
		return viold

	def constraintScorez(self):
		toreturn={}
		for c in self.constraints:
			toreturn[c]=0
			for pos in self.positions:
				toreturn[c]+=pos.constraintScores[c]
		return toreturn

	# return a representation of the bounding relation between self and parse
	def boundingRelation(self, parse):

		containsGreaterViolation = False
		containsLesserViolation = False

		for constraint in self.constraints:
			mark = self.constraintScores[constraint]
			mark2 = parse.constraintScores[constraint]

			#print str(mark)+"\t"+str(mark2)

			if mark > parse.constraintScores[constraint]:
				containsGreaterViolation = True

			if mark < parse.constraintScores[constraint]:
				containsLesserViolation = True

		if containsGreaterViolation:

			if containsLesserViolation:
				return Bounding.unequal # contains both greater and lesser violations

			else:
				logging.debug('Parse1: %s\nViols1: %s\n--bounds-->\nParse2: %s\nViols2: %s',parse,str([(k,v) for k,v in sorted(parse.constraintCounts.items()) if v]),self,str([(k,v) for k,v in sorted(self.constraintCounts.items()) if v]))
				return Bounding.bounded # contains only greater violations

		else:

			if containsLesserViolation:
				logging.debug('Parse1: %s\nViols1: %s\n--bounds-->\nParse2: %s\nViols2: %s',self,str([(k,v) for k,v in sorted(self.constraintCounts.items()) if v]),parse,str([(k,v) for k,v in sorted(parse.constraintCounts.items()) if v]))
				return Bounding.bounds # contains only lesser violations

			else:
				return Bounding.equal # contains neither greater nor lesser violations
