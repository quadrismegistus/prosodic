from tools import *
from copy import copy
import string
from entity import entity
import logging
from functools import total_ordering




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
DEFAULT_METER='default_english'

def genDefault(metername=DEFAULT_METER):
	import prosodic
	#metername = sorted(prosodic.config['meters'].keys())[0]
	meters=prosodic.config['meters']
	if metername in meters:
		meter=meters[metername]
	else:
		meter=meters[sorted(meters.keys())[0]]
	print('>> no meter specified. defaulting to this meter:')
	#raise Exception
	print(meter)
	return meter


#def meterShakespeare():
#	return Meter('strength.s=>')

DEFAULT_CONSTRAINTS = [
	'footmin-w-resolution/1',
	'footmin-f-resolution/1',
	'strength.w=>-p/1',
	'headedness!=rising/1',
	'number_feet!=5/1'
]

def get_meter(id=None, name=None, maxS=2, maxW=2, splitheavies=0, constraints=DEFAULT_CONSTRAINTS,return_dict=False):

	"""
	{'constraints': ['footmin-w-resolution/1',
	'footmin-f-resolution/1',
	'strength.w=>-p/1',
	'headedness!=rising/1',
	'number_feet!=5/1'],
	'id': 'iambic_pentameter',
	'maxS': 2,
	'maxW': 2,
	'name': 'Iambic Pentameter',
	'splitheavies': 0}"""
	if 'Meter.Meter' in str(id.__class__): return id

	if not id: id='Meter_%s' % now()
	if not name: name = id + '['+' '.join(constraints)+']'

	config = locals()

	import prosodic
	if id in prosodic.config['meters']:
		return prosodic.config['meters'][id]


	if return_dict: return config
	return Meter(config)




class Meter:
	Weak="w"
	Strong="s"
	## for caching meter-parses
	parseDict = {}

	@staticmethod
	def genMeters():
		meterd={}
		meterd['*StrongSyllableWeakPosition [Shakespeare]']=Meter(['strength.w=>-p/1'], (1,2), False)
		meterd['*WeakSyllableStrongPosition']=Meter(['strength.s=>-u/1'], (1,2), False)
		meterd['*StressedSyllableWeakPosition']=Meter(['stress.w=>-p/1'], (1,2), False)
		meterd['*UnstressedSyllableStrongPosition [Hopkins]']=Meter(['stress.s=>-u/1'], (1,2), False)
		return meterd

	def __str__(self):
		#constraints = '\n'.join(' '.join([slicex) for slicex in slice() )
		#constraint_slices=slice(self.constraints,slice_length=3,runts=True)
		constraint_slices={}
		for constraint in self.constraints:
			ckey=constraint.name.replace('-','.').split('.')[0]
			if not ckey in constraint_slices:
				constraint_slices[ckey]=[]
			constraint_slices[ckey]+=[constraint]
		constraint_slices = [constraint_slices[k] for k in sorted(constraint_slices)]
		constraints = '\n\t\t'.join(' '.join(c.name_weight for c in slicex) for slicex in constraint_slices)

		x='<<Meter\n\tID: {5}\n\tName: {0}\n\tConstraints: \n\t\t{1}\n\tMaxS, MaxW: {2}, {3}\n\tAllow heavy syllable split across two positions: {4}\n>>'.format(self.name, constraints, self.posLimit[0], self.posLimit[1], bool(self.splitheavies), self.id)
		return x

	@property
	def constraint_nameweights(self):
		return ' '.join(c.name_weight for c in self.constraints)

	#def __init__(self,constraints=None,posLimit=(2,2),splitheavies=False,name=None):
	def __init__(self,config):
		#self.type = type
		constraints=config['constraints']
		self.posLimit=(config['maxS'],config['maxW'])
		self.constraints = []
		self.splitheavies=config['splitheavies']
		self.name=config.get('name','')
		self.id = config['id']
		self.config=config
		#import prosodic
		#print(config)
		#self.prosodic_config=prosodic.config
		self.prosodic_config=config

		if not constraints:
			self.constraints.append(Constraint(id=0,name="foot-min",weight=1,meter=self))
			self.constraints.append(Constraint(id=1,name="strength.s=>p",weight=1,meter=self))
			self.constraints.append(Constraint(id=2,name="strength.w=>u",weight=1,meter=self))
			self.constraints.append(Constraint(id=3,name="stress.s=>p",weight=1,meter=self))
			self.constraints.append(Constraint(id=4,name="stress.w=>u",weight=1,meter=self))
			self.constraints.append(Constraint(id=5,name="weight.s=>p",weight=1,meter=self))
			self.constraints.append(Constraint(id=6,name="weight.w=>u",weight=1,meter=self))

		elif type(constraints) == type([]):
			for i in range(len(constraints)):
				c=constraints[i]
				if "/" in c:
					(cname,weightVal)=c.split("/")
					#cweight=int(cweight)
					if ";" in weightVal:
						weightVals = weightVal.split(";")
						cweight=float(weightVals[0])
						muVal =float(weightVals[1])
						if len(weightVals) > 2:
							sigmaVal =float(weightVals[2])
					else:
						cweight=float(weightVal)
						muVal = 0.0
						sigmaVal = 10000
				else:
					cname=c
					weightVal=1.0
					muVal = 0.0
					sigmaVal = 10000
				self.constraints.append(Constraint(id=i,name=cname,weight=cweight,meter=self, mu=muVal, sigma=sigmaVal))
		"""
		else:
			if os.path.exists(constraints):
				constraintFiles = os.listdir(constraints)
				for i in range(len(constraintFiles)):
					constraintFile = constraintFiles[i]
					if constraintFile[-3:] == ".py":
						self.constraints.append(Constraint(id=i,name=os.path.join(constraints, constraintFile[:-3]),weight=1))
		"""

		self.constraints.sort(key=lambda _c: -_c.weight)

	def maxS(self):
		return self.posLimit[0]

	def maxW(self):
		return self.posLimit[1]




	def genWordMatrix(self,wordtokens):
		wordlist = [w.children for w in wordtokens]

		#import prosodic
		if self.prosodic_config.get('resolve_optionality',True):
			return list(product(*wordlist))	# [ [on, the1, ..], [on, the2, etc]
		else:
			return [ [ w[0] for w in wordlist ] ]

	def genSlotMatrix(self,wordtokens):
		matrix=[]

		row_wordtokens = wordtokens
		rows_wordmatrix = self.genWordMatrix(wordtokens)

		for row in rows_wordmatrix:
			unitlist = []
			id=-1
			wordnum=-1
			for word in row:
				wordnum+=1
				syllnum=-1
				for unit in word.children:	# units = syllables
					syllnum+=1
					id+=1
					wordpos=(syllnum+1,len(word.children))
					slot=Slot(id, unit, word.sylls_text[syllnum], wordpos, word, i_word=wordnum, i_syll_in_word=syllnum,wordtoken=row_wordtokens[wordnum], meter=self)
					unitlist.append(slot)

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



	def parse(self,wordlist,numSyll=0,numTopBounded=10):
		numTopBounded = self.prosodic_config.get('num_bounded_parses_to_store',numTopBounded)
		maxsec = self.prosodic_config.get('parse_maxsec',None)
		#print '>> NTB!',numTopBounded
		from Parse import Parse
		if not numSyll:
			return []


		slotMatrix = self.genSlotMatrix(wordlist)
		if not slotMatrix: return None

		constraints = self.constraints


		allParses = []
		allBoundedParses=[]

		import time
		clockstart=time.time()
		for slots_i,slots in enumerate(slotMatrix):
			#for slot in slots:
				#print slot
				#print slot.feats
				#print

			## give up?
			if maxsec and time.time()-clockstart > maxsec:
				if self.prosodic_config.get('print_to_screen',None):
					print('!! Time limit ({0}s) elapsed in trying to parse line:'.format(maxsec), ' '.join(wtok.token for wtok in wordlist))
				return [],[]

			_parses,_boundedParses = self.parseLine(slots)

			"""
			for prs in _parses:
				print 'UNBOUNDED:'
				print prs.__report__()
				print

			for prs in _parses:
				print 'BOUNDED:'
				print prs.__report__()
				print

			print
			print
			"""

			allParses.append(_parses)
			allBoundedParses+=_boundedParses

		parses,_boundedParses = self.boundParses(allParses)

		parses.sort()

		allBoundedParses+=_boundedParses

		allBoundedParses.sort(key=lambda _p: (-_p.numSlots, _p.score()))
		allBoundedParses=allBoundedParses[:numTopBounded]
		#allBoundedParses=[]

		"""print parses
		print
		print allBoundedParses
		for parse in allBoundedParses:
			print parse.__report__()
			print
			print parse.boundedBy if type(parse.boundedBy) in [str,unicode] else parse.boundedBy.__report__()
			print
			print
			print
		"""

		return parses,allBoundedParses

	def boundParses(self, parseLists):
		unboundedParses = []
		boundedParses=[]
		for listIndex in range(len(parseLists)):
			for parse in parseLists[listIndex]:
				for parseList in parseLists[listIndex+1:]:
					for compParse in parseList:
						if compParse.isBounded:
							continue
						relation = parse.boundingRelation(compParse)
						if relation == Bounding.bounded:
							parse.isBounded = True
							parse.boundedBy = compParse
						elif relation == Bounding.bounds:
							compParse.isBounded = True
							compParse.boundedBy = parse

		for parseList in parseLists:
			for parse in parseList:
				if not parse.isBounded:
					unboundedParses.append(parse)
				else:
					boundedParses.append(parse)

		return unboundedParses,boundedParses

	def parseLine(self, slots):

		numSlots = len(slots)

		initialParse = Parse(self, numSlots)
		parses = initialParse.extend(slots[0])
		parses[0].comparisonNums.add(1)

		boundedParses=[]


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
											# print parse.__report__()
											# print '--> bounds -->'
											# print comparisonParse.__report__()
											# print
											comparisonParse.isBounded = True
											comparisonParse.boundedBy = parse

										elif boundingRelation == Bounding.bounded:
											# print
											# print comparisonParse.__report__()
											# print '--> bounds -->'
											# print parse.__report__()
											# print
											parse.isBounded = True
											parse.boundedBy = comparisonParse
											break

										elif boundingRelation == Bounding.equal:
											parse.comparisonParses.append(comparisonParse)

									else:
										parse.comparisonParses.append(comparisonParse)
						except IndexError:
							pass

			parses = []
			#boundedParses=[]
			parseNum = 0

			for parseSet in newParses:
				for parse in parseSet:
					if parse.isBounded:
						boundedParses+=[parse]
					elif parse.score() >= 1000:
						parse.unmetrical = True
						boundedParses+=[parse]
					else:
						parse.parseNum = parseNum
						parseNum += 1
						parses.append(parse)


			for parse in parses:

				parse.comparisonNums = set()

				for compParse in parse.comparisonParses:
					if not compParse.isBounded:
						parse.comparisonNums.add(compParse.parseNum)



		return parses,boundedParses

	def printParses(self,parselist,lim=False,reverse=True):		# onlyBounded=True, [option done through "report" now]
		n = len(parselist)
		l_i = list(reversed(list(range(n)))) if reverse else list(range(n))
		parseiter = reversed(parselist) if reverse else parselist
		#parselist.reverse()
		o=""
		for i,parse in enumerate(parseiter):
			#if onlyBounded and parse.isBounded:
			#	continue

			o+='-'*20+'\n'
			o+="[parse #" + str(l_i[i]+1) + " of " + str(n) + "]: " + str(parse.getErrorCount()) + " errors"

			if parse.isBounded:
				o+='\n[**** Harmonically bounded ****]\n'+str(parse.boundedBy)+' --[bounds]-->'
			elif parse.unmetrical:
				o+='\n[**** Unmetrical ****]'
			o+='\n'+str(parse)+'\n'
			o+='[meter]: '+parse.str_meter()+'\n'

			o+=parse.__report__(proms=False)+"\n"
			o+=self.printScores(parse.constraintScores)
			o+='-'*20
			o+="\n\n"
			i-=1
		return o

	def printScores(self, scores):
		output = "\n"
		for key, value in sorted(((str(k.name),v) for (k,v) in list(scores.items()))):
			if not value: continue
			#output += makeminlength("[*"+key+"]:"+str(value),24)
			#output+='[*'+key+']: '+str(value)+"\n"
			output+='[*'+key+']: '+str(value)+"  "
		#output = output[:-1]
		if not output.strip(): output=''
		output +='\n'
		return output


def parse_ent(ent,meter,init,toprint=True):
	#print init, type(init), dir(init)
	ent.parse(meter,init=init)
	init._Text__parses[meter.id].append( ent.allParses(meter) )
	init._Text__bestparses[meter.id].append( ent.bestParse(meter) )
	init._Text__boundParses[meter.id].append( ent.boundParses(meter) )
	init._Text__parsed_ents[meter.id].append(ent)
	if toprint:
		ent.scansion(meter=meter,conscious=True)
	return ent

def parse_ent_mp(input_tuple):
	(ent,meter,init,toprint) = input_tuple
	return parse_ent(ent,meter,init,toprint)





# class representing the potential bounding relations between to parses
class Bounding:
	bounds = 0 # first parse harmonically bounds the second
	bounded = 1 # first parse is harmonically bounded by the second
	equal = 2 # the same constraint violation scores
	unequal = 3 # unequal scores; neither set of violations is a subset of the other


@total_ordering
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
		for k,v in list(self.constraintScores.items()):
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
		#logging.debug('>> extending self (%s) with slot (%s)',self,slot)
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

		#logging.debug('>> self extended to be (%s) with extendedParses (%s)',self,extendedParses)
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
		for constraint, value in list(self.constraintScores.items()):
			if value == "*":
				self.totalScore = "*"
				return self.totalScore
			score += value
		self.totalScore = score

		return int(self.totalScore) if int(self.totalScore) == self.totalScore else self.totalScore

	"""
	Python 3 DEPRECATED
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
	"""
	def __lt__(self,other):
		return self.score() < other.score()

	def __eq__(self, other):
		return self.score() == other.score()

	def posString(self,viols=False):		# eg NE|ver|CAME|poi|SON|from|SO|sweet|A|place
		output = []
		for pos in self.positions:
			x=str(pos)
			if viols and pos.has_viol: x+='*'
			output.append(x)
		return '|'.join(output)

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
					for k,v in list(unit.feats.items()):
						if (not "prom." in k): continue
						if v:
							feats += "[+" + str(k) + "] "
						else:
							feats += "[-" + str(k) + "] "
					feats += '\t'
				feats = feats.strip()

			viols = ""
			for k,v in list(pos.constraintScores.items()):
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
			pass
			#logging.debug('Parse1: %s\nLastMeterVal1: %s\nLastNumSlots1: %s\n--can compare-->\nParse2: %s\nLastMeterVal2: %s\nLastNumSlots2: %s',self,self.positions[-1].meterVal,len(self.positions[-1].slots),parse,parse.positions[-1].meterVal,len(parse.positions[-1].slots))
		return isTrue
		#return (self.numSlots == self.totalSlots)
		#return False

	def violations(self,boolean=False):
		if not boolean:
			return self.constraintScores
		else:
			return [(k,(v>0)) for (k,v) in list(self.constraintScores.items())]

	@property
	def violated(self):
		viold=[]
		for c,viol in list(self.constraintScores.items()):
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
				##logging.debug('Parse1: %s\nViols1: %s\n--bounds-->\nParse2: %s\nViols2: %s',parse,str([(k,v) for k,v in sorted(parse.constraintCounts.items()) if v]),self,str([(k,v) for k,v in sorted(self.constraintCounts.items()) if v]))
				return Bounding.bounded # contains only greater violations

		else:

			if containsLesserViolation:
				##logging.debug('Parse1: %s\nViols1: %s\n--bounds-->\nParse2: %s\nViols2: %s',self,str([(k,v) for k,v in sorted(self.constraintCounts.items()) if v]),parse,str([(k,v) for k,v in sorted(parse.constraintCounts.items()) if v]))
				return Bounding.bounds # contains only lesser violations

			else:
				return Bounding.equal # contains neither greater nor lesser violations



import string
from copy import copy
from Parse import Parse
class MeterPosition(Parse):
	def __init__(self, meter, meterVal): # meterVal represents whether the position is 's' or 'w'
		self.slots=[]
		self.children=self.slots
		self.meter = meter
		self.constraintScores = {}
		for constraint in meter.constraints:
			self.constraintScores[constraint] = 0
		self.meterVal = meterVal
		for slot in self.slots:
			slot.meter=meterVal

		self.feat('prom.meter',(meterVal=='s'))
		#self.feat('meter',self.meterVal2)
		#self.token = ""

	def __copy__(self):
		other = MeterPosition(self.meter, self.meterVal)
		other.slots = self.slots[:]
		for k,v in list(self.constraintScores.items()):
			other.constraintScores[k]=copy(v)
		return other

	@property
	def has_viol(self):
		return bool(sum(self.constraintScores.values()))

	@property
	def violated(self):
		viold=[]
		for c,viol in list(self.constraintScores.items()):
			if viol:
				viold+=[c]
		return viold

	@property
	def isStrong(self):
		return self.meterVal.startswith("s")

	def append(self,slot):
		#self.token = ""
		self.slots.append(slot)

	@property
	def meterVal2(self):
		return ''.join([self.meterVal for x in self.slots])

	@property
	def mstr(self):
		return ''.join([self.meterVal for n in range(len(self.slots))])

	def posfeats(self):
		posfeats={'prom.meter':[]}
		for slot in self.slots:
			for k,v in list(slot.feats.items()):
				if (not k in posfeats):
					posfeats[k]=[]
				posfeats[k]+=[v]
			posfeats['prom.meter']+=[self.meterVal]

		for k,v in list(posfeats.items()):
			posfeats[k]=tuple(v)

		return posfeats
	#
	# def __repr__(self):
	#
	# 	if not self.token:
	# 		slotTokens = []
	#
	# 		for slot in self.slots:
	# 			#slotTokens.append(self.u2s(slot.token))
	# 			slotTokens.append(slot.token)
	#
	# 		self.token = '.'.join(slotTokens)
	#
	# 		if self.meterVal == 's':
	# 			self.token = self.token.upper()
	# 		else:
	# 			self.token = self.token.lower()
	# 	return self.token


	def __repr__(self):
		return self.token

	@property
	def token(self):
		if not hasattr(self,'_token') or not self._token:
			token = '.'.join([slot.token for slot in self.slots])
			token=token.upper() if self.meterVal=='s' else token.lower()
			self._token=token
		return self._token





from entity import entity
class MeterSlot(entity):
	def __init__(self,i,unit,token,wordpos,word,i_word=0,i_syll_in_word=0,wordtoken=None,meter=None):
		self.i=i					# eg, could be one of 0-9 for a ten-syllable line
		self.children=[unit]
		self.token=token
		self.featpaths={}
		self.wordpos=wordpos
		self.word=word
		self.issplit=False
		self.i_word=i_word
		self.i_syll_in_word=i_syll_in_word
		self.wordtoken=wordtoken
		self.meter=meter

		#self.feat('slot.wordpos',wordpos)
		self.feat('prom.stress',unit.feature('prom.stress'))
		self.feat('prom.strength',unit.feature('prom.strength'))
		self.feat('prom.kalevala',unit.feature('prom.kalevala'))
		self.feat('prom.weight',unit.children[0].feature('prom.weight'))
		self.feat('shape',unit.str_shape())
		self.feat('prom.vheight',unit.children[0].feature('prom.vheight'))
		self.feat('word.polysyll',self.word.numSyll>1)

		## Phrasal stress
		self.feat('prom.phrasal_stress',self.phrasal_stress)
		self.feat('prom.phrasal_strength',self.phrasal_strength)
		self.feat('prom.phrasal_head',self.phrasal_head)

	@property
	def phrasal_strength(self):
		if not self.wordtoken: return None
		if self.word.numSyll>1 and self.stress != 'P': return None
		if self.wordtoken.feats.get('phrasal_stress_peak',''): return True
		if self.wordtoken.feats.get('phrasal_stress_valley',''): return False
		return None

	@property
	def phrasal_head(self):
		if not self.wordtoken: return None
		if self.word.numSyll>1 and self.stress != 'P': return None
		if self.wordtoken.feats.get('phrasal_head',''): return True
		return None

	@property
	def phrasal_stress(self):
		if not self.wordtoken: return None
		if self.word.numSyll>1 and self.stress != 'P': return None

		if self.meter.config.get('phrasal_stress_norm_context_is_sentence',0):
			return self.wordtoken.phrasal_stress
		else:
			return self.wordtoken.phrasal_stress_line


	def str_meter(self):
		return self.meter

	def str_token(self):
		if not hasattr(self,'meter'):
			return self.token
		else:
			if self.meter=="s":
				return self.token.upper()
			else:
				return self.token.lower()

	@property
	def stress(self):
		if self.feature('prom.stress')==1.0:
			return "P"
		elif self.feature('prom.stress')==0.5:
			return "S"
		elif self.feature('prom.stress')==0.0:
			return "U"




