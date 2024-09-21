from ..imports import *


class LanguageModel:
    pronunciation_dictionary_filename = ""
    pronunciation_dictionary_filename_sep = "\t"
    cache_fn = "lang_wordtypes"
    lang_espeak = None
    lang = None
    name = None
    use_cache = False
    filename_ambig_stress = "ambig_stress_words.txt"
    filename_unstressed = "unstressed_words.txt"
    filename_token2ipa = None
    filename_token2ipa_sep = "\t"

    def __getitem__(self, token):
        return self.get(token)

    @property
    def path(self):
        path_langs = os.path.dirname(__file__)
        return path_langs if not self.name else os.path.join(path_langs, self.name)

    @property
    def path_token2ipa(self):
        if not self.filename_token2ipa and self.name:
            self.filename_token2ipa = self.name + ".tsv"

        if self.filename_token2ipa:
            path = os.path.join(self.path, self.filename_token2ipa)
            if os.path.exists(path):
                return path
        return None

    @property
    def path_unstressed(self):
        path = os.path.join(self.path, self.filename_unstressed)
        return path if os.path.exists(path) else None

    @property
    def path_ambig_stress(self):
        path = os.path.join(self.path, self.filename_ambig_stress)
        return path if os.path.exists(path) else None

    @cached_property
    def unstressed_words(self) -> set:
        if self.path_unstressed:
            with open(self.path_unstressed, encoding="utf-8") as f:
                return set(f.read().strip().split())
        return set()

    @cached_property
    def ambig_stressed_words(self) -> set:
        if self.path_ambig_stress:
            with open(self.path_ambig_stress, encoding="utf-8") as f:
                return set(f.read().strip().split())
        return set()

    @cached_property
    def token2ipa(self):
        d = {}
        if self.path_token2ipa:
            with open(self.path_token2ipa, encoding="utf-8") as f:
                for ln in f:
                    ln = ln.strip()
                    if ln and self.filename_token2ipa_sep in ln:
                        token, ipa = ln.split(
                            self.pronunciation_dictionary_filename_sep, 1
                        )
                        if not token in d:
                            d[token] = []
                        d[token].append(ipa.split("."))
        return d

    def get_sylls_ipa_ll_dict(self, token):
        return self.token2ipa.get(token, [])
    
    def get_sylls_ipa_ll_rule(self, token):
        return [], {}

    @cache
    def get_sylls_ipa_ll(self, token, force_unstress=None, force_ambig_stress=None):
        token = token.lower()
        meta = {}

        if force_unstress is None and token in self.unstressed_words:
            force_unstress = True
        elif force_ambig_stress is None and token in self.ambig_stressed_words:
            force_ambig_stress = True

        ## try dictionary
        sylls_ipa_ll = self.get_sylls_ipa_ll_dict(token)
        if sylls_ipa_ll:
            meta['ipa_origin']='dict'        
        else:
            ## use tts
            sylls_ipa_ll = self.get_sylls_ipa_ll_tts(token)
            if sylls_ipa_ll:
                meta["ipa_origin"] = "tts"
            else:
                log.error(f'cannot parse syll IPAs in {token}')
                meta['ipa_origin'] = 'error'
        
        ## format
        sylls_ipa_ll = [
            [format_syll_ipa_str(syll) for syll in sylls_ipa_l]
            for sylls_ipa_l in sylls_ipa_ll
        ]

        ## modify stresses
        if force_unstress and sylls_ipa_ll_has_stress(sylls_ipa_ll):
            sylls_ipa_l = sylls_ipa_ll[0]
            sylls_ipa_ll = [unstress_sylls_ipa_l(sylls_ipa_l)]
        elif force_ambig_stress and not sylls_ipa_ll_has_ambig_stress(sylls_ipa_ll):
            sylls_ipa_l = sylls_ipa_ll[0]
            if not sylls_ipa_ll_has_stress(sylls_ipa_ll):
                sylls_ipa_ll.append(stress_sylls_ipa_l(sylls_ipa_l))
            if not sylls_ipa_ll_has_unstress(sylls_ipa_ll):
                sylls_ipa_ll.append(unstress_sylls_ipa_l(sylls_ipa_l))

        ##
        sylls_ipa_lt = [tuple(x) for x in sylls_ipa_ll]
        sylls_ipa_ll = [list(x) for x in set(sylls_ipa_lt)]
        sylls_ipa_ll.sort(key=lambda x: (count_stresses_in_sylls_ipa_l(x), len(x)))
        meta = {
            "force_unstress": force_unstress,
            "force_ambig_stress": force_ambig_stress,
            **meta,
        }
        return sylls_ipa_ll, meta

    @cached_property
    def phonemizer(self):
        from phonemizer.backend import EspeakBackend

        return EspeakBackend(
            self.lang_espeak if self.lang_espeak else self.lang,
            preserve_punctuation=False,
            with_stress=True,
        )

    def get_sylls_ipa_l_tts(self, token):
        return self.syllabify_ipa(self.get_sylls_ipa_str_tts(token))
    
    def get_sylls_ipa_ll_tts(self, token):
        return [self.get_sylls_ipa_l_tts(token)]

    def get_sylls_ipa_str_tts(self, token, force=False):
        from phonemizer.separator import Separator
        log.trace("phonemizing")
        sep = Separator(phone=" ", word="|", syllable=".")
        res = self.phonemizer.phonemize(
            [token],
            separator=sep,
            strip=True,
        )
        obj = res[0]
        return obj

    @cache
    @profile
    def syllabify_ipa(self, ipa_str_with_spaces_between_phonemes):
        from ..words import Phoneme

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
        if syll:
            sylls.append(syll)

        def format_syll(phons):
            o = "".join(phons)
            if "ˌ" in o:
                o = "`" + o.replace("ˌ", "")
            elif "ˈ" in o:
                o = "'" + o.replace("ˈ", "")
            return o

        sylls = [format_syll(syll) for syll in sylls]
        osylls = []
        osyll = []
        for syll in sylls:
            osyll.extend([sx for sx in syll])
            if any(Phoneme(txt=ph).is_vowel for ph in osyll if ph.isalpha()):
                osylls.append("".join(osyll))
                osyll = []
        if osyll:
            if any(Phoneme(txt=ph).is_vowel for ph in osyll if ph.isalpha()):
                osylls.append("".join(osyll))
            elif osylls:
                osylls[-1] += "".join(osyll)
        return osylls

    @cached_property
    def syllabifier(self):
        from nltk.tokenize import SyllableTokenizer

        return SyllableTokenizer()

    @cached_property
    def syllabiphon(self):
        from prosodic.lib.syllabiphon.syllabify import Syllabify

        return Syllabify()

    @cache
    @profile
    def get_sylls_text_l(self, token, num_sylls=None):
        tokenl = token.lower()
        l = self.syllabifier.tokenize(tokenl)
        l = fix_recasing(l, token)
        if num_sylls:
            l = fix_num_sylls(l, num_sylls)
        return l
    
    def get_sylls_ll_rule(self, token):
        return [], {}

    # @cache
    def get_sylls_ll(
        self,
        tokenx,
        force_unstress=None,
        force_ambig_stress=None,
        **kwargs
    ) -> Tuple[List[Tuple[Tuple[str, str]]], Dict]:
        sylls_ll, meta = self.get_sylls_ll_rule(tokenx)
        if sylls_ll:
            return sylls_ll, meta

        sylls_ipa_ll, meta_ipa = self.get_sylls_ipa_ll(
            tokenx,
            force_unstress=force_unstress,
            force_ambig_stress=force_ambig_stress,
        )

        sylls_text_ll = [
            self.get_sylls_text_l(
                tokenx,
                num_sylls=len(sylls_ipa_l),
            )
            for sylls_ipa_l in sylls_ipa_ll
        ]

        meta = {**meta_ipa}#, 'sylls_text_origin':'heuristic'}
        return get_sylls_ll(sylls_ipa_ll, sylls_text_ll), meta
    
    def get(self, *args, **kwargs):
        return self.get_sylls_ll(*args, **kwargs)


def fix_recasing(l, token):
    # return lowercases
    tokenl = token.lower()
    if tokenl != token:
        o = []
        i = 0
        for x in l:
            xlen = len(x)
            o += [token[i : i + xlen]]
            i += xlen
        l = o
    return l


def fix_num_sylls(sylls, num, unknown="?"):
    while len(sylls) > num:
        last = sylls.pop()
        sylls[-1] += last
    while len(sylls) < num:
        last = sylls.pop()
        sylls.extend([last[: len(last) // 2], last[len(last) // 2 :]])
    return [unknown if not x else x for x in sylls]


def unstress(ipa):
    if not ipa:
        return ""
    if ipa[0] in {"`", "'"}:
        ipa = ipa[1:]
    return ipa


def stress(ipa, primary=True):
    if not ipa:
        return ""
    ipa = unstress(ipa)
    sstr = "'" if primary else "`"
    return sstr + ipa


def stress_sylls_ipa_l(ipa_l):
    return [stress(syllipa, primary=not i) for i, syllipa in enumerate(ipa_l)]


#     if any(get_stress(syllipa) != "U" for ipa in ipa_ll for syllipa in ipa):
#         ipa_ll.append([unstress(syllipa) for syllipa in ipa_ll[0]])
#     else:
#         ipa_ll.append(
#             [stress(syllipa, primary=not i) for i, syllipa in enumerate(ipa_ll[0])]
#         )
#     ipa_ll = [tuple(x) for x in ipa_ll]
#     ipa_ll = [list(x) for x in set(ipa_ll)]
#     ipa_ll.sort(
#         key=lambda ipal: sum(int(get_stress(syllipa) != "U") for syllipa in ipal)
#     )
#     return ipa_ll


def count_stresses_in_sylls_ipa_l(sylls_ipa_l):
    return sum(bool(get_syll_ipa_stress(syllipa) != "U") for syllipa in sylls_ipa_l)


def sylls_ipa_l_has_stress(sylls_ipa_l):
    return count_stresses_in_sylls_ipa_l(sylls_ipa_l) != 0


def syll_ipa_str_is_stressed(syll_ipa_str):
    return get_syll_ipa_stress(syll_ipa_str) != "U"


def syll_ipa_str_is_unstressed(syll_ipa_str):
    return not syll_ipa_str_is_stressed(syll_ipa_str)


def sylls_ipa_l_has_unstress(sylls_ipa_l):
    return any(syll_ipa_str_is_unstressed(syll_ipa_str) for syll_ipa_str in sylls_ipa_l)


def sylls_ipa_l_is_unstressed(syll_ipa_l):
    return not any(
        syll_ipa_str_is_stressed(syll_ipa_str) for syll_ipa_str in syll_ipa_l
    )


def sylls_ipa_l_has_stress(sylls_ipa_l):
    return any(syll_ipa_str_is_stressed(syll_ipa_str) for syll_ipa_str in sylls_ipa_l)


def sylls_ipa_ll_has_stress(sylls_ipa_ll):
    return any(sylls_ipa_l_has_stress(sylls_ipa_l) for sylls_ipa_l in sylls_ipa_ll)


def sylls_ipa_ll_has_unstress(sylls_ipa_ll):
    return any(sylls_ipa_l_is_unstressed(sylls_ipa_l) for sylls_ipa_l in sylls_ipa_ll)


def sylls_ipa_ll_has_ambig_stress(sylls_ipa_ll):
    return sylls_ipa_ll_has_stress(sylls_ipa_ll) and sylls_ipa_ll_has_unstress(
        sylls_ipa_ll
    )


def get_sylls_ll(sylls_ipa_ll, sylls_text_ll):
    sylls_ll = []
    for syll_ipa_l, syll_text_l in zip(sylls_ipa_ll, sylls_text_ll):
        sylls_l = list(zip(syll_ipa_l, syll_text_l))
        sylls_ll.append(sylls_l)
    return sylls_ll


def unstress_sylls_ipa_l(sylls_ipa_l):
    return [unstress(syllipa) for syllipa in sylls_ipa_l]


# def maybestress(sylls_ll):
#     sylls_ipa_ll,sylls_text_ll=zip(*sylls_ll)
#     if sylls_ipa_ll_has_unstress(sylls_ipa_ll) and sylls_ipa_ll_has_stress(sylls_ipa_ll):
#         return sylls_ll

#     if not sylls_ipa_ll_has_unstress(sylls_ipa_ll):
#         unstressed_syll_ipa_l = [unstress_sylls_ipa_l
#         new_syll = ()
#         sylls_ll.insert(0,)


#     # for sylls_text,sylls_ipa in sylls_ll:
#         # if
#     if any(get_stress(syllipa) != "U" for ipa in ipa_ll for syllipa in ipa):
#         ipa_ll.append([unstress(syllipa) for syllipa in ipa_ll[0]])
#     else:
#         ipa_ll.append(
#             [stress(syllipa, primary=not i) for i, syllipa in enumerate(ipa_ll[0])]
#         )
#     ipa_ll = [tuple(x) for x in ipa_ll]
#     ipa_ll = [list(x) for x in set(ipa_ll)]
#     ipa_ll.sort(
#         key=lambda ipal: sum(int(get_stress(syllipa) != "U") for syllipa in ipal)
#     )
#     return ipa_ll

# def ensure_unstressed(ipa_ll):
#     if not ipa_ll: return []
#     ipa_l = ipa_ll[0]
#     return [unstress(ipa_l)]


# def ensure_unstressed(ipa_ll):
#     if not ipa_ll: return []
#     ipa_l = ipa_ll[0]
#     return [unstress(ipa_l)]


def get_espeak_error_msg(paths):
    pathstr = "\n    * ".join(paths)
    return f"""
Cannot find espeak library ("libespeak.dylib" or "libespeak.so" or "libespeak-ng.dll") at any of the following paths: 
    * {pathstr}

Please install espeak:

    * On Mac: brew install espeak
        [install homebrew first if necessary: https://brew.sh/]

    * On Linux: apt-get install espeak libespeak1 libespeak-dev

    * On Windows: download and install from https://github.com/espeak-ng/espeak-ng/releases/latest

If you have placed espeak at another location than those listed above, 
set the environment variable PATH_ESPEAK. From within python:

    import os
    os.environ["PATH_ESPEAK"]="/my/path/to/libespeak.dylib"
    import prosodic

For more information on espeak: http://espeak.sourceforge.net
"""


def get_espeak_env(
    path_or_paths=ESPEAK_PATHS,
    lib_fns={"libespeak.dylib", "libespeak.so", "libespeak-ng.dll"},
):
    stored = os.environ.get("PATH_ESPEAK") or os.environ.get(
        "PHONEMIZER_ESPEAK_LIBRARY"
    )
    if stored:
        return stored
    paths = [path_or_paths] if type(path_or_paths) is str else path_or_paths
    for path in paths:
        if not os.path.exists(path):
            continue
        if os.path.isfile(path) and os.path.basename(path) in lib_fns:
            return path
        if os.path.isdir(path) and "espeak-ng" in set(os.listdir(path)):
            return path
        for root, dirs, fns in os.walk(path):
            fns = set(fns)
            for lib_fn in lib_fns:
                if lib_fn in fns:
                    return os.path.join(root, lib_fn)
    log.warning(get_espeak_error_msg(paths))
    return ""


def set_espeak_env(path_or_paths=ESPEAK_PATHS):
    path = get_espeak_env(path_or_paths)
    if path:
        os.environ["PHONEMIZER_ESPEAK_LIBRARY"] = path
        os.environ["PATH_ESPEAK"] = path


# set now
set_espeak_env()


@cache
def Language(lang: str = DEFAULT_LANG):
    if lang == "en":
        from .english import EnglishLanguage

        return EnglishLanguage()
    if lang == "fi":
        from .finnish import FinnishLanguage

        return FinnishLanguage()

    lang_obj = LanguageModel()
    lang_obj.lang = lang
    return lang_obj


@cache
def get_word(tokenx, lang=DEFAULT_LANG, force_unstress=None, force_ambig_stress=None):
    return Language(lang).get(tokenx, force_unstress=force_unstress, force_ambig_stress=force_ambig_stress)