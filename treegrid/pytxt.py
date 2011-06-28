import re,os

def yank(text,tag,none=None):
	if type(tag)==type(''):
		tag=tagname2tagtup(tag)
	
	try:
		return text.split(tag[0])[1].split(tag[1])[0]
	except IndexError:
		return none


def yanks(text,tag):
	if type(tag)==type(''):
		tag=tagname2tagtup(tag)

	return [ x.split(tag[1])[0] for x in text.split(tag[0])[1:] ]

def yanks2(text,tag):
	if type(tag)==type(''):
		tag=tagname2tagtup(tag)

	ys=[]
	#return [ tag[0][-1].join(x.split(tag[0][:-1])[1].split(tag[0][-1])[1:]) for x in text.split(tag[1])[:-1] ]
	
	for x in text.split(tag[1])[:-1]:
		try:
			x=x.split(tag[0][:-1])[1].split(tag[0][-1])[1:]
			x=tag[0][-1].join(x)
		except IndexError:
			pass
		ys.append(x)
	return ys

def tagname2tagtup(tagname):
	return ('<'+tagname+'>','</'+tagname+'>')

def safestr(string):
	try:
		return str(string)
	except UnicodeEncodeError:
		return str(string.encode('utf-8','replace'))
	except:
		return "<????>"

def dict2xml(d,root="xml"):
	o=[]
	for k,v in sorted(d.items(),reverse=False):
		o+=["<"+k+">"+v+"</"+k+">"]
	return "<"+root+">\n\t"+ "\n\t".join(o) + "\n</"+root+">"
	

def neginback(strnum):
	if strnum.startswith("-"):
		return strnum[1:]+"-"
	else:
		return strnum

def thetime():
	from time import localtime, strftime
	return strftime("%Y%m%d.%H%M", localtime())

# these two lists serves as building blocks to construt any number
# just like coin denominations.
# 1000->"M", 900->"CM", 500->"D"...keep on going 
decimalDens=[1000,900,500,400,100,90,50,40,10,9,5,4,1]
romanDens=["M","CM","D","CD","C","XC","L","XL","X","IX","V","IV","I"]


def roman(dec):
	"""
	Perform sanity check on decimal and throws exceptions when necessary
	"""		
        if dec <=0:
	  raise ValueError, "It must be a positive"
         # to avoid MMMM
	elif dec>=4000:  
	  raise ValueError, "It must be lower than MMMM(4000)"

	return decToRoman(dec,"",decimalDens,romanDens)

def decToRoman(num,s,decs,romans):
	"""
	  convert a Decimal number to Roman numeral recursively
	  num: the decimal number
	  s: the roman numerial string
	  decs: current list of decimal denomination
	  romans: current list of roman denomination
	"""
	if decs:
	  if (num < decs[0]):
	    # deal with the rest denomination
	    return decToRoman(num,s,decs[1:],romans[1:])		  
	  else:
	    # deduce this denomation till num<desc[0]
	    return decToRoman(num-decs[0],s+romans[0],decs,romans)	  
	else:
	  # we run out of denomination, we are done 
	  return s



def ynk(text,start,end,inout=""):
	if (not start in text) or (not end in text):
		return ""

		
	try:
		if (inout=="in" or inout==0):
			return text.split(start)[1].split(end)[0]
		elif (inout=="out" or inout==1):
			return text.split(end)[0].split(start)[-1]
		else:
			o=[]
			for x in text.split(start):
				#if x.count(">")>1:
				#	x=x[x.index(">")+1:]
				
				xx=x.split(end)[0].strip()
				if not xx: continue
				if xx.startswith("<!DOCTYPE"): continue		# NYT hack
				if xx.startswith("<NYT_"): continue 
				if xx.startswith("<script"): continue

				o.append(xx.replace("\n"," ").replace("\r"," "))
			return "\n\n".join(o)
	except:
		return ""
		
		
def tsv2ld(fn,tsep='\t',nsep='\n'):
	f=open(fn,'r')
	t=f.read()
	t=t.replace('\r\n','\n')
	t=t.replace('\r','\n')
	f.close()
	header=[]
	listdict=[]
	
	
	for line in t.split(nsep):
		if not line.strip(): continue
		line=line.replace('\n','')
		ln=line.split(tsep)
		#print ln
		if not header:
			header=ln
			continue
		edict={}
		for i in range(len(ln)):
			k=header[i]
			v=ln[i].strip()
			if v.startswith('"') and v.endswith('"'):
				v=v[1:-1]
			
			edict[k]=v
		if edict:
			listdict.append(edict)
	return listdict
	
def unhtml(data):
	return remove_html_tags(data)

def remove_html_tags(data):
	data=safestr(data)
	p=re.compile(r'<.*?>')
	y=str(p.sub('',data)).strip().split('">')
	while(('&' in y) and (';' in y)):
		y=y[:y.index('&')]+y[y.index(';')+1:]
	try:
		return y[1].strip()
	except:
		return y[0]



def extractTags(text,leavetexttags=[u"placeName"]):
	tags=[]
	tags_milestone=[]
	yankeds=[]
	
	if "</" in text:
		for x in text.split("</")[1:]:
			tags.append(x.split(">")[0])
	
	if "/>" in text:
		for x in text.split("/>")[:-1]:
			x=x.split("<")[-1]
			try:
				x=x.split()[0]
			except IndexError:
				x=x
			#if "/" in x: continue
			#if not x: continue
			tags_milestone.append(x)

	for tag in tags_milestone:
		yanked=yank(text,("<"+tag,"/>"))
		while yanked.strip():
			ydat="<"+tag+yanked+"/>"
			#yankeds.append(ydat)
			text=text.replace(ydat,' ')
			yanked=yank(text,("<"+tag,"/>"))
	
	for tag in tags:
		yanked=yank(text,("<"+tag,"</"+tag+">"))
		while yanked and yanked.strip():				
			ydat="<"+tag+yanked+"</"+tag+">"
			
			if tag in leavetexttags:
				text=text.replace(ydat,remove_html_tags(yanked.split(">")[-1]))
			else:
				yankeds.append(ydat)
				text=text.replace(ydat,' ')
			yanked=yank(text,("<"+tag,"</"+tag+">"))
	

	
	return (text.replace("\n","").replace("\r",""),yankeds)

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
	x=gleanPunc(token)[0]
	x=x.split('&')[0]
	y=x.split(';')
	try:
		x=y[1]
	except IndexError:
		pass
	x=x.split('\\')[0]
	return x

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
	

def readDict(fn,sep='\t'):
	try:
		d={}
		f=open(fn)
		for line in f:
			ln=line.split(sep)
			k=ln[0].strip()
			v=ln[1].strip()
			
			if v.isdigit():
				d[k]=int(v)
			else:
				d[k]=v
		
		if len(d):
			return d
		else:
			return None
		
	except IOError:
		return {}
	
def writeDict(fn,d,sep="\t",toprint=True):
	o=""
	for k,v in d.items():
		o+=sep.join(str(x) for x in [k,v])+"\n"
	write(fn,o,toprint)


def extractTagsAsDict(text,leavetexttags=[u"placeName"]):
	text,tags=extractTags(text,leavetexttags)
	tagdict={}
	for tag in tags:
		
		opentag=tag.split(">")[0].split("<")[1].strip()
		tagbody=unhtml(tag).strip()
		
		if not tagbody: continue
		
		if " " in opentag:
			spaces=opentag.split()
			tagname=spaces[0]
			for space in spaces[1:2]:
				if not space.strip(): continue
				dat=space.strip().split("=")
				k=dat[0]
				try:
					v=dat[1]
				except:
					continue
				v=v.replace('"','').replace("'","").strip()
				
				try:
					tagdict[tagname][k][v]=tagbody
				except KeyError:
					try:
						tagdict[tagname][k]={}
						tagdict[tagname][k][v]=tagbody
					except KeyError:
						tagdict[tagname]={}
						tagdict[tagname][k]={}
						tagdict[tagname][k][v]=tagbody
		
		else:
			tagname=opentag
			tagdict[tagname]=tagbody	
				
	return tagdict


def writeToFile(folder,fn,data,extension="tsv"):
	#ofolder=os.path.join(folder,'results','stats','corpora',name)

	if not os.path.exists(folder):
		os.makedirs(folder)

	ofn=os.path.join(folder,'.'.join([fn,extension]))
	print ">> saved: "+ofn
	of = open(ofn,'w')
	of.write(data)
	of.close()



def write_xls(fn,data,sheetname='index',toprint=True,limFields=None,widths=[]):
	import xlwt
	wb=xlwt.Workbook(encoding='utf-8')
	
	if type(data)!=({}):
		dd={}
		dd[sheetname]=data
	else:
		dd=data
	
	for sheetname,data in sorted(dd.items()):
		ws=wb.add_sheet(sheetname)
		nr=-1
		style = xlwt.easyxf('align: wrap True')
		#style=xlwt.easyxf('')
		for row in data:
			nc=-1
			nr+=1
			for cell in row:
				nc+=1
				# 
				# try:
				# 	cell=unicode(cell)
				# except UnicodeDecodeError:
				# 	cell=cell.decode('utf-8')
				# print cell
				
				if not (type(cell)==type(1) or type(cell)==type(1.0)):
					ws.row(nr).set_cell_text(nc,cell,style)
				else:
					
					ws.row(nr).set_cell_number(nc,cell,style)
		
		# for i in range(len(widths)):
		# 			w=widths[i]
		# 			if not w: continue
		# 			ws.col(i).width=w
	
	wb.save(fn)
	if toprint:
		print ">> saved: "+fn
	

def tmp(data):
	import tempfile
	f=tempfile.NamedTemporaryFile()
	f.write(data)
	#f.close()
	return f

def write_tmp(data,suffix=''):
	import time
	fn='/Lab/Processing/tmp/'+str(time.time()).replace('.','')+suffix
	write(fn,data)
	return fn	
	

def write(fn,data,toprint=False,join_line='\n',join_cell='\t'):
	if type(data)==type([]):
		o=""
		for x in data:
			if type(x)==type([]):
				z=[]
				for y in x:
					if type(y)==type(u''):
						y=y.encode('utf-8')
					z+=[y]
				x=z
				line=join_cell.join(x)
			else:
				try:
					line=str(x)
				except UnicodeEncodeError:
					line=x.encode('utf-8')
			line=line.replace('\r','').replace('\n','')
			o+=line+join_line
	else:
		o=str(data)
	of = open(fn,'w')
	of.write(o)
	of.close()
	if toprint:
		print ">> saved: "+fn
	

def makeminlength(string,numspaces):
	if len(string) < numspaces:
		for i in range(len(string),numspaces):
			string += " "
	return string
	
def get_class( kls ):
    parts = kls.split('.')
    module = ".".join(parts[:-1])
    m = __import__( module )
    for comp in parts[1:]:
        m = getattr(m, comp)            
    return m

def gleanPunc(aToken):
	aPunct = None
	while(len(aToken) > 0 and not aToken[0].isalnum()):
		aPunct = aToken[:1]
		aToken = aToken[1:]
	while(len(aToken) > 0 and not aToken[-1].isalnum()):
		aPunct = aToken[-1]
		aToken = aToken[:-1]
	return (aToken, aPunct)
	

def count(string, look_for):
    start   = 0
    matches = 0

    while True:
        start = string.find (look_for, start)
        if start < 0:
            break

        start   += 1
        matches += 1

    return matches
		


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


def hash(string):
	import hashlib
	return str(hashlib.sha224(string).hexdigest())