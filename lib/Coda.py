from entity import entity
class Coda(entity):
	def __init__(self,phonemes,lang):
		## initialize
		self.feats = {}
		self.featpaths={}
		self.lang=lang
		
		if phonemes:
			self.children = phonemes
		else:
			self.children=[]
		
	def isBranching(self):
		return len(self.children)>1

