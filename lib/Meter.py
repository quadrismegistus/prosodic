from tools import *
#from Queue import Queue
from MeterConstraint import MeterConstraint as Constraint
from MeterSlot import MeterSlot as Slot
from MeterPosition import MeterPosition as Position
from Parse import Parse, Bounding
from copy import copy
from tools import makeminlength
from entity import being
import os


def genDefault():
	import prosodic
	return Meter(prosodic.config['constraints'].split(),(prosodic.config['maxS'],prosodic.config['maxW']),prosodic.config['splitheavies'])
	

class Meter:
	Weak="w"
	Strong="s"
	## for caching meter-parses
	parseDict = {}
	
	def __init__(self,constraints=None,posLimit=(2,2),splitheavies=False):
		self.type = type
		self.posLimit=posLimit
		self.constraints = []
		self.splitheavies=splitheavies
		
		if not constraints:
			self.constraints.append(Constraint(0,"foot-min",None,1))
			self.constraints.append(Constraint(1,"strength.s=>p",None,1))
			self.constraints.append(Constraint(2,"strength.w=>u",None,1))
			self.constraints.append(Constraint(3,"stress.s=>p",None,1))
			self.constraints.append(Constraint(4,"stress.w=>u",None,1))
			self.constraints.append(Constraint(5,"weight.s=>p",None,1))
			self.constraints.append(Constraint(6,"weight.w=>u",None,1))
		elif type(constraints) == type([]):
			for i in range(len(constraints)):
				c=constraints[i]
				if "/" in c:
					(cname,cweight)=c.split("/")
					cweight=int(cweight)
				else:
					cname=c
					cweight=1
				self.constraints.append(Constraint(i,cname,None,cweight))
		else:
			if os.path.exists(constraints):
				constraintFiles = os.listdir(constraints)
				for i in range(len(constraintFiles)):
					constraintFile = constraintFiles[i]
					if constraintFile[-3:] == ".py":
						self.constraints.append(Constraint(i,os.path.join(constraints, constraintFile[:-3]),None,1))

	def maxS(self):
		return self.posLimit[0]
		
	def maxW(self):
		return self.posLimit[1]
	
	


	def genWordMatrix(self,wordlist):
		return list(product(*wordlist))	# [ [on, the1, ..], [on, the2, etc]
	
	def genSlotMatrix(self,words):
		matrix=[]
		
		for row in self.genWordMatrix(words):
			unitlist = []
			id=-1
			for word in row:
				syllnum=-1
				for unit in word.children:	# units = syllables
					syllnum+=1
					id+=1
					wordpos=(syllnum+1,len(word.children))
					unitlist.append(Slot(id, unit, word.sylls_text[syllnum], wordpos, word))
					
			if not self.splitheavies:
				matrix.append(unitlist)
			else:
				unitlist2=[]
				for slot in unitlist:
					if bool(slot.feature('prom.weight')):
						slot1=Slot(slot.i,slot.children[0],slot.token,slot.wordpos,slot.word)
						slot2=Slot(slot.i,slot.children[0],slot.token,slot.wordpos,slot.word)
						
						## mark as split
						slot1.issplit=True
						slot2.issplit=True
						
						## demote
						slot2.feats['prom.stress']=0.0
						slot1.feats['prom.weight']=0.0
						slot2.feats['prom.weight']=0.0
						
						## split token
						slot1.token= slot1.token[ : len(slot1.token)/2 ]
						slot2.token= slot2.token[len(slot1.token)/2 + 1 : ]
						
						unitlist2.append([slot,[slot1,slot2]])
					else:
						unitlist2.append([slot])
				
				#unitlist=[]
				for row in list(product(*unitlist2)):
					unitlist=[]
					for x in row:
						if type(x)==type([]):
							for y in x:
								unitlist.append(y)
						else:
							unitlist.append(x)
					matrix.append(unitlist)
			
			
				
		# for r in matrix:
		# 	for y in r:
		# 		print y
		# 	print
		# 	print	
		
		return matrix
		
		
	
	def parse(self,wordlist,numSyll=0):
		from Parse import Parse
		if not numSyll:
			return []
		
		
		slotMatrix = self.genSlotMatrix(wordlist)
		if not slotMatrix: return None


		constraints = self.constraints

		
		allParses = []
		for slots in slotMatrix:
			allParses.append(self.parseLine(slots))
		
		parses = self.boundParses(allParses)
		parses.sort()		
		
		return parses
		
	def boundParses(self, parseLists):
		unboundedParses = []
		for listIndex in range(len(parseLists)):
			for parse in parseLists[listIndex]:
				for parseList in parseLists[listIndex+1:]:
					for compParse in parseList:
						if compParse.isBounded:
							continue
						relation = parse.boundingRelation(compParse)
						if relation == Bounding.bounded:
							parse.isBounded = True
						elif relation == Bounding.bounds:
							compParse.isBounded = True
							
		for parseList in parseLists:
			for parse in parseList:
				if not parse.isBounded:
					unboundedParses.append(parse)
					
		return unboundedParses
		
	def parseLine(self, slots):
	
		numSlots = len(slots)
			
		initialParse = Parse(self, numSlots)
		parses = initialParse.extend(slots[0])
		parses[0].comparisonNums.add(1)
		
		for slotN in range(1, numSlots):
		
			newParses = []
			for parse in parses:
				newParses.append(parse.extend(slots[slotN]))
				
			for parseSetIndex in range(len(newParses)):
			
				parseSet = newParses[parseSetIndex]
				
				for parseIndex in range(len(parseSet)):
				
					parse = parseSet[parseIndex]
					parse.comparisonParses = []
					
					if len(parseSet) > 1 and parseIndex == 0:
						parse.comparisonNums.add(parseSetIndex)
					
					for comparisonIndex in parse.comparisonNums:
					
						# should be a label break, but not supported in Python
						# find better solution; redundant checking
						if parse.isBounded:
							break

						try:
							for comparisonParse in newParses[comparisonIndex]:
							
								if parse is comparisonParse:
									continue
							
								if not comparisonParse.isBounded:
								
									if parse.canCompare(comparisonParse):
									
										boundingRelation = parse.boundingRelation(comparisonParse)
										
										if boundingRelation == Bounding.bounds:
											comparisonParse.isBounded = True
											
										elif boundingRelation == Bounding.bounded:
											parse.isBounded = True
											break
											
										elif boundingRelation == Bounding.equal:
											parse.comparisonParses.append(comparisonParse)
										
									else:
										parse.comparisonParses.append(comparisonParse)
						except IndexError:
							pass
									
			parses = []
			parseNum = 0
								
			for parseSet in newParses:
				for parse in parseSet:		
					if not parse.isBounded:
						if (parse.score() < 1000):
							parse.parseNum = parseNum
							parseNum += 1
							parses.append(parse)
			
			for parse in parses:
			
				parse.comparisonNums = set()
				
				for compParse in parse.comparisonParses:
					if not compParse.isBounded:
						parse.comparisonNums.add(compParse.parseNum)
							
		return parses
	
	def printParses(self,parselist,onlyBounded=True,lim=False):		
		i = len(parselist)
		#i = n+1
		n = len(parselist)
		parselist.reverse()
		o=""
		for parse in parselist:
			if onlyBounded and parse.isBounded:
				continue
			
			o+="[parse #" + str(i) + " of " + str(n) + "]: " + str(parse.getErrorCount()) + " errors\n"
			o+=parse.__report__(proms=False)+"\n"
			o+=self.printScores(parse.constraintScores)
			o+="\n\n"
			i-=1
		return o
			
	def printScores(self, scores):
		output = ""
		for key, value in sorted(scores.items()):
			output += makeminlength("[*"+key.name+"]:"+str(value),24)
		output = output[:-1]
		return output
		
