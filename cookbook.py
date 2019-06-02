from . import prosodic as p
#t = p.Text('have you reckoned a thousand acres much?')
t=p.Text('corpora/corppoetry_fi/fi.koskenniemi.txt')
t.more()
print()

print(">> printing all heavy syllables...")
print(t.feature('+prom.weight',True))

def is_ntV(word):
	phonemes = word.phonemes()
	if phonemes[-3:-1] != [p.Phoneme("n"), p.Phoneme("t")]:
		return False
	return phonemes[-1].feature("syll")


print()
print(">> printing all -ntV words...")
nta = [word for word in t.words() if is_ntV(word)]
print(nta)