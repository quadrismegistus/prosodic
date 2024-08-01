from ..imports import *


class Language:
    pronunciation_dictionary_filename = ''
    pronunciation_dictionary_filename_sep = '\t'
    cache_fn = 'lang_wordtypes'
    lang_espeak = None
    lang = None
    use_cache = False

    def __getitem__(self, token):
        return self.get(token)

    def get(self, token):
        return []

    @cached_property
    def token2ipa(self):
        d = {}
        fn = self.pronunciation_dictionary_filename
        if fn and os.path.exists(fn):
            with open(fn, encoding='utf-8') as f:
                for ln in f:
                    ln = ln.strip()
                    if ln and self.pronunciation_dictionary_filename_sep in ln:
                        token,ipa=ln.split(self.pronunciation_dictionary_filename_sep, 1)
                        if not token in d: d[token] = []
                        d[token].append(ipa.split('.'))
        return d

    # def phoneme(self, ipastr):
    #     pass

    @cached_property
    @profile
    def cached(self):
        return SimpleCache(
            root_dir=os.path.join(PATH_HOME_DATA_CACHE, self.cache_fn)
        )
        # return SqliteDict(
        #     os.path.join(PATH_HOME_DATA,
        #                  self.cache_fn),
        #     autocommit=True,
        #     encode=orjson.dumps,
        #     decode=orjson.loads,
        #     journal_mode='WAL'
        #     # encode=pickle.dumps,
        #     # decode=pickle.loads
        # )

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
        o = self.phonemizer.phonemize(
            [token],
            separator=Separator(phone=' ',
                                word='|',
                                syllable='.'),
            strip=True
        )
        return o[0] if o else None

    @cache
    @profile
    def syllabify_ipa(self, ipa_str_with_spaces_between_phonemes):
        from ..phonemes import Phoneme
        phn = ipa_str_with_spaces_between_phonemes
        phns = phn.split()
        sylls = []
        syll = []
        grid = self.syllabiphon._to_grid(phn)
        bounds = self.syllabiphon.find_boundaries(grid)
        for phon, seg, is_bound in zip(phns, grid, bounds):
            if is_bound and syll:
                sylls.append(syll)
                syll = []
            syll.append(phon)
        if syll: sylls.append(syll)

        def format_syll(phons):
            o = ''.join(phons)
            if 'ˌ' in o: o = "`" + o.replace("ˌ", "")
            elif "ˈ" in o: o = "'" + o.replace("ˈ", "")
            return o

        sylls = [format_syll(syll) for syll in sylls]
        osylls = []
        osyll = []
        for syll in sylls:
            osyll.extend([sx for sx in syll])
            if any(Phoneme(ph).is_vowel for ph in osyll if ph.isalpha()):
                osylls.append(''.join(osyll))
                osyll = []
        if osyll:
            if any(Phoneme(ph).is_vowel for ph in osyll if ph.isalpha()):
                osylls.append(''.join(osyll))
            elif osylls:
                osylls[-1] += ''.join(osyll)
        return osylls

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
        tokenl = token.lower()
        l = self.syllabifier.tokenize(tokenl)
        l = fix_recasing(l, token)
        if num_sylls: l = fix_num_sylls(l, num_sylls)
        return l

    # @cache
    @profile
    def get(self, token):
        from ..words import WordForm, WordType
        tokenx = token.strip()
        if any(x.isspace() for x in tokenx):
            logger.error(
                f'Word "{tokenx}" has spaces in it, replacing them with hyphens for parsing'
            )
            tokenx = ''.join(x if not x.isspace() else '-' for x in tokenx)

        # if self.use_cache and tokenx in self.cached:
            # logger.trace(f'found token {tokenx} in cache')
            # wordforms = self.cached.get(tokenx)
            # return WordType.from_json(self.cached[tokenx])

        # else:
        wordforms = []
        if any(x.isalpha() for x in token):
            tokenl = tokenx.lower()
            ipa_l = self.phoneticize(tokenl)
            for ipa in ipa_l:
                sylls = self.syllabify(tokenx, num_sylls=len(ipa))
                wf = WordForm(tokenx, sylls_ipa=ipa, sylls_text=sylls)
                wordforms.append(wf)
            wordforms.sort(key=lambda w: w.num_stressed_sylls)
            # self.cached[tokenx] = wordforms
        wordtype = WordType(tokenx, children=wordforms, lang=self.lang)
        # if self.use_cache:
            # self.cached[tokenx] = wordtype.to_json()
        return wordtype


def fix_recasing(l, token):
    # return lowercases
    tokenl = token.lower()
    if tokenl != token:
        o = []
        i = 0
        for x in l:
            xlen = len(x)
            o += [token[i:i + xlen]]
            i += xlen
        l = o
    return l


def fix_num_sylls(sylls, num, unknown='?'):
    while len(sylls) > num:
        last = sylls.pop()
        sylls[-1] += last
    while len(sylls) < num:
        last = sylls.pop()
        sylls.extend([last[:len(last) // 2], last[len(last) // 2:]])
    return [unknown if not x else x for x in sylls]


def unstress(ipa):
    if not ipa: return ''
    if ipa[0] in {'`', "'"}: ipa = ipa[1:]
    return ipa


def stress(ipa, primary=True):
    if not ipa: return ''
    ipa = unstress(ipa)
    sstr = "'" if primary else '`'
    return sstr + ipa


def ensure_maybe_stressed(ipa_l):
    if any(get_stress(syllipa) != 'U' for ipa in ipa_l for syllipa in ipa):
        ipa_l.append([unstress(syllipa) for syllipa in ipa_l[0]])
    else:
        ipa_l.append(
            [
                stress(syllipa,
                       primary=not i) for i,
                syllipa in enumerate(ipa_l[0])
            ]
        )
    ipa_l = [tuple(x) for x in ipa_l]
    ipa_l = [list(x) for x in set(ipa_l)]
    ipa_l.sort(
        key=lambda ipal:
        sum(int(get_stress(syllipa) != 'U') for syllipa in ipal)
    )
    return ipa_l


def ensure_unstressed(ipa_l):
    return [[unstress(syllipa) for syllipa in ipa_l[0]]]


def get_espeak_error_msg(paths):
    pathstr = '\n    * '.join(paths)
    return f'''
Cannot find espeak library ("libespeak.dylib" or "libespeak.so") at any of the following paths: 
    * {pathstr}

Please install espeak:

    * On Mac: brew install espeak
        [install homebrew first if necessary: https://brew.sh/]

    * On Linux: apt-get install espeak libespeak1 libespeak-dev

    * On Windows: download and install from http://espeak.sourceforge.net/download.html

If you have placed espeak at another location than those listed above, 
set the environment variable PATH_ESPEAK. From within python:

    import os
    os.environ["PATH_ESPEAK"]="/my/path/to/libespeak.dylib"
    import prosodic

For more information on espeak: http://espeak.sourceforge.net
'''


def get_espeak_env(
    path_or_paths=ESPEAK_PATHS,
    lib_fns={'libespeak.dylib',
             'libespeak.so'}
):
    stored = os.environ.get('PATH_ESPEAK')
    if stored: return stored
    paths = [path_or_paths] if type(path_or_paths) is str else path_or_paths
    for path in paths:
        if not os.path.exists(path): continue
        if os.path.isdir(path) and 'espeak-ng' in set(os.listdir(path)):
            return path
        for root, dirs, fns in os.walk(path):
            fns = set(fns)
            for lib_fn in lib_fns:
                if lib_fn in fns:
                    return os.path.join(root, lib_fn)
    logger.warning(get_espeak_error_msg(paths))
    return ''


def set_espeak_env(path_or_paths=ESPEAK_PATHS):
    path = get_espeak_env(path_or_paths)
    if path:
        os.environ['PHONEMIZER_ESPEAK_LIBRARY'] = path
        os.environ['PATH_ESPEAK'] = path


# set now
set_espeak_env()
