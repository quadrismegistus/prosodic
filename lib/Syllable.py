
from entity import entity,being

class Syllable(entity):
	def __init__(self,syllstrengthstress,lang,token=""):
		## initialize
		self.feats = {}
		self.children=[syllstrengthstress[0]]
		self.syll=self.children[0]
		self.token=token
		self.lang=lang
		#self.stress=stress
		
		self.featpaths={}
		
		## load features
		self.feat('prom.strength', syllstrengthstress[1])
		self.feat('prom.stress', syllstrengthstress[2])
		#if (bool(self.feature('prom.stress'))):
		if (self.feature('prom.stress')==1.0):
			if (bool(self.children[0].feature('prom.weight'))):
				self.feat('prom.kalevala',self.feature('prom.stress'))
			else:
				self.feat('prom.kalevala',0.0)
		else:
			self.feat('prom.kalevala',None)

	def settok(self,tok):
		self.token=tok
	
	def __repr__(self):
		return "<"+self.classname()+"."+self.u2s(self.token)+"> ["+str(self)+"]"
	
	
	def getShape(self):
		return self.syll.getShape()

	def str_shape(self):
		shape=self.getShape()
		while "CC" in shape:
			shape=shape.replace("CC","C")
		while "VVV" in shape:
			shape=shape.replace("VVV","VV")
		return shape

	def isHeavy(self):
		return self.syll.isHeavy()
	
	def newRimeForSuffix(self,phon):
		return self.syll.newRimeForSuffix(phon)
		
	def str_ipa(self):
		return "".join(self.u2s(repr(x)) for x in self.phonemes())
	
	def str_cmu(self):
		return " ".join([str(x.str_cmu()) for x in self.phonemes()])
		
	def str_stress(self):
		if not hasattr(self,'stress'):
			self.stress=entity.stress_float2str[self.feature('prom.stress')]
		return self.stress
		
	def str_weight(self):
		if not hasattr(self,'weight'):
			self.weight=entity.weight_bool2str[self.syll.feature('prom.weight')]
		return self.weight
	
	def str_orth(self):
		if not self.token:
			ipaself=self.str_ipa()
			#print "<error> no orthographic syllabification available for syllable ["+self.str_ipa()+"] in language ["+self.lang+"]"
			return ipaself
		return str(self.u2s(self.token))
		
	def __str__(self):
		## begin string, add stress mark if stressed
		o=""
		stress=self.feature('prom.stress')
		if stress==1.0:
			o+="'"
		elif stress==0.5:
			o+="`"
		#o+=
		
		## get string output based on configuration for language
		if not hasattr(self,'lang') or not self.lang:
			lang='**'
		else:
			lang=self.lang

		import prosodic
		if (not 'output_'+lang in prosodic.config):
			lang="**"
		
		oer=getattr(self,'str_'+str(prosodic.config['output_'+lang]).strip())
		o+=oer()
		return o
