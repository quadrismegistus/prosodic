import os,tools

PSTRESS_THRESH_DEFAULT = 2

class MeterConstraint:
	def __init__(self,id=None,name=None,logic=None,weight=1,meter=None, mu=0.0, sigma=1.0):
		self.id=id
		self.constr = None
		self.meter=meter
		self.mu = mu
		self.sigma = sigma
		if not name:
			self.name=id
		else:
			self.name=name
			if os.path.exists(name + ".py"):
				originalPath = os.getcwd()
				constraintPath, constraintName = os.path.split(name)
				os.chdir(constraintPath)
				self.constr = __import__(constraintName)
				os.chdir(originalPath)
		self.weight=weight
		self.logic=logic

	def __repr__(self):
		return "[*"+self.name+"]"

	@property
	def name_weight(self):
		weight=str(self.weight) if int(self.weight)!=self.weight else str(int(self.weight))
		return "[*"+self.name+"/"+weight+"]"


	#def __hash__(self):
	#	return self.name.__hash__()

	def violationScore(self,meterPos,pos_i=None,slot_i=None,num_slots=None,all_positions=None,parse=None):
		"""call this on a MeterPosition to return an integer representing the violation value
		for this Constraint in this MPos (0 represents no violation)"""
		violation = None
		if self.constr != None:
			violation = self.constr.parse(meterPos)
		else:
			violation = self.__hardparse(meterPos,pos_i=pos_i,slot_i=slot_i,num_slots=num_slots,all_positions=all_positions,parse=parse)
		#violation = self.__hardparse(meterPos)
		if violation != "*":
			meterPos.constraintScores[self] += violation


		"""
		print
		print '>>',slot_i,num_slots, self.name, meterPos, violation, all_positions
		for slot in meterPos.slots:
			print slot, slot.feature('prom.stress')
		print"""

		return violation

	def __hardparse(self,meterPos,pos_i=None,slot_i=None,num_slots=None,all_positions=None,parse=None):
		import prosodic as p
		#if meterPos.slots[0].i<2:
		#	print meterPos.slots[0].word

		#print meterPos,pos_i,slot_i,num_slots,all_positions
		#prevpos=all_positions[pos_i-1]
		#print pos_i, meterPos, prevpos, pos_i,pos_i-1,all_positions, len(meterPos.slots)

		if '.' in self.name:	# kiparsky self.names
			## load variables

			#exception for first foot
			#if 'skip_initial_foot' in parse.constraintNames:
			#	if meterPos.slots[0].i<2:
			#		return 0

			if 'extrametrical-first-pos' in parse.constraintNames and pos_i==0:
				return 0
			elif 'skip_initial_foot' in parse.constraintNames and pos_i in [0,1]:
				return 0


			promSite = self.name.split(".")[1]
			promType = self.name.split(".")[0]
			promSite_meter = promSite.split("=>")[0].strip()	# s/w
			promSite_prom = promSite.split("=>")[1].strip()		# +- u/p

			if meterPos.meterVal != promSite_meter:	# then this constraint does not apply
				return 0

			if promSite_prom[0:1] == "-":						# -u or -p: eg, if s=>-u, then NOT EVEN ONE s can be u(nprom)
				promSite_isneg = True
				promSite_prom = promSite_prom[1:]				# u or p
			else:
				promSite_isneg = False							# u or p: eg, if s=>p, then AT LEAST ONE s must be p(rom)

			"""
			Removed 4/12/2017: apparently there was an option to restrict just 'P'rimary stresses
			But required using an uppercase P in the meter config. This was nowhere stated elsewhere
			and has never been used. I'm disabling it. Let's just use a separate prominence type
			if we want to restrict only primary stresses.

			if promSite_prom.lower()==promSite_prom:
				promSite_prom = (promSite_prom == 'p')				# string 2 boolean: p:True, u:False
			else:
				if promSite_prom=="P":
					promSite_prom=1.0
				#elif promSite_prom=="U":
				else:
					promSite_prom=0.0
			"""

			promSite_prom = (promSite_prom == 'p')				# string 2 boolean: p:True, u:False




			# NOT EVEN ONE unit_prom can be promSite_prom:
			if promSite_isneg:
				numtrue=0
				for slot in meterPos.slots:
					slot_prom=slot.feature('prom.'+promType,True)
					if slot_prom==None: continue

					#if type(promSite_prom)==type(True):
					#	slot_prom=bool(slot_prom)
					pstress_thresh=self.meter.config.get('phrasal_stress_threshold',PSTRESS_THRESH_DEFAULT)
					try:
						pstress_thresh=float(pstress_thresh)
					except ValueError:
						pstress_thresh=PSTRESS_THRESH_DEFAULT

					bool_prom_type = bool(slot_prom) if promType!='phrasal_stress' else slot_prom<=pstress_thresh

					if bool_prom_type == promSite_prom:
						#numtrue+=float(slot_prom)
						return self.weight
				#return 2 if numtrue else 0
				#print self.weight, numtrue
				## CHANGED 10/10/2016: This constraint returns its weight
				## *times* the number of slots/syllables that violated it.
				## CHANGED 4/12/2017: numtrue is actually float of the prominence
				## so for phrasal stress is its p-stress value, for seconday stress is 0.5, etc.

				return self.weight * numtrue
				#return 0

			# AT LEAST ONE unit_prom must be promSite_prom (or else, violate):
			else:
				violated=True
				ran=False
				for slot in meterPos.slots:
					slot_prom=slot.feature('prom.'+promType,True)
					if slot_prom==None:
						continue
					ran=True
					if bool(slot_prom)==promSite_prom:
						violated=False
				if ran and violated:
					return self.weight
				else:
					return 0

		elif self.name.lower().startswith('initialstrong'):
			#if meterPos.slots[0].i==0:
			if pos_i==0:
				if meterPos.meterVal == 's':
					return self.weight
			return 0

		elif self.name.lower().startswith('functiontow'):
			#exception for first foot
			if p.config.get('skip_initial_foot',0):
				if meterPos.slots[0].i<2:
					return 0

			if meterPos.meterVal != 's':	# then this constraint does not apply
				return 0

			vio = 0
			for slot in meterPos.slots:
				if slot.word.feature('functionword'):
					vio += self.weight
			return vio

		elif self.name.lower().startswith('footmin'):
			if len(meterPos.slots) < 2:
				return 0
			elif len(meterPos.slots) > 2:
				return self.weight
			name=self.name.lower()
			a = meterPos.slots[0]
			b = meterPos.slots[1]

			## should this apply to ALL foomin constraints?
			#if ( bool(a.feature('prom.stress',True)) and bool(b.feature('prom.stress',True))):
			#	return self.weight
			##

			if name=='footmin-nohx':
				if (bool(a.feature('prom.weight',True))):
					return self.weight

			if name=='footmin-w-resolution':
				if a.word != b.word: return 0 # only applies within word-boundaries
				firstsyll_islight=bool(a.feature('prom.weight',True)) == False
				firstsyll_isstressed=bool(a.feature('prom.stress',True)) == True
				if not (firstsyll_islight and firstsyll_isstressed):
					return self.weight

			if name=='footmin-f-resolution':
				if a.word == b.word: return 0 # only applies to word-boundaries
				if meterPos.meterVal=='s': return self.weight # cannot apply to strong positions
				a_is_fw = bool(a.word.feature('functionword'))
				b_is_fw = bool(b.word.feature('functionword'))
				if not (a_is_fw and b_is_fw): return self.weight

			if name=='footmin-s-nohx':
				if meterPos.meterVal=='s':
					if bool(a.feature('prom.weight',True)) or a.word!=b.word:
						return self.weight

			if "nolh" in name:
				if ( (bool(b.feature('prom.weight',True))) ):
					return self.weight

			if "strongconstraint" in name:
				if bool(b.feature('prom.strength',True)):
					return self.weight

				if bool(a.feature('prom.strength',True)):
					if not bool(a.feature('prom.weight',True)):
						 if a.word==b.word and not a.wordpos[0]==a.wordpos[1]:
						 	if not bool(b.feature('prom.stress',True)):
						 		return 0
					return self.weight

			if name=='footmin-none':
				return self.weight

			if name=='footmin-none-unless-in-first-two-positions':
				if pos_i!=0 and pos_i!=1:
					return self.weight

			if name=='footmin-none-unless-in-second-position':
				if pos_i!=1:
					return self.weight

			if name=='footmin-no-s': return self.weight * int(meterPos.meterVal=='s')
			if name=='footmin-no-w': return self.weight * int(meterPos.meterVal=='w')

			if name=='footmin-no-s-unless-preceded-by-ww':
				# @TODO: bug when number of syllables in maxW is > 2 ?
				if meterPos.meterVal!='s': return 0
				if pos_i==0: return self.weight
				prevpos=all_positions[pos_i-1]
				#print pos_i, meterPos, prevpos, pos_i,pos_i-1,all_positions
				if len(prevpos.slots)>1 and prevpos.meterVal=='w':
					return 0
				return self.weight




			if "wordbound" in name:
				if name=='footmin-wordbound':
					if a.word!=b.word:
						return self.weight

				if "nomono" in name:
					if (a.word.numSyll==1 or b.word.numSyll==1):
						return self.weight

				if 'lexmono' in name:
					#if a.word.numSyll==1 and a.word.stress=="P"
					if a.word.isLexMono() or b.word.isLexMono():
						return self.weight



				## everyone is happy if both are function words
				if a.word.feature('functionword') and b.word.feature('functionword'):
					return 0

				if a.word!=b.word:
					if "bothnotfw" in name:
						if not (a.word.feature('functionword') and b.word.feature('functionword')):
							return self.weight
					elif "neitherfw":
						if not (a.word.feature('functionword') or b.word.feature('functionword')):
							return self.weight
					elif "leftfw":
						if not (a.word.feature('functionword')):
							return self.weight
					elif "rightfw":
						if not (b.word.feature('functionword')):
							return self.weight



				# only remaining possibilities:
				#	i) slots a,b are from the same word
				#   ii) slots a,b are from contiguous words which are the same (haPPY HAppy)

				if a.wordpos[0]==a.wordpos[1]:	# in the firs slot's (start,end) wordpos : if (start==end) :  then poss. (ii) above
					if "bothnotfw" in name:
						if not (a.word.feature('functionword') and b.word.feature('functionword')):
							return self.weight
					elif "neitherfw":
						if not (a.word.feature('functionword') or b.word.feature('functionword')):
							return self.weight
					elif "leftfw":
						if not (a.word.feature('functionword')):
							return self.weight
					elif "rightfw":
						if not (b.word.feature('functionword')):
							return self.weight

				# poss. (i) remains
				return 0


		## Constraints about words
		if self.name=='word-elision':
			words=set([slot.word for slot in meterPos.slots if hasattr(slot.word,'is_elision') and slot.word.is_elision])
			sylls=[]
			for slot in meterPos.slots: sylls+=slot.children

			for word in words:
				lastsyll=word.children[-1]
				if lastsyll in sylls: # only break if this position contains the word's final syllable
					return self.weight


		# is this the end?
		is_end = slot_i+1==num_slots and meterPos.slots==all_positions[-1].slots

		## CONSTRAINTS ON PREVIOUS POSITIONS
		"""
		ABANDONED TEMPORARILY AS NOT POSSIBLE GIVEN THAT PARSES ARE BOUNDED AS PARSING GOES ON
		"""

		if self.name=='attridge-ss-not-by-ww':
			#if meterPos.meterVal!='s': return 0
			#if not is_end and meterPos.meterVal2 == 'ss':
			#	parse.pauseComparisons=True

			if pos_i==0: return 0
			prevpos=all_positions[pos_i-1]
			prevprevpos=all_positions[pos_i-2] if (pos_i-2)>=0 else None
			#print prevprevpos,prevpos,meterPos
			#print prevprevpos.meterVal2 if prevprevpos else None,prevpos.meterVal2, meterPos.meterVal2

			#print prevprevpos,prevpos,meterPos
			#print prevprevpos.meterVal2 if prevprevpos else None,prevpos.meterVal2, meterPos.meterVal2
			#print dir(prevprevpos) if prevprevpos else None
			#print dir(prevpos) if prevprevpos else None
			#print dir(meterPos)
			#print

			if prevpos.meterVal2 == 'ss':

				#if (prevprevpos and prevprevpos.meterVal2=='ww')

				if (prevprevpos and prevprevpos.meterVal2=='ww') and (not hasattr(prevprevpos,'_flag_already_served_as_ww')):
					prevprevpos._flag_already_served_as_ww=True
					pass
				elif meterPos.meterVal2=='ww' and (not hasattr(meterPos,'_flag_already_served_as_ww')):
					meterPos._flag_already_served_as_ww=True
					pass
				else:
					#print 'ERROR!'
					for cnstr in prevpos.constraintScores:
						if cnstr.name==self.name:
							prevpos.constraintScores[cnstr]=self.weight
							parse.constraintScores[cnstr]+=self.weight

				#parse.pauseComparisons=False
			elif is_end and meterPos.meterVal2=='ss':
				#parse.pauseComparisons=False
				if prevpos.meterVal2=='ww':
					pass
				else:
					#print 'ERROR!'
					return self.weight
			#print
		#"""



		## POST HOC CONSTRAINTS
		if is_end:
			final_meter_str=''.join([''.join(pos.meterVal for slot in pos.slots) for pos in all_positions])
			#print final_meter_str

			# headedness
			if self.name.startswith('headedness'):
				shouldbe = self.name.split('!=')[-1]

				"""
				Approach 1: This approach doesn't really work on individual lines:

				# binary or ternary?
				weak_pos = [pos for pos in all_positions if pos.meterVal=='w']
				if len(weak_pos)<2: return 0
				weak_pos_types = [''.join('w' for slot in pos.slots) for pos in weak_pos]

				if weak_pos_types.count('ww')>weak_pos_types.count('w'): # ternary
					if final_meter_str[3]=='w': # anapestic
						headedness = 'rising'
					else: # dactylic
						headedness = 'falling'
				else: # binary
					if final_meter_str[3]=='w':
						headedness = 'falling' # trochaic
					else:
						headedness = 'rising'

				if shouldbe != headedness:
					return self.weight
				"""

				"""
				Approach 2: count 'ws' vs 'sw' pairs and give categorical violation
				"""
				quasi_feet=[''.join(x) for x in tools.slice([pos.meterVal for pos in all_positions],slice_length=2,runts=False)]
				headedness = 'rising' if quasi_feet.count('ws')>=quasi_feet.count('sw') else 'falling'
				#print final_meter_str
				#print quasi_feet
				#print headedness
				#print

				if shouldbe != headedness:
					return self.weight
				#"""

				"""
				Approach 3: count 'ws' vs 'sw' pairs and give violation/num-pos per off foot

				quasi_feet=[''.join(x) for x in tools.slice([pos.meterVal for pos in all_positions],slice_length=2,runts=True)]
				if shouldbe == 'rising':
					num_not_rising = float(len([ft for ft in quasi_feet if ft!='ws']))
					return num_not_rising / float(len(all_positions)) * float(self.weight)
				elif shouldbe == 'falling':
					num_not_falling = float(len([ft for ft in quasi_feet if ft!='sw']))
					return num_not_falling / float(len(all_positions)) * float(self.weight)
				"""


			# number of feet
			if self.name.startswith('number_feet'):
				shouldbe = int(self.name.split('!=')[-1])
				strong_pos = [pos for pos in all_positions if pos.meterVal=='s']
				num_feet = len(strong_pos) # debatable
				if shouldbe != num_feet:
					return self.weight

			# other posthoc constraints
			if self.name.startswith('posthoc'):
				if self.name=='posthoc-no-final-ww':
					if len(all_positions[-1].slots)>1 and all_positions[-1].meterVal=='w':
						return self.weight

				if self.name=='posthoc-no-final-w':
					if all_positions[-1].meterVal=='w':
						return self.weight

				if self.name=='posthoc-standardize-weakpos':
					weak_pos = [pos for pos in all_positions if pos.meterVal=='w']
					if len(weak_pos)<2: return 0
					weak_pos_types = [''.join('w' for slot in pos.slots) for pos in weak_pos]
					maxcount = max([weak_pos_types.count(wtype) for wtype in set(weak_pos_types)])
					diff = len(weak_pos) - maxcount
					return self.weight*diff

		# made it through this minefield, eh?
		return 0
