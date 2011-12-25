from entity import entity
class MeterSlot(entity):
	def __init__(self,i,unit,token,wordpos,word):
		self.i=i					# eg, could be one of 0-9 for a ten-syllable line
		self.children=[unit]
		self.token=token
		self.featpaths={}
		self.wordpos=wordpos
		self.word=word
		self.issplit=False
		
		#self.feat('slot.wordpos',wordpos)
		self.feat('prom.stress',unit.feature('prom.stress'))
		self.feat('prom.strength',unit.feature('prom.strength'))
		self.feat('prom.kalevala',unit.feature('prom.kalevala'))
		self.feat('prom.weight',unit.children[0].feature('prom.weight'))
		self.feat('shape',unit.str_shape())
		self.feat('prom.vheight',unit.children[0].feature('prom.vheight'))
		
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