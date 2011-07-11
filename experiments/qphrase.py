import sys,os

## defaults
folder='/Lab/Projects/adjectives/parsed'
phrase='NP'
embedlimit=1

try:
	folder=sys.argv[1]
	phrase=sys.argv[2]
except:
	print "[usage:] python qphrase.py [folder_of_parsed_xml] [NP or other phrase-type]"
	print ">> defaulting to:",folder,phrase

pdict={}
for fn in sorted(os.listdir(folder)):
	if not fn.endswith('.xml'): continue
	f=open(os.path.join(folder,fn)); t=f.read(); f.close()
	print fn
	
	for parse in t.split('<parse>')[1:]:
		sentstr=[]
		for x in parse.split(')'):
			x=x.split(' ')[-1].strip()
			if x: sentstr+=[x]
			
		sentstr=" ".join(sentstr)
		#continue
		
		
	
		for p in parse.split('('+phrase+' ')[1:]:
			embedlevel=0
			pstr=''
			for x in p:
				if x=='(' or x==')':
					if x=='(':
						embedlevel+=1
					elif x==')':
						embedlevel-=1
					
					if embedlevel<0 or embedlevel>embedlimit:
						break
				else:
					print x
					if x.isalpha() and x==x.upper(): continue
					pstr+=x
			exit()
		
			pstr=pstr.replace('  ',' ').strip()
			if not pstr: continue
			if not ' ' in pstr: continue
			# try:
			# 				pdict[pstr]+=1
			# 			except:
			# 				pdict[pstr]=1
			
			try:
				print pstr,sentstr.index(pstr)
			except:
				print "!!"*10
				print sentstr
				print pstr
				print "!!"*10
			



exit()
o=''
for k,v in sorted(pdict.items(),key=lambda x: -x[1]):
	o+=str(k)+'\t'+str(v)+'\n'
import pytxt
pytxt.write('np-stats.txt',o,toprint=True)
