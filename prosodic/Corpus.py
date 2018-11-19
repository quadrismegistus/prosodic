import glob,os
from entity import entity,being
from tools import *
from Text import Text


class Corpus(entity):

	def __init__(self,corpusRoot,lang=None,printout=None,corpusFiles="*.txt",phrasebreak=',;:.?!()[]{}<>',limWord=None):
		import prosodic
		## entity-shared attribtues

		self.lang=prosodic.config['lang'] if not lang else lang
		self.dict=prosodic.dict[self.lang]
		self.parent=False
		#self.foldername=corpusRoot.split("/").pop().strip()
		self.children=[]	# texts
		self.feats = {}
		self.featpaths={}
		self.finished = False
		self.config=prosodic.config
		self.meter=None
		if printout==None: printout=being.printout

		## corpus attributes
		self.corpusRoot = corpusRoot
		self.corpusFiles = corpusFiles
		self.name=os.path.split(os.path.abspath(self.corpusRoot))[-1]
		self.foldername=self.name
		self.dir_results = prosodic.dir_results

		## language may be **, ie, determinable by the first two character of the textfile ("en" for english, "fi" for finnish, etc)
		if not lang:
			lang=being.lang
		self.lang = lang

		## [loop] through filenames
		for filename in sorted(glob.glob(os.path.join(corpusRoot, corpusFiles))):
			## create and adopt the text
			newtext = Text(filename,printout=printout)
			self.newchild(newtext)	# append Text to children


	def parse(self,meter=None,arbiter='Line',num_processes=1):
		if not meter and self.meter: meter=self.meter

		# if num_processes>1:
		# 	#print '!! MULTIPROCESSING PARSING IS NOT WORKING YET !!'
		# 	import multiprocessing as mp
		# 	pool = mp.Pool(num_processes)
		# 	objects = [(text,meter,arbiter) for text in self.children]
		# 	jobs = [pool.apply_async(parse_text,(text,meter,arbiter)) for x in objects]
		# 	for j in jobs:
		# 		j.get()
		#else:
		for text in self.children:
			text.parse(meter=meter,arbiter=arbiter)
			if not meter: self.meter=meter=text.meter

	def report(self,meter=None,include_bounded=False):
		for text in self.children:
			print
			print '>> text:',text.name
			text.report(meter=meter,include_bounded=include_bounded)

	def scansion(self,meter=None):
		for text in self.children:
			print '>> text:',text.name
			text.scansion(meter=meter)
			print

	def get_meter(self,meter=None):
		if not meter:
			child=self.children[0] if self.children else None
			if self.meter:
				meter=self.meter
			elif child and hasattr(child,'_Text__bestparses') and child.__bestparses:
				return self.get_meter(sorted(child.__bestparses.keys())[0])
			else:
				import Meter
				meter=Meter.genDefault()
		elif type(meter) in [str,unicode]:
			meter= self.config['meters'][meter]
		else:
			pass

		return meter

	def stats(self,meter=None,all_parses=False,funcs=['stats_lines','stats_lines_ot','stats_positions']):
		for funcname in funcs:
			func=getattr(self,funcname)
			for dx in func(meter=meter,all_parses=all_parses):
				yield dx


	def stats_lines(self,meter=None,all_parses=False):
		meter=self.get_meter(meter)

		def _writegen():
			for text in self.children:
				for dx in text.stats_lines(meter=meter):
					dx['header']=['text']+dx['header']
					yield dx

		ofn=os.path.join(self.dir_results, 'stats','corpora',self.name, self.name+'.lines.'+('meter='+meter.id if meter else 'unknown')+'.csv')
		if not os.path.exists(os.path.split(ofn)[0]): os.makedirs(os.path.split(ofn)[0])
		for dx in writegengen(ofn, _writegen): yield dx
		print '>> saved:',ofn

	def isParsed(self):
		#return (not False in [bool(_poemline.isParsed()) for _poemline in self.lines()])
		return not (False in [child.isParsed() for child in self.children])

	def stats_lines_ot(self,meter=None,all_parses=False):
		meter=self.get_meter(meter)

		def _writegen():
			for text in self.children:
				for dx in text.stats_lines_ot(meter=meter):
					#dx['text']=text.name
					#dx['corpus']=self.name
					dx['header']=['text']+dx['header']
					yield dx

		ofn=os.path.join(self.dir_results, 'stats','corpora',self.name, self.name+'.lines_ot.'+('meter='+meter.id if meter else 'unknown')+'.csv')
		if not os.path.exists(os.path.split(ofn)[0]): os.makedirs(os.path.split(ofn)[0])
		for dx in writegengen(ofn, _writegen): yield dx
		print '>> saved:',ofn

	def grid(self,nspace=10):
		grid=[]
		for text in self.children:
			textgrid=text.grid(nspace=nspace)
			if textgrid:
				grid+=['## TEXT: '+text.name+'\n\n'+textgrid]
		return '\n\n\n'.join(grid)


	def stats_positions(self,meter=None,all_parses=False):

		def _writegen():
			for text in self.children:
				for dx in text.stats_positions(meter=meter,all_parses=all_parses):
					#dx['text']=text.name
					#dx['corpus']=self.name
					dx['header']=['text']+dx['header']
					yield dx

		ofn=os.path.join(self.dir_results, 'stats','corpora',self.name, self.name+'.positions.csv')
		if not os.path.exists(os.path.split(ofn)[0]): os.makedirs(os.path.split(ofn)[0])
		for dx in writegengen(ofn, _writegen): yield dx
		print '>> saved:',ofn


	def sentences(self):
		return [sent for text in self.children for sent in text.sentences()]

def parse_text(text,meter,arbiter):
	text.parse(meter=meter,arbiter=arbiter)
