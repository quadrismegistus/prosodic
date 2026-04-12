"""Build a flat syllable-level DataFrame from tokenized text.

This is the Phase 1 foundation of the v3 DataFrame-first architecture.
One row per syllable, with all features needed by the vectorized parser.
"""

import numpy as np
from ..imports import *
from ..words.syllables import _parse_ipa_cached
from ..words.phonemes import get_phoneme_feats


def _phone_is_vowel(phone_txt):
    """Check if a phone is a vowel using cached panphon features."""
    feats = get_phoneme_feats(phone_txt)
    cons = feats.get('cons')
    if cons is None:
        return None
    return cons < 1


def _syll_is_heavy_from_ipa(ipa):
    """Compute is_heavy from IPA string without constructing Entity objects.

    Heavy = has consonant ending OR has diphthong (>1 vowel).
    """
    phones = _parse_ipa_cached(ipa)
    if not phones:
        return False
    # consonant ending
    last_is_cons = not _phone_is_vowel(phones[-1])
    if last_is_cons:
        return True
    # diphthong
    num_vowels = sum(1 for p in phones if _phone_is_vowel(p))
    return num_vowels > 1


def build_syll_df(token_dicts, lang=DEFAULT_LANG):
    """Build a syllable-level DataFrame from tokenized word dicts.

    Args:
        token_dicts: list of dicts from tokenize_sentwords_iter()
        lang: language code

    Returns:
        DataFrame with one row per syllable, columns:
            word_num, line_num, para_num, sent_num, sentpart_num, linepart_num,
            word_txt, is_punc, form_idx, syll_idx, syll_ipa, syll_text,
            is_stressed, is_heavy, is_strong, is_weak, is_functionword, num_forms
    """
    from ..langs import get_word
    from ..words.wordtype import get_wordform_token, token_is_punc

    rows = []
    for d in token_dicts:
        word_txt = d['txt']
        word_num = d['num']
        line_num = d.get('line_num')
        para_num = d.get('para_num')
        sent_num = d.get('sent_num')
        sentpart_num = d.get('sentpart_num')
        linepart_num = d.get('linepart_num')
        is_punc = d.get('is_punc', 0)

        tokenx = get_wordform_token(word_txt)
        if token_is_punc(tokenx):
            # punctuation token — no syllables, just record the word-level info
            rows.append({
                'word_num': word_num,
                'line_num': line_num,
                'para_num': para_num,
                'sent_num': sent_num,
                'sentpart_num': sentpart_num,
                'linepart_num': linepart_num,
                'word_txt': word_txt,
                'is_punc': 1,
                'form_idx': -1,
                'num_forms': 0,
                'syll_idx': -1,
                'syll_ipa': '',
                'syll_text': '',
                'is_stressed': False,
                'is_heavy': False,
                'is_strong': False,
                'is_weak': False,
                'is_functionword': False,
            })
            continue

        sylls_ll, meta = get_word(
            tokenx, lang=lang,
        )

        if not sylls_ll:
            # no pronunciation found
            rows.append({
                'word_num': word_num,
                'line_num': line_num,
                'para_num': para_num,
                'sent_num': sent_num,
                'sentpart_num': sentpart_num,
                'linepart_num': linepart_num,
                'word_txt': word_txt,
                'is_punc': is_punc,
                'form_idx': -1,
                'num_forms': 0,
                'syll_idx': -1,
                'syll_ipa': '',
                'syll_text': '',
                'is_stressed': False,
                'is_heavy': False,
                'is_strong': False,
                'is_weak': False,
                'is_functionword': False,
            })
            continue

        num_forms = len(sylls_ll)

        # build rows for each wordform
        for form_idx, sylls_l in enumerate(sylls_ll):
            # sylls_l is a list of (ipa, text) tuples
            num_sylls = len(sylls_l)

            # pre-compute stress per syllable for is_strong/is_weak
            stress_list = [
                get_syll_ipa_stress(syll_ipa) in ("P", "S")
                for syll_ipa, _ in sylls_l
            ]
            is_func = (num_sylls == 1 and not stress_list[0])

            for syll_idx, (syll_ipa, syll_text) in enumerate(sylls_l):
                is_stressed = stress_list[syll_idx]
                is_heavy = _syll_is_heavy_from_ipa(syll_ipa)

                # is_strong/is_weak: polysyllabic context
                is_strong = False
                is_weak = False
                if num_sylls > 1:
                    if is_stressed:
                        # strong if neighbor is unstressed
                        if syll_idx > 0 and not stress_list[syll_idx - 1]:
                            is_strong = True
                        elif syll_idx < num_sylls - 1 and not stress_list[syll_idx + 1]:
                            is_strong = True
                    else:
                        # weak if neighbor is stressed
                        if syll_idx > 0 and stress_list[syll_idx - 1]:
                            is_weak = True
                        elif syll_idx < num_sylls - 1 and stress_list[syll_idx + 1]:
                            is_weak = True

                rows.append({
                    'word_num': word_num,
                    'line_num': line_num,
                    'para_num': para_num,
                    'sent_num': sent_num,
                    'sentpart_num': sentpart_num,
                    'linepart_num': linepart_num,
                    'word_txt': word_txt,
                    'is_punc': 0,
                    'form_idx': form_idx,
                    'num_forms': num_forms,
                    'syll_idx': syll_idx,
                    'syll_ipa': syll_ipa,
                    'syll_text': syll_text,
                    'is_stressed': is_stressed,
                    'is_heavy': is_heavy,
                    'is_strong': is_strong,
                    'is_weak': is_weak,
                    'is_functionword': is_func,
                })

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    # optimize dtypes
    for col in ('is_stressed', 'is_heavy', 'is_strong', 'is_weak', 'is_functionword'):
        df[col] = df[col].astype(bool)
    for col in ('word_num', 'line_num', 'para_num', 'sent_num', 'is_punc', 'form_idx', 'num_forms', 'syll_idx'):
        df[col] = df[col].astype(np.int32)
    return df


class SyllData:
    """Lightweight syllable stand-in for DataFrame-based parsing.

    Duck-types the Syllable interface used by ParseSlot and _build_single_parse.
    No Entity overhead, no Phoneme children.
    """
    __slots__ = ('ipa', '_txt', 'is_stressed', 'is_heavy', 'is_strong',
                 'is_weak', 'parent', '_num', 'stress', 'children')

    def __init__(self, ipa, txt, is_stressed, is_heavy, is_strong, is_weak):
        self.ipa = ipa
        self._txt = txt
        self.is_stressed = is_stressed
        self.is_heavy = is_heavy
        self.is_strong = is_strong
        self.is_weak = is_weak
        self.parent = None
        self._num = None
        self.stress = get_syll_ipa_stress(ipa)
        self.children = []

    @property
    def txt(self):
        return self._txt

    @property
    def num(self):
        return self._num

    def __repr__(self):
        return f"SyllData({self.ipa!r})"


def extract_features_from_df(syll_df_slice, form_idx=0):
    """Extract syllable features from a _syll_df slice for one line.

    Args:
        syll_df_slice: DataFrame rows for one line (from text._syll_df)
        form_idx: which wordform to use (0 = first/default)

    Returns:
        dict matching extract_features() format, with SyllData in 'sylls'
    """
    # filter to non-punctuation, requested form
    df = syll_df_slice
    df = df[(df['is_punc'] == 0)]

    # for each word, pick form_idx if available, else form 0
    # group by word_num, for each group pick the right form
    word_groups = df.groupby('word_num', sort=False)
    selected = []
    for word_num, wdf in word_groups:
        forms_available = wdf['form_idx'].unique()
        if form_idx in forms_available:
            selected.append(wdf[wdf['form_idx'] == form_idx])
        elif 0 in forms_available:
            selected.append(wdf[wdf['form_idx'] == 0])
        elif len(forms_available) > 0:
            selected.append(wdf[wdf['form_idx'] == forms_available[0]])

    if not selected:
        return {
            "sylls": [],
            "stressed": np.array([], dtype=bool),
            "heavy": np.array([], dtype=bool),
            "strong": np.zeros(0, dtype=np.int8),
            "weak": np.zeros(0, dtype=np.int8),
            "word_ids": np.array([], dtype=np.int32),
            "func_word": np.array([], dtype=bool),
        }

    df = pd.concat(selected)

    sylls = [
        SyllData(
            ipa=row['syll_ipa'],
            txt=row['syll_text'],
            is_stressed=row['is_stressed'],
            is_heavy=row['is_heavy'],
            is_strong=row['is_strong'],
            is_weak=row['is_weak'],
        )
        for _, row in df.iterrows()
    ]

    n = len(sylls)
    return {
        "sylls": sylls,
        "stressed": df['is_stressed'].values.astype(bool),
        "heavy": df['is_heavy'].values.astype(bool),
        "strong": df['is_strong'].values.astype(np.int8),
        "weak": df['is_weak'].values.astype(np.int8),
        "word_ids": df['word_num'].values.astype(np.int32),
        "func_word": df['is_functionword'].values.astype(bool),
    }
