from .imports import *



class Language:
    pronunciation_dictionary_filename = ''
    pronunciation_dictionary_filename_sep = '\t'

    def __getitem__(self, token): return self.get(token)
    def get(self, token): return []

    @cached_property
    def token2ipa(self):
        d={}
        fn=self.pronunciation_dictionary_filename
        if fn and os.path.exists(fn):
            with open(fn) as f:
                for ln in f:
                    ln=ln.strip()
                    if ln and self.pronunciation_dictionary_filename_sep in ln:
                        token,ipa=ln.split(self.pronunciation_dictionary_filename_sep, 1)
                        if not token in d: d[token]=[]
                        d[token].append(ipa.split('.'))
        return d

    # def phoneme(self, ipastr):
    #     pass



@cache
def English(): return EnglishLanguage()

class EnglishLanguage(Language):
    pronunciation_dictionary_filename = os.path.join(PATH_DICTS,'en','english.tsv')
    lang = 'en-us'
    cache_fn = 'english_wordforms.sqlitedict'

    @cache
    @profile
    def phoneticize(self, token):
        if token in self.token2ipa: return self.token2ipa[token]
        # otherwise tts...
        ipa_str = self.phonemize(token.lower())
        if not ipa_str:
            logger.exception(f'no phonemes from phonemize, token = {token}')
            return []
        
        ipa_sylls = self.syllabify_ipa(ipa_str)
        return [ipa_sylls]


    @cached_property
    @profile
    def phonemizer(self):
        from phonemizer.backend import EspeakBackend
        return EspeakBackend(
            self.lang,
            preserve_punctuation=False,
            with_stress=True
        )
    

    @cache
    @profile
    def phonemize(self, token):
        from phonemizer.separator import Separator
        logger.trace('phonemizing')
        o=self.phonemizer.phonemize(
            [token],
            separator=Separator(phone=' ', word='|', syllable='.'),
            strip=True
        )
        return o[0] if o else None

    @cache
    @profile
    def syllabify_ipa(self, ipa_str_with_spaces_between_phonemes):
        phn = ipa_str_with_spaces_between_phonemes
        phns=phn.split()
        sylls = []
        syll = []
        grid=self.syllabiphon._to_grid(phn)
        bounds=self.syllabiphon.find_boundaries(grid)
        for phon,seg,is_bound in zip(phns,grid,bounds):
            if is_bound and syll:
                sylls.append(syll)
                syll=[]
            syll.append(phon)
        if syll: sylls.append(syll)
        
        def format_syll(phons):
            o=''.join(phons)
            if 'ˌ' in o: o="`"+o.replace("ˌ","")
            elif "ˈ" in o: o="'"+o.replace("ˈ","")
            return o
        return [format_syll(syll) for syll in sylls]
    
    @cached_property
    @profile
    def syllabifier(self):
        from nltk.tokenize import SyllableTokenizer
        return SyllableTokenizer()
    
    @cached_property
    @profile
    def syllabiphon(self):
        from syllabiphon.syllabify import Syllabify
        return Syllabify()
    
    @cache
    @profile
    def syllabify(self, token, num_sylls=None):
        tokenl=token.lower()
        l = self.syllabifier.tokenize(tokenl)
        l = fix_recasing(l, token)
        if num_sylls: l = fix_num_sylls(l, num_sylls)
        return l
    
    @cached_property
    @profile
    def cached(self):
        from sqlitedict import SqliteDict
        import pickle
        
        return SqliteDict(
            os.path.join(PATH_HOME_DATA, self.cache_fn),
            autocommit=True,
            encode=pickle.dumps,
            decode=pickle.loads
        )

    @cache
    @profile
    def get(self, token):
        from .words import WordForm
        if token in self.cached: 
            return self.cached.get(token)
    
        if not any(x.isalpha() for x in token): return []
        tokenl = token.lower()
        ipa_l = self.phoneticize(tokenl)
        l=[]
        for ipa in ipa_l:
            sylls = self.syllabify(token, num_sylls=len(ipa))
            l.append(WordForm(sylls_ipa=ipa, sylls_text=sylls))
        l.sort(key=lambda w: w.num_stressed_sylls)
        self.cached[token]=l
        return l




def fix_recasing(l, token):
    # return lowercases
    tokenl=token.lower()
    if tokenl!=token:
        o=[]
        i=0
        for x in l:
            xlen=len(x)
            o+=[token[i:i+xlen]]
            i+=xlen
        l=o
    return l

def fix_num_sylls(sylls, num, unknown='?'):
    while len(sylls)>num:
        last = sylls.pop()
        sylls[-1]+=last
    while len(sylls)<num:
        last = sylls.pop()
        sylls.extend([last[:len(last)//2], last[len(last)//2:]])
    return [
        unknown if not x else x 
        for x in sylls
    ]




def get_espeak_env(paths=ESPEAK_PATHS, lib_fn='libespeak.dylib'):
    for path in paths:
        if not os.path.exists(path): continue
        if 'espeak-ng' in os.listdir(path): 
            return path
        for root,dirs,fns in os.walk(path):
            if lib_fn in set(fns):
                return os.path.join(root,lib_fn)
    return ''

def set_espeak_env(paths=ESPEAK_PATHS):
    path=get_espeak_env(paths)
    if path:
        os.environ['PHONEMIZER_ESPEAK_LIBRARY']=path

# set now
set_espeak_env()


LANGS = {'en':English}