from entity import entity
class MeterSlot(entity):
	def __init__(self,i,unit,token,wordpos,word,i_word=0,i_syll_in_word=0,wordtoken=None,meter=None):
		self.i=i					# eg, could be one of 0-9 for a ten-syllable line
		self.children=[unit]
		self.token=token
		self.featpaths={}
		self.wordpos=wordpos
		self.word=word
		self.issplit=False
		self.i_word=i_word
		self.i_syll_in_word=i_syll_in_word
		self.wordtoken=wordtoken
		self.meter=meter

		#self.feat('slot.wordpos',wordpos)
		self.feat('prom.stress',unit.feature('prom.stress'))
		self.feat('prom.strength',unit.feature('prom.strength'))
		self.feat('prom.kalevala',unit.feature('prom.kalevala'))
		self.feat('prom.weight',unit.children[0].feature('prom.weight'))
		self.feat('shape',unit.str_shape())
		self.feat('prom.vheight',unit.children[0].feature('prom.vheight'))
		self.feat('word.polysyll',self.word.numSyll>1)

		## Phrasal stress
		self.feat('prom.phrasal_stress',self.phrasal_stress)
		self.feat('prom.phrasal_strength',self.phrasal_strength)
		self.feat('prom.phrasal_head',self.phrasal_head)

	@property
	def phrasal_strength(self):
		if not self.wordtoken: return None
		if self.word.numSyll>1 and self.stress != 'P': return None
		if self.wordtoken.feats.get('phrasal_stress_peak',''): return True
		if self.wordtoken.feats.get('phrasal_stress_valley',''): return False
		return None

	@property
	def phrasal_head(self):
		if not self.wordtoken: return None
		if self.word.numSyll>1 and self.stress != 'P': return None
		if self.wordtoken.feats.get('phrasal_head',''): return True
		return None

	@property
	def phrasal_stress(self):
		if not self.wordtoken: return None
		if self.word.numSyll>1 and self.stress != 'P': return None

		if self.meter.config.get('phrasal_stress_norm_context_is_sentence',0):
			return self.wordtoken.phrasal_stress
		else:
			return self.wordtoken.phrasal_stress_line


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
