# -*- coding: UTF-8 -*-
from __future__ import division
import os,glob
from tools import *

class being:
	persists=False
	excels=False
	om=''
	omm=''
	#omms=bool(int(prosodic.config['print_to_screen']))
	linelen=40
	lang=False
	printout=True
	pointsofcomparison=[]
	pass
	
try:
	import networkx
	being.networkx=True
except ImportError:
	being.networkx=False



class entity(being):	## this class, like the godhead, never instantiates, but is the Form and Archetype for all.	
	## temp ###
	count=0 #eliminate!
	time=0	# for timing the parsers.. also eliminate
	###########
	
	stress_str2int={'P':1,'S':2,'U':0}
	stress_str2strikes={'P':'`','S':"'",'U':''}
	stress_int2strikes={0:'',1:"'",2:"`"}
	stress_float2str={1.0:'P',0.5:'S',0.0:'U'}
	weight_bool2str={True:'H',False:'L',None:'?'}
	
	## classes
	def __init__(self):
		self.parent=False
		self.children=[]
		self.feats={}
		self.featpaths={}
		self.finished = False
	
	def __hash__(self):
		"""
		Returns a unique integer [returned by Python's built-in __hash__()]
		based on the string representation of this object's phonemes [ie, self.phonstr()]
		"""
		
		return self.phonstr().__hash__()
	def phonstr(self):
		return "".join([str(x) for x in self.phonemes()])
	
	def __repr__(self):
		"""
		Default string representation.
		"""
		
		return "<"+self.classname()+"> ["+self.__repr2__()+"]"
	def __repr2__(self):
		"""
		Helper function for the default __repr__()
		"""
		
		return ", ".join([child.__repr__() for child in self.children])
	
	def descendants(self,collapseLists=True):
		"""
		A more genteel method of accessing an object's children (than self.children)
		If collapseLists==True, the returned list is guaranteed not to be a list of lists.
		If collapseLists==False, the returned list *may* be a list of lists, [cf. self.children]
			in the case of optionality among children
			eg, a line's children is a list of lists of Words.
		"""
		
		if not collapseLists:
			return self.children
		
		if not self.children:
			return []
			
		if type(self.children[0])==type([]):
			return [x[0] for x in self.children]
		
		return self.children
	
	def classname(self):
		"""
		Returns the classname for this object [ie, self.__class__.__name__]
		"""
		
		return self.__class__.__name__
	
	
	def hits(self):
		"""
		Returns number of 'hits' for this object
		[eg, number of times this syllable used in representing the corpus/texts.]
		A hit is activated by self.hit().
		"""
		
		return self.numhits
		
		
	def hit(self):
		"""
		Increment by 1 this object's 'numhits' attribute [ie, self.numhits].
		"""
		
		
		if (not hasattr(self,'numhits')):
			self.numhits=0
		self.numhits+=1

	def om(self,breath):
		"""
		Print the string passed via argument 'breath',
		and store the string for saving in prosodic.being.om.
		[accessed interactively using the '/save' command]
		(The string just prior to this one will remain available at prosodic.being.omm).		
		"""
		
		import prosodic
		if bool(prosodic.config['print_to_screen']):
			being.om+=str(breath)+"\n"
			print self.u2s(breath)

	## features
	def feat(self,k,v):
		"""
		Store value 'v' as a feature name 'k' for this object.
		Features are stored in the dictionary self.feats.
		[IMPORTANT NOTE:]
		If the feature 'k' is not yet defined, then:
			self.feats[k]=v
		OTHERWISE:
			self.feats[k] becomes a list (if not already)
			'v' is added to this list
		"""
		
		
		if (not hasattr(self,'feats')):
			self.feats = {}
			if (not hasattr(self,'featpaths')):
				self.featpaths={}
		if (not k in self.feats):
			self.feats[k] = v
		else:
			if type(self.feats[k])==type([]):
				self.feats[k].append(v)
			else:
				obj=self.feats[k]
				self.feats[k]=[obj,v]
			
	def feature(self,feat,searchforit=False):
		"""
		Returns value of self.feats[feat].
		If searchforit==True, will search in this object's children recursively.
		If not found, returns None.
		"""
		
		
		if (hasattr(self,'feats')) and (feat in self.feats):
			if type(self.feats[feat]) == type([]):
				if len(self.feats[feat]) > 1:
					return self.feats[feat]
				else:
					return self.feats[feat][0]
			else:
				return self.feats[feat]
		else:
			if searchforit:
				return self.search(SearchTerm(feat))
			else:
				None
		
		
	## unicode-ascii conversion
	def u2s(self,u):
		"""
		Returns an ASCII representation of the Unicode string 'u'.
		"""
		
		try:
			return str(u.encode('utf-8','replace'))
		except UnicodeDecodeError:
			return str(u)
			
	

	
	## children
	def givebirth(self):
		"""
		The default method for getting an object of type (A)
		to return a brand new object of type (child_of_A)
		**This method must be rewritten by each object class!**
		Can be called directly, or indirectly using method newchild().
		"""
		
		return entity()				#### needs to be rewritten by each entity (eg, Word would give birth to Syllables, its children)
	
	
	def newchild(self,chld=False):
		"""Like givebirth(), but also appends the new child to the list of children."""
		
		if not chld:
			chld = self.givebirth()
		self.children.append(chld)
		return chld
	
	def empty(self):
		"""Returns TRUE if object is childless, FALSE if otherwise."""
		return (len(self.children) == 0)
	
	
	
	## object build status
	def finish(self):
		"""Marks the current object as 'finished', such as a Line which has been successfully populated with its words. Currently used by classes: Stanza, Line."""
		self.finished = True

	def finished(self):
		"""Returns whether object is finished or not -- see finish()."""
		return self.finished
	
		


	## getting entities of various kinds
	def ents(self,cls="Word",flattenList=True):
		"""Returns a list of entities of the classname specified the second argument. For instance. to call a Word-object's ents('Phoneme') would return a list of the word's Phoneme objects sequentially. This method recursively searches the self-object's children for the type of object specified."""
		
		ents = []
		if self.classname() == cls:
			return [self]
		else:
			for child in self.children:
				if type(child)==type([]):
					if flattenList:
						ents+=child[0].ents(cls=cls,flattenList=flattenList)
					else:
						ents_list2ndlevel=[]
						for chld in child:
							if chld:
								ents_list2ndlevel+=chld.ents(cls=cls,flattenList=flattenList)
						ents+=[ents_list2ndlevel]
						
				else:
					if child:
						ents += child.ents(cls=cls,flattenList=flattenList)
		return ents
	
	## helper functions of ents()
	def phonemes(self):
		"""
		Returns a list of this object's Phonemes in order of their appearance.
		"""
		
		return self.ents('Phoneme')


	def phones(self):
		"""
		Returns a list of this object's Phonemes in order of their appearance.
		"""
		
		return self.phonemes()
		
		
		
	def onsets(self):
		"""Returns a list of this object's Onsets in order of their appearance."""
		
		return self.ents('Onset')


	def nuclei(self):
		"""Returns a list of this object's Nuclei in order of their appearance."""
		return self.ents('Nucleus')
		
		
	def codae(self):
		"""Returns a list of this object's Codae in order of their appearance."""
				
		return self.ents('Coda')


	def rimes(self):
		"""Returns a list of this object's Rimes in order of their appearance."""
		
		return self.ents('Rime')


	def syllables(self):
		"""Returns a list of this object's Syllables in order of their appearance."""
		
		return self.ents('Syllable')


	def sylls(self):
		"""Returns a list of this object's Syllables in order of their appearance."""
		
		return self.syllables()
		
		
	def words(self):
		"""Returns a list of this object's Words in order of their appearance.
		NOTE: This will be a list of lists, as optionality exists among Words
			(ie, different stressings/weightings of the word).
		"""
		
		return self.ents('Word')
		
	def lines(self):
		"""Returns a list of this object's Lines in order of their appearance."""
		
		return self.ents('Line')
		
	def stanzas(self):
		"""Returns a list of this object's Stanzas in order of their appearance."""
		
		return self.ents('Stanza')
		
		
	def texts(self):
		"""Returns a list of this object's Texts in order of their appearance."""
		
		return self.ents('Text')
	
	def show(self):
		"""
		'Prints' (using self.om()) the basic stats about the loaded text. Eg:
			001776	ecstatic            	P:'ecs.ta.tic                      	S:PUU	W:HLH
			001777	breath              	P:'bre.ath                         	S:PU	W:LH
		"""
		
		
		if self.classname()=="Corpus":
			for text in self.children:
				text.om("## showing Text " + text.name)
				text.show()
		else:
			words=self.words()
			for i in range(len(words)):
				word=words[i]
				word.om(str(i+1).zfill(6)+"\t"+str(word.output_minform()))
	
	def dir(self):
		for k,v in sorted(self.__dict__.items()):
			print "."+k,"\t",v
	
	
	## outputs
	def str_ipasyllstress(self):
		"""
		Returns a string representation of the self-object
		in a syllabified, stressed, IPA form. For example:
		if I am the Word('abandonment'), this method will return:
		ə.'bæn.dən.mənt
		"""
		
		phonsylls=["".join([str(x) for x in child.phonemes()]) for child in self.children] 
		try:
			if hasattr(self,'stress'):
				for i in range(len(self.stress)):
					phonsylls[i]=entity.stress_str2strikes[self.stress[i]]+phonsylls[i]
		except IndexError:
			print "<"+self.classname()+" creation failed on:\n"+str(self)+"\n"
		return ".".join(phonsylls)
				
	
	
	
	## attribute finding
	def findattr(self,attr,connector='parent'):
		"""Returns the attribute named {attr}, from either the self or the self's parents (recursively)."""
		if (not hasattr(self,attr)):
			if (not hasattr(self,connector)):
				return None
			else:
				con=getattr(self,connector)
				if not con:
					return None
				if type(con)==type([]):
					return [x.findattr(attr,connector) for x in con]	
				else:
					return con.findattr(attr,connector)
		else:
			return getattr(self,attr)
	
	def findDict(self):
		"""Returns the dictionary stored on the self or the self's parents."""
		return self.findattr('dict')
	
	
	
	
	
	
	## parsing
	def parse(self,arbiter='Line',init=None,namestr=[]):
		import time
		if entity.time==0:
			entity.time=time.clock()
		
		if self.classname().lower()=="corpus":
			for child in self.children:
				child.parse()
			return None
		
		if not init:
			init=self
			if not hasattr(init,'meter_stats'):
				init.meter_stats={'lines':{},'positions':{},'texts':{}, '_ot':{},'_constraints':{}}
			if not hasattr(init,'bestparses'):
				init.bestparses=[]
			from Meter import Meter
			init.meter=Meter(config['constraints'].split(),(config['maxS'],config['maxW']),config['splitheavies'])
			init.meter_stats['_constraints']=sorted(init.meter.constraints)
			
			init.ckeys="\t".join(sorted([str(x) for x in init.meter.constraints]))
			#self.om("\t".join([makeminlength(str("text"),being.linelen),				makeminlength(str("parse"),being.linelen),	"meter",init.ckeys]))
			
			if being.omms:
				self.scansion_prepare()
			
		if (hasattr(self,'name')):
			print "## parsing: "+str(self.name)
			
			
		if arbiter != self.classname():
			for child in self.children:
				child.parse(arbiter,init,namestr)
		else:
			if self.isBroken(): return []
			if hasattr(self,'ignoreMe') and self.ignoreMe: return []
			words = self.words()
			numSyll=0
			for word in words:
				if type(word)==type([]):
					for wrd in word:
						if wrd.isBroken():
							#print wrd
							return []
					numSyll+=word[0].getNumSyll()
				else:
					if word.isBroken():
						return []
					numSyll+=word.getNumSyll()
			if not words: return []
			##
			
			if (numSyll < config['line_minsylls']):
				#print "\t>skipping ("+str(numSyll)+" is fewer than minimum of "+str(config['parse_line_numsyll_min'])+" sylls)"
				return []
			elif(numSyll > config['line_maxsylls']):
				#print "\t>skipping ("+str(numSyll)+" is more than maximum of "+str(config['parse_line_numsyll_max'])+" sylls)"
				return []
			
			#print "\n\t>parsing:\t"+str(self)+"\t("+str(numSyll)+" sylls)"
			
			
			self.parses=init.meter.parse(words,numSyll)
			self.numparses=len(self.parses)
			self.__bestparse=self.parses[0]
			
			if hasattr(being,'line_headedness'):
				for parse in self.parses:
					if parse.str_meter().startswith(str(being.line_headedness)):
						self.__bestparse=parse
						break
			init.bestparses.append(self.__bestparse)


			if being.omms:
				self.scansion()

			textname=self.findattr('name')
			if not textname:
				textname=str(self).replace(" ","_")
			
			## store stats
			if (not textname in init.meter_stats['lines']):
				init.meter_stats['lines'][textname]={}
			if (not textname in init.meter_stats['positions']):
				init.meter_stats['positions'][textname]={}
			if (not textname in init.meter_stats['texts']):
				init.meter_stats['texts'][textname]={}
			if (not textname in init.meter_stats['_ot']):
				init.meter_stats['_ot'][textname]=makeminlength("line",being.linelen)+"\tmeter\t"+init.ckeys+"\n"
			
			parsedat=[]
			for k,v in sorted(self.__bestparse.constraintScores.items()):
				if (not k in init.meter_stats['texts'][textname]):
					init.meter_stats['texts'][textname][k]=[]
				init.meter_stats['texts'][textname][k].append(v)
				
				#parsedat.append(v/len(self.__bestparse.positions))	#???
				parsedat.append(v)
				
			linekey=str(len(init.meter_stats['lines'][textname])+1).zfill(6)+"_"+str(self.__bestparse.posString())
			init.meter_stats['lines'][textname][linekey]=parsedat
			
			## OT stats
			init.meter_stats['_ot'][textname]+=makeminlength(str(self),being.linelen)+"\t"+self.parses[0].str_ot()+"\n"
			if len(self.parses)>1:
				for parse in self.parses[1:]:
					init.meter_stats['_ot'][textname]+=makeminlength("",being.linelen)+"\t"+parse.str_ot()+"\n"
				
			
			
			for posn in range(len(self.__bestparse.positions)):
				pos=self.__bestparse.positions[posn]
				(posdat,ckeys)=pos.formatConstraints(normalize=True,getKeys=True)
				
				for cnum in range(len(ckeys)):
					if (not posn in init.meter_stats['positions'][textname]):
						init.meter_stats['positions'][textname][posn]={}
					if (not ckeys[cnum] in init.meter_stats['positions'][textname][posn]):
						init.meter_stats['positions'][textname][posn][ckeys[cnum]]=[]
					init.meter_stats['positions'][textname][posn][ckeys[cnum]].append(posdat[cnum])

			return self.parses
		
		if self==init:
			init.maxparselen=0
			init.minparselen=None
			for parse in self.__bestparses:
				if not init.maxparselen:
					init.maxparselen=len(parse.positions)
					init.minparselen=len(parse.positions)
					continue

				if len(parse.positions)>init.maxparselen:
					init.maxparselen=len(parse.positions)
				if len(parse.positions)<init.minparselen:
					init.minparselen=len(parse.positions)
	
	
	def parseStats(self,init=None):
		if not init:
			init=self
			init.mstats={'lines':{},'positions':{},'positionsRaw':{},'positionsT':{},'texts':{},'_ot':{}}
			init.statsByPositionTKeys=[]
			#self.genCorrStats()
			#exit()
		
		if not hasattr(self,'meter_stats'):
			for child in self.children:
				child.parseStats(init)
		else:
			name=self.getName()
			
			constraintNames=[str(constraint.name) for constraint in self.meter_stats['_constraints']]
		
			statsByLine="line\t"+"\t".join(constraintNames)+"\n"
			
			statsByPosition="position\t"+"\t".join(constraintNames)+"\n"
			statsByPositionRaw="position\t"+"\t".join(constraintNames)+"\n"
			statsByPositionTLines={}
			statsByPositionTKeys=[]
			statsByText="textname\t"+"\t".join(constraintNames)+"\n"
		
			tosave=[]
		
			for typename,typedict in self.meter_stats.items():
				if typename.startswith('_'): continue

				for textname,textdict in self.meter_stats[typename].items():
					if not self.meter_stats[typename][textname]: continue
					tosave.append(typename)
					
					if typename.startswith("text"):
						statsByText+=textname+"\t"+"\t".join([str(sum(x)/len(x)) for x in self.meter_stats[typename][textname].values()])+"\n"
						continue
					
				
					datadict=self.meter_stats[typename][textname]
					
					if typename.startswith("position"):
						for posnum,posdat in sorted(datadict.items()):
							if (not ("pos"+str(posnum)) in init.statsByPositionTKeys):
								init.statsByPositionTKeys.append("pos"+str(posnum))
							if (not ("pos"+str(posnum)) in statsByPositionTKeys):
								statsByPositionTKeys.append("pos"+str(posnum))
							
							statsByPosition+="pos"+str(posnum)
							statsByPositionRaw+="pos"+str(posnum)
							for ckey,cscores in sorted(posdat.items()):
								scoreCount=sum(cscores)
								scoreMean=sum(cscores)/len(cscores)
								statsByPosition+="\t"+str(scoreMean)
								statsByPositionRaw+="\t"+str(scoreCount)
								try:
									statsByPositionTLines[ckey][posnum]=scoreMean
								except KeyError:
									statsByPositionTLines[ckey]={}
									statsByPositionTLines[ckey][posnum]=scoreMean
								
							statsByPosition+="\n"
							statsByPositionRaw+="\n"
							
							
					elif typename.startswith("line"):
						#pass
						for posnum,v in datadict.items():
							statsByLine+="line"+str(posnum)+"\t"+"\t".join([str(x) for x in v])+"\n"

			if 'lines' in tosave:
				init.mstats['lines'][name]=statsByLine
			
			if 'positions' in tosave:
				init.mstats['positions'][name]=statsByPosition
				init.mstats['positionsRaw'][name]=statsByPositionRaw
				
				statsByPositionT="constraint\t"+"\t".join(sorted(statsByPositionTKeys))+"\n"
				for ckey,posdict in sorted(statsByPositionTLines.items()):
					statsByPositionT+=str(ckey)
					for posnum,score in sorted(posdict.items()):
						statsByPositionT+="\t"+str(score)
					statsByPositionT+="\n"
				
				init.mstats['positionsT'][name]=statsByPositionT
				
			if 'texts' in tosave:
				init.mstats['texts'][name]=statsByText
							
			try:
				init.mstats['_ot'][name]=self.meter_stats['_ot'][name]
			except KeyError:
				try:
					init.mstats['_ot'][name]=self.meter_stats['_ot'][name+'.txt']
				except KeyError:
					init.mstats['_ot'][name]=""
					#print "<< error: no OT stats found for textname "+name+" >>"
			if (init!=self): return None
		
		name=self.getName()
		for stattype,textdict in init.mstats.items():
			totalstr=""
			header=False
			for textname,strtowrite in textdict.items():
				if not strtowrite: continue
				writeToFile(textname,stattype.replace("_",""),strtowrite)
				if stattype.startswith("_"): continue
				
				lines=strtowrite.split("\n")
				for linenum in range(len(lines)):
					ln=lines[linenum]
					if not ln.strip(): continue
					
					if not linenum:
						if not header:
							if stattype=="positionsT":
								totalstr+="text\tconstraint\t"+"\t".join(sorted(init.statsByPositionTKeys))+"\n"
							elif stattype!="texts":
								totalstr+="text_"+ln+"\n"
							else:
								totalstr+=ln+"\n"
							header=True
						continue
					if stattype=="positionsT":
						tabs=ln.strip().split("\t")
						for n in range(len(tabs),len(init.statsByPositionTKeys)+1):
							tabs+=[str(0)]
						tname=textname
						if tname[0].isdigit():
							tname='t'+tname
						totalstr+=tname+"\t"+"\t".join(tabs)+"\n"
					elif stattype!="texts":
						totalstr+=textname+"_"+ln+"\n"
					else:
						totalstr+=ln+"\n"
			
			if stattype.startswith("_"): continue
			writeToFile(name,stattype,totalstr,iscorpus=True)
		return None					

	def getFeatValDict(self,init=None):		
		if not init:
			init=self
			init.unitfeats={}
		
		if not hasattr(self,'bestparses'):
			for child in self.children:
				if type(child)==type([]): return None
				child.getFeatValDict(init)
		else:
			for parse in self.__bestparses:
				print parse
				for pos in parse.positions:
					posfeats=pos.posfeats()
					
					for k,v in posfeats.items():
						v=tuple(v)
						if (not k in init.unitfeats):
							init.unitfeats[k]={}
						if (not v in init.unitfeats[k]):
							init.unitfeats[k][v]={}
			return init.unitfeats
		
		return init.unitfeats
	
	#def make_pkey(self,posdict,domainfeat,domainfeatval,domainfeat1,domainfeatval1,targetfeat=None,targetfeatval=None):
	#	pkey=".".join(["of_all",domainfeat.replace("prom.","")+"_is_"+str(domainfeatval)])
	
	def groom(self,init=None):
		if self.classname()!="Corpus":
			return "<< cannot groom object smaller than corpus: grooming meant to normalize corpus of texts to a standard >>"
		
		
		textdict={}
		text2lines={}
		for text in self.children:
			validlines=text.validlines()
			textdict[text]=str(len(validlines))+" lines"
			text2lines[text]=validlines
		
		sels=choose(textdict,"please select the primary text whose attributes will be sought after in the others:")
		primary=sels[0]
		
		sels=choose(['wordbound','stress','weight'],"please choose the dimensions on which lines of primary text <"+repr(primary)+"> must be matched:")
		being.pointsofcomparison=[]
		for sel in sels:
			being.pointsofcomparison.append("str_"+sel.strip())
		
		sels=choose({'difference':'remove non-matching lines in non-primary texts only','intersection':'remove non-matching lines in all texts'},"please select method of grooming:")
		diffmethod=sels[0]
		
		#if diffmethod=="intersection":
		#	
		
		# lineset=set(text2lines[primary])
		# 		if diffmethod=="intersection":
		# 			for text in self.children:
		# 				thislineset=set(text2lines[text])
		# 				for line in (lineset ^ thislineset):
		# 					line.ignoreMe=True
		# 				
		# 		else:
		# 			
		# 			for text in self.children:
		# 				thislineset=set(text2lines[text])
		# 				
		# 				for line in set(thislineset - lineset):
		# 					line.ignoreMe=True
		
		print ">> groomed:"
		for text in self.children:
			print "\t".join(str(x) for x in [text,str(len(text.validlines()))+" lines"])
		
		
						
	
	def plot(self,init=None):
		if not init:
			init=self
			init.plotstats={}
			init.unitfeats=self.getFeatValDict()
			
			sels=[]
			for k,v in sorted(init.unitfeats.items()):
				for kk,vv in v.items():
					sels.append((k,kk))
			
			conditions={'x':[],'y':[]}
			targets={'x':[],'y':[]}
			pkey={'x':[],'y':[]}
			
			print str(0)+"\t[no condition]"
			for selnum in range(len(sels)):
				print str(selnum+1)+"\t"+str(sels[selnum][0])+" = "+str(sels[selnum][1])
			print
			
			stepnum=0
			for a in sorted(conditions.keys()):
				stepnum+=1
				sel=raw_input(">> [step "+str(stepnum)+"/4] ["+a+" coord] [conditions of population] please type in the number (or numbers separated by commas)\n\tof the conditions determining the total population from which the percentage of the sample is taken:\n").strip()
				for x in sel.split(","):
					try:
						conditions[a].append(sels[int(x)-1])
						pkey[a]+=["of_"+str(sels[int(x)-1][0])+"_is_"+str(sels[int(x)-1][1])]
					except:
						pass
						
				stepnum+=1
				sel=raw_input(">> [step "+str(stepnum)+"/4] ["+a+" coord] [conditions of sample] please type in the number (or numbers separated by commas)\n\tof the conditions determining the sample:\n").strip()
				for x in sel.split(","):
					try:
						targets[a].append(sels[int(x)-1])
						pkey[a]+=[str(sels[int(x)-1][0])+"_is_"+str(sels[int(x)-1][1])]
					except:
						pass
				
			
			# print ">> POPULATION:"
			# print conditions
			# 
			# print ">> SAMPLE:"
			# print targets

			init.population=conditions
			init.sample=targets
			
			init.pkey="X_"+"-".join(pkey['x'])+"."+"Y_"+"-".join(pkey['y'])
			print ">> plotting: "+ init.pkey
			
		
		if not hasattr(self,'bestparses'):
			for child in self.children:
				child.plot(init)
		else:
			posdict={}
			#if not hasattr(self,'minparselen'): return None
			for posnum in range(self.minparselen):
				posdict[posnum]={'x':[],'y':[]}
				for parse in self.__bestparses:
					posfeats=parse.positions[posnum].posfeats()
					
					for a in ['x','y']:
						conds=init.population[a]
						targs=init.sample[a]
						
						condsHold=True
						if len(conds):							
							for cond in conds:
								condK=cond[0]
								condV=cond[1]
							
								try:
									if posfeats[condK]==condV:
										continue
								except:
									condsHold=False
									break
								condsHold=False
								break
						
						if condsHold:
							targsHold=True
							for targ in targs:
								targK=targ[0]
								targV=targ[1]

								try:
									if posfeats[targK]==targV:
										continue
								except:
									targsHold=False
									break
								targsHold=False
								break
							
							if targsHold:
								posdict[posnum][a].append(1)
							else:
								posdict[posnum][a].append(0)
			
			for a in ['x','y']:
				if not posdict[posnum][a]:
					print "<< not enough data: position number ("+str(posnum)+") empty on dimension ["+str(a)+"]"
					return None

			init.plotstats[self.getName()]=posdict
			if (self!=init): return None

		totalstrs=[]
		totaltsvs=[]
		for textname,posdict in sorted(init.plotstats.items()):
			
			tsv="posnum\tx_mean\ty_mean\tx_std\ty_std\n"
			xs=[]
			ys=[]
			for posnum,xydict in posdict.items():
				x_avg,x_std=mean_stdev(xydict['x'])
				y_avg,y_std=mean_stdev(xydict['y'])
				
				xs.append(x_avg)
				ys.append(y_avg)
				tsv+="\t".join(str(bb) for bb in [(posnum+1),x_avg,y_avg,x_std,y_std])+"\n"
			
			
			ccmsg=""
			cc=None
			p=None
			try:
				from statlib import stats
				(cc,p)=stats.pearsonr(xs,ys)
				
				aa=makeminlength("    correlation coefficient: ",int(being.linelen/1.4))+str(cc)
				bb=makeminlength("    p-value: ",int(being.linelen/1.4))+str(p)
				
				tsv+=aa.strip().replace(":",":\t")+"\n"
				tsv+=bb.strip().replace(":",":\t")+"\n"
				
				for l in tsv.split("\n"):
					totaltsvs.append(textname+"_"+l)
				
				ccmsg+=aa+"\n"+bb+"\n"
				
			except:
				pass
			
			writeToFile(textname,init.pkey,tsv,extension="tsv")
			totaltsvs.append(tsv)
			
			try:
				strtowrite=self.makeBubbleChart(posdict,".".join([textname,init.pkey]),(cc,p))
				totalstrs+=[strtowrite]
				writeToFile(textname,init.pkey,self.getBubbleHeader()+strtowrite+self.getBubbleFooter(),extension="htm")
			except:
				pass
			
			if ccmsg:
				print ccmsg
		
		if not self.classname()=="Corpus": return None
		writeToFile(self.getName(),
			init.pkey,
			self.getBubbleHeader()+"\n<br/><br/><br/><br/><br/><br/><br/><br/>\n".join(totalstrs)+self.getBubbleFooter(),
			iscorpus=True,
			extension="htm")
		writeToFile(self.getName(),init.pkey,"\n\n\n\n".join(totaltsvs),iscorpus=True,extension="tsv")
		
	
	def getBubbleHeader(self):
		return '<html> <head> <script type="text/javascript" src="[[prosodic_dir]]/lib/mootools-core-1.3-full-compat.js"></script> <script type="text/javascript" src="[[prosodic_dir]]/lib/moochart-0.1b1-nc.js"></script></head><body>'.replace('[[prosodic_dir]]',sys.path[0])
		
	def getBubbleFooter(self):
		return '</body></html>'
	
	def makeBubbleChart(self,posdict,name,stattup=None):
		xname=[x for x in name.split(".") if x.startswith("X_")][0]
		yname=[x for x in name.split(".") if x.startswith("Y_")][0]
		#elsename=name.replace(xname,'').replace(yname,'').replace('..','.').replace('..','.')
		
		
		
		o='<div id="'+name+'"><h2>'+name+'</h2>'
		
		if stattup:
			cc=stattup[0]
			p=stattup[1]
			o+='<h3>corr.coef='+str(cc)+' / p-value='+str(p)+'</h3>'
		
		o+='<br/><script type="text/javascript">\nvar myChart = new Chart.Bubble("'+name+'", {\nwidth: 400,\nheight: 400,\n bubbleSize: 10,\nxlabel:"'+xname+'",\nylabel:"'+yname+'"});\n'
		
		for posnum,xydict in posdict.items():
			x_avg,x_std=mean_stdev(xydict['x'])
			y_avg,y_std=mean_stdev(xydict['y'])
			
			z=1/(x_std+y_std)
			
			o+='myChart.addBubble('+str(x_avg*100)+', '+str(y_avg*100)+', '+str(z)+', "#666", "'+str(posnum+1)+' [%'+str(x_avg*100)[0:5]+', %'+str(y_avg*100)[0:5]+']");\n'
		o+='myChart.redraw();\n</script>\n</div>'
		return o
		
		
	
	def genCorrStats(self,init=None):
		from copy import deepcopy
		
		if not init:
			init=self
			init.corrstats={}
			init.unitfeats=self.getFeatValDict()
		
		if not hasattr(self,'bestparses'):
			for child in self.children:
				child.genCorrStats(init)
		else:
			stats=deepcopy(init.unitfeats)
			posdict={}
			pkeydict={}
			
			for posnum in range(self.minparselen):
				posdict[posnum]={}

				
				for parse in self.__bestparses:
					posfeats=parse.positions[posnum].posfeats()
				
					for domainfeat,domainfeatvals in stats.items():
						for domainfeatval,targetfeats in domainfeatvals.items():
							thisdomainfeatval=posfeats[domainfeat]
							
							pkey=".".join(["of_all",domainfeat.replace("prom.","")+"_is_"+str(domainfeatval)])
							#if (not pkey in posdict[posnum]):
							#	posdict[posnum][pkey]=[]
							if (not pkey in pkeydict):
								pkeydict[pkey]={}
							if (not posnum in pkeydict[pkey]):
								pkeydict[pkey][posnum]=[]
							
							if thisdomainfeatval==domainfeatval:
								pkeydict[pkey][posnum].append(1)
							else:
								pkeydict[pkey][posnum].append(0)
							
							for domainfeat1,domainfeatvals1 in stats.items():
								if domainfeat==domainfeat1: continue
								for domainfeatval1,targetfeats1 in domainfeatvals1.items():
									thisdomainfeatval1=posfeats[domainfeat1]
									
									pkey=".".join(["of_"+domainfeat.replace("prom.","")+"_is_"+str(domainfeatval),
										domainfeat1.replace("prom.","")+"_is_"+str(domainfeatval1)])
									#print pkey
										
									#if (not pkey in posdict[posnum]):
									#	posdict[posnum][pkey]=[]
									if (not pkey in pkeydict):
										pkeydict[pkey]={}
									if (not posnum in pkeydict[pkey]):
										pkeydict[pkey][posnum]=[]
									
									if thisdomainfeatval==domainfeatval:
										if thisdomainfeatval1==domainfeatval1:
											pkeydict[pkey][posnum].append(1)
										else:
											pkeydict[pkey][posnum].append(0)
									
									for targetfeat,targetfeatvals in stats.items():
										if domainfeat1==targetfeat: continue
										for targetfeatval,targetfeats1 in targetfeatvals.items():
											thistargetfeatval=posfeats[targetfeat]
											
											pkey=".".join(["of_"+domainfeat.replace("prom.","")+"_is_"+str(domainfeatval),
												"of_"+domainfeat1.replace("prom.","")+"_is_"+str(domainfeatval1),
												targetfeat.replace("prom.",""	)+"_is_"+str(targetfeatval)])
											#if (not pkey in posdict[posnum]):
											#	posdict[posnum][pkey]=[]
											if (not pkey in pkeydict):
												pkeydict[pkey]={}
											if (not posnum in pkeydict[pkey]):
												pkeydict[pkey][posnum]=[]
																								
											if thisdomainfeatval==domainfeatval:
												if thisdomainfeatval1==domainfeatval1:
													if thistargetfeatval==targetfeatval:
														pkeydict[pkey][posnum].append(1)
													else:
														pkeydict[pkey][posnum].append(0)
			#print pkeydict
			self.correlatePositionAttributes(pkeydict)
			exit()	
			#print len(pkeydict.keys())

	def correlatePositionAttributes(self,keyposdict,threshold=0.9):
		data=[]
		keys=[]
		thisword=None
		thisdata=[]
		rightlength=None

		tfdict={}

		for pkey,posdict in keyposdict.items():
			posvals=[]
			for pos,vallist in posdict.items():
				if not len(vallist):
					break
				
				avg=sum(vallist)/len(vallist)
				posvals.append(avg)
					
			if len(posvals)!=len(posdict): continue
			
			
			print pkey
			print posvals
			print
			
			keys.append(pkey)
			data.append(posvals)
			
		import numpy
		arr=numpy.array(data)
		
		print ">> correlating..."
		matrix=numpy.corrcoef(arr)
		tuples=[]
		for seedindex in range(len(keys)):
			seedword=keys[n]

			for i in range(len(matrix[seedindex])):
				absVal=abs(matrix[seedindex][i])
				if absVal>threshold:
					print "\t".join(str(x) for x in [keys[seedindex],keys[i],matrix[seedindex][i],absVal])
					
					#G.add_edge(seedword,keys[i],weight=matrix[seedindex][i])
					#tuples.append((matrix[seedindex][i],keys[i]))
			
		

	def str_numseg(self):
		return len(self.phonemes())

	def getName(self):
		name=self.findattr('name')
		if not name:
			name="_directinput_"
			if self.classname().lower()=="line":
				name+="."+str(self).replace(" ","_").lower()
		else:
			name=name.replace('.txt','')
		
		while name.startswith("."):
			name=name[1:]
		
		return name

	def genfsms(self):
		if (hasattr(self,'bestparses')):
			name=self.getName()
				
			import networkx as nx
			m2int={'w':'0','s':'1'}

			gs={}
			gs['weight']=['str_weight']
			gs['stress']=['str_stress']
			gs['stressweight']=['str_stress','str_weight']
			gs['meterweight']=['str_meter','str_weight']
			gs['meterstress']=['str_meter','str_stress']
			#gs['numseg']=['str_numseg']
			#gs['metershape']=['str_meter','getShape']
			gs['meter']=['str_meter']
			#gs['shape']=['str_shape']
			#gs['weightshape']=['str_weight','str_shape']

			Gs={}
			for gtype in gs.keys():
				G=nx.DiGraph()
				sumweight={}
				nodetypes=[]
				linelens=[]
				for parse in self.__bestparses:
					node1=None
					node2=None
				
					posnum=0
					linelens.append(len(parse.positions))
					for pos in parse.positions:
						posnum+=1
						if hasattr(being,'line_maxsylls'):
							if posnum>int(being.line_maxsylls):
								break
						
						nodestr=""
						
						for strcaller in sorted(gs[gtype]):
							for unit in pos.slots:
								unit.meter=pos.meterVal
								
								z=unit.findattr(strcaller,'children')
								#if len(pos.children)>1:
								#print z
								if type(z)==type([]):
									nodestr+="".join( [str(x()) for x in z] )
								else:
									nodestr+=str(z())

						if not nodestr: continue
						
						if (not nodestr in nodetypes):
							nodetypes.append(nodestr)
						node=str(posnum)+"_"+str(nodestr)
					
						if not node1:
							node1=node
							continue
						node2=node
					
						if G.has_edge(node1,node2):
							G[node1][node2]['weight']+=1
						else:
							G.add_edge(node1,node2,weight=1)
						try:
							sumweight[(str(node1)[0],str(node2)[0])]+=1
						except KeyError:
							sumweight[(str(node1)[0],str(node2)[0])]=1
							
						node1=node2							
				
				if not linelens: continue
				
				maxlinesize=6
				for n1,nbrs in G.adjacency_iter():
					for n2,eattr in nbrs.items():
						count=G[n1][n2]['weight']
						G[n1][n2]['weight']=count/sumweight[(n1[0],n2[0])]
						strfreq=str(G[n1][n2]['weight']*100)
						if len(strfreq)>3:
							strfreq=strfreq[0:3]
						G[n1][n2]['label']=str(count)+" ["+str(strfreq)+"%]"
						G[n1][n2]['fontsize']=10
						G[n1][n2]['penwidth']=G[n1][n2]['weight']*maxlinesize
						G.node[n1]['width']=1
						G.node[n2]['width']=1
						G[n1][n2]['weight']=0
						#G[n1][n2]['style']="setlinewidth("+str(int(G[n1][n2]['weight']*maxlinesize)+1)+")"
						#print G[n1][n2]['style']
						#G[n1][n2]['arrowhead']='none'

				import math
				avglinelen=int(max(linelens))
				for n in range(2,avglinelen):
					for ntype in nodetypes:
						node1=str(n-1)+"_"+ntype
						node2=str(n)+"_"+ntype
						if not G.has_edge(node1,node2):
							G.add_edge(node1,node2,weight=0,penwidth=0,color='white')

				fn='results/fsms/'+str(gtype)+"."+name+'.png'
				print ">> saved: "+fn+""
				#plt.savefig(fn)
				#nx.write_dot(G,fn)
				pyd=nx.to_pydot(G)
				pyd.set_rankdir('LR')

				for node in pyd.get_node_list():
					node.set_orientation('portrait')
				pyd.write_png(fn, prog='dot') 
			
		else:
			if not self.children:
				return ""
			elif type(self.children[0])==type([]):
				return []
			else:
				[child.genfsms() for child in self.children]
	
	def genmetnet(self):
		import networkx as nx
		#import matplotlib.pyplot as plt
		m2int={'w':'0','s':'1'}
		if (hasattr(self,'parses')):
			G=nx.DiGraph()
			slot1=None
			slot2=None
			for parse in self.parses:
				slot1=None
				slot2=None
				for pos in parse.positions:
					edge_weight=1
					errorSum=sum([i for i in pos.constraintScores.values()])*1000000
					if errorSum:
							edge_weight=1/errorSum
					for slot in pos.slots:
						
						if pos.meterVal=="s":
							unit=slot.token.upper()
						else:
							unit=slot.token.lower()
						
						if not slot1:
							slot1=str(slot.i)+str(pos.meterVal)+"_"+unit
							continue
						slot2=str(slot.i)+str(pos.meterVal)+"_"+unit
						G.add_edge(slot1,slot2,weight=edge_weight)
						slot1=slot2												
			self.G=G
			#nx.draw_graphviz(G)
			
			
			fn='results/metnets/'+".".join(self.namestr())+'.'+str(self).replace(" ","_").lower()+'.png'
			print ">> saved: "+fn+""
			#plt.savefig(fn)
			#nx.write_dot(G,fn)
			pyd=nx.to_pydot(G)
			pyd.set_rankdir('LR')

			for node in pyd.get_node_list():
				node.set_orientation('portrait')
			pyd.write_png(fn, prog='dot') 
			
		else:
			if not self.children:
				return ""
			elif type(self.children[0])==type([]):
				return []
			else:
				[child.genmetnet() for child in self.children]
		
	
	
	
			
	def isParsed(self):
		if (hasattr(self,'parses')):
			return True
		for child in self.children:
			if type(child)==type([]):
				return False
			if child.isParsed():
				return True

	def _scansion_prepare(self):
		from Meter import Meter
		meter=Meter(config['constraints'].split(),(config['maxS'],config['maxW']),self.findattr('dict'))
		ckeys="\t".join(sorted([str(x) for x in meter.constraints]))
		self.om("\t".join([makeminlength(str("text"),being.linelen),makeminlength(str("parse"),being.linelen),"#pars","#viol","meter",ckeys]))
		
	def scansion_prepare(self,meter=None):
		if not meter:
			if not hasattr(self,'_Text__bestparses'): return
			x=getattr(self,'_Text__bestparses')
			if not x.keys(): return
			meter=x.keys()[0]
		
		ckeys="\t".join(sorted([str(x) for x in meter.constraints]))
		self.om("\t".join([makeminlength(str("text"),being.linelen), makeminlength(str("parse"),being.linelen),"#pars","#viol","meter",ckeys]))
		

	def scansion(self,meter=None):
		if (hasattr(self,'bestParse')):
			bp=self.bestParse(meter)
			if not bp: return
			lowestScore=bp.score()
			self.om("\t".join( [ str(x) for x in [makeminlength(str(self),being.linelen), makeminlength(str(bp), being.linelen),len(self.allParses(meter)),lowestScore,bp.str_ot()] ] ))
			
		else:
			if not self.children:
				return ""
			elif type(self.children[0])==type([]):
				return "\t??"+str(self)	## no parse on the word level (where optionality begins?) -- then no parses for this line
			else:
				[child.scansion() for child in self.children]
		
		
	def namestr(self,namestr=[]):
		if hasattr(self,'name'):
			return [self.name.replace('.txt','')]
		elif hasattr(self,'parent') and self.parent and hasattr(self.parent,'namestr'):
			return self.parent.namestr()+[self.classname().lower()+format(self.parent.children.index(self)+1, '0'+str(len(str(len(self.parent.children))))+'d')]
			#return self.parent.namestr()
			#return self.parent.namestr()+[self.classname().lower()+format(self.parent.children.index(self)+1, '0'+str(len(str(len(self.parent.children))))+'d')]
			
		else:
			return ["_directinput_"]
		
		
		
		
	def report(self):
		from Meter import Meter
		meter=Meter('default')
		if (hasattr(self,'parses')):
			self.om(str(self))
			self.om(meter.printParses(self.parses))
		else:
			for child in self.children:
				if type(child)==type([]): continue
				child.report()
	
	def getcorr_prepkey(self,key):
		(newkey,etc)=(key.split(":")[0],key.split(":")[1:])
		newkey=newkey.strip()
		
		if newkey=="meter":
			if "," in etc:
				newkey+=etc.split(",")[1].split("[")[0]
		return newkey
	

				
	
	def isBroken(self):
		if not hasattr(self,'broken'):
			return False
		else:
			return getattr(self,'broken')
				
	## outputs
	def tree(self,offset=0,prefix_inherited="",nofeatsplease=['Phoneme']):
		tree = ""
		numchild=0
		for child in self.children:
			if type(child)==type([]):
				child=child[0]
			numchild+=1
			
			classname=child.classname()
			if classname=="Word":
				tree+="\n\n"
			elif classname=="Line":
				tree+="\n\n\n"
			elif classname=="Stanza":
				tree+="\n\n\n\n"
			
			if offset!=0:
				tree+="\n"
				for i in range(0,offset):
					tree+="      "
				#if not len(child.feats):
				#	tree+="	  "
				tree+="|"
			
			
			tree+="\n"
			newline=""
			for i in range(0,offset):
				newline+="      "
			newline+="|"
			
			
			cname=""
			for letter in classname:
				if letter==letter.upper():
					cname+=letter
						
			prefix=prefix_inherited+cname+str(numchild) + "." 
			newline+="-----| ("+prefix[:-1]+") <"+classname+">"
			if child.isBroken():
				newline+="<<broken>>"
			else:
				string=str(child)
				if (not "<" in string):
					newline=makeminlength(newline,99)
					newline+="["+string+"]"
				elif string[0]!="<":
					newline+="\t"+string
				if len(child.feats):
					if (not child.classname() in nofeatsplease):
						for k,v in child.feats.items():
							if v==None:
								continue
							
							newline+="\n"
							for i in range(0,offset+1):
								newline+="      "
							newline+="|     "
							newline+=self.showFeat(k,v)
							

			tree+=newline
			tree+=child.tree(offset+1,prefix)
			
		return tree
	
	def showFeat(self,k,v):
		if type(v) == type(True):
			if v:
				r="[+"+k+"]"
			else:
				r="[-"+k+"]"
		else:
			r="["+k+"="+str(v)+"]"
		return r
	
	def writeFeats(self,sheet,feats,row=0,bool=True,posmark="+",negmark=False):
		for dat in feats:
			row+=1
			col=0
			sheet.row(row).write(col,'['+posmark+dat+']')
			for feat in feats:
				col+=1
				feat=unit.feature(dat)
				feat=self.filterFeat(feat, bool, posmark, negmark)
				sheet.row(row).write(col,feat)
		return row+1
	
	def writeViols(self,sheet,units,viols,unitviols,row=0,bool=True,posmark="+",negmark=False):
		for violtype in viols:
			row+=1
			col=0
			sheet.row(row).write(col,'['+posmark+violtype+']')
			i =-1
			for unit in units:
				i+=1
				col+=1
				if (not i in unitviols):
					continue
				if (not violtype in unitviols[i]):
					continue
				feat=unitviols[i][violtype]
				feat=self.filterFeat(feat, bool, posmark, negmark)
				sheet.row(row).write(col,feat)
		return row
	
	def filterFeat(self,feat,bool=True,posmark="+",negmark=False):
		if feat==None: feat=""
		elif feat==True: feat=posmark
		elif feat==1: feat=posmark
		elif feat==0:
			if negmark: feat=negmark
			else: feat=""
		elif feat==False:
			if negmark: feat=negmark
			else: feat=""
		elif type(feat)==type(float()):
			if bool==True:
				if feat > 0:
					feat=posmark
				else:
					if negmark: feat=negmark
					else: feat=""
			else:
				feat = str(feat)
		else:
			feat=str(feat)
		
		return feat
	
	def getNumEnts(self,numents={}):
		if type(self.children)!=type([]): return numents
		for child in self.children:
			if child==None: continue
			if (not child.classname() in numents):
				numents[child.classname()]={}
				numents[child.classname()]['toks']=0
				numents[child.classname()]['typs']={}
			if (not child in numents[child.classname()]['typs']):
				numents[child.classname()]['typs'][child]=0
			
			numents[child.classname()]['toks']+=1
			numents[child.classname()]['typs'][child]+=1
			numents=child.getNumEnts(numents)
		return numents
	
	def getStats(self):
		numents=self.getNumEnts()
		
		stats={}
		for k,v in numents.items():
			numtok=v['toks']
			numtyp=len(v['typs'])
			typovertok=round((numtyp/numtok*100),2)
			stats[k]=(numtok,numtyp,typovertok)
			
		return stats
	
	def writeUnits(self,sheet,units,row=-1):
		col=0
		sheet.row(row).write(col,"[meter.s]")
		sheet.row(row+1).write(col,"[meter.w]")
		for unit in units:
			if unit==unit.upper():
				sheet.row(row).write(col,unit)
			else:
				sheet.row(row+1).write(col,unit)
		return row+1

	def tiergraph(self,parses,colwidth=24):
		from xlwt import Workbook
		book = Workbook()
		headers = False
		
		parse_i=0
		for parse in parses:
			parse_i+=1
			sheet = book.add_sheet(str(parse_i)+'__'+str(parse.getErrorCount())+'errs') 
			sheet.col(0).width=(colwidth*256)

			row=0
			proms = []
			viols = []
			feats = []
			units = []
			
			col=0
			for pos in parse.positions:
				for slot in pos.slots:
					if pos.meterVal=="s":
						unit=str(slot).upper()
					else:
						unit=str(slot).lower()
					units.append(unit)
					
					col+=1
					sheet.row(row).write(col,str(unit))

					for k,v in slot.feats.items():
						if k.startswith('prom'):
							if (not k in proms):
								proms.append(k)
						else:
							if (not k in feats):
								feats.append(k)
			proms.sort()
			viols.sort()
			feats.sort()
			
			row=self.writeFeats(sheet,proms,bool=True,posmark="+",row=1) # prom feats


			row=self.writeUnits(sheet,units,row=(row+1))	# the units and their metrical parsing
			

			row=self.writeFeats(sheet,proms,bool=True,posmark="+",row=1) # prom feats
			#row=self.writeViols(sheet,parse.units,viols,parse.unitviols,row=(row+1),bool=True,posmark="*")	# constraint violations
			#row=self.writeFeats(sheet,parse.units,feats,row=(row+1),bool=False,posmark="1",negmark="0")	# all other feats
			
			book.save('results/tiergraphs/'+str(self)+'.xls')
	
	
	def searchSingleValue(self, value, feature):
		matches = []
		#print feature
		#print value
		#print
		if feature in self.feats:
			if matchValue(self.feats[feature], value):
				matches.append(self)
		else:
			for child in self.descendants():
				if not child: continue
				matches.extend(child.searchSingleValue(value, feature))
		return matches
		
	def searchSingleTerm(self, searchTerm):
		value = searchTerm.terms[0]
		feature = valueToFeature(value)
		return self.searchSingleValue(value, feature)
		
	def searchMultipleTerms(self, searchTerm):
		termList = searchTerm.terms
		found = True
		for term in termList:
			if not self.search(term):
				found = False
				break
		return found
		
	def searchInChildren(self, searchTerm):
		matches = []
		for child in self.descendants():
			matches.extend(child.search(searchTerm))
		return matches
	
	def search(self, searchTerm):
		if searchTerm not in self.featpaths:
			matches = None	
			if searchTerm.type != None and searchTerm.type != self.classname():
				matches = self.searchInChildren(searchTerm)
			elif searchTerm.isAtomic():
				matches = self.searchSingleTerm(searchTerm)
			else:
				matches = self.searchMultipleTerms(searchTerm)		
				if matches == True:
					matches = [self]
				if matches == False:
					matches = []
			self.featpaths[searchTerm] = matches
			
		return self.featpaths[searchTerm]
					
	def getTypesFromHereOnDown(self,types=[]):
		classname=self.classname()
		if (not classname in types):
			types.append(classname) 
		if self.descendants():
			return self.descendants()[0].getTypesFromHereOnDown(types)
		else:
			return types
	
	
	
	def output_min(self):
		words=self.words()
		o=""
		for word in words:
			o+=word.__str__minform()+"\n"
		return o
			
	
	
	
	
	
