import prosodic as p
print p.config
p.lang='fi'



koskenniemi = p.Text('corpora/corppoetry_fi/fi.koskenniemi.txt')
print koskenniemi
print

for line in koskenniemi.lines():
	print line.words()
	

