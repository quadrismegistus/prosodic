import os,sys; sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from prosodic.imports import *
from pandas.testing import assert_frame_equal
disable_caching()
def test_WordFormList():
    # parsing not done yet so these are just testing the ordering of slot/word combos

    l = TextModel('in door').line1
    assert len(l.wordtoken_matrix)==2
    assert l.wordtoken_matrix[0].sylls[0].is_stressed is False

    l = TextModel('in duty').line1
    assert len(l.wordtoken_matrix)==2
    assert l.wordtoken_matrix[0].sylls[0].is_stressed is False

    l = TextModel('disaster in embrace').line1
    assert len(l.wordtoken_matrix)==2
    assert l.wordtoken_matrix[0].sylls[0].is_stressed is False

def test_word():
    try:
        TextModel('szia',lang='hu').wordtype1
        assert 0, 'Testing exception failed'
    except Exception:
        assert 1

    word = TextModel('hello').wordtype1
    assert word.num_sylls == 2
    assert word.num_stressed_sylls == 1
    

def test_number_normalization():
    # Digit tokens used to be classified as punctuation (no alpha chars) and
    # silently dropped from the scansion. They should now be spelled out via
    # num2words and become scannable words.
    from prosodic.words.tokenizers import (
        is_numeral, numeral_to_words, normalize_number_commas,
    )

    # helper behavior
    assert is_numeral('3')
    assert is_numeral('1867')
    assert not is_numeral('3rd')      # ordinals keep their letters
    assert not is_numeral('')
    assert numeral_to_words('3') == 'three'
    # thousands-separator commas are stripped so the numeral stays one token
    assert normalize_number_commas('1,000') == '1000'
    assert normalize_number_commas('3,4') == '3,4'   # not a thousands group

    # a plain integer becomes a real, non-punc, syllabified word
    t = TextModel('I saw 3 ships come sailing by')
    df = t._syll_df
    words = [w.strip() for w in df[df['is_punc'] == 0]['word_txt'].unique()]
    assert 'three' in words
    assert '3' not in words           # the digit itself is not left as a token
    three_rows = df[df['word_txt'].str.strip() == 'three']
    assert len(three_rows) >= 1       # it has at least one syllable
    assert not three_rows['is_punc'].any()

    # the numeral contributes a position to the parse
    t.parse()
    assert 'three' in t.lines[0].best_parse.txt.lower()

    # a comma-grouped number ("1,000") is normalized and spelled out
    df2 = TextModel('We counted 1,000 stars')._syll_df
    words2 = [w.strip() for w in df2[df2['is_punc'] == 0]['word_txt'].unique()]
    assert 'one' in words2 and 'thousand' in words2

    # a year ("1867") is spelled out as a cardinal and no digit token survives
    df3 = TextModel('In 1867 they came')._syll_df
    words3 = [w.strip() for w in df3[df3['is_punc'] == 0]['word_txt'].unique()]
    assert 'thousand' in words3
    assert not any(w.isdigit() for w in df3['word_txt'].str.strip())
