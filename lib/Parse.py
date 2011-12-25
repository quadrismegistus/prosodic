from tools import *
from copy import copy
import string
from entity import entity

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
		self.numSlots = 0
		self.totalSlots = totalSlots
		self.isBounded = False
		self.comparisonNums = set()
		self.comparisonParses = []
		self.parseNum = 0
		self.totalScore = None
			
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
	def slots(self):
		slots = []
		for pos in self.positions:
			for slot in pos.slots:
				slots.append(slot)				
		return slots
	
	
	def str_meter(self):
		str_meter=""
		for pos in self.positions:
			for slot in pos.slots:
				str_meter+=pos.meterVal
		return str_meter
	
	# add an extra slot to the parse
	# returns a list of the parse with a new position added and (if it exists) the parse with the last position extended
	def extend(self, slot):
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
			
			for constraint in self.constraints:
				vScore = constraint.violationScore(self.positions[-2])
				if vScore == "*":
					self.constraintScores[constraint] = "*"
				else:
					self.constraintScores[constraint] += vScore
				
		if self.numSlots == self.totalSlots:

			# assign violation scores for the (completed) ultimate position
			for parse in extendedParses:
				for constraint in self.constraints:
					vScore = constraint.violationScore(parse.positions[-1])
					if vScore == "*":
						parse.constraintScores[constraint] = "*"
					else:
						parse.constraintScores[constraint] += vScore
				
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
	
	def score(self):
		if self.totalScore == None:
			score = 0
			for constraint, value in self.constraintScores.items():
				if value == "*":
					self.totalScore = "*"
					return self.totalScore
				score += value
			self.totalScore = score
			
		return self.totalScore
		
	def __cmp__(self, other):
		return cmp(self.score(), other.score())
	
	def posString(self):		# eg NE|ver|CAME|poi|SON|from|SO|sweet|A|place
		output = []
		for pos in self.positions:			
			output.append(repr(pos))
		return string.join(output, '|')
	
	def __repr__(self):
		return self.posString()
		#return "["+str(self.getErrorCount()) + "] " + self.getUpDownString()

	def __repr2__(self):
		return str(self.getErrorCount())

	def str_ot(self):
		ot=[]
		ot+=[self.str_meter()]
		for k,v in sorted(self.constraintScores.items()):
			ot+=[str(v)]
		return "\t".join(ot)

	def __report__(self,proms=False):
		o = ""
		i=0
		for pos in self.positions:
			unitlist = ""
			factlist = ""
			for unit in pos.slots:
				unitlist += str(unit.token) + " "
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
			o+=str(i) +'\t'+ pos.meterVal + '\t' + unitlist + '\t' + viols
			if proms:
				o+='\t' + feats + '\n'
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
		return (self.numSlots == self.totalSlots) or ((self.positions[-1].meterVal == parse.positions[-1].meterVal) and (len(self.positions[-1].slots) == len(parse.positions[-1].slots)))

	def violations(self,boolean=False):
		if not boolean:
			return self.constraintScores
		else:
			return [(k,(v>0)) for (k,v) in self.constraintScores.items()]
		


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
				return Bounding.bounded # contains only greater violations
				
		else:
		
			if containsLesserViolation:
				return Bounding.bounds # contains only lesser violations
				
			else:
				return Bounding.equal # contains neither greater nor lesser violations

