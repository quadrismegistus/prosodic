"""Compute phrasal stress from dependency parse (Liberman & Prince 1977).

Uses spaCy dependency parsing to assign prominence levels per word.
Vectorized: no tree objects, just numpy arrays over head/deprel/POS.

Values: 0 = sentence root (most prominent), -1 = direct dependent, etc.
NSR adjustment: rightmost content-word sibling promoted by +1.
CSR adjustment: leftmost NN sibling in NN compounds promoted by +1.
"""

import numpy as np
import pandas as pd

# POS tags for content words (Universal POS)
CONTENT_UPOS = frozenset({'NOUN', 'VERB', 'ADJ', 'ADV', 'PROPN', 'INTJ', 'NUM'})

# spaCy xpos tags for noun compounds (CSR)
NN_XPOS = frozenset({'NN', 'NNS', 'NNP', 'NNPS'})

_NLP_CACHE = {}


def _get_nlp(model="en_core_web_sm"):
    """Load spaCy model, lazy + cached. Disable unused components."""
    if model not in _NLP_CACHE:
        try:
            import spacy
        except ImportError:
            raise ImportError(
                "spacy is required for syntax=True. "
                "Install with: pip install spacy && python -m spacy download en_core_web_sm"
            )
        try:
            nlp = spacy.load(model, disable=["ner", "lemmatizer"])
        except OSError:
            raise OSError(
                f"spaCy model '{model}' not found. "
                f"Install with: python -m spacy download {model}"
            )
        _NLP_CACHE[model] = nlp
    return _NLP_CACHE[model]


def _compute_depth(heads, n):
    """Vectorized depth computation. Converges in O(max_depth) iterations."""
    depth = np.zeros(n, dtype=np.int32)
    current = heads.copy()
    mask = current >= 0
    while mask.any():
        depth[mask] += 1
        current[mask] = heads[current[mask]]
        mask = current >= 0
    return depth


def _compute_phrasal_stress(heads, pos, xpos, n):
    """Compute L&P phrasal stress from dependency arrays.

    Args:
        heads: int array, head index per word (-1 = root)
        pos: str array, universal POS tags
        xpos: str array, language-specific POS tags
        n: number of words

    Returns:
        int array of phrasal stress values (0 = most prominent, negative = demoted)
    """
    depth = _compute_depth(heads, n)

    # Base prominence = negative depth (root=0, deeper=more negative)
    stress = -depth.astype(np.int32)

    # NSR: among siblings (same head), rightmost content word gets +1
    # CSR: among NN siblings in same NP, leftmost NN gets +1 instead
    is_content = np.array([p in CONTENT_UPOS for p in pos])
    is_nn = np.array([p in NN_XPOS for p in xpos])

    for h in range(n):
        siblings = np.where(heads == h)[0]
        if len(siblings) < 2:
            continue

        # CSR: check for NN compound (2+ adjacent NN siblings)
        nn_sibs = siblings[is_nn[siblings]]
        if len(nn_sibs) >= 2:
            # leftmost NN gets the promotion (compound stress rule)
            stress[nn_sibs[0]] += 1
            continue

        # NSR: rightmost content-word sibling gets promotion
        content_sibs = siblings[is_content[siblings]]
        if len(content_sibs) >= 2:
            stress[content_sibs[-1]] += 1

    return stress


def add_phrasal_stress(syll_df, model="en_core_web_sm"):
    """Add phrasal_stress column to syll_df.

    Groups words by sentence, runs spaCy dep parsing, computes L&P
    phrasal stress, and broadcasts word-level values to syllable rows.

    Args:
        syll_df: DataFrame with word_num, sent_num, word_txt, is_punc columns
        model: spaCy model name

    Returns:
        syll_df with phrasal_stress column added (modified in place)
    """
    if syll_df.empty:
        syll_df['phrasal_stress'] = pd.array([], dtype=pd.Int32Dtype())
        return syll_df

    nlp = _get_nlp(model)

    # get unique words per sentence (form_idx 0 or -1, no duplicates)
    word_df = syll_df[syll_df['form_idx'].isin([0, -1])].drop_duplicates('word_num')

    # group by sentence
    stress_by_word = {}
    for sent_num, group in word_df.groupby('sent_num'):
        words = group['word_txt'].values
        word_nums = group['word_num'].values
        is_punc = group['is_punc'].values.astype(bool)

        # filter to non-punctuation for parsing, strip whitespace
        parse_mask = ~is_punc
        parse_words = [w.strip() for w in words[parse_mask]]
        parse_word_nums = word_nums[parse_mask]

        if len(parse_words) == 0:
            for wn in word_nums:
                stress_by_word[wn] = None
            continue

        # run spaCy on pre-tokenized words
        from spacy.tokens import Doc
        spaces = [True] * len(parse_words)
        if len(spaces):
            spaces[-1] = False
        doc = Doc(nlp.vocab, words=list(parse_words), spaces=spaces)
        for name, proc in nlp.pipeline:
            doc = proc(doc)

        n = len(doc)
        # extract head indices (-1 for root)
        heads = np.array([
            tok.head.i if tok.head.i != tok.i else -1
            for tok in doc
        ], dtype=np.int32)
        pos = np.array([tok.pos_ for tok in doc])
        xpos = np.array([tok.tag_ for tok in doc])

        stress = _compute_phrasal_stress(heads, pos, xpos, n)

        for i, wn in enumerate(parse_word_nums):
            stress_by_word[wn] = int(stress[i])

        # punctuation gets None
        for wn in word_nums[is_punc]:
            stress_by_word[wn] = None

    # broadcast to syllable rows
    syll_df['phrasal_stress'] = syll_df['word_num'].map(stress_by_word).astype(pd.Int32Dtype())
    return syll_df
