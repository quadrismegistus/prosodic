import glob

from ..imports import *


# Normalize IPA symbols that panphon's ipa_segs drops or mis-segments.
# Each replacement must be a sequence of phonemes panphon can segment,
# joined by spaces so it stays consistent with espeak's space-delimited
# output. Without this, the zip between espeak phns and panphon segs in
# syllabify_ipa misaligns and segments vanish (see tests/test_ipa_norm).
_ESPEAK_IPA_NORMALIZATIONS = [
    # (a) characters panphon's ipa_segs drops entirely — silent segment loss
    ("ɚ", "ə ɹ"),   # unstressed r-colored schwa (riper, teacher)
    ("ɝ", "ˈə ɹ"),  # stressed r-colored schwa (defined for completeness;
                    # en-us espeak uses ɜː instead)
    ("ᵻ", "ɪ"),     # barred-i: reduced /ɪ/ in roses, hunted, wishes
    # (b) hiatus tokens espeak emits as one phn but represent two syllables
    # (split so syllabiphon can find the boundary between them)
    ("ˈaɪə", "ˈaɪ ə"), ("ˌaɪə", "ˌaɪ ə"), ("aɪə", "aɪ ə"),
    ("ˈiə",  "ˈi ə"),  ("ˌiə",  "ˌi ə"),  ("iə",  "i ə"),
]


def _normalize_espeak_ipa(ipa_str):
    for src, tgt in _ESPEAK_IPA_NORMALIZATIONS:
        ipa_str = ipa_str.replace(src, tgt)
    return " ".join(ipa_str.split())


class LanguageModel:
    pronunciation_dictionary_filename = ""
    pronunciation_dictionary_filename_sep = "\t"
    cache_fn = "lang_wordtypes"
    lang_espeak = None
    lang = None
    name = None
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

    @property
    def path_token2ipa_cache(self):
        """Path to user-local TTS pronunciation cache file."""
        if not self.name:
            return None
        path = os.path.join(PATH_HOME_DATA, f"{self.name}_cache.tsv")
        return path

    @cached_property
    def token2ipa(self):
        d = {}
        # load main pronunciation dictionary
        if self.path_token2ipa:
            d = self._load_token2ipa_file(self.path_token2ipa, d)
        # load user-local TTS cache
        cache_path = self.path_token2ipa_cache
        if cache_path and os.path.exists(cache_path):
            d = self._load_token2ipa_file(cache_path, d)
        return d

    def _load_token2ipa_file(self, path, d=None):
        if d is None:
            d = {}
        sep = self.pronunciation_dictionary_filename_sep
        with open(path, encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if ln and sep in ln:
                    token, ipa = ln.split(sep, 1)
                    if token not in d:
                        d[token] = []
                    d[token].append(ipa.split("."))
        return d

    def _cache_tts_result(self, token, sylls_ipa_l):
        """Append a TTS pronunciation result to the user-local cache file."""
        cache_path = self.path_token2ipa_cache
        if not cache_path:
            return
        ipa_str = ".".join(sylls_ipa_l)
        sep = self.pronunciation_dictionary_filename_sep
        with open(cache_path, "a", encoding="utf-8") as f:
            f.write(f"{token}{sep}{ipa_str}\n")

    def get_sylls_ipa_ll_dict(self, token):
        return self.token2ipa.get(token, [])
    
    def get_sylls_ipa_ll_rule(self, token):
        return [], {}

    @cache(maxsize=None)
    def get_sylls_ipa_ll(self, token, force_unstress=None, force_ambig_stress=None):
        token = token.lower()
        meta = {}

        if force_unstress is None and token in self.unstressed_words:
            force_unstress = True
        elif force_ambig_stress is None and token in self.ambig_stressed_words:
            force_ambig_stress = True

        ## try dictionary (includes user cache)
        sylls_ipa_ll = self.get_sylls_ipa_ll_dict(token)
        if sylls_ipa_ll:
            meta['ipa_origin']='dict'
        else:
            ## use tts
            sylls_ipa_ll = self.get_sylls_ipa_ll_tts(token)
            if sylls_ipa_ll:
                meta["ipa_origin"] = "tts"
                # cache TTS result to disk for next startup
                for sylls_ipa_l in sylls_ipa_ll:
                    self._cache_tts_result(token, sylls_ipa_l)
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
        # Include the syllable content as a final sort key so pronunciation
        # variants with equal stress-count and length get a DETERMINISTIC order.
        # Without it the dedup `set(...)` leaves equal-key variants in
        # hash-seed-dependent order, which propagates to form_idx and makes the
        # best-parse tie-break flip across runs on lines with tied scansions.
        sylls_ipa_ll.sort(key=lambda x: (count_stresses_in_sylls_ipa_l(x), len(x), tuple(x)))
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
        obj = _normalize_espeak_ipa(obj)
        return obj

    @cache(maxsize=None)
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

    @cache(maxsize=None)
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


# Unversioned library filenames: the symlink the espeak "-dev" package
# provides, plus what macOS Homebrew and Windows ship. Preferred over
# versioned runtime libraries so that on machines where espeak is fully
# installed the resolved path stays identical to prior behavior.
ESPEAK_LIB_FNS = {
    "libespeak.dylib",
    "libespeak.so",
    "libespeak-ng.dylib",
    "libespeak-ng.so",
    "libespeak-ng.dll",
}

# Bounded, non-recursive globs for the espeak shared library across common
# install locations. These replace a full os.walk of /usr/lib (a multi-second
# import penalty on Linux without the espeak -dev package) with a fixed number
# of shallow glob lookups. Ordered so the first hit on a working machine
# reproduces the previously-resolved path.
ESPEAK_LIB_GLOBS = [
    # macOS Homebrew (Apple Silicon) — Cellar first to match prior resolution
    "/opt/homebrew/Cellar/espeak/*/lib/libespeak*.dylib",
    "/opt/homebrew/Cellar/espeak-ng/*/lib/libespeak-ng*.dylib",
    "/opt/homebrew/lib/libespeak*.dylib",
    # macOS Homebrew (Intel) and other /usr/local installs
    "/usr/local/Cellar/espeak/*/lib/libespeak*.dylib",
    "/usr/local/Cellar/espeak-ng/*/lib/libespeak-ng*.dylib",
    "/usr/local/lib/libespeak*.dylib",
    "/usr/local/lib/libespeak*.so*",
    # Linux: Debian/Ubuntu multiarch, generic, and espeak subdir
    "/usr/lib/*/libespeak*.so*",
    "/usr/lib/libespeak*.so*",
    "/usr/lib/espeak*/libespeak*.so*",
    "/lib/*/libespeak*.so*",
]


# Broad system library directories that must NOT be recursively searched:
# a full walk here is exactly the multi-second import penalty T15 fixes. They
# are covered instead by the bounded, fixed-depth globs in _glob_espeak_lib().
# Compared by os.path.normpath, so trailing slashes don't matter.
ESPEAK_NO_RECURSE = {
    "/usr/lib",
    "/usr/lib/x86_64-linux-gnu",
    "/usr/lib64",
    "/lib",
    "/lib64",
    "/usr/local/lib",
}


def _glob_espeak_lib(globs=ESPEAK_LIB_GLOBS, preferred=ESPEAK_LIB_FNS):
    """Find the espeak shared library via a bounded set of shallow globs.

    Prefers an unversioned filename (stable across machines) but falls back to
    a versioned runtime library (e.g. libespeak.so.1 / libespeak-ng.so.1) --
    the only file present on Linux systems without the espeak -dev package.
    Returns "" if nothing is found; never raises.
    """
    for pattern in globs:
        try:
            matches = sorted(glob.glob(pattern))
        except OSError:
            continue
        if not matches:
            continue
        for m in matches:
            if os.path.basename(m) in preferred:
                return m
        return matches[0]
    return ""


def _find_espeak_lib_recursive(paths, lib_fns, skip=ESPEAK_NO_RECURSE):
    """Recursively search each explicitly-provided directory for a library.

    Only the paths passed in are walked -- and broad system dirs (see
    ESPEAK_NO_RECURSE) are skipped so we never reintroduce the slow /usr/lib
    walk. Returns the first match in sorted (deterministic) order, or "".
    Never raises.
    """
    for path in paths:
        try:
            if not os.path.isdir(path):
                continue
            if os.path.normpath(path) in skip:
                continue
            hits = []
            for fn in lib_fns:
                hits.extend(
                    glob.glob(os.path.join(path, "**", fn), recursive=True)
                )
            if hits:
                return sorted(hits)[0]
        except OSError:
            continue
    return ""


def get_espeak_env(
    path_or_paths=ESPEAK_PATHS,
    lib_fns=ESPEAK_LIB_FNS,
):
    stored = os.environ.get("PATH_ESPEAK") or os.environ.get(
        "PHONEMIZER_ESPEAK_LIBRARY"
    )
    if stored:
        return stored
    paths = [path_or_paths] if type(path_or_paths) is str else list(path_or_paths)
    # 1. Cheap direct checks against the configured paths: an explicit library
    #    file (e.g. the Windows .dll entries) or the espeak-ng data dir. No
    #    recursion -- os.listdir is a single syscall.
    for path in paths:
        try:
            if not os.path.exists(path):
                continue
            if os.path.isfile(path) and os.path.basename(path) in lib_fns:
                return path
            if os.path.isdir(path) and "espeak-ng" in set(os.listdir(path)):
                return path
        except OSError:
            continue
    # 2. Recursively search the explicitly-provided directories (small, known
    #    espeak locations like Homebrew's Cellar), skipping broad system dirs.
    #    Passed dirs win over the system libraries found in step 3.
    found = _find_espeak_lib_recursive(paths, lib_fns)
    if found:
        return found
    # 3. Bounded glob of well-known system library locations (see
    #    ESPEAK_LIB_GLOBS). Replaces the old full os.walk of /usr/lib/** and
    #    also catches libespeak-ng.so, which the previous name set missed.
    found = _glob_espeak_lib()
    if found:
        return found
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


@cache(maxsize=None)
def get_word(tokenx, lang=DEFAULT_LANG, force_unstress=None, force_ambig_stress=None):
    return Language(lang).get(tokenx, force_unstress=force_unstress, force_ambig_stress=force_ambig_stress)