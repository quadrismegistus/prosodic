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
		self.token = ""
	
	def __copy__(self):
		other = MeterPosition(self.meter, self.meterVal)
		other.slots = self.slots[:]
		for k,v in self.constraintScores.items():
			other.constraintScores[k]=copy(v)		
		return other
	
	def append(self,slot):
		self.token = ""
		self.slots.append(slot)	
	
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
	
	def __repr__(self):
	
		if not self.token:
			slotTokens = []
			
			for slot in self.slots:
				slotTokens.append(self.u2s(slot.token))
				
			self.token = string.join(slotTokens, '.')
		
			if self.meterVal == 's':
				self.token = self.token.upper()
			else:
				self.token = self.token.lower()
				
		return self.token