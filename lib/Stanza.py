from entity import entity
from Line import Line

class Stanza(entity):
	def givebirth(self):
		line=Line()
		line.ignoreMe=False
		#line.parent=self
		return line

	def __repr__(self):
		num=self.parent.children.index(self)+1
		return "<Stanza "+str(num)+"> ("+str(len(self.children))+" lines)"
	
	def str_meter(self):
		return ''.join([l.bestParse().str_meter() for l in self.children if l.bestParse()])
	
	def viols_bysyll(self):
		lis=[]
		for l in self.children:
			if not l.bestParse(): continue
			lis.extend( l.bestParse().viols_bysyll() )
		return lis