from .imports import *



class Word(Text):
	child_type: str = 'WordForm'

	def init(self):
		if self._init: return self
		
		self._children = []
		sylls,ipa_l = self.lang_obj.get(self.txt)
		for ipa in ipa_l:
			wf = WordForm(self.txt, sylls_text = sylls, sylls_ipa = ipa)
			self._children.append(wf)
		self._init=True
		return self


class WordForm(Word):
	pass


# class WordToken(entity):
# 	def __init__(self,words,token,is_punct=False,sentence=None,line=None):
# 		self.children=words
# 		self.token=token
# 		self.is_punct=is_punct
# 		self.sentence=None
# 		self.feats={}
# 		self.line=line

# 	def __getitem__(self,key):
# 		return self.children[key]

# 	def __repr__(self):
# 		return "<"+self.classname()+":"+self.u2s(self.token)+">"

# 	def set_as_best_word_option(self,wordobj):
# 		if not wordobj in self.children:
# 			raise Exception("You're trying to prioritize this wordobj "+str(wordobj)+ ", but it was never in this wordtoken "+str(self)+" to begin with!")
# 		if len(self.children)<2: return
# 		self.children = list(self.children)
# 		self.children.remove(wordobj)
# 		self.children.insert(0,wordobj)

# 	def has_stressed_variant(self):
# 		return True in ['P' in word.stress for word in self.children]

# 	def has_unstressed_variant(self):
# 		return True in [not 'P' in word.stress for word in self.children]

# 	def add_unstressed_variant(self):
# 		if not self.children: return
# 		wordobj = self.children[0]
# 		wordobj.feats['functionword']=True
# 		self.children += [wordobj.get_unstressed_variant()]

# 	def add_stressed_variant(self,stress_pattern=None):
# 		if not self.children: return
# 		wordobj = self.children[0]

# 		new_wordobj = wordobj.get_stressed_variant(stress_pattern)
# 		if new_wordobj: self.children += [new_wordobj]

# 	def remove_unstressed_variant(self):
# 		new_wordobjs = []
# 		for wordobj in self.children:
# 			if not 'P' in wordobj.stress: #unstressed
# 				continue
# 			new_wordobjs+=[wordobj]
# 		self.children = new_wordobjs

# 	def remove_stressed_variant(self):
# 		new_wordobjs = []
# 		for wordobj in self.children:
# 			if 'P' in wordobj.stress: #stressed
# 				continue
# 			new_wordobjs+=[wordobj]
# 		self.children = new_wordobjs

# 	def make_stress_ambiguous(self,stress_pattern=None):
# 		if not self.children: return
# 		if self.has_stressed_variant() and not self.has_unstressed_variant():
# 			self.add_unstressed_variant()
# 		elif self.has_unstressed_variant() and not self.has_stressed_variant():
# 			self.add_stressed_variant(stress_pattern=stress_pattern)

# 	def make_unstressed(self):
# 		if not self.children: return
# 		if not self.has_unstressed_variant(): self.add_unstressed_variant()
# 		if self.has_stressed_variant(): self.remove_stressed_variant()

# 	def make_stressed(self,stress_pattern=None):
# 		if not self.children: return
# 		if not self.has_stressed_variant(): self.add_stressed_variant()
# 		if self.has_unstressed_variant(): self.remove_unstressed_variant()


# 	@property
# 	def stress(self):
# 		if not self.children: return ''
# 		return self.children[0].stress

# 	@property
# 	def weight(self):
# 		if not self.children: return ''
# 		return self.children[0].weight

# 	@property
# 	def phrasal_stress(self):
# 		#ps=self.feats.get('norm_mean',None)
# 		ps=self.feats.get('mean',None)
# 		#if ps: return None
# 		if ps==None: return None
# 		import numpy as np
# 		if np.isnan(ps): return None
# 		return ps

# 	@property
# 	def phrasal_stress_line(self):

# 		#ps=self.feats.get('norm_mean_line',None)
# 		ps=self.feats.get('mean_line',None)
# 		#if ps: return None
# 		if ps==None: return None
# 		import numpy as np
# 		if np.isnan(ps): return None
# 		return ps

# 	@property
# 	def phrasal_stress_norm(self):

# 		ps=self.feats.get('norm_mean',None)
# 		#if not ps: return None
# 		if ps==None: return None
# 		import numpy as np
# 		if np.isnan(ps): return None
# 		return ps

# 	@property
# 	def phrasal_stress_norm_line(self):

# 		ps=self.feats.get('norm_mean_line',None)
# 		#if not ps: return None
# 		if ps==None: return None
# 		import numpy as np
# 		if np.isnan(ps): return None
# 		return ps




# class Word(entity):
# 	def __init__(self,token,syllables=None,sylls_text=[],broken=False,lang=None):
# 		if syllables==None:
# 			import prosodic
# 			if lang==None:
# 				lang=prosodic.lang
# 			w=prosodic.dict[lang].get(token)[0]
# 			if not len(w.__dict__):
# 				self.broken=True
# 			else:
# 				for k,v in list(w.__dict__.items()):
# 					setattr(self,k,v)
# 			return


# 		self.token = token.lower()	# the case-sensitive, non-punctuation representation
# 		self.punct = ""	# the right-aligned punctuation (if any)
# 		self.sylls_text=sylls_text	# a list of strings, representing this word's syllabification
# 		self.finished = False	# finished parameter

# 		self.children = syllables	# pre-loaded Syllable objects
# 		self.numSyll = len(syllables)	# the number of syllables
# 		self.broken=broken
# 		self.featpaths={}
# 		self.stress='?'
# 		self.lang='?'


# 		self.feats = {}	# the feats

# 		# check to see if pos-tagged
# 		if("/" in self.token):
# 			tt = self.token.split("/")
# 			self.token = tt[0]
# 			self.pos = tt[1]

# 		# glean punctuation from token
# 		(self.token, self.punct) = gleanPunc(self.token)

# 		## if not yet, get sylltokens
# 		self.setSyllText()
# 		self.feat('numSyll',self.numSyll)

# 		## am i broken?
# 		if (not len(syllables)) or (self.token==""):
# 			self.broken = True
# 			self.token='?'+self.token
# 		else:
# 			## set sylltokens
# 			len_sylls=len(self.children)
# 			len_sylls_text=len(self.sylls_text)
# 			if len_sylls!=len_sylls_text:
# 				self.om("<error> numSyll mismatch: [ipa] "+self.u2s(".".join([child.str_ipa() for child in self.children]))+" vs [orth] "+str(".".join([self.u2s(x) for x in self.sylls_text])))
# 				#self.om("<error> numSyll mismatch: [ipa] ... vs [orth] "+str(".".join([self.u2s(x) for x in self.sylls_text])))
# 				length=min([len_sylls,len_sylls_text])
# 			else:
# 				length=len_sylls
# 			for i in range(length):
# 				self.children[i].settok(self.sylls_text[i])



# 	def __repr__(self):
# 		return "<"+self.classname()+"."+self.u2s(self.token)+"> ["+self.__str__stressedSylls()+"]"

# 	def __str__(self):
# 		tok=self.token if type(self.token)==str else self.token.encode('utf-8')
# 		return tok+str("\t<")+str(self.__str__stressedSylls())+str(">")
# 		#return self.token+"\t<"+self.__str__stressedSylls()+">"

# 	def __str__weight(self):
# 		if not hasattr(self,'weight'):
# 			self.weight="".join([entity.weight_bool2str[syll.children[0].feature('prom.weight')] for syll in self.children])
# 		return self.weight

# 	def __str__stressedSylls(self):
# 		lang=self.lang
# 		import prosodic
# 		if (not 'output_'+lang in prosodic.config):
# 			lang="**"
# 		if prosodic.config.get('output_'+lang,'')=="cmu":
# 			return " . ".join([str(syll) for syll in self.children])
# 		else:
# 			return ".".join([str(syll) for syll in self.children])


# 	def output_minform(self):
# 		return str(makeminlength(self.u2s(self.token),20))+"\t"+str(makeminlength("P:"+self.__str__stressedSylls(),35))+"\tS:"+str(self.stress)+"\tW:"+str(self.__str__weight())




# 	def CorV(self):
# 		o = ""
# 		for phoneme in self.phonemes():
# 			o+=phoneme.CorV()
# 		return o


# #		def getSyllText(self):
# #			return self.sylls_text

# 	def setSyllText(self):
# 		if not self.children: return
# 		if not self.sylls_text or len(self.sylls_text)!=len(self.children):
# 			self.setSyllText_byphonemes()

# 	def addSuffix(self,phon):
# 		self.children[len(self.children)-1].addSuffix(phon)

# 	def lastsyll(self):
# 		return self.children[len(self.children)-1]

# 	def setSyllText_byphonemes(self):
# 		return self.setSyllText_byletters(self.CorV())


# 		corv = self.CorV()
# 		corvi=0
# 		self.sylls_text = []
# 		for syll in self.children:
# 			syllshape = syll.feature('shape')
# 			if not syllshape:
# 				continue
# 			sylltail = syllshape[-1]
# 			vowi = corv.find('V',corvi)
# 			if (len(corv)-1) == vowi:
# 				self.sylls_text.append(corv[corvi:vowi])
# 			elif sylltail == "V":
# 				if(corv[vowi+1] == "V"):
# 					self.sylls_text.append(corv[corvi:vowi+1])
# 					corvi=vowi+1+1
# 				else:
# 					self.sylls_text.append(corv[corvi:vowi])
# 					corvi=vowi+1
# 			elif sylltail == "C":
# 				self.sylls_text.append(corv[corvi:vowi+1])
# 				corvi=vowi+1+1

# 	def setSyllText_byletters(self,lengthby=None):
# 		i = 0
# 		textSyll = []
# 		self.sylls_text=[]
# 		numSyll = len(self.children)
# 		numLetters = len(self.token)

# 		if not numLetters:
# 			for x in self.stress:
# 				self.sylls_text.append('?')
# 			return None

# 		while(i < numSyll):
# 			textSyll.append("")
# 			i+=1

# 		word = self.token
# 		if not lengthby:
# 			inc=numLetters/numSyll
# 		else:
# 			inc=len(lengthby)/numSyll
# 		if not inc: inc=1
# 		curSyll = 0
# 		unit = ""
# 		curLetter = 1
# 		for letter in word:
# 			textSyll[curSyll] += letter
# 			if(curLetter % inc == 0):
# 				if ((curSyll + 1) < numSyll):
# 					curSyll += 1
# 			curLetter += 1
# 		self.sylls_text = textSyll

# 	def addPunct(self,punct):
# 		self.punct=punct

# 	@property
# 	def weight(self):
# 		return "".join([entity.weight_bool2str[syll.children[0].feature('prom.weight')] for syll in self.children])




# 	def getToken(self,punct=True):
# 		if punct and (self.punct != None):
# 			return self.u2s(self.token) + self.u2s(self.punct)
# 		else:
# 			return self.u2s(self.token)


# 	def getPOS(self):
# 		return self.pos
# 	def getStress(self):
# 		return self.stress
# 	def getWeight(self):
# 		return self.weight
# 	def getFeet(self):
# 		return self.feet
# 	def getPunct(self):
# 		return self.punct
# 	def isIgnored(self):
# 		return ("?" in self.stress) or ("?" in self.weight)

# 	def isLexMono(self):
# 		return self.numSyll==1 and self.stress=='P'

# 	def getTokenSyll(self):
# 		return ".".join([str(syll) for syll in self.children])

# 	def getNumSyll(self):
# 		return len(self.children)
# 		#return self.numSyll

# 	def isMonoSyllab(self):
# 		return (self.getNumSyll() == 1)
# 	def isPolySyllab(self):
# 		return (self.getNumSyll() > 1)

# #	def __repr__(self):
# #		if (self.punct != None):
# #			return '{'+str(self.getTokenSyll())+'['+str(self.punct)+']}'
# #		else:
# #			return '{'+str(self.getTokenSyll())+'}'

# 	def get_unstressed_variant(self):
# 		new_ipa=self.ipa.replace("'","").replace("`","")
# 		return self.get_word_variant(new_ipa)

# 	def get_stressed_variant(self,stress_pattern=None):
# 		#assert len(stress_pattern) == len(self.children)
# 		if not stress_pattern:
# 			if len(self.children)==1:
# 			    stress_pattern=['P']
# 			else:
# 			    print("!! cannot force stressed variant to polysyllabic word",self,"without a stress pattern set")
# 			    return

# 		if len(stress_pattern) != len(self.children):
# 			print("!! stress_pattern",stress_pattern,"does not match # sylls of this word:",len(self.children),self.children)
# 			return

# 		#assert len(stress_pattern) == len(self.ipa.split('.'))
# 		if len(stress_pattern) != len(self.ipa.split('.')):
# 			print("!! stress_pattern",stress_pattern,"does not match # sylls of this word:",len(self.children),self.children)
# 			return

# 		## Re-code stress pattern if necessary
# 		new_stress_pattern = []
# 		for x in stress_pattern:
# 			if x in ['P','S','U']:
# 				new_stress_pattern+=[x]
# 			elif x in ['1',1,1.0]:
# 				new_stress_pattern+=['P']
# 			elif x in ['2',2,2.0]:
# 				new_stress_pattern+=['S']
# 			elif x in ['0',0,0.0]:
# 				new_stress_pattern+=['U']
# 		stress_pattern = new_stress_pattern
# 		##

# 		newipa=[]
# 		for i,x in enumerate(self.ipa.replace("'","").replace("`","").split(".")):
# 			stress=stress_pattern[i]
# 			if stress=='P':
# 				newipa+=["'"+x]
# 			elif stress=='S':
# 				newipa+=["`"+x]
# 			else:
# 				newipa+=[x]
# 		newipa='.'.join(newipa)

# 		return self.get_word_variant(newipa)


# 	def get_word_variant(self,stressedipa):
# 		from Dictionary import stressedipa2stress,getStrengthStress
# 		from Syllable import Syllable

# 		stress=stressedipa2stress(stressedipa)
# 		(prom_stress,prom_strength)=getStrengthStress(stress)

# 		syllphons=[tuple(child.phonemes()) for child in self.children]
# 		syllbodies = self.syllableBodies()

# 		sylls=[]
# 		for i in range(len(syllphons)):
# 			syllbody=syllbodies[i]
# 			syll=Syllable((syllbody,prom_strength[i],prom_stress[i]),lang=self.lang,token=self.sylls_text[i])
# 			sylls.append(syll)

# 		word=Word(self.token,sylls,self.sylls_text)
# 		word.ipa=stressedipa
# 		word.stress=stress
# 		word.lang=self.lang

# 		# when is word broken?
# 		if not word.ipa:
# 			word.broken=True

# 		return word

