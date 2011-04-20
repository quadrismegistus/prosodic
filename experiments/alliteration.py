"""
alliteration.py
	This file reads in Shakespeare's sonnets,
	and ranks for each poem,
	consononantal phonemes in order of their alliterativity.
"""
from __future__ import division
import sys
sys.path.append('/Users/ryan/Projects/prosodic/')
from prosodic import *
sys.path.append('/Lab/Code/python')
import pystats
from operator import itemgetter
shak = Text('/Users/ryan/Projects/prosodic/corpora/corppoetry_en/en.test.txt')

for stanza in shak.stanzas():
	brk=False
	for l in stanza.lines():
		if l.broken: brk=True
	if brk: continue
	
	phonemes=stanza.phonemes()
	#for onset in stanza.onsets():
	#	phonemes.extend(onset.phonemes())
	phontypes=set(phonemes)
	
	print stanza.lines()
	print phonemes
	print phontypes
	print
	phondict={}
	for phon in phontypes:
		if not phon.feature('cons'): continue
		#print phon.__dict__
		phondict[phon]=[]
	
	i=-1
	for phon in phonemes:
		i+=1
		try:
			phondict[phon].append(i)
		except:
			continue
	
	for phon in phondict:
		sumdist=[]
		
		print phon
		print phondict[phon]
		
		for x in phondict[phon]:
			for y in phondict[phon]:
				#print abs(x-y)
				divisor=(abs(x-y))
				if not divisor: continue
				sumdist+=[1/divisor]
		try:
			phondict[phon]=(sum(sumdist))
		except ZeroDivisionError:
			phondict[phon]=0
	
	
	print sorted(phondict.items(),key=itemgetter(1),reverse=True)
	print sorted(pystats.zfy(phondict).items(),key=itemgetter(1),reverse=True)
	print