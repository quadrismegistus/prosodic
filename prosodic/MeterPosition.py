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
		for k,v in self.constraintScores.items():
			other.constraintScores[k]=copy(v)
		return other

	@property
	def has_viol(self):
		return bool(sum(self.constraintScores.values()))

	@property
	def violated(self):
		viold=[]
		for c,viol in self.constraintScores.items():
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
			for k,v in slot.feats.items():
				if (not k in posfeats):
					posfeats[k]=[]
				posfeats[k]+=[v]
			posfeats['prom.meter']+=[self.meterVal]

		for k,v in posfeats.items():
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
			token = u'.'.join([slot.token for slot in self.slots])
			token=token.upper() if self.meterVal=='s' else token.lower()
			self._token=token
		return self._token
