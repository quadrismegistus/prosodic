from ipa import ipa,ipakey,ipa2cmu
from entity import entity
class Phoneme(entity):	
	def __init__(self,phons,ipalookup=True):
		self.feats = {}
		self.children = []	# should remain empty
		self.featpaths={}
		self.phon=None
		
		if type(phons)==type([]):
			for phon in phons:
				if type(phon)==type(""):
					self.children.append(Phoneme(phon))
				else:
					self.children.append(phon)
			self.feat('dipthong',True)
		else:
			self.phon=phons.strip()
	
		if ipalookup and self.phon:
			if(self.phon in ipa):
				k=-1
				for v in ipa[self.phon]:
					k+=1
					self.feat(ipakey[k],v)
			self.finished = True
		
			if self.isLong() or self.isDipthong():
				self.len=2
			else:
				self.len=1
	def str_cmu(self):
		strself=str(repr(self))
		if strself in ipa2cmu:
			return ipa2cmu[strself].lower()
		else:
			print "<error> no cmu transcription for phoneme: ["+strself+"]"
			return strself
		
	def __str__(self):
		if self.children:
			return self.u2s(u"".join([x.phon for x in self.children]))
		else:
			return self.u2s(self.phon)
			
	def __repr__(self):
		return "["+str(self)+"]"
	
	def isConsonant(self):
		return self.feature('cons')
	def isVowel(self):
		return (self.isDipthong() or self.isPeak())
	def isPeak(self):
		return self.feature('syll')
	def isDipthong(self):
		return self.feature('dipthong')
	def isLong(self):
		return self.feature('long')
	def isHigh(self):
		return self.feature('high')
	
	
	def CorV(self):
		if self.isDipthong() or self.isLong():
			return "VV"
		
		if self.isPeak():
			return "V"
		else:
			return "C"
			

	def __eq__(self,other):
		return self.feats == other.feats