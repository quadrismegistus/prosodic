# -*- coding: UTF-8 -*-
import os,pickle,glob,time,sys
from tools import *
from entity import *
from Word import Word
from Syllable import Syllable

from ipa import ipa
import codecs
LANGCODES = {'en':'english', 'fi':'finnish'}

class Dictionary:	# cf Word, in that Text.py will really instantiate Dictionary_en,Dictionary_fi,usw.
	classnames=['Phoneme','Onset','Nucleus','Coda','Rime','SyllableBody','Syllable','Word','Phrase']
	char2phons=[]
	for k in ipa.keys():
		if len(k)>1:
			for x in k[1:]:
				char2phons.append(x)

	def __init__(self,lang):
		import prosodic
		dirself=prosodic.dir_prosodic
		libfolder=os.path.join(dirself,'lib')
		dictsfolder=os.path.join(dirself,'dicts')
		self.config=prosodic.config
		self.unstressedWords=[]
		self.maybestressedWords=[]

		self.lang = lang
		self.libfolder = libfolder
		self.dictsfolder = os.path.join(dictsfolder,self.lang)
		sys.path.append(self.dictsfolder)

		self.language=""
		self.getprep=False
		self.booted=False

		"""
		for filename in glob.glob(os.path.join(self.dictsfolder, self.lang+'*')):
			self.language = filename.split(os.path.sep).pop().split(".")[0]
			break
		if not self.language:
			exit('!! language could not be ascertained from files in '+self.dictsfolder+'. Please name your .tsv and/or .py dictionary file(s) using a string which begins with the two characters which serve as the name for the dictionary folder (eg, "en")')
		"""
		self.language = LANGCODES[self.lang]


		for filename in glob.glob(os.path.join(self.dictsfolder, 'unstressed*')):
			file=codecs.open(filename,encoding='utf-8')
			for ln in file:
				for word in ln.split():
					self.unstressedWords.append(word)
			file.close()
			break


		for filename in glob.glob(os.path.join(self.dictsfolder, 'maybestressed*')):
			file=codecs.open(filename,encoding='utf-8')
			for ln in file:
				for word in ln.split():
					self.maybestressedWords.append(word)
			file.close()
			break

		pyfile=os.path.join(self.dictsfolder,self.language+'.py')
		if os.path.exists(pyfile):
			self.getprep=get_class(self.language+'.get')

		self.cachefolder=os.path.join(self.dictsfolder,'_cache')
		self.dictentries=None
		build=False

		## language objects
		timestart=time.clock()
		if being.persists:
			if __name__=='__main__':
				print "## booting ontology: " + self.language + " ..."
			if not os.path.exists(self.cachefolder):os.mkdir(self.cachefolder)
			self.storage = FileStorage(self.cachefolder+'ontology.zodb')
			self.db = DB(self.storage)
			self.conn = self.db.open()
			self.dict = self.conn.root()
			self.t=transaction

			if not len(self.dict.values()):
				build=True
		else:
			self.dict={}
			self.refresh()
			topickle=self.exists_pickle()
			topickle=False
			if topickle:
				self.boot_pickle(topickle)
			else:
				build=True

		if build:
			self.refresh()
			self.boot()

		if __name__=='__main__':
			print self.stats(prefix="\t").replace("[[time]]",str(round((time.clock() - timestart),2)))


	def boot(self):		## NEEDS EXTENSION
		if not self.getprep:
			bootfile=os.path.join(self.dictsfolder,self.language+'.tsv')
			if os.path.exists(bootfile):
				self.boot_general(bootfile)
				self.booted=True

			if not self.booted:
				exit("<error:dictionary> neither a "+self.language+".tsv nor a "+self.language+".py in directory "+self.dictsfolder)

	def str2unicode(self,string):
		o=u""
		for x in string:
			try:
				o+=unicode(x)
			except UnicodeDecodeError:
				print "error"
				o+=unichr(ord(x))
		return o


	def boot_general(self,bootfile):
		if __name__=='__main__':
			print "## booting dictionary: " + self.language + " ..."
		file=codecs.open(bootfile,encoding='utf-8')
		for ln in file:
			line=ln.split('\t')
			line.reverse()
			token=line.pop().strip()
			if token.startswith('#'): continue
			stressedipa=line.pop().strip()

			if ("." in token) and (token.count(".")==stressedipa.count(".")):
				sylls_text=token.split(".")
				token=token.replace(".","")
			else:
				sylls_text=None

			#line.reverse()
			#otherfeats=line

			if (not token in self.dict['Word']):
				self.dict['Word'][token]=[]
			self.dict['Word'][token].append((stressedipa,sylls_text))



	def build(self):	## NEEDS EXTENSION
		pass

	def refresh(self):
		if being.persists:
			self.dict.clear()
			for k in Dictionary.classnames:
				self.dict[k]=OOBTree()
		else:
			for k in Dictionary.classnames:
				self.dict[k]={}

	# boot options
	def exists_pickle(self,picklefile=False):
		if not picklefile:
			picklefile=self.dictsfolder+self.language+'.pickle'
		if not os.path.exists(picklefile):
			return False
		else:
			return picklefile

	def boot_pickle(self,picklefile):
		file=open(picklefile)
		self.dict=pickle.load(file)
		file.close()

	def boot_dict(self,filename):	# filename = *.txt or *.pickle
		print ">> loading Dictionary " + filename + "..."
		fileobj = open(self.dictsfolder + filename, 'r')
		if filename[-7:] == ".pickle":
			return None	# the bare-bones text file [language].tsv should not be pickled--wasteful
		elif filename[-4:] == ".txt":
			dictionary = {}
			curLine = fileobj.readline().strip()
			while(curLine):
				curLine = fileobj.readline().strip()
				if(curLine == ""): break
				if(curLine.startswith("#")): continue

				tokens = curLine.split()
				if(len(tokens) < 2): continue
				curKey = tokens[0].lower()
				if("(" in curKey):
					wrd = curKey.split("(")[0].strip()
				else:
					wrd = curKey.strip()
				if(not wrd in dictionary):
					dictionary[wrd] = []
				dictionary[wrd].append(curLine)
			self.dictentries=dictionary
		else:
			self.dictentries={}

	# boot_dict_specific
	def boot_dict_specific(self,filename,sep="\t"):
		newdict={}
		if (not "/" in filename):
			filename=self.dictsfolder+filename
		file=open(filename,'r')
		for line in file:
			linedat=line.split(sep)
			key=linedat[0]
			val=linedat[1]
			if key.startswith('#'): continue
			if (not key in newdict):
				newdict[key]=val
			else:
				if type(newdict[key])==list:
					newdict[key].append(val)
				else:
					newdict[key]=[newdict[key],val]
		return newdict

	def boot_build(self):
		self.build(save=False)

	# lookup options
	def lookup_db(self,tok):	# needs to be rewritten
		rows=[]
		for row in self.c.execute('select entry from dict where lower(word)="' + tok.lower() + '"'):
				for x in row:
					if (not x in rows):
						rows.append(x)
		return rows

	def lookup_dict(self,tok):
		if (not tok in self.dict):
			return {}
		else:
			return self.dictentries[tok]

	def gleanPunc(self,word):
		return gleanPunc(word)

	def has(self,word):
		if not word: return False
		word=unicode(word)
		(p0,word,p1)=gleanPunc2(word)
		word_l = word.lower()


		## if not there, but a contractino
		# if already there, say yes
		if word_l in self.dict['Word'] and self.dict['Word'][word_l]: return True
		"""
		for contr,add_ipa in [("'s","z"), ("'d","d")]:
			if word_l.endswith(contr):
				word_l_unc = word_l[:-2]
				# if the uncontracted in the dictionary
				if word_l_unc in self.dict['Word'] and self.dict['Word'][word_l_unc]:
					for obj in self.dict['Word'][word_l_unc]:
						if type(obj) in [tuple]:
							ipa,sylls_text=obj
						else:
							ipa=obj.ipa
							sylls_text=obj.sylls_text

						ipa+=add_ipa
						#sylls_text[-1]+=contr

						## save new word
						if not word_l in self.dict['Word']: self.dict['Word'][word_l]=[]
						self.dict['Word'][word_l]+=[(ipa,sylls_text)]
		"""

		return (word_l in self.dict['Word'] and self.dict['Word'][word_l])


	def use(self,classtype,key):
		"""
		HACKED 9/29/16: No longer caching SyllableBodies. Reuse was causing bugs. More thorough solution would be helpful.
		"""

		if type(key)==type([]):
			key=tuple(key)
		if (not key in self.dict[classtype]):
			if classtype in ['Phoneme','Onset','Nucleus','Coda','Rime','Syllable']:
				self.dict[classtype][key]=get_class(classtype+'.'+classtype)(key,self.lang)
				#return get_class(classtype+'.'+classtype)(key,self.lang)
			elif classtype=="SyllableBody":
				#self.dict[classtype][key]=self.syllphon2syll(key,self.lang)
				return self.syllphon2syll(key,self.lang)

		return self.dict[classtype][key]

	def haveAlready(self,classtype,key):
		if type(key)==type([]):
			key=tuple(key)
		return (key in self.dict[classtype])

	def ipa2phons(self,stressedipa):
		sylls=[]
		for syllphon in stressedipa.split("."):
			syll=[]
			syllphon.strip()
			for i in range(len(syllphon)):
				phon=syllphon[i]
				if (phon in Dictionary.char2phons): continue
				if (phon=="`") or (phon=="'"): continue

				try:
					phonN=syllphon[i+1]
				except IndexError:
					phonN=False
				if phonN and (phonN in Dictionary.char2phons):
					phon=phon+phonN

				phonobj=self.use('Phoneme',phon)
				syll.append(phonobj)

			Vwaslast=False
			k=-1
			for phon in syll:
				k+=1
				if phon.isVowel():

					if Vwaslast:
						if self.haveAlready('Phoneme', (Vwaslast.phon,phon.phon)):
							newphon=self.use('Phoneme',(Vwaslast.phon,phon.phon))
						else:
							newphon=get_class('Phoneme.Phoneme')([self.use('Phoneme',x) for x in [Vwaslast.phon,phon.phon]], self.lang)
							#self.dict['Phoneme'][(Vwaslast.phon,phon.phon)]=newphon
							self.dict['Phoneme'][Vwaslast.phon+phon.phon]=newphon
						syll[k]=newphon
						syll.remove(Vwaslast)
						break
					else:
						Vwaslast=phon
			sylls.append(tuple(syll))
		#print sylls
		return sylls

	def syllphon2syll(self,syllphon,lang):
		onset=[]
		nucleus=[]
		coda=[]
		for x in syllphon:
			if x.isVowel():
				nucleus.append(x)
			else:
				if not nucleus:
					onset.append(x)
				else:
					coda.append(x)

		return get_class('SyllableBody.SyllableBody')(self.use('Onset',onset),self.use('Rime', (self.use('Nucleus',nucleus),self.use('Coda',coda))), lang)






	def getStrengthStress0(self,stress):
		prom_strength=[]
		prom_stress=[]
		for i in range(len(stress)):
			syll=stress[i]
			syllP=False
			syllN=False

			try:
				syllP=stress[i-1]
			except IndexError:
				pass
			try:
				syllN=stress[i+1]
			except IndexError:
				pass

			if syll=="P":
				prom_stress.append(1.0)

				if (len(stress)>1):
					if syllN and (syllN=="P"):
						prom_strength.append(None)
					elif syllP and (syllP=="P"):
						if len(stress)>2:
							prom_strength.append(1.0)
						else:
							prom_strength.append(None)
					else:
						prom_strength.append(1.0)

			elif syll=="S":
				prom_stress.append(0.5)

				if (len(stress)>1):
					if syllP and ((syllP=="P") or (syllP=="S")):
						prom_strength.append(0.5)
					elif syllN and (syllN=="P"):
						prom_strength.append(0.5)
					else:
						prom_strength.append(0.5)

			elif syll=="U":
				prom_stress.append(0.0)

				if (len(stress)>1):
					if syllP and ((syllP=="P") or (syllP=="S")):
						prom_strength.append(0.0)
					elif syllN and ((syllN=="P") or (syllN=="S")):
						prom_strength.append(0.0)
					else:
						prom_strength.append(None)
		if len(stress)==1:
			prom_strength=[None]

		return (prom_stress,prom_strength)

	def reset(self):
		for classtype in [ct for ct in self.dict if ct!='Word']: self.dict[classtype]={}
		for word in self.dict['Word']:
			self.dict['Word'][word]=[((wordobj.ipa,wordobj.sylls_text) if type(wordobj)!=tuple else wordobj) for wordobj in self.dict['Word'][word]]


	def make(self,stressedipasylls_text,token):
		stressedipa=stressedipasylls_text[0]
		sylls_text=stressedipasylls_text[1]

		stress=stressedipa2stress(stressedipa)
		(prom_stress,prom_strength)=getStrengthStress(stress)
		syllphons=self.ipa2phons(stressedipa)

		sylls=[]

		for i in range(len(syllphons)):
			syllbody=self.use('SyllableBody',syllphons[i])
			syll=self.use('Syllable',(syllbody,prom_strength[i],prom_stress[i]))
			#print token,i,syllbody,syll,syllphons,stressedipa,stress,prom_stress,prom_strength
			sylls.append(syll)

		word=Word(token,sylls,sylls_text)
		word.ipa=stressedipa
		word.stress=stress
		word.lang=self.lang

		# when is word broken?
		if not word.ipa:
			word.broken=True


		return word

	def maybeUnstress(self,words):
		word=words[0].token.lower()

		def unstress_word(wordobj):
			#wordobj.feat('functionword',True)
			wordobj.feats['functionword']=True
			wordobj.stress=""
			for child in wordobj.children:
				wordobj.stress+="U"
				child.feats['prom.stress']=0.0
				child.feats['prom.kalevala']=None
				child.children[0].feats['prom.weight']=False


		if word in self.maybestressedWords:		# only for monosyllabs
			wordobjs=self.dict['Word'][word]
			stresses = [wordobj.stress for wordobj in wordobjs]
			if max([len(sx) for sx in stresses])>1:
				return wordobjs

			if 'U' in stresses and 'P' in stresses:
				unstressed_words = [wordobj for wordobj in wordobjs if wordobj.stress=='U']
				for wordobj in unstressed_words: unstress_word(wordobj)
				return wordobjs

			else:
				wordobj1=wordobjs[0]
				ipa=wordobj1.ipa
				if 'U' in stresses and not 'P' in stresses:
					newipa="'"+ipa
					newobjs=[self.make((_ipa,None),word) for _ipa in [ipa,newipa]]
					#newobjs[0].feat('functionword',True)
					newobjs[0].feats['functionword']=True
				elif 'P' in stresses and not 'U' in stresses:
					newipa=ipa[1:]
					newobjs=[self.make((_ipa,None),word) for _ipa in [ipa,newipa]]
					#newobjs[-1].feat('functionword',True)
					newobjs[-1].feats['functionword']=True
				else:
					print "??",word,stresses

				return newobjs



		elif word in self.unstressedWords:
			wordobj=self.dict['Word'][word][0]
			unstress_word(wordobj)
			return [wordobj]

		return words


	def get(self,word,stress_ambiguity=True):
		if type(word)==str:
			word=word.decode('utf-8',errors='ignore')

		(word,punct)=gleanPunc(word)

		if self.has(word):
			words=self.dict['Word'][word.lower()]
		elif self.getprep:
			words=self.getprep(word,config=self.config)
		else:
			return [Word(word,[],None)]

		if not words:
			return [Word(word,[],None)]

		if type(words)==list:
			if type(words[0])==tuple:	# New word needs to be built
				wordobjs=[]
				for wordtuple in words:
					wrd=wordtuple[:2]
					attrs=wordtuple[2] if len(wordtuple)>2 else {}
					wordobj=self.make(wrd,word)
					for _k,_v in attrs.items(): setattr(wordobj,_k,_v)
					wordobjs+=[wordobj]
				self.dict['Word'][word.lower()]=wordobjs
				return self.maybeUnstress(wordobjs) if stress_ambiguity else wordobjs
			else:
				wordobjs=words
		else:
			wordobjs=[words]

		return self.maybeUnstress(wordobjs) if stress_ambiguity else wordobjs



	## featpaths:experimental
	def featpath(self):
		pass




	# save options
	def save_tabbed(self):
		for k,v in self.dict.items():
			if k!='word': continue # just the words for now
			o="token\tstress\tipa\n"
			for kk,vv in v.items():
				if type(vv)!=type([]):
					vv=[vv]
				for vvv in vv:
					if not vvv: continue
					o+=str(kk)+"\t"+str(vvv.str_ipasyllstress())+"\n"
			file=open(self.dictsfolder+self.language+'.tsv','w')
			file.write(o)
			file.close()

	def save_pickle(self):
		file=open(self.dictsfolder+self.language+'.pickle','w')
		pickle.dump(self.dict,file)
		file.close()

	def persist(self):
		if being.persists:
			self.t.commit()

	def save(self):
		if being.persists:
			print "saving..."
			self.t.commit()
			#transaction.commit()

		self.save_tabbed()

	def words(self):
		words=[]
		for k,v in self.dict['word'].items():
			for vv in v:
				words.append(vv)
		return words

	def close(self):
		if being.persists:
			self.conn.close()

	## output option
	def stats(self,prefix="\t"):
		#self.numents={}
		o=""
		for k,v in self.dict.items():
			if not len(v): continue
			if k[-2:]=="us":
				ks=k[:-2]+"i"
			else:
				ks=k+'s'
			o+=prefix + str(len(v)).replace('0','?') + ' ' + ks + '\n'
		if o:
			return "## [[[time]]s] loaded:\n"+o
		else:
			return ""
		return o





def getStrengthStress(stress):
	prom_stress=[]
	prom_strength=[]
	for x in stress:
		if x=='P': prom_stress+=[1.0]
		elif x=='S': prom_stress+=[0.5]
		elif x=='U': prom_stress+=[0.0]

	for i,x in enumerate(prom_stress):
		prevx=prom_stress[i-1] if i-1>=0 else None
		nextx=prom_stress[i+1] if i+1<len(prom_stress) else None
		#print i,prevx,x,nextx


		if nextx!=None and nextx>x:
			strength=0.0
		elif nextx!=None and nextx<x:
			strength=1.0
		elif prevx!=None and prevx>x:
			strength=0.0
		elif prevx!=None and prevx<x:
			strength=1.0
		else:
			strength=None
		#print i,prevx,x,nextx
		prom_strength+=[strength]
	return (prom_stress,prom_strength)

def stressedipa2stress(stressedipa):
	o=""
	for x in stressedipa.split("."):
		if "'" in x:
			o+="P"
		elif "`" in x:
			o+="S"
		else:
			o+="U"
	return o
