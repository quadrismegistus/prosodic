import os

class MeterConstraint:
	def __init__(self,id=None,name=None,logic=None,weight=1):
		self.id=id
		self.constr = None
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
	
	#def __hash__(self):
	#	return self.name.__hash__()
	
	def violationScore(self,meterPos):
		"""call this on a MeterPosition to return an integer representing the violation value
		for this Constraint in this MPos (0 represents no violation)""" 
		violation = None
		if self.constr != None:
			violation = self.constr.parse(meterPos)
		else:
			violation = self.__hardparse(meterPos)
		#violation = self.__hardparse(meterPos)
		if violation != "*":
			meterPos.constraintScores[self] += violation
		return violation
	
	def __hardparse(self,meterPos):
		if '.' in self.name:	# kiparsky self.names
			## load variables
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
			
			if promSite_prom.lower()==promSite_prom:
				promSite_prom = (promSite_prom == 'p')				# string 2 boolean: p:True, u:False
			else:
				if promSite_prom=="P":
					promSite_prom=1.0
				#elif promSite_prom=="U":
				else:
					promSite_prom=0.0
					
			
			
			
			# NOT EVEN ONE unit_prom can be promSite_prom:
			if promSite_isneg: 
				for slot in meterPos.slots:
					slot_prom=slot.feature('prom.'+promType,True)
					if slot_prom==None: continue
					if type(promSite_prom)==type(True):	
						slot_prom=bool(slot_prom)
					if slot_prom == promSite_prom:
							return self.weight
				return 0
			
			# AT LEAST ONE unit_prom must be promSite_prom (or else, violate):
			else:			
				violated=True
				ran=False
				for slot in meterPos.slots:
					slot_prom=slot.feature('prom.'+promType,True)
					if slot_prom==None:
						continue
					if type(promSite_prom)==type(True):	
						slot_prom=bool(slot_prom)
					ran=True
					if slot_prom==promSite_prom:
						violated=False
				if ran and violated:
					return self.weight
				else:
					return 0
		
		elif self.name.lower().startswith('footmin'):
			if len(meterPos.slots) < 2:
				return 0
			elif len(meterPos.slots) > 2:
				return self.weight
			name=self.name.lower()
			a = meterPos.slots[0]
			b = meterPos.slots[1]
			
			## should this apply to ALL foomin constraints?
			if ( bool(a.feature('prom.stress',True)) and bool(b.feature('prom.stress',True))):
				return self.weight
			##
			
			if "nohx" in name:
				if (bool(a.feature('prom.weight',True))):
					return self.weight
			
			if "nolh" in name:
				if ( (bool(b.feature('prom.weight',True))) ):
					return self.weight
			
			if "wordbound" in name:
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
				
			# made it through this minefield, eh?
			return 0