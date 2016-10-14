from entity import entity
class MeterSlot(entity):
	def __init__(self,i,unit,token,wordpos,word,i_word=0,i_syll_in_word=0):
		self.i=i					# eg, could be one of 0-9 for a ten-syllable line
		self.children=[unit]
		self.token=token
		self.featpaths={}
		self.wordpos=wordpos
		self.word=word
		self.issplit=False
		self.i_word=i_word
		self.i_syll_in_word=i_syll_in_word
		
		#self.feat('slot.wordpos',wordpos)
		self.feat('prom.stress',unit.feature('prom.stress'))
		self.feat('prom.strength',unit.feature('prom.strength'))
		self.feat('prom.kalevala',unit.feature('prom.kalevala'))
		self.feat('prom.weight',unit.children[0].feature('prom.weight'))
		self.feat('shape',unit.str_shape())
		self.feat('prom.vheight',unit.children[0].feature('prom.vheight'))
		self.feat('word.polysyll',self.word.numSyll>1)
		
	def str_meter(self):
		return self.meter
			
	def str_token(self):
		if not hasattr(self,'meter'):
			return self.token
		else:
			if self.meter=="s":
				return self.token.upper()
			else:
				return self.token.lower()

	@property
	def stress(self):
		if self.feature('prom.stress')==1.0:
			return "P"
		elif self.feature('prom.stress')==0.5:
			return "S"
		elif self.feature('prom.stress')==0.0:
			return "U"