from .imports import *
from .texts import Text
from .parsing import ParseTextUnit

class Stanza(Subtext):
	sep: str = ''
	child_type: str = 'Line'
	

class Line(ParseTextUnit, Subtext):
	sep: str = ''
	child_type: str = 'Word'

	def init(self):
		if self._init or self.children: return self
		if self.txt:
			line = Text(self.txt.replace('\n',' / '), **self._attrs).lines[0]
			self._attrs = line._attrs
			self.children = line.children

		
		self._init=True
		return self
