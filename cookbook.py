import prosodic as p
t = p.Text('have you reckoned a thousand acres much?')


print
print t.feature('prom.weight',True)

exit()

def is_ntV(word):
	phonemes = word.phonemes()
	if phonemes[-3:-1] != [p.Phoneme("n"), p.Phoneme("t")]:
		return False
	return phonemes[-1].feature("syll")



nta = [word for word in t.words() if is_ntV(word)]
print nta