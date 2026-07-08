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


def _phone_is_long(phone_txt):
    """A long vowel (iː, uː, ɔː, ...) per panphon's `long` feature."""
    return get_phoneme_feats(phone_txt).get('long', -1) == 1


def _syll_is_heavy_from_ipa(ipa):
    """Compute is_heavy from IPA string without constructing Entity objects.

    Heavy = a branching rime: a coda (consonant ending) OR a long/complex
    nucleus. A long/complex nucleus is a diphthong (>1 vowel) OR a long
    monophthong (iː/uː/...). Long monophthongs were previously missed (only
    coda + diphthong counted), so e.g. "see"/"too" were scored light.
    """
    phones = _parse_ipa_cached(ipa)
    if not phones:
        return False
    # coda (consonant ending)
    if not _phone_is_vowel(phones[-1]):
        return True
    # long/complex nucleus: diphthong (>1 vowel) or a long monophthong
    vowels = [p for p in phones if _phone_is_vowel(p)]
    if len(vowels) > 1:
        return True
    return any(_phone_is_long(p) for p in vowels)


def strong_weak_from_levels(levels, idx):
    """Local-max / local-min "strong / weak" rule over a prominence-level list.

    The single source of the rise/fall rule, called by BOTH parse paths so they
    can never drift: the DF builder (``build_syll_df`` below) and the entity
    properties (``words/syllables.py`` ``Syllable.is_strong`` / ``is_weak``).

    Given relative prominence ``levels`` (higher = more prominent) and the index
    of one syllable, decide whether that syllable is a local prominence MAXIMUM
    (strong) or MINIMUM (weak) versus its immediate neighbours:

        strong = higher than a neighbour, lower than none   (rises and not falls)
        weak   = lower  than a neighbour, higher than none   (falls and not rises)

    A "shoulder" on a monotonic slope (both rises and falls) or a flat plateau
    (neither) is NEITHER; strong and weak are mutually exclusive.

    Only the ORDERING of levels matters, not the scale: the DF path passes
    {P:2, S:1, U:0}, the entity path passes ``stress_num`` {P:1.0, S:0.5, U:0.0}
    — both preserve P > S > U, so the rises/falls comparisons agree.

    Returns:
        (is_strong, is_weak) tuple of bools.
    """
    lvl = levels[idx]
    neigh = []
    if idx > 0:
        neigh.append(levels[idx - 1])
    if idx < len(levels) - 1:
        neigh.append(levels[idx + 1])
    rises = any(lvl > n for n in neigh)   # more prominent than a neighbour
    falls = any(lvl < n for n in neigh)   # less prominent than a neighbour
    return (rises and not falls), (falls and not rises)


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
            # relative prominence level: primary > secondary > unstressed. Using
            # levels (not binary stressed) means a primary-secondary word — AL-most
            # ('ɔːl `moʊst) — has a strength peak on its primary, instead of reading
            # as "both stressed / no peak" and leaving w_peak inert. (v3 bug: the
            # old binary test collapsed P and S, so P-S words had no strong/weak.)
            level_list = [
                {"P": 2, "S": 1}.get(get_syll_ipa_stress(syll_ipa), 0)
                for syll_ipa, _ in sylls_l
            ]
            is_func = (num_sylls == 1 and not stress_list[0])

            for syll_idx, (syll_ipa, syll_text) in enumerate(sylls_l):
                is_stressed = stress_list[syll_idx]
                is_heavy = _syll_is_heavy_from_ipa(syll_ipa)

                # is_strong / is_weak: relative prominence within a polysyllable
                # (primary > secondary > unstressed). strong = a local prominence
                # MAXIMUM (higher than a neighbour, lower than none); weak = a local
                # MINIMUM (lower than a neighbour, higher than none). The two are
                # mutually exclusive — a syllable is never both.
                #   POetry (P-U-U)  -> strong, weak, neither  ("e" falls from PO,
                #                       equal to "try", so a trough not a shoulder)
                #   AL-most (P-S)   -> strong, weak
                #   a "shoulder" on a monotonic slope (the secondary of U-S-P /
                #     P-S-U, which BOTH rises above one neighbour and falls below
                #     the other) -> NEITHER, and a flat plateau -> neither.
                #
                # NOTE (possible v1 discrepancy): v1's getStrengthStress instead
                # resolves a shoulder by its NEXT neighbour (so it labels the
                # secondary strong or weak, never neither). Agrees with v1 on the
                # common cases; differs only on 3+ syllable words with a mid
                # secondary — a minor possible source of w_peak/s_trough drift vs
                # the 2020 v1 data. See cmp_prosodics COMPARISON.md §8.
                is_strong = False
                is_weak = False
                if num_sylls > 1:
                    is_strong, is_weak = strong_weak_from_levels(
                        level_list, syll_idx)

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
                 'is_weak', 'parent', '_num', 'stress', 'children', 'word_num')

    def __init__(self, ipa, txt, is_stressed, is_heavy, is_strong, is_weak,
                 word_num=None):
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
        self.word_num = word_num

    @property
    def txt(self):
        return self._txt

    @property
    def num(self):
        return self._num

    def __repr__(self):
        return f"SyllData({self.ipa!r})"


