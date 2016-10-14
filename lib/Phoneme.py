from ipa import ipa,ipakey,ipa2cmu,formantd
from entity import entity
class Phoneme(entity):	
	def __init__(self,phons,ipalookup=True):
		self.feats = {}
		self.children = []	# should remain empty unless dipthong
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
		strself=str(self)
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
		#return "["+str(self)+"]"
		return str(self)
	
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
	
	@property
	def phon_str(self):
		if self.phon: return self.phon
		return u''.join(phon.phon for phon in self.children)

	@property
	def featset(self):
		if self.children:
			featset=set()
			for child in self.children:
				featset|=child.featset
			return featset
		else:
			return {feat for feat in self.feats if self.feats[feat]}

	@property
	def featspace(self):
		fs={}
		if self.children:
			for child in self.children:
				#print "CHILD:",child,child.featset
				for f,v in child.feats.items():
					fs[f]=int(v) if v!=None else 0
		else:
			for f,v in self.feats.items():
				fs[f]=int(v) if v!=None else 0
		return fs



	def CorV(self):
		if self.isDipthong() or self.isLong():
			return "VV"
		
		if self.isPeak():
			return "V"
		else:
			return "C"

	def distance(self,other):
		lfs1=[self.featspace] if not self.children else [c.featspace for c in self.children]
		lfs2=[other.featspace] if not other.children else [c.featspace for c in other.children]
		dists=[]
		for fs1 in lfs1:
			for fs2 in lfs2:
				allkeys=set(fs1.keys() + fs2.keys())
				f=sorted(list(allkeys))
				v1=[float(fs1.get(fx,0)) for fx in f]
				v2=[float(fs2.get(fx,0)) for fx in f]
				from scipy.spatial import distance
				dists+=[distance.euclidean(v1,v2)]
		return sum(dists)/float(len(dists))

	def distance0(self,other):
		import math
		feats1=self.featset
		feats2=other.featset
		jc=len(feats1&feats2) / float(len(feats1 | feats2))
		vdists=[]
		if not 'cons' in feats1 and not 'cons' in feats2:
			## ADD VOWEL F1,F2 DIST
			v1=[p for p in self.phon_str if p in formantd]
			v2=[p for p in other.phon_str if p in formantd]
			if not v1 or not v2:
				vdists+=[2]
			for v1x in v1:
				for v2x in v2:
					#print v1x,v2x
					vdist=math.sqrt( (formantd[v1x][0] - formantd[v2x][0])**2 + (formantd[v1x][1] - formantd[v2x][1])**2)
					#print "ADDING",vdist
					vdists+=[vdist]
		#print self,other,feats1,feats2
		return jc + sum(vdists)

			

	def __eq__(self,other):
		return self.feats == other.feats