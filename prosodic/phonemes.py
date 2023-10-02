from .imports import *

class PhonemeClass(Subtext): 
	pass

@cache
def Phoneme(phon):
	import panphon
	ft = panphon.FeatureTable()
	phonl = ft.word_fts(phon)
	if not phonl: 
		# logger.error(f'What is this phoneme? {phon}')
		if phon in get_ipa_info():
			phond = get_ipa_info().get(phon, {})
		else:
			logger.error(f'What is this phoneme? No features found for it: {phon}')
			phond = {}
	else:
		phond = phonl[0].data
	phonobj = PhonemeClass(phon,**{f'phon_{k}':v for k,v in phond.items()})
	return phonobj

