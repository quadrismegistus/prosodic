#try:
from rpy2 import robjects as ro
r = ro.r
from rpy2.robjects.packages import importr
import rpy2.robjects.lib.ggplot2 as ggplot2
#except ImportError:
#	exit("!! class DataFrame requires rpy2 to be intalled: <http://rpy.sourceforge.net/rpy2.html>")

class InputNotRecognizedError(Exception):
	pass

class DataFrame(ro.DataFrame):
	def __init__(self,input,**kwargs):
		## set defaults
		self.cols=None
		self.rownamecol=None
		self.factorcol=None
		self.thresholds=[]
		self.allcols=False
		self.trimbyVariance=True
		self.factor=True
		self.rank=False
		self.sumcol=''
		self.z=False
		self.df=True
		self.zero=0.0
		
		## override defaults with
		for k,v in kwargs.items():
			setattr(self,k,v)
		
		## double override with non-keyword
		self.input=input
		
		if not input: return
		if not len(input): return
	
		
		if type(input)==type([]) and type(input[0])==type({}):
			self._gen_LD(input)
		elif type(input)==type(self):
			self._gen_self(input)
		elif type(input)==type(ro.DataFrame):
			self._gen_DF(input)
		elif type(input)==type({}) and type(input.values()[0]==type([])):
			self._gen_DL(input)
		else:
			raise InputNotRecognizedError("Cannot recognize input of type "+type(input))
		
		for k,v in self.df.__dict__.items():
			setattr(self,k,v)

	def __str__(self):
		return self.df.__str__()
	
	#def __repr__(self):
	#	return self.df.__repr__()
	
	
	
	def col(self,colname):
		return list(self.df[list(self.df.colnames).index(colname)])
	
	def row(self,rowname):
		rownum=list(self.df.rownames).index(rowname)
		return [ self.df[i][rownum] for i in range(self.df.ncol)]
	
	def getCols(self,allcols=False):
		""" Returns a list of columns which,
			if allcols=False, returns only columns which all rows share;
			if allcols"""
		
		if self.origin!='ld':
			raise InputNotRecognizedError("Cannot recognize input of type "+type(self.input))
	
		
		ld=self.input
		
		cols=[]
		for row in ld:
			if not type(row)==type({}): continue
			if not len(row.keys()): continue
			
			if not len(cols):
				cols=row.keys()
				continue
			
			if allcols:
				for x in set(row.keys())-set(cols):
					cols.append(x)
			else:
				for x in set(cols)-set(row.keys()):
					cols.remove(x)
			
		
		if self.rownamecol:
			if self.rownamecol in cols:
				cols.remove(self.rownamecol)
		
		return cols
	
	
	def trimCols(self,maxcols,rank=True,byVariance=True,byFrequency=False,printStats=True):
		if self.origin!='ld':
			raise InputNotRecognizedError("Cannot recognize input of type "+type(self.input))
		ld=self.input
	
		
		keysums={}
		for col in self.cols:
			keysums[col]=[]
		
		for x in ld:
			for k in x:
				value=x[k]
				if type(value)==type(float()) or type(value)==type(1):
					try:
						keysums[k]+=[value]
					except KeyError:
						continue
		from operator import itemgetter
		i=0
		allowedkeys=[]
		
		for k in keysums:
			if len(keysums[k])<=1:
				keysums[k]=0
				continue
			if byVariance or not byFrequency:
				keysums[k]=sum([abs(x) for x in zfy(keysums[k])])
			else:
				keysums[k]=sum(keysums[k])
	
		
		sumvariances_df=sum(keysums.values())
		sumvariances=0.0
		
		for key,score in sorted(keysums.items(),key=itemgetter(1),reverse=True):
			print key,"\t",score
			i+=1
			if i>allcols:
				break
			sumvariances+=score
			allowedkeys.append(key)
		#print allowedkeys
		
		self.cols=[]
		for i in range(len(allowedkeys)):
			if rank:
				k='r'+str(i+1).zfill(len(str(len(allowedkeys))))+'.'+allowedkeys[i]
			self.cols.append(k)
		
		#cols=allowedkeys
		#print cols
		if byVariance or not byFrequency:
			Zvariances = "Z-variances"
		else:
			Zvariances = "TermFrequencies"
		
		if printStats:
			print ">> sum of "+Zvariances+" in dataset:", sumvariances_df
			print ">> sum of "+Zvariances+" loaded:", sumvariances
			print ">> (ratio) sum of loaded "+Zvariances+" / sum of possible:", sumvariances/sumvariances_df
			print ">> # features loaded:", len(cols)
			print ">> (ratio) sum of loaded "+Zvariances+" / # of features loaded:", sumvariances/len(cols)
			print
		#print cols
	
	
	
	
	def _gen_LD(self,ld):
		self.origin='ld'
		ld=self.input
		dd={}
		
		if not self.cols:
			self.cols=self.getCols(self.allcols)
			if type(self.allcols)==type(2):
				self.trimCols(self.allcols)
		
		for i in range(len(self.cols)):
			k=self.cols[i]
			dd[k]=[]
		
		rownames=[]
		for x in ld:
			if self.rownamecol: rownames.append(x[self.rownamecol])
			
			for k in self.cols:
				try:
					value=x[k]
				except KeyError:
					try:
						value=x[".".join(k.split(".")[1:])]
					except:
						value=zero
				dd[k].append(value)
		
		for k,v in dd.items():
			if type(v[0])==type(''):
				dd[k]=ro.StrVector(v)
				if self.factor:
					dd[k]=ro.FactorVector(dd[k])
			else:
				if self.z:
					v=zfy(v)
				
				dd[k]=ro.FloatVector(v)
		
		df=ro.DataFrame(dd)
		if self.rownamecol:
			rownames=ro.FactorVector(rownames)
			#print df.rownames
			df.rownames=rownames
		
		self.df=df

	def plot(self, fn, x='x', y='y', col=None, group=None, w=1100, h=800, size=2, smooth=True, point=True, jitter=False, boxplot=False, boxplot2=False, title=False, flip=False, se=False, density=False, line=False):
		df=self.df
		#import math, datetime
		

		grdevices = importr('grDevices')

		if not title:
			title=fn.split("/")[-1]

		grdevices.png(file=fn, width=w, height=h)
		gp = ggplot2.ggplot(df)
		pp = gp	
		if col and group:
			pp+=ggplot2.aes_string(x=x, y=y,col=col,group=group)
		elif col:
			pp+=ggplot2.aes_string(x=x, y=y,col=col)
		elif group:
			pp+=ggplot2.aes_string(x=x, y=y,group=group)
		else:
			pp+=ggplot2.aes_string(x=x, y=y)	

		if boxplot:
			if col:
				pp+=ggplot2.geom_boxplot(ggplot2.aes_string(fill=col),color='blue')
			else:
				pp+=ggplot2.geom_boxplot(color='blue')	

		if point:
			if jitter:
				if col:
					pp+=ggplot2.geom_point(ggplot2.aes_string(fill=col,col=col),size=size,position='jitter')
				else:
					pp+=ggplot2.geom_point(size=size,position='jitter')
			else:
				if col:
					pp+=ggplot2.geom_point(ggplot2.aes_string(fill=col,col=col),size=size)
				else:
					pp+=ggplot2.geom_point(size=size)


		if boxplot2:
			if col:
				pp+=ggplot2.geom_boxplot(ggplot2.aes_string(fill=col),color='blue',outlier_colour="NA")
			else:
				pp+=ggplot2.geom_boxplot(color='blue')

		if smooth:
			if smooth=='lm':
				if col:
					pp+=ggplot2.stat_smooth(ggplot2.aes_string(col=col),size=1,method='lm',se=se)
				else:
					pp+=ggplot2.stat_smooth(col='blue',size=1,method='lm',se=se)
			else:
				if col:
					pp+=ggplot2.stat_smooth(ggplot2.aes_string(col=col),size=1,se=se)
				else:
					pp+=ggplot2.stat_smooth(col='blue',size=1,se=se)

		if density:
			pp+=ggplot2.geom_density(ggplot2.aes_string(x=x,y='..count..'))

		if line:
			pp+=ggplot2.geom_line(position='jitter')


		pp+=ggplot2.opts(**{'title' : title, 'axis.text.x': ggplot2.theme_text(size=24), 'axis.text.y': ggplot2.theme_text(size=24,hjust=1)} )
		#pp+=ggplot2.scale_colour_brewer(palette="Set1")
		pp+=ggplot2.scale_colour_hue()
		if flip:
			pp+=ggplot2.coord_flip()



		pp.plot()
		grdevices.dev_off()
		print ">> saved: "+fn

	def summary(self):
		return r['summary'](self.df)
		
	def xtabs(self,cols=[]):
		frmla='~'+'+'.join(cols)
		return r['xtabs'](frmla,data=self.df)

	def ca(self,fn,cols=[],toprint=True):
		importr('ca')
		fit=r['ca'](self.xtabs(cols))
		if toprint:
			print fit
		
		r_plot(fit,fn)
		return fit
	
	
	def pca(self,fn='pca.png',col=None,w=1200,h=1200):
		stats    = importr('stats')
		graphics = importr('graphics')

		# 
		# if col:
		# 	df,factors=dataframe(df,factorcol=col)
		df=self.df
		pca = stats.princomp(df)

		grdevices = importr('grDevices')
		ofn=".".join(fn.split(".")[:-1]+["eigens"]+[fn.split(".")[-1]])
		strfacts=str(df.nrow)+" items using "+str(df.ncol)+" features ["+ofn.split("/")[-1]+"]"
		grdevices.png(file=ofn, width=w, height=h)
		graphics.plot(pca, main = "Eigenvalues for "+strfacts)
		# if col:
		# 	graphics.hilight(pca,factors)
		grdevices.dev_off()
		print ">> saved: "+ofn	

		grdevices = importr('grDevices')
		ofn=".".join(fn.split(".")[:-1]+["biplot"]+[fn.split(".")[-1]])
		strfacts=str(df.nrow)+" items using "+str(df.ncol)+" features ["+ofn.split("/")[-1]+"]"
		grdevices.png(file=ofn, width=w, height=h)
		stats.biplot(pca, scale=1,main = "biplot of "+strfacts)
		grdevices.dev_off()
		print ">> saved: "+ofn
	

	def testIndependence(self,cols=[]):
		return r['chisq.test'](self.xtabs(cols))


	def lm(self,ykey='y',toprint=True):
		keys=set(self.df.colnames)
		ykeys=set([ykey])
		xkeys=keys.difference(ykeys)
		frmla=ykey+" ~ "+"+".join(xkeys)
		
		fit=r['lm'](frmla,data=self.df)
		if toprint:
			print r['summary'](fit)
		return fit
		

	def glm(self,ykey='y',family='gaussian',anovaTest='Chisq'):
		"""
		API to R's glm:
			http://web.njit.edu/all_topics/Prog_Lang_Docs/html/library/base/html/glm.html
		
		Family can be:
			[ref: http://web.njit.edu/all_topics/Prog_Lang_Docs/html/library/base/html/family.html]
			
			
		"""


		keys=set(self.df.colnames)
		ykeys=set([ykey])
		xkeys=keys.difference(ykeys)

		#lm=r['lsfit'](dataframe(ld,xkeys),dataframe(ld,ykeys))

		#df=dataframe(ld)
		frmla=ykey+" ~ "+"+".join(xkeys)
		lm=r['glm'](formula=frmla,data=self.df,family=family)
		#return "\n\n".join(str(x) for x in [ r['anova'](lm,test=anovaTest) ] )
		anova=r['anova'](lm,test=anovaTest)
		return anova
		# try:
		# 			import werwerwe
		# 			from rpy2.robjects.packages import importr
		# 			rjson=importr('rjson')
		# 			import json
		# 			return json.loads(str(r['toJSON'](anova)[0]))
		# 
		# 		except:
		# 			return anova
		
		#r['ls.print'](lm)





def mean_stdev(x):
	from math import sqrt
	n, mean, std = len(x), 0, 0
	for a in x:
		mean = mean + a
		mean = mean / float(n)
	for a in x:
		std = std + (a - mean)**2
		std = sqrt(std / float(n-1))
	return mean, std




def r_plot(obj,fn,w=800,h=800,xlabel="",ylabel="",label=""):
	from rpy2.robjects.packages import importr
	from rpy2.robjects import r
	grdevices = importr('grDevices')
	grdevices.png(file=fn, width=w, height=h)

	r.plot(obj)

	grdevices.dev_off()
	print ">> saved: "+fn

		

def zfy(tfdict,limit=None):
	if type(tfdict)==type({}):
		mean,stdev=mean_stdev(tfdict.values())
		zdictz={}
		for k,v in tfdict.items():
			if not stdev:
				zdictz[k]=0
			else:
				zdictz[k]=(v-mean)/stdev
			if limit:
				if zdictz[k]>limit:
					del zdictz[k]
		
		return zdictz
	elif type(tfdict)==type([]):
		mean,stdev=mean_stdev(tfdict)
		zdictz=[]
		for v in tfdict:
			if not stdev:
				score=0
			else:
				score=(v-mean)/stdev
			if limit and score>limit:
				continue
			zdictz+=[score]
		return zdictz
	else:
		return tfdict
