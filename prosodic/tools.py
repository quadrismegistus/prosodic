import pickle,sys,os,codecs

def slice(l,num_slices=None,slice_length=None,runts=True,random=False):
	"""
	Returns a new list of n evenly-sized segments of the original list
	"""
	if random:
		import random
		random.shuffle(l)
	if not num_slices and not slice_length: return l
	if not slice_length: slice_length=int(len(l)/num_slices)
	newlist=[l[i:i+slice_length] for i in range(0, len(l), slice_length)]
	if runts: return newlist
	return [lx for lx in newlist if len(lx)==slice_length]

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

def loadConfigPy(toprint=True,dir_prosodic=None,dir_home='',config=None):
	import imp
	settings={'constraints':[]}
	if not dir_prosodic: dir_prosodic=sys.path[0]
	path_home=os.path.join(dir_home,'config.py')
	path_root=os.path.join(dir_prosodic,'config.py')

	if config:
		pass
	elif os.path.exists(path_home):
		print '>> loading config from:',path_home
		config=imp.load_source('config', path_home)
	else:
		config=imp.load_source('config', path_root)

	vnames = [x for x in dir(config) if not x.startswith('_')]

	for vname in vnames:
		vval=getattr(config,vname)
		if vname=='Cs':
			for k,v in vval.items():
				if not isinstance(v, tuple):
					cname=k+'/'+str(v)
				else:
					cname=k+'/'
					cname+=str(v[0])
					for i in range(1, min(3, len(v))):
						cname+=';' + str(v[i])
				settings['constraints']+=[cname]
		else:
			settings[vname]=vval


	if toprint:
		print ">> loaded settings:"
		for k,v in sorted(settings.items()):
			if type(v) == list:
				print '\t',k
				for x in v:
					print '\t\t',x
			else:
				print '\t',k,'\t',v

	#settings['constraints']=" ".join(settings['constraints'])
	#settings['meters']=loadMeters()

	return settings
#
# def loadMeters():
# 	import meters
# 	from Meter import Meter
# 	d={}
# 	for name,module in meters.d.items():
# 		#d[name]=loadConfigPy(toprint=False,config=module)
# 		#d[name]['id']=name
# 		mconfig = loadConfigPy(toprint=False,config=module)
# 		mconfig['id']=name
# 		mobj = Meter(config=mconfig)
# 		d[name]=mobj
# 	return d


def loadMeters(meter_dir_root,meter_dir_home):
	d={}
	import imp
	for meter_dir in [meter_dir_root,meter_dir_home]:
		if os.path.exists(meter_dir) and os.path.isdir(meter_dir):
			for fn in os.listdir(meter_dir):
				if not fn.endswith('.py') or fn.startswith('_'): continue
				idx=fn.replace('.py','').replace('-','_')
				d[idx]=imp.load_source(idx, os.path.join(meter_dir,fn))

	from Meter import Meter
	for name,module in d.items():
		mconfig = loadConfigPy(toprint=False,config=module)
		mconfig['id']=name
		mobj = Meter(config=mconfig)
		d[name]=mobj
	return d

def now(now=None,seconds=True):
	import datetime as dt
	if not now:
		now=dt.datetime.now()
	elif type(now) in [int,float,str]:
		now=dt.datetime.fromtimestamp(now)

	return '{0}{1}{2}-{3}{4}{5}'.format(now.year,str(now.month).zfill(2),str(now.day).zfill(2),str(now.hour).zfill(2),str(now.minute).zfill(2),'-'+str(now.second).zfill(2) if seconds else '')



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



"""
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
"""

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

def noPunc(token):
	if not token: return token
	x=gleanPunc(token)[0]
	x=x.split('&')[0]
	y=x.split(';')
	try:
		x=y[1]
	except IndexError:
		pass
	x=x.split('\\')[0]
	return x

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
	try:
		from pyparsing import nestedExpr
	except ImportError:
		raise Exception("""
			In order to use the query language, you need to install the pyparsing python module. Run:
			pip install pyparsing
			""")

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


def read_ld(fn):
	if fn.endswith('.xls') or fn.endswith('.xlsx'):
		return xls2ld(fn)
	else:
		return tsv2ld(fn)

def xls2ld(fn,header=[],sheetname=True,keymap={}):
	try:
		import xlrd
	except ImportError:
		raise Exception("""
			In order to load Excel files, you need to install the xlrd python module. Run:
			pip install xlrd
			""")

	headerset=True if len(header) else False
	f=xlrd.open_workbook(fn)
	ld=[]
	def _boot_xls_sheet(sheet,header=[]):
		ld2=[]
		for y in range(sheet.nrows):
			if not header:
				for xi in range(sheet.ncols):
					cell=sheet.cell_value(rowx=y,colx=xi)
					header+=[cell]
				continue
			d={}
			for key in header:
				try:
					value=sheet.cell_value(rowx=y, colx=header.index(key))
					d[key]=value
					#print key,value,y,header.index(key),row[header.index(key)]
				except:
					#print "!! "+key+" not found in "+str(sheet)
					#d[key]=''
					pass
			if len(d):
				if sheetname: d['sheetname']=sheet.name
				ld2.append(d)
		return ld2


	if f.nsheets > 1:
		sheetnames=sorted(f.sheet_names())
		for sheetname in sheetnames:
			sheet=f.sheet_by_name(sheetname)
			for d in _boot_xls_sheet(sheet,header=header if headerset else []):
				ld.append(d)
	else:
		sheet = f.sheet_by_index(0)
		ld.extend(_boot_xls_sheet(sheet,header=header if headerset else []))

	return ld

def tsv2ld(fn,tsep='\t',nsep='\n',u=True,header=[],keymap={},zero='',removeEmpties=False):
	import time
	now=time.time()
	print '>> reading as ld:',fn
	import os
	if fn.startswith('http'):
		print '>> reading webpage...'
		import urllib
		f=urllib.urlopen(fn)
		t=f.read()
		if fn.endswith('/pubhtml'):
			return goog2tsv(t)
		f.close()
	elif not os.path.exists(fn):
		t=fn
	elif u:
		import codecs
		f=codecs.open(fn,encoding='utf-8')
		t=f.read()
		f.close()
	else:
		f=open(fn,'r')
		t=f.read()
		f.close()
	t=t.replace('\r\n','\n')
	t=t.replace('\r','\n')

	#header=[]
	listdict=[]


	for line in t.split(nsep):
		if not line.strip(): continue
		line=line.replace('\n','')
		ln=line.split(tsep)
		#print ln
		if not header:
			header=ln
			for i,v in enumerate(header):
				if v.startswith('"') and v.endswith('"'):
					header[i]=v[1:-1]
			continue
		edict={}
		for i in range(len(ln)):
			try:
				k=header[i]
			except IndexError:
				#print "!! unknown column for i={0} and val={1}".format(i,ln[i])
				continue
			v=ln[i].strip()

			if k in keymap:
				#print v, type(v)
				v=keymap[k](v)
				#print v, type(v)
			else:
				if v.startswith('"') and v.endswith('"'):
					v=v[1:-1]
				try:
					v=float(v)
				except ValueError:
					v=v

			if type(v) in [str,unicode] and not v:
				if zero=='' and removeEmpties:
					continue
				else:
					v=zero
			edict[k]=v
		if edict:
			listdict.append(edict)

	nownow=time.time()
	print '>> done ['+str(round(nownow-now,1))+' seconds]'

	return listdict

def product(*args):
	if not args:
		return iter(((),)) # yield tuple()
	return (items + (item,)
		for items in product(*args[:-1]) for item in args[-1])

def writegen(fnfn,generator,header=None,sep=','):
	import codecs
	of = codecs.open(fnfn,'w',encoding='utf-8')
	header_written=False
	for dx in generator():
		if not header_written:
			if not header:
				if 'header' in dx:
					header=dx['header']
				else:
					header=sorted(dx.keys())
			of.write(sep.join(['"'+x+'"' for x in header]) + '\n')
			header_written=True

		vals=[]
		for h in header:
			v=dx.get(h,'')
			is_str = type(v) in [str,unicode]
			if type(v) in [float,int] and int(v)==v: v=int(v)
			try:
				o=unicode(v)
			except UnicodeDecodeError:
				o=v.decode('utf-8',errors='ignore')
			if is_str and v:
				o='"'+o+'"'
			vals+=[o]


		of.write(sep.join(vals) + '\n')

def writegengen(fnfn,generator,header=None,sep=',',save=True):
	import codecs
	if save: of = codecs.open(fnfn,'w',encoding='utf-8')
	header_written=False
	for dx in generator():
		if not header_written:
			if not header:
				if 'header' in dx:
					header=dx['header']
				else:
					header=sorted(dx.keys())
			if save: of.write(sep.join(['"'+x+'"' for x in header]) + '\n')
			header_written=True

		vals=[]
		for h in header:
			v=dx.get(h,'')
			is_str = type(v) in [str,unicode]
			if type(v) in [float,int] and int(v)==v: v=int(v)
			try:
				o=unicode(v)
			except UnicodeDecodeError:
				o=v.decode('utf-8',errors='ignore')
			if is_str and v:
				o='"'+o+'"'

			vals+=[o]


		if save: of.write(sep.join(vals) + '\n')
		yield dx



def report(text):
	t=Text(text)
	t.parse()
	t.report()


def assess(fn,meter=None,key_meterscheme=None, key_line='line',key_parse='parse'):
	#from prosodic import Text
	import prosodic as p
	Text=p.Text
	if not meter:
		import Meter
		meter=Meter.genDefault()

	p.config['print_to_screen']=0

	def parse2list(parse):
		l=[]
		for i,x in enumerate(parse):
			if not l or l[-1]!=x:
				l+=[x]
			else:
				l[-1]+=x
		return l

	def get_num_sylls_correct(parse_human,parse_comp):
		maxlen=max([len(parse_comp),len(parse_human)])
		#parse_human=parse2list(parse_human)
		#parse_comp=parse2list(parse_comp)
		#parse_comp_forzip = parse_comp + ['x' for x in range(maxlen-len(parse_comp))]
		#parse_human_forzip = parse_human + ['x' for x in range(maxlen-len(parse_human))]
		parse_comp_forzip = parse_comp + ''.join(['x' for x in range(maxlen-len(parse_comp))])
		parse_human_forzip = parse_human + ''.join(['x' for x in range(maxlen-len(parse_human))])

		## sylls correct?
		_sylls_iscorrect=[]
		#print '\t'.join(parse_human_forzip)
		#print '\t'.join(parse_comp_forzip)
		for syll1,syll2 in zip(parse_human_forzip,parse_comp_forzip):
			syll_iscorrect = int(syll1==syll2)
			_sylls_iscorrect+=[syll_iscorrect]
		return _sylls_iscorrect

	import codecs
	ld=read_ld(fn)
	fn_split = fn.split('.')
	ofn_split=fn_split[:-1] + ['evaluated','meter='+meter.id] + [fn_split[-1]]
	ofn_split_ot=fn_split[:-1] + ['evaluated', 'ot','meter='+meter.id] + [fn_split[-1]]
	ofn='.'.join(ofn_split)
	ofn_ot='.'.join(ofn_split_ot)

	def _print(dx):
		print
		for k,v in sorted(dx.items()):
			print k,'\t',v
		print 'HUMAN   :','\t'.join(dx['parse_human'])
		print 'PROSODIC:','\t'.join(dx['parse_comp'])
		print '         ','\t'.join(['*' if x!=y else ' ' for x,y in zip(dx['parse_human'],dx['parse_comp'])])
		print

	def _recapitalize(parse,code):
		code=' '.join([x for x in code])
		parse=parse.replace('|',' ').replace('.',' ')
		newparse=[]
		for s,c in zip(parse.split(),code.split()):
			if c=='w':
				newparse+=[s.lower()]
			else:
				newparse+=[s.upper()]
		return '  '.join(newparse)

	def _writegen():
		lines_iscorrect=[]
		lines_iscorrect_control=[]
		lines_iscorrect_control2=[]
		lines_iscorrect_human2=[]
		sylls_iscorrect_control=[]
		sylls_iscorrect_control2=[]
		sylls_iscorrect_human2=[]
		sylls_iscorrect=[]
		lines_iscorrect_nonbounded=[]

		otf=codecs.open(ofn_ot,'w',encoding='utf-8',errors='replace')
		otf_nl=0

		for di,d in enumerate(ld):
			line=d[key_line]
			parse_human=''.join([x for x in d[key_parse].lower() if x in ['s','w']])
			if not parse_human: continue
			t=Text(line)
			t.parse(meter=meter)
			#if not t.isParsed: continue

			parse_comp=t.parse_str(viols=False, text=False).replace('|','')

			#if len(parse_comp) != len(parse_human): continue

			parse_str=t.parse_str(viols=False, text=True)
			parses_comp = [x.replace('|','') for x in t.parse_strs(viols=False,text=False)]

			parse_human2=''.join([x for x in d.get('parse_human2','').lower() if x in ['s','w']])

			#parse_human,parse_human2=parse_human2,parse_human

			### OT
			if not otf_nl:
				header=['','','']
				for c in meter.constraints: header+=['[*'+c.name+']']
				otf.write('\t'.join(header)+'\n')

			humans = [parse_human]
			if parse_human2: humans+=[parse_human2]
			for _i,_parses in enumerate(t.allParses()):
				if not _parses: continue
				_parses.sort(key=lambda _P: (-humans.count(_P.str_meter()), _P.totalCount))
				if not humans.count(_parses[0].str_meter()):
					# is the good parse in the bounded ones?
					for _bndp in t.boundParses()[_i]:
						if _bndp.str_meter() in humans:
							_parses.insert(0,_bndp)

				for _pi,_parse in enumerate(_parses):
					otf_nl+=1
					code=_parse.str_meter()
					row=[line if not _pi else '', unicode(_parse) + (' [*Bounded]' if _parse.isBounded else ''), unicode(humans.count(code)) if code in humans else '']
					for c in meter.constraints: row+=[str(_parse.constraintCounts[c]) if _parse.constraintCounts[c] else '']
					otf.write('\t'.join(row)+'\n')




			parse_comp_dummy2 = ''.join(['w' if not i%2 else 's' for i in range(len(parse_comp))])
			if key_meterscheme:
				if d[key_meterscheme]=='iambic':
					parse_comp_dummy = ('ws'*100)[:len(parse_comp)]
				elif d[key_meterscheme]=='trochaic':
					parse_comp_dummy = ('sw'*100)[:len(parse_comp)]
				elif d[key_meterscheme]=='anapestic':
					parse_comp_dummy = ('wws'*100)[:len(parse_comp)]
				elif d[key_meterscheme]=='dactylic':
					parse_comp_dummy = ('sww'*100)[:len(parse_comp)]
				else:
					parse_comp_dummy=parse_comp_dummy2
			else:
				parse_comp_dummy=parse_comp_dummy2



			## sylls correct?
			this_sylls_correct = get_num_sylls_correct(parse_human, parse_comp)
			this_sylls_correct_dummy = get_num_sylls_correct(parse_human, parse_comp_dummy)
			this_sylls_correct_dummy2 = get_num_sylls_correct(parse_human, parse_comp_dummy2)
			if parse_human2: this_sylls_correct_human2 = get_num_sylls_correct(parse_human, parse_human2)
			num_sylls_correct=sum(this_sylls_correct)
			num_sylls_correct_dummy = sum(this_sylls_correct_dummy)
			num_sylls_correct_dummy2 = sum(this_sylls_correct_dummy2)
			if parse_human2: num_sylls_correct_human2 = sum(this_sylls_correct_human2)
			sylls_iscorrect+=this_sylls_correct
			sylls_iscorrect_control+=this_sylls_correct_dummy
			sylls_iscorrect_control2+=this_sylls_correct_dummy2
			if parse_human2: sylls_iscorrect_human2+=this_sylls_correct_human2


			# line correct?
			line_iscorrect=int(parse_comp == parse_human)
			lines_iscorrect+=[line_iscorrect]
			line_iscorrect_dummy = int(parse_comp_dummy == parse_human)
			line_iscorrect_dummy2 = int(parse_comp_dummy2 == parse_human)
			if parse_human2: line_iscorrect_human2 = int(parse_human2 == parse_human)
			lines_iscorrect_control+=[line_iscorrect_dummy]
			lines_iscorrect_control2+=[line_iscorrect_dummy2]
			if parse_human2: lines_iscorrect_human2+=[line_iscorrect_human2]

			# line at least in list of nonbounded parses?
			line_iscorrect_nonbounded=int(parse_human in parses_comp)
			lines_iscorrect_nonbounded+=[line_iscorrect_nonbounded]

			parse_stress = []
			for w in t.words():
				for x in w.stress:
					parse_stress += ['w' if x=='U' else 's']
			parse_stress=''.join(parse_stress)


			odx=d
			odx['parse_human']=parse_human
			if parse_human2: odx['parse_human2']=parse_human2
			odx['parse_comp']=parse_comp
			odx['parses_comp_nonbounded']=' | '.join(parses_comp)
			odx['num_sylls']=len(parse_human)
			odx['num_sylls_correct']=num_sylls_correct
			odx['num_sylls_correct_control']=num_sylls_correct_dummy
			odx['num_sylls_correct_control_iambic']=num_sylls_correct_dummy2
			if parse_human2:
				odx['num_sylls_correct_human2']=num_sylls_correct_human2
				odx['perc_sylls_correct_human2']=num_sylls_correct_human2 / float(len(parse_human))
				odx['line_iscorrect_human2']=line_iscorrect_human2
			odx['perc_sylls_correct']=num_sylls_correct / float(len(parse_human))
			odx['perc_sylls_correct_control']=num_sylls_correct_dummy  / float(len(parse_human))
			odx['perc_sylls_correct_control_iambic']=num_sylls_correct_dummy2 / float(len(parse_human))
			odx['line_iscorrect']=line_iscorrect
			odx['line_iscorrect_dummy']=line_iscorrect_dummy
			odx['line_iscorrect_dummy_iambic']=line_iscorrect_dummy2
			odx['line_is_in_nonbounded_parses']=line_iscorrect_nonbounded
			odx['parse_str_human']=_recapitalize(parse_str, parse_human)
			odx['parse_str_compu']=_recapitalize(parse_str, parse_comp)
			odx['parse_str_stress']=_recapitalize(parse_str, parse_stress)
			odx['prosody_ipa']=' '.join([w.str_ipasyllstress() for w in t.words()])
			odx['prosody_stress']=' '.join([w.stress for w in t.words()])
			odx['meter_info']=str(t.meter).replace('\n',' ').replace('\t',' ')
			sumconstr=0
			for k,v in t.constraintViolations(use_weights=False,normalize=False).items():
				odx['constraint_'+k]=v
				sumconstr+=v
			odx['constraint_SUM_VIOL']=sumconstr

			#if not line_iscorrect and line_iscorrect_dummy:
			#if len(parse_comp) != len(parse_human):
			#if len(parse_human)>len(parse_comp):
			_print(odx)
			yield odx

		print
		print '##'*10
		print 'RESULTS SUMMARY'
		print '##'*10
		perc_sylls_correct = sum(sylls_iscorrect) / float(len(sylls_iscorrect)) * 100
		perc_lines_correct = sum(lines_iscorrect) / float(len(lines_iscorrect)) * 100
		perc_lines_correct_control = sum(lines_iscorrect_control) / float(len(lines_iscorrect_control)) * 100
		perc_sylls_correct_control = sum(sylls_iscorrect_control) / float(len(sylls_iscorrect_control)) * 100
		perc_lines_correct_nonbound = sum(lines_iscorrect_nonbounded) / float(len(lines_iscorrect_nonbounded)) * 100
		print 'PERCENT SYLLABLES CORRECT:',round(perc_sylls_correct,2),'% [vs.',round(perc_sylls_correct_control,2),'% for control]'
		print 'PERCENT LINES CORRECT:',round(perc_lines_correct,2),'% [vs.',round(perc_lines_correct_control,2),'% for control]'
		print 'PERCENT LINES IN AVAILABLE NONBOUNDED PARSES:',round(perc_lines_correct_nonbound,2),'%'

	writegen(ofn, _writegen)




def ld2dld(ld,key='rownamecol'):
	dld={}
	for d in ld:
		if not d[key] in dld: dld[d[key]]=[]
		dld[d[key]]+=[d]
	return dld

def wordtoks2str(wordtoks):
	x=[]
	for i,wtok in enumerate(wordtoks):
		if wtok.is_punct and x:
			x[-1]+=wtok.token
		else:
			x+=[wtok.token]
	return u' '.join(x)
