import sys,rpyd2,pickle

stats=pickle.load(open(sys.argv[1]))

for i in stats:
	r=rpyd2.RpyD2([d for d in stats[i]])
	r.plot(fn='cadences-length-'+str(i).zfill(4)+'.',
		x='pattern',
		y='oe',
		title='Cadences of '+str(i)+' syllables in length, measured for their observed/expected appearance at ends of sentences',
		boxplot=True,group='pattern',col='pattern',point=True,smooth=False,flip=True)
