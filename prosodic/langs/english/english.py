from ..langs import LanguageModel, cache

class EnglishLanguage(LanguageModel):
    lang = 'en'
    name = 'english'
    lang_espeak = 'en-us'
    use_g2p_alignment = True

@cache
def English(): return EnglishLanguage()
