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
