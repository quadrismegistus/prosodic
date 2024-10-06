from ..langs import LanguageModel, cache

class EnglishLanguage(LanguageModel):
    lang = 'en'
    name = 'english'
    lang_espeak = 'en-us'

@cache
def English(): return EnglishLanguage()
