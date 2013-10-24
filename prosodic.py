# -*- coding: UTF-8 -*-
import sys,glob,os,time

#dir_prosodic=sys.path[0]
dir_prosodic=os.path.split(globals()['__file__'])[0]
sys.path.insert(0,dir_prosodic)
dir_imports=os.path.join(dir_prosodic,'lib')
dir_corpus=os.path.join(dir_prosodic,'corpora')
sys.path.append(dir_imports)

## import necessary objects
from tools import *
config=loadConfig(__name__=='__main__',dir_prosodic=dir_prosodic)
import entity
from entity import being
from Text import Text
from Corpus import Corpus
from Stanza import Stanza
from Line import Line
from Phoneme import Phoneme
from Word import Word

## set defaults
languages=['en','fi']
lang=config['lang']

## load defaults
dict={}
for lng in languages:
	dict[lng]=loadDict(lng)
del lng


## load config
if __name__ != "__main__":
	being.printout=False
	#config['print_to_screen']=0
else:	## if not imported, go into interactive mode
	skip=False
	
	## but do not go into interactive mode if only a single argument
	## (which is later proven to be a real file or directory)
	try:
		cmd=sys.argv[2]
		being.printout=False
		if not cmd.startswith('/'):
			cmd=""
	except IndexError:
		cmd="/exit"
		#cmd=""
		being.printout=True

	try:
		if os.path.exists(sys.argv[1]):
			if os.path.isdir(sys.argv[1]):
				text="/corpus "+sys.argv[1]
				#dir_corpus=sys.argv[1]
				skip=True
			else:
				#dir_corpus=os.path.dirname(sys.argv[1])
				basename=os.path.basename(sys.argv[1])
				text="/text "+sys.argv[1]
				if basename[0:2] in languages:
					lang=basename[0:2]
				skip=True
		else:
			print "<error> file not found"
	except:
		## welcome
		print ""
		print "################################################"
		print "## welcome to prosodic!                  v0.2 ##"
		print "################################################"
		print ""
		text=""
		cmd=""



	## start clock
	timestart=time.clock()




	obj=None
	sameobj=None
	while(text!="/exit"):	
	
		if being.om:
			being.omm=being.om
			being.om=''
		#msg="\n########################################################################\n"
		msg="\n\t[please type a line of text, or enter one of the following commands:]\n"
		msg+="\t\t/text\t"+dir_corpus+"[folder/file.txt] or [blank for file-list]\n"
		msg+="\t\t/corpus\t"+dir_corpus+"[folder] or [blank for dir-list]\n"
		msg+="\n"
	
		if text!="":
		
			msg+="\t\t/show\tshow annotations on input\n"
			msg+="\t\t/tree\tsee phonological structure\n"
			msg+="\t\t/query\tquery annotations\n\n"
		
			msg+="\t\t/parse\tparse metrically\n"
		if obj and obj.isParsed:
			msg+="\t\t/scan\tprint out the scanned lines\n"
			msg+="\t\t/report\tlook over the parse outputs\n"
			msg+="\t\t/stats\tget statistics from the parser\n"
			msg+="\t\t/plot\tcompare features against positions\n"
			if being.networkx:
				msg+="\t\t/draw\tdraw finite-state machines\n" 

			msg+="\n"
	
		# msg+="\t\t/config\tchange settings\n"
		if config['print_to_screen']:
			msg+="\t\t/mute\thide output from screen\n"
		else:
			msg+="\t\t/unmute\tunhide output from screen\n"
		msg+="\t\t/save\tsave previous output to file\n"
		msg+="\t\t/exit\texit\n"
		#msg+="#######################################################################\n\n"
		msg+="\n>>["+str(round((time.clock() - timestart),2))+"s] prosodic:"+lang+"$ "
 	
	 	## restart timer
		timestart=time.clock()
	
		## ask for input only if argument not received
		if not skip:
			text=raw_input(msg).strip()
		else:
			skip=False
	
		if text=="/exit":
			for k,v in dict.items():
				#dict[k].save_tabbed()
				dict[k].persist()
				dict[k].close()
			exit()
	
		elif text and text[0]!="/":
			## load line #######
			fn=os.path.join(dir_corpus,'.directinput.txt')
			write(fn,text.replace('//','\n\n').replace('/','\n'))
			obj = Text(fn)
			####################
	
		elif text=="/parse":
			obj.parse()
		
		elif text=="/plot":
			obj.plot()
		
		elif text=="/groom":
			obj.groom()
		
		elif text=="/report":
			obj.report()
	
		elif text=="/chart":
			obj.chart()
		
		elif text=="/stats":
			obj.stats()
		
		elif text=="/scan":
			obj.scansion()
		
		elif text=="/draw":
			if being.networkx:
				obj.genfsms()
				#obj.genmetnet()
		
		elif text=="/tree":
			obj.om(obj.tree()+"\n\n")
	
		elif text=="/show":
			obj.show()
	
	
		elif text=="/query":
			q=""
			while (not q.startswith("/")):
				q=raw_input(">> please type the conjunction of features for which you are searching [type /exit to exit]:\neg: [-voice] (Syllable: (Onset: [+voice]) (Coda: [+voice]))\n\n").strip()
			
				matchcount=0
				try:
					qq=SearchTerm(q)
				except:
					break
				
				for words in obj.words():
					wordobj=words[0]
					for match in wordobj.search(qq):
						matchcount+=1
						if "Word" in str(type(match)):
							matchstr=""
						else:
							matchstr=str(match)
						wordobj.om(makeminlength(str(matchcount),int(being.linelen/6))+"\t"+makeminlength(str(wordobj),int(being.linelen))+"\t"+matchstr)
			
			cmd = q
		
		
		#elif text.startswith('/query'):
		#	print obj.search(SearchTerm(text.replace('/query','').strip()))
		
		elif text=="/try":
			obj=Text('corpora/corppoetry/fi.kalevala2.txt')
			#print obj.tree()
			self.parses=obj.parse()

		
		elif text.startswith('/text'):
			fn=text.replace('/text','').strip()
		
			if not fn:
				for filename in os.listdir(dir_corpus):
					if filename.startswith("."): continue
					if os.path.isdir(os.path.join(dir_corpus,filename)):
						print "\t"+filename+"/"
						files=[]
						for filename2 in glob.glob(os.path.join(os.path.join(dir_corpus,filename), "*.txt")):
							files.append(filename2.replace(dir_corpus,'').replace(filename+'/',''))
						print "\t\t"+" | ".join(files)
						print
					else:
						if filename[-4]==".txt":
							print "\t"+filename
			else:
				if os.path.exists(os.path.join(dir_corpus,fn)):
					obj=Text(os.path.join(dir_corpus,fn))
				elif os.path.exists(fn):
					obj=Text(fn)
				else:
					print "<file not found>\n"
					continue
		
		elif text.startswith('/corpus'):
			from Corpus import Corpus
			fn=text.replace('/corpus','').strip()
		
			if not fn:
				for filename in os.listdir(dir_corpus):
					if filename.startswith("."): continue
					if os.path.isdir(os.path.join(dir_corpus,filename)):
						print "\t"+filename
			else:		
				if os.path.exists(os.path.join(dir_corpus,fn)):
					obj = Corpus(os.path.join(dir_corpus,fn))
				elif os.path.exists(fn):
					obj = Corpus(fn)
				else:
					print "<path not found>\n"
					continue
	
		elif text.startswith('/save'):
			fn=text.replace('/save','').strip()
			if not fn:
				fn=raw_input('\n>> please enter a file name to save output to,\n\t- either as a simple filename in the current working directory ['+os.getcwd()+'],\n\t- or as a full path.\n\n').strip()
		
			try:
				ofn=None
				if os.path.exists(os.path.join(os.path.dirname(fn))):
					ofn=fn
				else:
					ofn=os.path.join(os.getcwd(),fn)
			
				of=open(fn,'w')
				of.write(being.omm)
				of.close()
				print ">> saving previous output to: "+ofn
			except IOError:
				print "** [error: file not saved.]\n\n"
	
	
		elif text.startswith('/mute'):
			if config['print_to_screen']:
				config['print_to_screen']=False
			else:
				config['print_to_screen']=True
	
		elif text.startswith('/unmute'):
			config['print_to_screen']=True
		if cmd:
			text=cmd
			cmd=""
