from __future__ import division

# call make_artist with a list of the locations of the texts
# this will return a dictionary to some stuff keyed by an index for each text

from collections import defaultdict

profile_stats={}


therange=range(2,10)

profile_eg={}
for i in therange:
	profile_eg[i]={}

def pattern2croll(p):
	return [(len(p)-ei) for (ei,ex) in enumerate(p) if ex==1]			

def pattern2croll_str(p):
	return "-".join(str(x) for x in pattern2croll(p))

# range: the range of windows to be considered
# start: how the window must start. 1 if stressed, 0 if unstressed, None if either
def make_artist(texts, range=therange, start=1):
	result = {}
	ind = 0
	for i in range:
		dict = defaultdict(zero_vector_2)
		for text in texts:
			add_profile(text, dict, i, start)
		result[i] = dict_to_ratios(dict)
	return result

def top(lst, min=1):
	result = []
	for x in lst:
		if x[1] > min:
			result.append(x)
	result.sort()
	return result

def print_top(lst, min=1):
	x = top(lst, min)
	for pattern in x:
			print str(pattern[0]) + ": %.2f," % pattern[1],

def print_top2(l,min=1):
	for p,v in sorted(l,key=lambda lx: -lx[1]):
		if v<min: break
		print p,"\t",v

def print_artist(x, min = 1.1):
	for i in x.keys():
		print i
		print_top2(x[i], min)
		print
	print


def sorted_dict(adict, max_num=-1):
	items = adict.items()
	items.sort(key = lambda items:items[1], reverse=True)
	results = [(key, val) for key, val in items]
	if max_num == -1:
		max_num = len(results)
	return results[:max_num]

def get_profile(lineobj, start, num_sylls):
	profile = []
	profile_str=[]
	#line=lineobj.syllables()
	#for syll in line[start:start+num_sylls]:
	#	profile.append(1 if syll.feats['prom.stress']==1.0 else 0)
	
	for WorS in lineobj.str_meter()[start:start+num_sylls]:
		profile.append(1 if WorS=='s' else 0)
	ptup=tuple(profile)
	return ptup
	

# def add_line_profile(stanza, dict, num_sylls, start):
# 	global profile_stats
# 	try:
# 		line=stanza.syllables()
# 		for i in range(len(line)-num_sylls):
# 			profile = get_profile(lineobj, i, num_sylls)
# 			if not len(profile): continue
# 			if start == None or profile[0] == start:
# 				dict[profile][0] += 1
# 		profile = get_profile(lineobj, len(line)-num_sylls, num_sylls)
# 		if start == None or profile[0] == start:
# 			dict[profile][1] += 1
# 	except:
# 		pass

def add_line_profile(stanza, dict, num_sylls, start):
	lineobj=stanza
	#print stanza.lines()
	
	breakpoints=[]
	breakpoint=0
	for l in stanza.lines():
		lenl=len(l.syllables())
		breakpoints+=[lenl+breakpoint]
		breakpoint+=lenl
	#print breakpoints
	try:
		line=stanza.syllables()
		
		## MID-SENTENCE STATS
		for i in range(len(line)-num_sylls):
			
			good=False
			prange=range(i,i+num_sylls)
			for bpoint in breakpoints:
				if bpoint in prange and (bpoint-1) in prange:
					break
			else:
				good=True
			if not good: continue
			
			
			profile = get_profile(lineobj, i, num_sylls)
			if not len(profile): continue
			#if profile[0]==1:
			if start == None or profile[0] == start:
				dict[profile][0] += 1
		
		
		## END OF SENTENCE STATS
		good=False
		i=len(line)-num_sylls
		prange=range(i,i+num_sylls)
		for bpoint in breakpoints:
			if bpoint in prange and (bpoint-1) in prange:
				break
		else:
			good=True
		if good:
			profile = get_profile(lineobj, i, num_sylls)
			# if profile[0]==1:
			if start == None or profile[0] == start:
				dict[profile][1] += 1
	except:
		pass

def add_profile(text, dict, num_sylls, start):
	import prosodic
	prosodic.config['print_to_screen']=0
	for stanza in text.stanzas():
		try:
			if True in [line.broken for line in stanza.children]:
				continue
			
			for parse in [line.bestParse() for line in stanza.children]:
				if not parse:
					goodness=False
					break
			else:
				goodness=True
			
			if not goodness: continue
		except:
			continue
		
		sylls = stanza.syllables()
		if len(sylls) <= num_sylls: continue
		
			
		add_line_profile(stanza, dict, num_sylls, start)

def dict_to_ratios(dict):
	total_sentence = 0
	total_ending = 0
	for k in dict:
		total_sentence += dict[k][0]
		total_ending += dict[k][1]
	ratios = {}
	for k in dict:
		try:
			ratios[k] = (dict[k][1]/total_ending)/(dict[k][0]/total_sentence)
			
			#print k, 'OBS:', dict[k][1], total_ending, (dict[k][1]/total_ending), 'EXP:', (dict[k][0]), (total_sentence), (dict[k][0]/total_sentence)
			
		except ZeroDivisionError:
			pass
			#ratios[k] = None
		
	return sorted_dict(ratios)

def zero_vector_2():
	return [0, 0]

def get_profiled_lines(t, profile):
	for line in t.lines():
		if get_profile(line.syllables(), len(line.syllables())-len(profile), len(profile)) == profile:
			print line
			


if __name__ == '__main__':
	import sys
	corpusfolder=sys.argv[1]
	
	stats={}
	for i in therange:
		stats[i]=[]
	
	import os,random
	from prosodic import *
	import prosodic
	prosodic.config['print_to_screen']=0
	
	pattern_totals={}
	
	numtrials=100
	numtextspertrial=1
	
	for trial in range(numtrials):
		texts=[Text(os.path.join(corpusfolder,fn)) for fn in random.sample(os.listdir(corpusfolder),numtextspertrial)]
		[text.parse() for text in texts]
	
		artist=make_artist(texts)
		for i in artist:
			for p,v in artist[i]:
				pc=pattern2croll_str(p)
				if pc[0]!=str(i): continue
				
				print i,pc,v
				
				d={'pattern':pc, 'oe':v}
				stats[i]+=[ d ]

	import pickle
	pickle.dump(stats, open('stats.pickle','wb'))
	exit()

	import rpyd2
	for i in stats:
		r=rpyd2.RpyD2([d for d in stats[i]])
		r.plot(fn='cadences-length-'+str(i).zfill(4)+'.',
			x='pattern',
			y='oe',
			title='Cadences of '+str(i)+' syllables in length, measured for their observed/expected appearance at ends of sentences',
			boxplot=True,group='pattern',col='pattern',point=True,smooth=False,flip=True)
	
	exit()
	o=[]
	for p,count in sorted(profile_stats.items(),key=lambda lx: -lx[1]):
		#print p,"\t",count
		o+=[ [str(p),str(count)] ]

	import pytxt
	pytxt.write('cadence-stats.txt',o,toprint=True)
	
	for i in profile_eg:
		o=[]
		lines=1000
		line=0
		for p,count in sorted(profile_eg[i].items(),key=lambda lx: -lx[1]):
			#print p,"\t",count
			line+=1
			o+=[ [str(p),str(count)] ]
			if line>lines: break
	
		pytxt.write('cadence-egs.'+str(i).zfill(2)+'.txt',o,toprint=True)