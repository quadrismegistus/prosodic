import pickle,sys,os
from pyparsing import nestedExpr

def bigrams(l):
	return ngram(l,2)

def ngram(l,n=3):
	grams=[]
	gram=[]
	for x in l:
		gram.append(x)
		if len(gram)<n: continue
		g=tuple(gram)
		grams.append(g)
		gram.reverse()
		gram.pop()
		gram.reverse()
	return grams

def gleanPunc2(aToken):
	aPunct0 = ''
	aPunct1 = ''
	while(len(aToken) > 0 and not aToken[0].isalnum()):
		aPunct0 = aPunct0+aToken[:1]
		aToken = aToken[1:]
	while(len(aToken) > 0 and not aToken[-1].isalnum()):
		aPunct1 = aToken[-1]+aPunct1
		aToken = aToken[:-1]
	return (aPunct0, aToken, aPunct1)


def findall(L, value, start=0):
	# generator version
	i = start - 1
	try:
		i = L.index(value, i+1)
		yield i
	except ValueError:
		pass

def loadConfig(toprint=True,dir_prosodic=None):
	settings={'constraints':[]}
	if not dir_prosodic: dir_prosodic=sys.path[0]
	file=open(os.path.join(dir_prosodic,'config.txt'), 'r')
	for ln in file:
		ln=ln.strip()
		if not ln: continue
		if ln.startswith("#"): continue
		
		if ("=" in ln) and (not "=>" in ln):
			dat=ln.split("=")
			k=dat[0].strip()
			v=[z for z in dat[1].split() if z.strip()][0].strip()
			if v.isdigit(): v=int(v)
			settings[k]=v
			
		else:
			dat=ln.split("\t")
			constraint=dat[0].strip()
			settings['constraints']+=[constraint]
	settings['constraints']=" ".join(settings['constraints'])
	
	if toprint:
		print ">> loaded settings:"
		for k,v in sorted(settings.items()):
			print "\t"+"\t".join(str(x) for x in [k,v])
	return settings

def choose(optionlist,msg="please select from above options [using commas for individual selections and a hyphen for ranges]:\n"):
	seldict={}
	
	selnum=0
	print
	print
	
	if type(optionlist)==type([]):
		for option in optionlist:
			selnum+=1
			seldict[selnum]=option
			print "\t"+"\t".join(str(x) for x in [selnum,option])
	elif type(optionlist)==type({}):
		for option,desc in optionlist.items():
			selnum+=1
			seldict[selnum]=option
			print "\t"+"\t".join(str(x) for x in [selnum,option,desc])
	
	inp=raw_input("\n\t>> "+msg+"\n\t").strip()
	sels=[]
	for np in inp.split(","):
		np=np.strip()
		if "-" in np:
			try:
				nn=np.split("-")
				for n in range(int(nn[0]),int(nn[1])+1):
					sels.append(seldict[n])
			except:
				continue
		else:
			try:
				sels.append(seldict[int(np)])
			except:
				continue
	
	return sels



"""
Calculate mean and standard deviation of data x[]:
    mean = {\sum_i x_i \over n}
    std = sqrt(\sum_i (x_i - mean)^2 \over n-1)
"""
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
	
def linreg(X, Y):
	from math import sqrt
	from numpy import nan, isnan
	from numpy import array, mean, std, random
	"""
	Summary
	    Linear regression of y = ax + b
	Usage
	    real, real, real = linreg(list, list)
	Returns coefficients to the regression line "y=ax+b" from x[] and y[], and R^2 Value
	"""
	if len(X) != len(Y):  raise ValueError, 'unequal length'
	N = len(X)
	Sx = Sy = Sxx = Syy = Sxy = 0.0
	for x, y in map(None, X, Y):
	    Sx = Sx + x
	    Sy = Sy + y
	    Sxx = Sxx + x*x
	    Syy = Syy + y*y
	    Sxy = Sxy + x*y
	det = Sxx * N - Sx * Sx
	a, b = (Sxy * N - Sy * Sx)/det, (Sxx * Sy - Sx * Sxy)/det
	meanerror = residual = 0.0
	for x, y in map(None, X, Y):
	    meanerror = meanerror + (y - Sy/N)**2
	    residual = residual + (y - a * x - b)**2
	RR = 1 - residual/meanerror
	ss = residual / (N-2)
	Var_a, Var_b = ss * N / det, ss * Sxx / det
	#print "y=ax+b"
	#print "N= %d" % N
	#print "a= %g \\pm t_{%d;\\alpha/2} %g" % (a, N-2, sqrt(Var_a))
	#print "b= %g \\pm t_{%d;\\alpha/2} %g" % (b, N-2, sqrt(Var_b))
	#print "R^2= %g" % RR
	#print "s^2= %g" % ss
	return a, b, RR

def writeToFile(name,key,data,iscorpus=False,extension="tsv"):
	if not iscorpus:
		ofolder=os.path.join(sys.path[0],'results','stats','texts',name)
	else:
		ofolder=os.path.join(sys.path[0],'results','stats','corpora',name)
	
	if not os.path.exists(ofolder):
		os.makedirs(ofolder)
	
	ofn=os.path.join(ofolder,'.'.join([name,key,extension]))
	print ">> saved: "+ofn
	of = open(ofn,'w')
	of.write(data)
	of.close()			

def write(fn,data,toprint=False):
	of = open(fn,'w')
	of.write(data)
	of.close()
	if toprint:
		print ">> saved: "+fn



def loadDict(dictFile):
	cmuFile = open(dictFile, 'r')
	if dictFile[-7:] == ".pickle":
		return pickle.load(cmuFile)
	elif dictFile[-4:] != ".txt":
		return {}
	
	cmuDict = dict()
	curLine = cmuFile.readline().strip()
	while(curLine):
		curLine = cmuFile.readline().strip()
		if(curLine == ""): break
		if(curLine.startswith("#")): continue
	
		tokens = curLine.split()
		if(len(tokens) < 2): continue
		curKey = tokens[0].lower()
		if("(" in curKey):
			wrd = curKey.split("(")[0].strip()
		else:
			wrd = curKey.strip()
		if(not wrd in cmuDict):
			cmuDict[wrd] = []
		cmuDict[wrd].append(curLine)
			
	return cmuDict

def loadDicts(dictFolder,srch='dict.*'):
	import os,glob
	dict = {}
	for filename in glob.glob(os.path.join(dictFolder, srch)):
		if (os.path.exists(filename+'.pickle')):
			continue
		else:
			for k,v in loadDict(filename).items():
				dict[k] = v
	return dict

def makeminlength(string,numspaces):
	if len(string) < numspaces:
		for i in range(len(string),numspaces):
			string += " "
	return string

def loadDict(lang):
	return get_class('Dictionary.Dictionary')(lang)

def get_class( kls ):
    parts = kls.split('.')
    module = ".".join(parts[:-1])
    m = __import__( module )
    for comp in parts[1:]:
        m = getattr(m, comp)            
    return m

class Bin:
	def __init__(self,name):
		self.name = name
		self.bin = ""
	def __repr__(self):
		return self.bin
	def write(self,str):
		self.bin += str
	def read(self):
		return self.bin
	def nameplease(self):
		return self.name

def gleanPunc(aToken):
	aPunct = None
	while(len(aToken) > 0 and not aToken[0].isalnum()):
		aPunct = aToken[:1]
		aToken = aToken[1:]
	while(len(aToken) > 0 and not aToken[-1].isalnum()):
		aPunct = aToken[-1]
		aToken = aToken[:-1]
	return (aToken, aPunct)

class string2(str):
	def overcount(self, pattern): #Returns how many p on s, works for overlapping
		ocu = 0
		x = 0
		while 1:
			try:
				i = self.index(pattern, x)
			except ValueError:
				break
			ocu += 1
			x = i + 1
		return ocu
	
def word2syll(word, numSyll):
	i = 0
	textSyll = []
	while(i < numSyll):
		textSyll.append("")
		i+=1
	
	numLetters = len(word)
	try:
		inc = int(numLetters/numSyll)
		
		curSyll = 0
		unit = ""
		curLetter = 1
		for letter in word:
			textSyll[curSyll] += letter
			if(curLetter % inc == 0):
				if ((curSyll + 1) < numSyll):
					curSyll += 1
			curLetter += 1
	except ZeroDivisionError:
		return '<?>'
			
	return textSyll

def dict_ksort(adict):
    items = adict.items()
    items.sort()
    return [value for key, value in items]
		
def product(*args):
    if not args:
        return iter(((),)) # yield tuple()
    return (items + (item,) 
            for items in product(*args[:-1]) for item in args[-1])	



# trim the value off a feature
# [+sonorant] becomes [sonorant]
def valueToFeature(val):
	return val[2:-1]

# return True if value is + and bool is True or value is - and bool is False
def matchValue(bool, val):
	return bool == (val[1] == '+')
	
def searchStringToList(str):
	if len(str) < 1 or str[0] != '(' or str[-1] != ')':
		str = '(' + str + ')'
	return nestedExpr().parseString(str).asList()[0]

def isTypeName(expr):
	return type(expr) == type('') and len(expr) > 0 and expr[0] != '['

class SearchTerm:
	def __init__(self, termList):
		if type(termList) == type(''):
			termList = searchStringToList(termList)
		
		self.type = None
		possibleType = termList[0]
		if isTypeName(possibleType):
			self.type = possibleType[:-1]
			termList = termList[1:]
			
		self.terms = termList
		if self.isAtomic():
			return
		
		self.terms = []
		for i in range(len(termList)):
			term = termList[i]
			self.terms.append(SearchTerm(term))
			
	def isAtomic(self):
		return len(self.terms) == 1
	
	def __cmp__(self, other):
		return cmp(id(self.terms), id(other.terms))
		
	def __hash__(self):
		return id(self.terms)





def describe_func(obj, method=False):
	""" Describe the function object passed as argument.
	If this is a method object, the second argument will
	be passed as True """
	import inspect
	o=[]

	try:
		arginfo = inspect.getargspec(obj)
	except TypeError:
		return

	args = arginfo[0]
	argsvar = arginfo[1]

	if args:
		if args[0] == 'self':
			#o+=['self']
			args.pop(0)

		#o+=['\t-Method Arguments:', args]

		if arginfo[3]:
			dl = len(arginfo[3])
			al = len(args)
			defargs = args[al-dl:al]
			o=zip(defargs, arginfo[3])

	# if arginfo[1]:
	# 		o+=['\t-Positional Args Param: %s' % arginfo[1]]
	# 	if arginfo[2]:
	# 		o+=['\t-Keyword Args Param: %s' % arginfo[2]]
	
	return o