def strong_clash(s1, s2):
	return s1.feats['prom.stress'] == s2.feats['prom.stress'] == 1

def weak_clash(s1, s2):
	return s1.feats['prom.stress'] != 0 and s2.feats['prom.stress'] != 0

def count_lapse_n(sylls, n):
	weak_count = 0
	lapse_count = 0
	for syll in sylls:
		if syll.feats['prom.stress'] == 0:
			weak_count += 1
		else:
			weak_count = 0
		if weak_count >= n:
			lapse_count += 1
	return lapse_count

def count_lapse(sylls):
	return count_lapse_n(sylls, 3)

def count_clash_general(sylls, is_clash):
	count = 0
	for i in range(len(sylls)-1):
		if is_clash(sylls[i], sylls[i+1]):
			count += 1
	return count

def count_clash(sylls):
	return count_clash_general(sylls, strong_clash)

def count_wsm(sylls):
	count = 0
	for syll in sylls:
		if syll.isHeavy() != (syll.feats['prom.stress'] != 0):
			count += 1
	return count

def count_heavy(sylls):
	count = 0
	for syll in sylls:
		if syll.isHeavy():
			count += 1
	return count

def count_stress(sylls):
	count = 0
	for syll in sylls:
		if syll.feats['prom.stress'] != 0:
			count += 1
	return count

def split_list(l):
	if len(l) % 2 != 0:
		l = l[1:]
	midpoint = len(l)/2
	return (l[:midpoint], l[midpoint:])

def check_text(text, counter):
	initial_count = 0
	final_count = 0
	for line in text.lines():
		initial, final = split_list(line.syllables())
		initial_count += counter(initial)
		final_count += counter(final)
	return (initial_count, final_count)

def old_check_text(t):
	clash = check_text(t, count_clash)
	lapse = check_text(t, count_lapse)
	return (clash, lapse)
	
def rhythmic_profile(line):
	strong_0 = -1
	strong_1 = -1
	for i, syll in enumerate(line.syllables()):
		if syll.feats['prom.strength'] == 1.0:
			if strong_0 != -1:
				strong_1 = strong_0
			strong_0 = i
	syll_count = len(line.syllables())
	if strong_1 == -1:
		return (-1, -1)
	return (syll_count-strong_1, syll_count-strong_0)

def profile_counts(text):
	hist = {}
	for line in text.lines():
		profile = rhythmic_profile(line)
		if profile not in hist:
			hist[profile] = 0
		hist[profile] += 1
	return sorted_dict(hist)

def sorted_dict(adict):
	items = adict.items()
	items.sort(key = lambda items:items[1], reverse=True)
	return [key for key, val in items if val > 50]