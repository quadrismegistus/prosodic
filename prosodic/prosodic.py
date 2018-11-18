#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import sys,glob,os,time,codecs
import logging
#logging.basicConfig(level=logging.DEBUG, format='#### %(levelname)s:\n%(message)s\n####\n')
#logging.basicConfig(level=logging.INFO, format='## LOG #############\n%(message)s\n####################\n')
#print '>> importing prosodic...'

#dir_prosodic=sys.path[0]
dir_prosodic=os.path.split(globals()['__file__'])[0]
sys.path.insert(0,dir_prosodic)

dir_mtree=os.path.abspath(os.path.join(dir_prosodic,'..','metricaltree'))
sys.path.append(dir_mtree)

from os.path import expanduser
home = expanduser("~")
dir_prosodic_home=os.path.join(home,'prosodic_data')

## import necessary objects
#toprintconfig=__name__=='__main__'
toprintconfig=False
from tools import *
config=loadConfigPy(toprint=toprintconfig,dir_prosodic=dir_prosodic,dir_home=dir_prosodic_home)

meter_dir_root=os.path.join(dir_prosodic,'meters')
meter_dir_home=os.path.join(dir_prosodic_home,'meters')
config['meters']=loadMeters(meter_dir_root=meter_dir_root,meter_dir_home=meter_dir_home)
METER=config['meter']=config['meters'][config['meter']] if 'meter' in config and config['meter'] else None

dir_corpus=os.path.join(dir_prosodic_home,config['folder_corpora']) if not config['folder_corpora'].startswith('/') else config['folder_corpora']
dir_results=os.path.join(dir_prosodic_home,config['folder_results']) if not config['folder_results'].startswith('/') else config['folder_results']
dir_tagged=os.path.join(dir_prosodic_home,config['folder_tagged_samples']) if not config['folder_tagged_samples'].startswith('/') else config['folder_tagged_samples']

text=''


import entity
from entity import being
being.config=config
from Text import Text
from Corpus import Corpus
from Stanza import Stanza
from Line import Line
from Phoneme import Phoneme
from Word import Word
from WordToken import WordToken
from Meter import Meter
from MaxEnt2 import DataAggregator
from MaxEnt2 import MaxEntAnalyzer
from Meter import get_meter
import ipa
hdrbar="################################################"

## set defaults
languages=['en','fi']
lang=config['lang']

## load defaults
dict={}
for lng in languages:
	dict[lng]=loadDict(lng)
del lng

## etc
def install_stanford_parser(dir_mtree=dir_mtree):
	print '>> INSTALLING STANFORD CORENLP PARSER TO DIRECTORY:',dir_mtree
	os.system('cd '+dir_mtree+' && '+'./get-deps.sh')

## load config
if __name__ != "__main__":
	being.printout=False
	#config['print_to_screen']=0


# else:	## if not imported, go into interactive mode
# 	skip=False
#
# 	## but do not go into interactive mode if only a single argument
# 	## (which is later proven to be a real file or directory)
# 	## ACTUALLY NVERMIND ABOVE: GO INTO INTERACTIVE MODE IF SINGLE ARGUMENT
# 	try:
# 		cmd=sys.argv[1]
# 		config['print_to_screen']=0
# 		being.config['print_to_screen']=0
# 		if not cmd.startswith('/'):
# 			cmd=""
# 	except IndexError:
# 		cmd="/exit"
# 		#cmd=""
# 		being.printout=True
#
# 	try:
# 		arg=sys.argv[1]
# 		if os.path.exists(arg):
# 			if os.path.isdir(arg):
# 				text="/corpus "+arg
# 				#dir_corpus=sys.argv[1]
# 				skip=True
# 			else:
# 				#dir_corpus=os.path.dirname(sys.G[1])
# 				basename=os.path.basename(arg)
# 				text="/text "+arg
# 				if basename[0:2] in languages and basename[2]=='.':
# 					lang=basename[0:2]
# 				skip=True
# 		elif arg=='install':
# 			try:
# 				arg2=sys.argv[2]
# 			except IndexError:
# 				pass
#
# 			if arg2=='stanford_parser':
# 				install_stanford_parser(dir_mtree)
#
# 		else:
# 			print "<error> file not found"
#
#
# 	except:
# 		## welcome
# 		print ""
# 		print "################################################"
# 		print "## welcome to prosodic!                  v1.1 ##"
# 		print "################################################"
# 		print ""
# 		text=""
# 		cmd=""
#
#
#
# 	## start clock
# 	timestart=time.clock()
#
#
#
#
# 	obj=None
# 	sameobj=None
# 	while(text!="/exit"):
#
# 		if being.om:
# 			being.omm=being.om
# 			being.om=''
# 		#msg="\n########################################################################\n"
# 		msg="\n\t[please type a line of text, or enter one of the following commands:]\n"
# 		#msg+="\t\t/text\t"+dir_corpus+"[folder/file.txt] or [blank for file-list]\n"
# 		#msg+="\t\t/corpus\t"+dir_corpus+"[folder] or [blank for dir-list]\n"
# 		msg+="\t\t/text\tload a text\n"
# 		msg+="\t\t/corpus\tload folder of texts\n"
# 		msg+="\t\t/paste\tenter multi-line text\n"
#
# 		msg+="\n"
#
# 		msg+="\t\t/weight\trun maximum entropy on a pipe-delimited file\n"
# 		msg+="\t\t/weight2\trun maximum entropy on a tab-delimited file\n"
# 		try:
# 			learner
# 		except NameError:
# 			pass
# 		else:
# 			if learner != None:
# 				msg+="\t\t/weightsave\tsave the results of the last run of /weight or /weight2 \n"
#
# 		msg+="\n"
#
# 		if obj:
# 			msg+="\t\t/show\tshow annotations on input\n"
# 			if config.get('parse_using_metrical_tree',False): msg+="\t\t/grid\tsee stress grids\n"
# 			msg+="\t\t/tree\tsee phonological structure\n"
# 			msg+="\t\t/query\tquery annotations\n\n"
#
# 			msg+="\t\t/parse\tparse metrically\n"
# 			msg+="\t\t/meter\tset the meter used for parsing\n"
# 			msg+="\t\t/eval\tevaluate this meter against a hand-tagged sample\n\n"
# 			msg+="\t\t/save\tsave previous output to file (except for /weight and /weight2; see /weightsave)\n"
#
# 		if obj and obj.isParsed():
# 			msg+="\t\t/scan\tprint out the scanned lines\n"
# 			msg+="\t\t/report\tlook over the parse outputs\n"
# 			msg+="\t\t/stats\tsave statistics from the parser\n"
# 			#msg+="\t\t/plot\tcompare features against positions\n"
# 			#if being.networkx:
# 			#	msg+="\t\t/draw\tdraw finite-state machines\n"
#
# 			msg+="\n"
#
# 		#msg+="\t\t/config\tchange settings\n"
#
# 		#"""
# 		if config['print_to_screen']:
# 			msg+="\t\t/mute\thide output from screen\n"
# 		else:
# 			msg+="\t\t/unmute\tunhide output from screen\n"
# 		#"""
# 		msg+="\t\t/exit\texit\n"
# 		#msg+="#######################################################################\n\n"
# 		msg+="\n>> ["+str(round((time.clock() - timestart),2))+"s] prosodic:"+lang+"$ "
#
# 	 	## restart timer
# 		timestart=time.clock()
#
# 		## ask for input only if argument not received
# 		if not skip:
# 			try:
# 				text=raw_input(msg).strip().decode('utf-8',errors='ignore')
# 			except (KeyboardInterrupt,EOFError) as e:
# 				text='/exit'
# 		else:
# 			skip=False
#
# 		if text=="/exit":
# 			for k,v in dict.items():
# 				#dict[k].save_tabbed()
# 				dict[k].persist()
# 				dict[k].close()
# 			print
# 			print ">> goodbye."
# 			exit()
#
# 		elif text and text[0]!="/":
# 			## load line #######
# 			obj = Text(text,lang=lang)
# 			####################
#
# 		elif text.startswith('/paste'):
# 			print ">> enter or paste your content here. press Ctrl-D when finished."
# 			contents = []
# 			while True:
# 				try:
# 					line = raw_input("").decode('utf-8',errors='ignore')
# 					contents.append(line)
# 				except EOFError:
# 					break
# 				except KeyboardInterrupt:
# 					contents=[]
# 					break
#
# 			if contents:
# 				txt="\n".join(contents)
# 				obj=Text(txt,lang=lang)
#
# 		elif text=="/parse":
# 			obj.parse(meter=METER)
#
# 		elif text.startswith("/weight"):
#
# 			# Check if learner is defined
# 			try:
# 				learner
# 			except NameError:
# 				learner = None
#
# 			if text.startswith("/weightsave"):
# 				if not learner:
# 					print "Cannot save weights as no weights have been trained. First train the MaxEnt learner with /weight or /weight2"
# 				else:
# 					# save the weights to a file
# 					fn=text.replace('/weightsave','').strip()
# 					if not fn:
# 						fn=raw_input('\n>> please enter a file name to save output to,\n\t- either as a simple filename in the default directory ['+config['folder_results']+'],\n\t- or as a full path.\n\n').strip()
#
# 					try:
# 						ofn=None
# 						dirname=os.path.dirname(fn)
# 						if dirname:
# 							ofn=fn
# 						else:
# 							dirname=config['folder_results']
# 							ofn=os.path.join(dirname,fn)
#
# 						if not os.path.exists(dirname): os.makedirs(dirname)
# 						of=codecs.open(ofn,'w',encoding='utf-8')
# 						output_str = learner.generate_save_string()
# 						of.write(output_str)
# 						of.close()
# 						print ">> saving weights to: "+ofn
# 					except IOError as e:
# 						print e
# 						print "** [error: file not saved.]\n\n"
#
# 			else:
# 				if text.startswith("/weight2"):
# 					data_path = text[len("/weight2 "):]
# 					if data_path == "" or data_path is None:
# 						print "You must enter the filename after the command i.e., /weight2 <filename>"
# 						continue
# 					aggregator = data_aggregator = DataAggregator(METER, data_path, lang, True)
#
# 				else:
# 					data_path = text[len("/weight "):]
# 					if data_path == "" or data_path is None:
# 						print "You must enter the filename after the command i.e., /weight <filename>"
# 						continue
# 					data_aggregator = DataAggregator(METER, data_path, lang)
#
#
# 				learner = MaxEntAnalyzer(data_aggregator)
#
# 				step_size = float(config['step_size'])
# 				negative_weights_allowed = bool(config['negative_weights_allowed'])
# 				max_epochs = int(config['max_epochs'])
# 				gradient_norm_tolerance = float(config['gradient_norm_tolerance'])
#
# 				learner.train(step = step_size, epochs=max_epochs, tolerance=gradient_norm_tolerance, only_positive_weights=not negative_weights_allowed)
# 				learner.report()
#
# 		elif text=="/plot":
# 			obj.plot()
#
# 		elif text=="/groom":
# 			obj.groom()
#
# 		elif text.startswith("/report") and obj.isParsed():
# 			arg=' '.join(text.split()[1:]) if len(text.split())>1 else None
# 			include_bounded = arg=='all'
# 			obj.report(meter=METER, include_bounded=include_bounded)
# 			print '\t>> options:\n\t\t/report\t\treport unbounded, metrical parses\n\t\t/report all\treport all parses, including those bounded or unmetrical'
#
# 		elif text=="/chart":
# 			obj.chart()
#
# 		elif text.startswith("/stats") and obj.isParsed():
# 			arg=' '.join(text.split()[1:]) if len(text.split())>1 else None
# 			funcname = None
# 			if arg=='lines':
# 				funcname='stats_lines'
# 			elif arg=='pos':
# 				funcname='stats_positions'
# 			elif arg=='all':
# 				funcname='stats'
# 			elif arg=='ot':
# 				funcname='stats_lines_ot'
#
# 			if funcname:
# 				func=getattr(obj,funcname)
# 				for dx in func(meter=METER,all_parses=False):
# 					pass
#
# 			print '\t>> options:\n\t\t/stats all\t\tsave all stats\n\t\t/stats lines\t\tsave stats on lines\n\t\t/stats ot\t\tsave stats on lines in OT/maxent format\n\t\t/stats pos\t\tsave stats on positions'
#
# 		elif text=="/scan" and obj.isParsed():
# 			obj.scansion(meter=METER)
#
# 		elif text=="/draw":
# 			try:
# 				obj.genfsms(meter=METER)
# 				#obj.genmetnet()
# 			except ImportError:
# 				raise Exception("Loading of networkx failed. Please install networkx: pip install networkx")
#
#
# 		elif text=="/tree":
# 			obj.om(obj.tree()+"\n\n",conscious=False)
# 			#print obj.tree()
# 			print
#
# 		elif text=="/grid":
# 			grid=obj.grid()
# 			obj.om("\n"+grid+"\n",conscious=False)
# 			print
#
# 		elif text=="/show":
# 			obj.show()
#
# 		elif text.startswith("/meter"):
# 			tl = text.split()
# 			arg=None
# 			if len(tl)>1:
# 				arg=' '.join(tl[1:])
# 				if not arg.isdigit(): arg=None
#
# 			mnum2name={}
# 			for mi,(mname,mmeter) in enumerate(sorted(config['meters'].items())):
# 				mnum=mi+1
# 				mnum2name[mnum]=mname
# 				#print '>> meter #'+str(mnum)+': '+mname
# 				if not arg:
# 					print '[#'+str(mnum)+']'
# 					print mmeter
# 					#print '\t>> id:',mname
# 					#print '\t>> name:',msettings['name']
# 					#print '\t>> constraints:'
# 					#for cname in sorted(msettings['constraints']):
# 					#	print '\t\t>>',cname
# 					print
#
# 			if arg and arg.isdigit():
# 				meteri=int(arg)
# 			else:
# 				try:
# 					meteri = raw_input('>> please type the number of the meter you would like to use.\n').strip()
# 				except (KeyboardInterrupt,EOFError) as e:
# 					continue
#
# 				if not meteri.isdigit():
# 					print '>> not a number. meter not selected.'
# 					continue
#
# 				meteri=int(meteri)
# 			config['meter']=mnum2name[meteri]
# 			METER = config['meters'][config['meter']]
# 			print '>> meter set to ['+METER.id+']: '+METER.name
#
#
#
#
#
# 		elif text=="/query":
# 			q=""
# 			while (not q.startswith("/")):
# 				try:
# 					q=raw_input(">> please type the conjunction of features for which you are searching [type / to exit]:\neg: [-voice] (Syllable: (Onset: [+voice]) (Coda: [+voice]))\n\n").strip()
# 				except (KeyboardInterrupt,EOFError) as e:
# 					text=''
# 					break
#
# 				matchcount=0
# 				try:
# 					qq=SearchTerm(q)
# 				except:
# 					break
#
# 				for words in obj.words(flattenList=False):
# 					wordobj=words[0]
# 					for match in wordobj.search(qq):
# 						matchcount+=1
# 						if "Word" in str(type(match)):
# 							matchstr=""
# 						else:
# 							matchstr=str(match)
# 						wordobj.om(makeminlength(str(matchcount),int(being.linelen/6))+"\t"+makeminlength(str(wordobj),int(being.linelen))+"\t"+matchstr, conscious=False)
#
# 			cmd = q
#
#
# 		#elif text.startswith('/query'):
# 		#	print obj.search(SearchTerm(text.replace('/query','').strip()))
#
# 		elif text=="/try":
# 			obj=Text('corpora/corppoetry/fi.kalevala2.txt')
# 			#print obj.tree()
# 			self.parses=obj.parse()
#
#
# 		elif text.startswith('/text'):
# 			fn=text.replace('/text','').strip()
#
# 			if not fn:
# 				for filename in os.listdir(dir_corpus):
# 					if filename.startswith("."): continue
# 					if os.path.isdir(os.path.join(dir_corpus,filename)):
# 						print "\t"+filename+"/"
# 						files=[]
# 						for filename2 in glob.glob(os.path.join(os.path.join(dir_corpus,filename), "*.txt")):
# 							files.append(filename2.replace(dir_corpus,'').replace(filename+'/',''))
# 						print "\t\t"+" | ".join(files)
# 						print
# 					else:
# 						if filename[-4]==".txt":
# 							print "\t"+filename
#
# 				print
# 				print "\t" + hdrbar
# 				#print ">> to load a text, please either:"
# 				print "\t>> select from one of the relative paths above:"
# 				print "\t     i.e. /text [foldername]/[filename.txt]"
# 				print "\t     e.g. /text shakespeare/sonnet-001.txt"
# 				print "\t>> or use an absolute path to a text file on your disk:"
# 				print "\t     e.g. /text /absolute/path/to/file.txt"
# 				print "\t" + hdrbar
# 				print
#
# 			else:
# 				if os.path.exists(os.path.join(dir_corpus,fn)):
# 					obj=Text(os.path.join(dir_corpus,fn))
# 				elif os.path.exists(fn):
# 					obj=Text(fn)
# 				else:
# 					print "<file not found>\n"
# 					continue
#
# 		elif text.startswith('/corpus'):
# 			from Corpus import Corpus
# 			fn=text.replace('/corpus','').strip()
#
# 			if not fn:
# 				for filename in os.listdir(dir_corpus):
# 					if filename.startswith("."): continue
# 					if os.path.isdir(os.path.join(dir_corpus,filename)):
# 						print "\t"+filename
#
#
# 				print
# 				print "\t" + hdrbar
# 				#print ">> to load a text, please either:"
# 				print "\t>> select from one of the relative paths above:"
# 				print "\t     i.e. /corpus [foldername]"
# 				print "\t     e.g. /corpus yeats"
# 				print "\t>> or use an absolute path to a folder of text files on your disk:"
# 				print "\t     e.g. /corpus /absolute/path/to/folder/of/text/files"
# 				print "\t" + hdrbar
# 				print
#
# 			else:
# 				if os.path.exists(os.path.join(dir_corpus,fn)):
# 					obj = Corpus(os.path.join(dir_corpus,fn))
# 				elif os.path.exists(fn):
# 					obj = Corpus(fn)
# 				else:
# 					print "<path not found>\n"
# 					continue
#
# 		elif text.startswith('/save'):
# 			fn=text.replace('/save','').strip()
# 			if not fn:
# 				fn=raw_input('\n>> please enter a file name to save output to,\n\t- either as a simple filename in the default directory ['+config['folder_results']+'],\n\t- or as a full path.\n\n').strip()
#
# 			try:
# 				ofn=None
# 				dirname=os.path.dirname(fn)
# 				if dirname:
# 					ofn=fn
# 				else:
# 					dirname=config['folder_results']
# 					ofn=os.path.join(dirname,fn)
#
# 				if not os.path.exists(dirname): os.makedirs(dirname)
# 				of=codecs.open(ofn,'w',encoding='utf-8')
# 				if type(being.omm) in [str]:
# 					being.omm=being.omm.decode('utf-8',errors='ignore')
# 				of.write(being.omm)
# 				of.close()
# 				print ">> saving previous output to: "+ofn
# 			except IOError:
# 				print "** [error: file not saved.]\n\n"
#
# 		elif text.startswith('/eval'):
# 			path=os.path.join(dir_prosodic,config['folder_tagged_samples'])
# 			fn=None
#
# 			if not fn:
# 				fns=[]
# 				for _fn in os.listdir(path):
# 					if _fn.startswith('.'): continue
# 					if '.evaluated.' in _fn: continue
# 					fn_i=len(fns)
# 					fns+=[_fn]
# 					print '[{0}] {1}'.format(fn_i+1, _fn)
# 				inp=raw_input('\n>> please enter the number of the file to use as evaluation data:\n').strip()
# 				if not inp.isdigit():
# 					print '<<invalid: not a number>>'
# 					continue
#
# 				fn_i=int(inp)-1
# 				fn=fns[fn_i]
#
# 			key_line = raw_input('\n>> please enter the column name in the file for the column of lines to parse: [default: line]\n').strip()
# 			if not key_line: key_line='line'
#
# 			key_parse = raw_input('\n>> please enter the column name in the file for the column of hand-done parses (using "s" for metrically strong syllables, "w" for metrically weak ones): [default: parse]\n').strip()
# 			if not key_parse: key_parse='parse'
#
# 			key_meterscheme = raw_input('\n>> [optional, will use if present] please enter the column name in the file for the column indicating the metrical template in the poem (anapestic, dactylic, iambic, or trochaic): [default: Meter Scheme]\n').strip()
# 			if not key_meterscheme: key_meterscheme='Meter Scheme'
#
# 			assess(os.path.join(path,fn), key_meterscheme=key_meterscheme, key_parse=key_parse, key_line=key_line, meter=METER)
#
#
# 		elif text.startswith('/mute'):
# 			being.config['print_to_screen']=0
#
# 		elif text.startswith('/unmute'):
# 			being.config['print_to_screen']=1
#
# 		if cmd:
# 			text=cmd
# 			cmd=""
