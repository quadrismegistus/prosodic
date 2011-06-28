from __future__ import division
"""
Handles sentence parsing procedures.
"""

PARSE='/Lab/Tools/bin/parse'
import os,pytxt

def getSents(ifn):
	f=open(ifn)
	t=str(f.read())
	f.close()
	sents=t.split('<sentence ')
	return sents[1:]

def getNumWords(sentence):
	return len(sentence.split('<word>'))-1
	
def parsetxt(txt):
	import pytxt
	fn=pytxt.write_tmp(txt,suffix='.txt')
	return parse(fn)
	
def parse(fn):
	import subprocess
	re=subprocess.call([PARSE,fn])


def parse2grid(ifn,ldlim=None,shuffle=False):
	ofn=os.path.basename(ifn)
	f=open(ifn)
	t=str(f.read())
	f.close()
	sents=t.split('<sentence ')
	
	if shuffle:
		import random
		random.shuffle(sents)
	
	sentnum=0
	
	ld=[]
	for sentence in sents[1:]:
		sentnum+=1
		
		if ldlim and sentnum>ldlim: break
		parse=sentence.split('<parse>')[1].split('</parse>')[0]
		pdat=parse.split()
		wordi=0
		
		pstack=[]
		words=[]
		for pnum in range(len(pdat)):
			p=pdat[pnum]
			
			if p.startswith('('):		# is tag
				pstack.append((p,0))
			else:						# is word
				## get word stats
				wordi+=1
				word=p.replace(')','')
				words+=[word]
				stresslevel=0
				
				## go through tags in stack according to the number of tags which closed
				num_closing_paren=p.count(')')
				for i in range(num_closing_paren):
					pt=pstack.pop()
					if pt[1]>0:		# if more than one word since this tag began:
						stresslevel+=1
				
				## add 1 to all remaining tags
				for i in range(len(pstack)):
					pstack[i]=(pstack[i][0],pstack[i][1]+1)
				
				## add this word to LD
				d={}
				d['wordnum']=wordi
				d['word']=word
				d['stresslevel']=stresslevel
				d['sentnum']=str(sentnum).zfill(3)
				ld.append(d)
		
		print " ".join(words)	
		
	return ld
				

def parse2tree(ifn,ldlim=None,shuffle=False):
	ofn=os.path.basename(ifn)
	f=open(ifn)
	t=str(f.read())
	f.close()
	sents=t.split('<sentence ')

	if shuffle:
		import random
		random.shuffle(sents)

	sentnum=0
	import networkx as nx
	noderoot=None
	
	
	ld=[]
	for sentence in sents[1:]:
		sentnum+=1
		G=nx.DiGraph()
		if ldlim and sentnum>ldlim: break
		parse=sentence.split('<parse>')[1].split('</parse>')[0]
		
		print parse
		
		pdat=parse.split()
		wordi=0
		pnumi=-1

		pstack=[]
		words=[]
		wordnodes=[]
		for pnum in range(len(pdat)):
			p=pdat[pnum]
			pnumi+=1
			
			pnop=p.replace('(','').replace(')','')
			if not pytxt.noPunc(pnop): continue
			pnode=(pnumi,pnop)
			
			## lay first stone
			if not len(pstack):
				pstack.append(pnode)
				noderoot=pnode
				continue
			
			
			## make sure maximally binary
			if len(G.edge):
				edges_already=sorted(G.edge[pstack[-1]].keys())
				
				if len(edges_already)>1:
					print edges_already
					
					#newnode=(pnumi+0.1,'NODE')
					newnode=(str(pnumi)+"b",'NODE')
					G.add_edge(pstack[-1],newnode,type='real',prom=None,weight=0)
					for e in edges_already[1:]:
						G.remove_edge(pstack[-1],e)
						G.add_edge(newnode,e,type='real',prom=None,weight=0)
					pstack.pop()
					pstack.append(newnode)
			
			G.add_edge(pstack[-1],pnode,weight=0,type='real',prom=None)
			
			if p.startswith('('):		# is tag	
				#G.edge[pstack[-1]][pnode]['isFinal']=False
				pstack.append(pnode)
			else:						# is word
				#G.edge[pstack[-1]][pnode]['isFinal']=True
			
				## get word stats
				word=p.replace(')','')
				
				words+=[word]
				wordnodes+=[pnode]
				stresslevel=0

				## go through tags in stack according to the number of tags which closed
				num_closing_paren=p.count(')')
				for i in range(num_closing_paren):
					pt=pstack.pop()
		
		for node in G.nodes():
			if node in wordnodes:
				G.node[node]['type']='word'
				G.node[node]['color']='green'
			else:
				G.node[node]['type']='nonword'
		
		G=treeStress(G)
		#G=treeAlign(G)
		#G.graph['nodesep']=0.5
		
		for node in wordnodes:
			path=nx.shortest_path(G,noderoot,node)
			print node, pathsum(G,path)
		

		pyd=nx.to_pydot(G)
		pyd.write_png('test.png')
		#pyd.set_rankdir('LR')
		exit()

		#print " ".join(words)	

	return ld

def tree2grid(G):
	pass

def pathsum(G,path,attr='prom',avg=True):
	ea=None
	psum=[]
	for eb in path:
		if ea:
			psum+=[G.edge[ea][eb][attr]]
		ea=eb
	print psum,
	
	psum=[px for px in psum if px!=None]
	if avg:
		return sum(psum)/len(psum)
	return sum(psum)
		
	

def treeStress(G,edgeFrom=None):
	if not edgeFrom:
		edgeLast=None
		for edge in sorted(list( set( [e[0] for e in G.edges()] ) )):
			G.edge[edge]=treeStress(G,edgeFrom=edge)
	else:
		edges=G.edge[edgeFrom]
		edgesReal=[e for e in G.edge[edgeFrom] if G.edge[edgeFrom][e]['type']!='graphic']
		if len(edgesReal)>1:
			edgei=0
			edgeL=None
			for edge in sorted(edges):
				if G.edge[edgeFrom][edge]['type']=='graphic': continue
				edgei+=1
				
				heavy=(edgei==len(edgesReal))
				
				if heavy:
					G.edge[edgeFrom][edge]['weight']=0
					G.edge[edgeFrom][edge]['label']='+'
					G.edge[edgeFrom][edge]['color']='blue'
					G.edge[edgeFrom][edge]['prom']=1
				else:
					G.edge[edgeFrom][edge]['weight']=0
					G.edge[edgeFrom][edge]['prom']=0
					G.edge[edgeFrom][edge]['label']='-'
					G.edge[edgeFrom][edge]['color']='red'
				G.edge[edgeFrom][edge]['minlen']=1
				
				if edgeL:
					G.add_edge(edgeL,edge,type='graphic',weight=1,prom=None,label='',color='white',minlen=0)
					#G.add_edge(edge,edgeL,type='graphic',weight=0,label='',color='green')
				edgeL=edge

		return edges
	
	return G

# def treeAlign(G,edgeFrom=None):
# 	if not edgeFrom:
# 		edgeLast=None
# 		for edge in sorted(list( set( [e[0] for e in G.edges()] ) )):
# 			G.edge[edge]=treeAlign(G,edgeFrom=edge)
# 	else:
# 		edges=[e for e in G.edge[edgeFrom].keys() if G.edge[]
# 		if len(edges)>1:
# 			edgei=0
# 			edgeL=None
# 			for edge in sorted(edges):
# 				edgei+=1
# 				if edgeL:
# 					G.add_edge(edgeL,edge,type='graphic',weight=0,label=edgeFrom,color='green')
# 				edgeL=edge
# 
# 		return edges
# 	return G
	

def parse2lines(fn):
	#ifn=sys.argv[1]
	ifn='/Lab/Projects/sentence/parsed/middlemarch.txt.xml'
	ofn=os.path.basename(ifn)
	f=open(ifn)
	t=str(f.read())
	f.close()
	sents=t.split('<sentence ')

	ldlim=100
	for nn in range(30,31):
		ld=[]
		dl={}
		df=None
		o=[]
		sentnum=0
		random.shuffle(sents)
		print nn, "?"
		for sentence in sents[1:]:
			tokens=[]
			for token in sentence.split('<word>')[1:]:
				token=token.split('</word>')[0]
				tokens+=[token]

			if len(tokens)!=nn: continue

			try:
				x=[unicode(bb) for bb in tokens]
			except UnicodeDecodeError:
				continue

			sentnum+=1
			if ldlim and sentnum>ldlim: break
			parse=sentence.split('<parse>')[1].split('</parse>')[0]
			pdat=parse.split()
			wordi=0
			y=4
			o+=[['sent'+str(sentnum).zfill(3)," ".join(tokens)]]


			for pnum in range(len(pdat)):
				p=pdat[pnum]
				try:
					w=tokens[wordi]
				except IndexError:
					continue
				pnop=p.replace('(','').replace(')','')


				if pnop==w:
					wordi+=1
					if wordi>=len(tokens): break

					d={}
					d['wordnum']=wordi
					d['depth']=y
					d['sentnum']=str(sentnum).zfill(3)

					try:
						dl['sent'+str(sentnum).zfill(3)]+=[y]
					except KeyError:
						dl['sent'+str(sentnum).zfill(3)]=[]
						dl['sent'+str(sentnum).zfill(3)]+=[y]

					ld.append(d)

				y+=p.count(')')
				y-=p.count('(')


		if not ld: continue
		if ldlim and sentnum<ldlim: continue
		r1=rpyd2.RpyD2(dl)
		r2=rpyd2.RpyD2(ld)
		pytxt.write('sentkey.'+os.path.basename(ifn)+'.'+str(nn).zfill(3)+'.txt',o,toprint=True)
		#r2.plot(x='wordnum',y='depth',col='sentnum',group='sentnum',line=True,point=False)
		#r1.corrgram()
		r1.kclust(cor=True)
		r1.hclust(cor=True)