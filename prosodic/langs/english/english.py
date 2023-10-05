from prosodic.imports import *
from prosodic.langs.langs import Language

class EnglishLanguage(Language):
    pronunciation_dictionary_filename = os.path.join(PATH_DICTS,'en','english.tsv')
    lang_espeak = 'en-us'
    lang = 'en'
    cache_fn = 'english_wordtypes.sqlitedict'

    pass


@cache
def English(): return EnglishLanguage()
LANGS['en'] = English
