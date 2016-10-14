from entity import entity
class Nucleus(entity):
	def __init__(self,phonemes,lang):
		## initialize
		self.feats = {}
		self._p_changed=True	# for persistence
		self.featpaths={}
		self.lang=lang
		
		if phonemes:
			self.children = phonemes
		else:
			self.children=[]
		#self.len=len(self.children)
		
		## load features
		#self.feat('isBranching',self.getShape())
		self.feat('prom.vheight',self.isHigh())
		#print self
		
	def isBranching(self):
		return (self.isDipthong() or self.isLong())

	def isDipthong(self):
		for phon in self.children:
			if phon.isDipthong():
				return True
		return False
	def isHigh(self):
		for phon in self.children:
			if phon.isHigh():
				return True
		return False
	
	def isLong(self):
		for phon in self.children:
			if phon.isLong():
				return True
		return False