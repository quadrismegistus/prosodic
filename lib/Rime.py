from entity import entity
class Rime(entity):
	def __init__(self,nucleuscoda,lang):
		## initialize
		self.feats = {}
		self.nucleus = nucleuscoda[0]
		self.coda = nucleuscoda[1]
		self.featpaths={}
		self.lang=lang
		
		self.children=[]
		if self.nucleus:
			self.children.append(self.nucleus)
		else:
			self.broken=True
			
		
		if self.coda:
			self.children.append(self.coda)

		
	def isBranching(self):
		return self.hasCoda()

	def hasCoda(self):
		if (self.coda.children):
			return True
		else:
			return False
