
from entity import entity,being
from tools import *
import Meter
class Word(entity):
	def __init__(self,token,syllables=None,sylls_text=[],broken=False,lang=None):
		if syllables==None:
			import prosodic
			if lang==None:
				lang=prosodic.lang
			w=prosodic.dict[lang].get(token)[0]
			if not len(w.__dict__):
				self.broken=True
			else:
				for k,v in w.__dict__.items():
					setattr(self,k,v)
			return
		
		
		self.token = token.lower()	# the case-sensitive, non-punctuation representation
		self.punct = ""	# the right-aligned punctuation (if any)
		self.sylls_text=sylls_text	# a list of strings, representing this word's syllabification
		self.finished = False	# finished parameter
		
		self.children = syllables	# pre-loaded Syllable objects
		self.numSyll = len(syllables)	# the number of syllables
		self.broken=broken
		self.featpaths={}
		self.stress='?'
		self.lang='?'
		
		
		self.feats = {}	# the feats
		
		# check to see if pos-tagged
		if("/" in self.token):
			tt = self.token.split("/")
			self.token = tt[0]
			self.pos = tt[1]

		# glean punctuation from token
		(self.token, self.punct) = gleanPunc(self.token)
		
		## if not yet, get sylltokens
		self.setSyllText()
		self.feat('numSyll',self.numSyll)
		
		## am i broken?	
		if (not len(syllables)) or (self.token==""):
			self.broken = True
			self.token='?'+self.token
		else:
			## set sylltokens
			len_sylls=len(self.children)
			len_sylls_text=len(self.sylls_text)
			if len_sylls!=len_sylls_text:
				self.om("<error> numSyll mismatch: [ipa] "+self.u2s(".".join([child.str_ipa() for child in self.children]))+" vs [orth] "+str(".".join([self.u2s(x) for x in self.sylls_text])))
				#self.om("<error> numSyll mismatch: [ipa] ... vs [orth] "+str(".".join([self.u2s(x) for x in self.sylls_text])))
				length=min([len_sylls,len_sylls_text])
			else:
				length=len_sylls
			for i in range(length):
				self.children[i].settok(self.sylls_text[i])
		


	def __repr__(self):
		return "<"+self.classname()+"."+self.u2s(self.token)+"> ["+self.__str__stressedSylls()+"]"
		
	def __str__(self):
		return str(self.token)+str("\t<")+str(self.__str__stressedSylls())+str(">")

	def __str__weight(self):
		if not hasattr(self,'weight'):
			self.weight="".join([entity.weight_bool2str[syll.children[0].feature('prom.weight')] for syll in self.children])
		return self.weight

	def __str__stressedSylls(self):
		lang=self.lang
		import prosodic
		if (not 'output_'+lang in prosodic.config):
			lang="**"
		if prosodic.config['output_'+lang]=="cmu":
			return " . ".join([str(syll) for syll in self.children])
		else:
			return ".".join([str(syll) for syll in self.children])
		
	def output_minform(self):
		return str(makeminlength(self.u2s(self.token),20))+"\t"+str(makeminlength("P:"+self.__str__stressedSylls(),35))+"\tS:"+str(self.stress)+"\tW:"+str(self.__str__weight())
		


	
	def CorV(self):
		o = ""
		for phoneme in self.phonemes():
			o+=phoneme.CorV()
		return o
			

#		def getSyllText(self):
#			return self.sylls_text
	
	def setSyllText(self):
		if (not self.sylls_text) and (len(self.children)):
			self.setSyllText_byphonemes()

	def addSuffix(self,phon):
		self.children[len(self.children)-1].addSuffix(phon)
			
	def lastsyll(self):
		return self.children[len(self.children)-1]
	
	def setSyllText_byphonemes(self):
		return self.setSyllText_byletters(self.CorV())
		
		
		corv = self.CorV()
		corvi=0
		self.sylls_text = []
		for syll in self.children:
			syllshape = syll.feature('shape')
			if not syllshape:
				continue
			sylltail = syllshape[-1]
			vowi = corv.find('V',corvi)
			if (len(corv)-1) == vowi:
				self.sylls_text.append(corv[corvi:vowi])
			elif sylltail == "V":
				if(corv[vowi+1] == "V"):
					self.sylls_text.append(corv[corvi:vowi+1])
					corvi=vowi+1+1
				else:
					self.sylls_text.append(corv[corvi:vowi])
					corvi=vowi+1
			elif sylltail == "C":
				self.sylls_text.append(corv[corvi:vowi+1])
				corvi=vowi+1+1

	def setSyllText_byletters(self,lengthby=None):		
		i = 0
		textSyll = []
		self.sylls_text=[]
		numSyll = len(self.children)
		numLetters = len(self.token)
		
		if not numLetters:
			for x in self.stress:
				self.sylls_text.append('?')
			return None
		
		while(i < numSyll):
			textSyll.append("")
			i+=1
		
		word = self.token
		if not lengthby:
			inc=numLetters/numSyll
		else:
			inc=len(lengthby)/numSyll
		if not inc: inc=1
		curSyll = 0
		unit = ""
		curLetter = 1
		for letter in word:
			textSyll[curSyll] += letter
			if(curLetter % inc == 0):
				if ((curSyll + 1) < numSyll):
					curSyll += 1
			curLetter += 1
		self.sylls_text = textSyll
		
	def addPunct(self,punct):
		self.punct=punct






	def getToken(self,punct=True):
		if punct and (self.punct != None):
			return self.u2s(self.token) + self.u2s(self.punct)
		else:
			return self.u2s(self.token)
	def getPOS(self):
		return self.pos
	def getStress(self):
		return self.stress
	def getWeight(self):
		return self.weight
	def getFeet(self):
		return self.feet
	def getPunct(self):
		return self.punct
	def isIgnored(self):
		return ("?" in self.stress) or ("?" in self.weight)
	def getTokenSyll(self):
		return ".".join([str(syll) for syll in self.children])
		
	def getNumSyll(self):
		return len(self.children)
		#return self.numSyll
	 
	def isMonoSyllab(self):
		return (self.getNumSyll() == 1)
	def isPolySyllab(self):
		return (self.getNumSyll() > 1)
		
#	def __repr__(self):
#		if (self.punct != None):
#			return '{'+str(self.getTokenSyll())+'['+str(self.punct)+']}'
#		else:
#			return '{'+str(self.getTokenSyll())+'}'

