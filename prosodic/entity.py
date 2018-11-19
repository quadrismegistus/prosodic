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

"""
try:
	import networkx
	being.networkx=True
except ImportError:
	being.networkx=False
"""
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
		""" Returns the classname for this object [ie, self.__class__.__name__] """
		return self.__class__.__name__


	def _hits(self):
		"""
		Returns number of 'hits' for this object
		[eg, number of times this syllable used in representing the corpus/texts.]
		A hit is activated by self.hit().
		"""

		return self.numhits


	def _hit(self):
		"""
		Increment by 1 this object's 'numhits' attribute [ie, self.numhits].
		"""

		if (not hasattr(self,'numhits')):
			self.numhits=0
		self.numhits+=1

	def om(self,breath,conscious=True):
		"""
		Print the string passed via argument 'breath',
		and store the string for saving in prosodic.being.om.
		[accessed interactively using the '/save' command]
		(The string just prior to this one will remain available at prosodic.being.omm).
		"""

		#import prosodic
		if (not conscious) and bool(being.config['print_to_screen']):
			if not type(breath) in [str,unicode]:
				breath=unicode(breath)
			being.om+=breath+"\n"
			print self.u2s(breath)
		return breath

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

	def feature(self,feat=None,searchforit=False,init=None):
		"""
		Returns value of self.feats[feat].
		If searchforit==True, will search in this object's children recursively.
		If not found, returns None.
		"""
		if feat==None:
			return self.feats

		if not init:
			init=self
			init.tick=0
			init._matches=[]
			feat=feat.strip()
			if feat.startswith("+"):
				init._eval=True
				feat=feat[1:]
			elif feat.startswith("-"):
				init._eval=False
				feat=feat[1:]
			else:
				init._eval=None

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

				for child in self.descendants():
					init.tick+=1
					x=child.feature(feat,searchforit,init)
					#print init.tick, self.classname(), child.classname(), x
					if x==None: continue
					init._matches.append ( (child,x) )


				#return [child.feature(feat,searchforit) for child in self.descendants()]
			else:
				return None
			#if searchforit:
			#	return self.search(SearchTerm(feat))
			#else:
			#	None

		if self==init:

			if init._eval==None:
				return init._matches
			else:
				return [ x for (x,y) in init._matches if bool(y)==init._eval ]


	## unicode-ascii conversion
	def u2s(self,u):
		"""Returns an ASCII representation of the Unicode string 'u'."""

		try:
			return u.encode('utf-8',errors='ignore')
		except (UnicodeDecodeError,AttributeError) as e:
			try:
				return str(u)
			except UnicodeEncodeError:
				return unicode(u).encode('utf-8',errors='ignore')




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

		lchld=[chld] if type(chld)!=list else chld
		for chldx in lchld: chldx.parent=self
		self.children.append(chld)

		return chld

	def empty(self):
		"""Returns TRUE if object is childless, FALSE if otherwise."""
		return (len(self.children) == 0)



	## object build status
	def finish(self):
		"""Marks the current object as 'finished', such as a Line which has been successfully populated with its words."""
		self.finished = True

	def finished(self):
		"""Returns whether object is finished or not -- see finish()."""
		return self.finished




	## getting entities of various kinds
	def ents(self,cls="Word",flattenList=True):
		"""Returns a list of entities of the classname specified the second argument.
		For instance. to call a Word-object's ents('Phoneme') would return a list of the word's Phoneme objects sequentially.
		This method recursively searches the self-object's children for the type of object specified."""

		ents = []
		"""
		print 'getting entities',self.classname()
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
		"""
		#print 'getting entities',self.classname()
		if self.classname() == cls:
			return [self]
		else:
			for child in self.children:
				#print child,child.classname()
				if child.classname()=='WordToken':
					if cls=='WordToken':
						ents+=[child]
					elif not child.children:
						pass
					elif cls=='Word':
						if flattenList:
							ents+=[child.children[0]]
						else:
							ents+=[child.children]
					else:
						if child:
							ents += child.children[0].ents(cls=cls,flattenList=flattenList)
				else:
					if child:
						ents += child.ents(cls=cls,flattenList=flattenList)


		return ents

	## helper functions of ents()
	def phonemes(self):
		"""Returns a list of this object's Phonemes in order of their appearance."""
		return self.ents('Phoneme')


	def onsets(self):
		"""Returns a list of this object's Onsets in order of their appearance."""
		return self.ents('Onset')


	def nuclei(self):
		"""Returns a list of this object's Nuclei in order of their appearance."""
		return self.ents('Nucleus')


	@property
	def num_syll(self):
		if not hasattr(self,'_num_syll'):
			self._num_syll=sum([w.numSyll for w in self.words()])
		return self._num_syll


	def codae(self):
		"""Returns a list of this object's Codae in order of their appearance."""
		return self.ents('Coda')


	def rimes(self):
		"""Returns a list of this object's Rimes in order of their appearance."""
		return self.ents('Rime')

	def rimestr(self):
		sylls=self.syllables()
		last_sylls=[]
		for syll in reversed(sylls):
			last_sylls.insert(0, syll)
			if syll.stressed: break
		if last_sylls: last_sylls[0] = last_sylls[0].rimes()[0]
		return ''.join(x.phonstr() for x in last_sylls)



	def syllables(self):
		"""Returns a list of this object's Syllables in order of their appearance.
		NOTE: A Syllable knows its stress, but not its shape and weight: its only child, SyllableBody, will know that."""

		return self.ents('Syllable')

	def syllableBodies(self):
		"""Returns a list of this object's SyllableBody's in order of their appearance.
		A SyllableBody does not know its stress, but does know its shape and weight."""

		return self.ents('SyllableBody')


	def words(self,flattenList=True):
		"""Returns a list of this object's Words in order of their appearance.
		Set flattenList to False to receive a list of lists of Words."""
		return self.ents('Word',flattenList=flattenList)

	def wordtokens(self,include_punct=True):
		"""Returns a list of this object's Words in order of their appearance.
		Set flattenList to False to receive a list of lists of Words."""
		ws=self.ents('WordToken')
		if not include_punct: return [w for w in ws if not w.is_punct]
		return ws

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
		"""'Prints' (using self.om()) the basic stats about the loaded text. Eg:
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
				word.om(str(i+1).zfill(6)+"\t"+str(word.output_minform()),conscious=False)

	def less(self):
		"""Show this object's attributes only."""
		self.dir(methods=False)

	def more(self):
		"""Show this object's attributes and methods."""
		self.dir(methods=True,showall=False)


	def dir(self,methods=True,showall=True):
		"""Show this object's attributes and methods."""
		import inspect
		#print "[attributes]"
		for k,v in sorted(self.__dict__.items()):
			if k.startswith("_"): continue
			print makeminlength("."+k,being.linelen),"\t",v

		if not methods:
			return

		entmethods=dir(entity)

		print
		#print "[methods]"
		for x in [x for x in dir(self) if ("bound method "+self.classname() in str(getattr(self,x))) and not x.startswith("_")]:
			if (not showall) and (x in entmethods): continue

			attr=getattr(self,x)

			#print attr.__dict__
			#print dir(attr)

			#doc=inspect.getdoc(attr)
			doc = attr.__doc__
			if not doc:
				doc=""
			#else:
			#	docsplit=[z for z in doc.replace("\r","\n").split("\n") if z]
			#	if len(docsplit)>1:
			#		doc = docsplit[0] + "\n" + makeminlength(" ",being.linelen) + "\n".join( makeminlength(" ",being.linelen)+"\t"+z for z in docsplit[1:])
			#	else:
			#		doc = docsplit[0]
			y=describe_func(attr)
			if not y:
				y=""
			else:
				y=", ".join(a+"="+str(b) for (a,b) in y)
			print makeminlength("."+x+"("+y+")",being.linelen),"\t", doc
			if showall: print


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





	def _getFeatValDict(self,init=None):
		if not init:
			init=self
			init.unitfeats={}

		if not hasattr(self,'bestparses'):
			for child in self.children:
				if type(child)==type([]): return None
				child._getFeatValDict(init)
		else:
			for parse in self.bestParses():
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

	def _groom(self,init=None):
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
		"""Interactive plotting of parsing features."""

		if not init:
			init=self
			init.plotstats={}
			init.unitfeats=self._getFeatValDict()

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


		if not hasattr(self,'bestParses'):
			for child in self.children:
				child.plot(init)
		else:
			posdict={}
			minparselen = min([len(parse.positions) for parse in self.bestParses()])
			maxparselen = max([len(parse.positions) for parse in self.bestParses()])
			#if not hasattr(self,'minparselen'): return None
			for posnum in range(maxparselen):
				posdict[posnum]={'x':[],'y':[]}
				for parse in self.bestParses():
					try:
						posfeats=parse.positions[posnum].posfeats()
					except IndexError:
						# there is no position number `posnum` in this parse `parse`
						continue

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

			tsv="posnum\tnumobs\tx_mean\ty_mean\tx_std\ty_std\n"
			xs=[]
			ys=[]
			for posnum,xydict in posdict.items():
				x_avg,x_std=mean_stdev(xydict['x'])
				y_avg,y_std=mean_stdev(xydict['y'])

				assert len(xydict['x'])==len(xydict['y'])

				xs.append(x_avg)
				ys.append(y_avg)
				tsv+="\t".join(str(bb) for bb in [(posnum+1),len(xydict['x']),x_avg,y_avg,x_std,y_std])+"\n"


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

			"""
			try:
				strtowrite=self.makeBubbleChart(posdict,".".join([textname,init.pkey]),(cc,p))
				totalstrs+=[strtowrite]
				writeToFile(textname,init.pkey,self._getBubbleHeader()+strtowrite+self._getBubbleFooter(),extension="htm")
			except:
				pass
			"""

			if ccmsg:
				print ccmsg

		if not self.classname()=="Corpus": return None

		"""
		writeToFile(self.getName(),
			init.pkey,
			self._getBubbleHeader()+"\n<br/><br/><br/><br/><br/><br/><br/><br/>\n".join(totalstrs)+self._getBubbleFooter(),
			iscorpus=True,
			extension="htm")
		"""

		writeToFile(self.getName(),init.pkey,"\n\n\n\n".join(totaltsvs),iscorpus=True,extension="tsv")


	def _getBubbleHeader(self):
		return '<html> <head> <script type="text/javascript" src="[[prosodic_dir]]/lib/mootools-core-1.3-full-compat.js"></script> <script type="text/javascript" src="[[prosodic_dir]]/lib/moochart-0.1b1-nc.js"></script></head><body>'.replace('[[prosodic_dir]]',sys.path[0])

	def _getBubbleFooter(self):
		return '</body></html>'

	def makeBubbleChart(self,posdict,name,stattup=None):
		"""Returns HTML for a bubble chart of the positin dictionary."""

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



	def _genCorrStats(self,init=None):
		from copy import deepcopy

		if not init:
			init=self
			init.corrstats={}
			init.unitfeats=self._getFeatValDict()

		if not hasattr(self,'bestparses'):
			for child in self.children:
				child.genCorrStats(init)
		else:
			stats=deepcopy(init.unitfeats)
			posdict={}
			pkeydict={}

			for posnum in range(self.minparselen):
				posdict[posnum]={}


				for parse in self.bestParses():
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
			self._correlatePositionAttributes(pkeydict)
			exit()
			#print len(pkeydict.keys())

	def _correlatePositionAttributes(self,keyposdict,threshold=0.9):
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




	def getName(self):
		"""Return a Name string for this object."""

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

	def genfsms(self,meter=None):
		"""Generate FSM images. Requires networkx and GraphViz."""

		if (hasattr(self,'allParses')):
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

			if len(self.bestParses(meter=meter))==1: # if this is a direct input or a single line
				parses=[]
				for _parses in self.allParses():
					parses+=_parses
				use_labels = True
			else:
				parses=self.bestParses()
				use_labels = False

			for gtype in gs.keys():
				G=nx.DiGraph()
				sumweight={}
				nodetypes=[]
				linelens=[]

				for parse in parses:
					node1=None
					node2=None

					posnum=0
					linelens.append(len(parse.positions))
					for pos in parse.positions:
						has_viol = bool(sum(pos.constraintScores.values()))
						for unit in pos.slots:
							spelling=unit.children[0].str_orth()
							posnum+=1
							if hasattr(being,'line_maxsylls'):
								if posnum>int(being.line_maxsylls):
									break

							nodestr=""
							unit.meter=pos.meterVal
							for strcaller in sorted(gs[gtype]):

								z=unit.findattr(strcaller,'children')
								if type(z)==type([]):
									nodestr+="".join( [str(x()) for x in z] )
								else:
									nodestr+=str(z())

							if not nodestr: continue
							if use_labels:
								nodestr+='_'+ (spelling.upper() if unit.meter=='s' else spelling.lower())
							nodestr=str(posnum)+"_"+str(nodestr)
							if (not nodestr in nodetypes):
								nodetypes.append(nodestr)
							#node=str(posnum)+"_"+str(nodestr)
							node=nodestr

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
				nodes=G.nodes()
				#for n1,nbrs in G.adjacency_iter():
				#	for n2,eattr in nbrs.items():
				for n1,n2,eattr in G.edges(data=True):
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
				"""avglinelen=int(max(linelens))
				for n in range(2,avglinelen):
					for ntype in nodetypes:
						node1=str(n-1)+"_"+ntype
						node2=str(n)+"_"+ntype
						if not G.has_edge(node1,node2):
							G.add_edge(node1,node2,weight=0,penwidth=0,color='white')
				"""

				fn='results/fsms/'+str(gtype)+"."+name+'.png'
				print ">> saved: "+fn+""
				#plt.savefig(fn)
				#nx.write_dot(G,fn)
				pyd=nx.to_pydot(G)
				pyd.set_rankdir('LR')

				for node in pyd.get_node_list():
					node.set_orientation('portrait')

				import prosodic as p
				fnfn=os.path.join(p.dir_prosodic,fn)
				_path=os.path.split(fnfn)[0]
				if not os.path.exists(_path):
					os.makedirs(_path)
				pyd.write_png(fnfn, prog='dot')

		else:
			if not self.children:
				return ""
			elif type(self.children[0])==type([]):
				return []
			else:
				[child.genfsms() for child in self.children]





	#
	#
	def isParsed(self):
		#if (hasattr(self,'bestparses')) and bool(self.bestparses):
		#	return True
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

	def scansion_prepare(self,meter=None,conscious=False):
		"""Print out header column for line-scansions for a given meter. """
		import prosodic
		config=prosodic.config

		if not meter:
			if not hasattr(self,'_Text__bestparses'): return
			x=getattr(self,'_Text__bestparses')
			if not x.keys(): return
			meter=x.keys()[0]

		ckeys="\t".join(sorted([str(x) for x in meter.constraints]))
		self.om("\t".join([makeminlength(str("text"),config['linelen']), makeminlength(str("parse"),config['linelen']),"meter","num_parses","num_viols","score_viols",ckeys]),conscious=conscious)



	def namestr(self,namestr=[]):
		if hasattr(self,'name'):
			return [self.name.replace('.txt','')]
		elif hasattr(self,'parent') and self.parent and hasattr(self.parent,'namestr'):
			return self.parent.namestr()+[self.classname().lower()+format(self.parent.children.index(self)+1, '0'+str(len(str(len(self.parent.children))))+'d')]
			#return self.parent.namestr()
			#return self.parent.namestr()+[self.classname().lower()+format(self.parent.children.index(self)+1, '0'+str(len(str(len(self.parent.children))))+'d')]

		else:
			return ["_directinput_"]




	def report(self,meter=None,include_bounded=False,reverse=True):
		""" Print all parses and their violations in a structured format. """

		ReportStr = ''
		if not meter:
			from Meter import Meter
			meter=Meter.genDefault()
		if (hasattr(self,'allParses')):
			self.om(unicode(self))
			allparses=self.allParses(meter=meter,include_bounded=include_bounded)
			numallparses=len(allparses)
			#allparses = reversed(allparses) if reverse else allparses
			for pi,parseList in enumerate(allparses):
				line=self.iparse2line(pi).txt
				#parseList.sort(key = lambda P: P.score())
				hdr="\n\n"+'='*30+'\n[line #'+str(pi+1)+' of '+str(numallparses)+']: '+line+'\n\n\t'
				ftr='='*30+'\n'
				ReportStr+=self.om(hdr+meter.printParses(parseList,reverse=reverse).replace('\n','\n\t')[:-1]+ftr,conscious=False)
		else:
			for child in self.children:
				if type(child)==type([]): continue
				ReportStr+=child.report()

		return ReportStr

	def _getcorr_prepkey(self,key):
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
		"""Print a tree-structure of this object's phonological representation."""

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
				string=self.u2s(child)
				if (not "<" in string):
					newline=makeminlength(newline,99)
					newline+="["+string+"]"
				elif string[0]!="<":
					newline+="\t"+string
				if len(child.feats):
					if (not child.classname() in nofeatsplease):
						for k,v in sorted(child.feats.items()):
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
				feat=self._filterFeat(feat, bool, posmark, negmark)
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
				feat=self._filterFeat(feat, bool, posmark, negmark)
				sheet.row(row).write(col,feat)
		return row

	def _filterFeat(self,feat,bool=True,posmark="+",negmark=False):
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
		### Returns a dictionary of [classname][toks], [classname][typs]

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


	def _searchSingleValue(self, value, feature):
		matches = []
		#print feature
		#print value
		#print
		#for x,y in zip([self, value, feature, self.feats],['self','value','feature','feats']):
		#	print y,'-->',x,type(x)
		#print
		#if not feature and type(value)==list and len(value)==2:
		#	print "!!!!"
		#	value=value[-1]
		#	feature=noPunc(value)

		if not type(feature) in [str,unicode]:
			print '>> Query failed:',self,value,feature
			return []

		if feature in self.feats:
			if matchValue(self.feats[feature], value):
				matches.append(self)
		else:
			for child in self.descendants():
				if not child: continue
				matches.extend(child._searchSingleValue(value, feature))
		return matches

	def _searchSingleTerm(self, searchTerm):
		value = searchTerm.terms[0]
		feature = valueToFeature(value)
		return self._searchSingleValue(value, feature)

	def _searchMultipleTerms(self, searchTerm):
		termList = searchTerm.terms
		found = True
		for term in termList:
			if not self.search(term):
				found = False
				break
		return found

	def _searchInChildren(self, searchTerm):
		matches = []
		for child in self.descendants():
			matches.extend(child.search(searchTerm))
		return matches

	def query(self,query_string,toprint=False):
		"""Prints words matching the given query. Eg:   [-voice] (Syllable: (Onset: [+voice]) (Coda: [+voice]))"""
		qq=SearchTerm(query_string)
		matchcount=0
		matches=[]
		for word in self.words():
			for match in word.search(qq):
				matches.append(match)
				matchcount+=1
				if "Word" in str(type(match)):
					matchstr=""
				else:
					matchstr=str(match)
				if toprint:
					word.om(makeminlength(str(matchcount),int(being.linelen/6))+"\t"+makeminlength(str(word),int(being.linelen))+"\t"+matchstr)
		return matches

	def search(self, searchTerm):
		"""Returns objects matching the query."""
		if type(searchTerm)==type(''):
			searchTerm=SearchTerm(searchTerm)

		if searchTerm not in self.featpaths:
			matches = None
			if searchTerm.type != None and searchTerm.type != self.classname():
				matches = self._searchInChildren(searchTerm)
			elif searchTerm.isAtomic():
				matches = self._searchSingleTerm(searchTerm)
			else:
				matches = self._searchMultipleTerms(searchTerm)
				if matches == True:
					matches = [self]
				if matches == False:
					matches = []
			self.featpaths[searchTerm] = matches

		return self.featpaths[searchTerm]

	def _getTypesFromHereOnDown(self,types=[]):
		classname=self.classname()
		if (not classname in types):
			types.append(classname)
		if self.descendants():
			return self.descendants()[0]._getTypesFromHereOnDown(types)
		else:
			return types



	def output_min(self):
		words=self.words()
		o=""
		for word in words:
			o+=word.__str__minform()+"\n"
		return o

	def get_available_rime(self):
		#print self
		last_word=self.words()[-1]
		import copy
		def reduce_word(word0):
			word=word0
			sylls=word.syllables()
			stress_yet=False
			to_keep=[]
			if sylls[-2].feature('prom.stress') and not sylls[-1].feature('prom.stress'):
				for i in reversed(range(len(sylls))):
					to_keep.insert(0,i)
					if sylls[i].feature('prom.stress'): break
			else:
				to_keep=[range(len(sylls))[-1]]

			obj=entity()
			children=[word.children[i] for i in to_keep]
			#print "KEEPING:",children
			sbody=children[0].children[0] # first syllable's syllable body
			for x in sbody.children[1:]: # all but onset (only rime)
				obj.children+=x.phonemes()
			for x in children[1:]:
				obj.children+=x.phonemes()
			return obj

		if len(last_word.syllables())==1:
			rime=self.rimes()[-1]
			if not rime.phonemes():
				return self.syllables()[-1].children[0]
			return rime
		else:
			#print "REDUCING:",last_word.token
			return reduce_word(last_word)

	def rime_distance(self,other,normalized=False):
		my_rime=self.get_available_rime()
		other_rime=other.get_available_rime()

		#print "COMPARING:"
		#print self.words()[-1], my_rime.phonemes()
		#print other.words()[-1], other_rime.phonemes()
		#print
		return my_rime.phonetic_distance(other_rime,normalized=normalized)


	def phonetic_distance(self,other,normalized=False):
		phonemes1=self.phonemes()
		phonemes2=other.phonemes()

		p2chr={}
		for p in phonemes1+phonemes2:
			pstr=p.phon_str
			if not pstr in p2chr: p2chr[pstr]=unichr(len(p2chr))

		chr1=u''.join([p2chr[p.phon_str] for p in phonemes1])
		chr2=u''.join([p2chr[p.phon_str] for p in phonemes2])

		# @HACK @TODO
		#return 0 if chr1==chr2 else 10
		###

		from Levenshtein import editops
		dist=0.0
		for edit_type,index1,index2 in editops(chr1,chr2):
			if edit_type!='replace':
				dist+=1
				continue
			try:
				p1=phonemes1[index1]
				p2=phonemes2[index2]
				#print edit_type,p1,p2,index1,index2 #,p1.distance(p2)
				dist+=p1.distance(p2)
			except IndexError:
				dist+=1

		## @NEW
		# add a distpoint if does not end with same phoneme?
		try:
			if phonemes1[-1]!=phonemes2[-1]: dist+=2
		except IndexError:
			# ???? @TODO
			dist+=2

		if normalized: return dist / float(max(len(phonemes1),len(phonemes2)))
		return dist
