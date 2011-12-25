import glob,os
from entity import entity,being
from tools import *
from Text import Text


class Corpus(entity):
	def __init__(self,corpusRoot,lang=None,printout=None,corpusFiles="*.txt",phrasebreak=',;:.?!()[]{}<>',limWord=None):
		## entity-shared attribtues
		
		dict=being.dict
		self.dict=dict
		self.parent=False
		#self.foldername=corpusRoot.split("/").pop().strip()
		self.children=[]	# texts
		self.feats = {}
		self.featpaths={}
		self.finished = False
		if printout==None: printout=being.printout
		
		## corpus attributes
		self.corpusRoot = corpusRoot
		self.corpusFiles = corpusFiles
		self.name=os.path.split(os.path.abspath(self.corpusRoot))[-1]
		self.foldername=self.name
		
		## language may be **, ie, determinable by the first two character of the textfile ("en" for english, "fi" for finnish, etc)
		if not lang:
			lang=being.lang
		self.lang = lang
		
		## [loop] through filenames
		for filename in glob.glob(os.path.join(corpusRoot, corpusFiles)):
			## create and adopt the text
			newtext = Text(filename,printout=printout)			
			self.newchild(newtext)	# append Text to children

