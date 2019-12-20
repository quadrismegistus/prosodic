from entity import entity
class Onset(entity):
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
		
	def isBranching(self):
		return len(self.children)>1

