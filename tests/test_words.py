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


def test_get_wordform_token():
    # get_wordform_token() normalizes the raw token before a WordType is built:
    #   (a) a bare numeral is spelled out (so it becomes a scannable word), and
    #   (b) any internal whitespace is turned into hyphens (a WordType is a
    #       single word, so embedded spaces would break parsing).
    from prosodic.words.wordtype import get_wordform_token

    # (a) numeral spell-out — single-word results stay clean
    assert get_wordform_token('3') == 'three'
    assert get_wordform_token('16') == 'sixteen'
    # (b) whitespace collapses to hyphens (and the token is stripped first)
    assert get_wordform_token('  hello world  ') == 'hello-world'
    assert get_wordform_token('New York') == 'New-York'
    # both rules at once: "100" -> "one hundred" -> "one-hundred"
    assert get_wordform_token('100') == 'one-hundred'
    # an ordinary token is returned unchanged
    assert get_wordform_token('cat') == 'cat'
    assert get_wordform_token('  cat  ') == 'cat'


def test_wordtype_form_and_puncts():
    from prosodic.words.wordtype import WordType, Word

    cat = Word('cat')
    # .form is the first WordForm; .forms is the full list
    assert cat.form is cat.children[0]
    assert cat.form.txt == 'cat'
    assert cat.num_forms == len(cat.forms) == 1
    assert cat.num_sylls == 1
    assert cat.num_stressed_sylls == 1

    # is_punc: alphabetic word -> None (falsy), punctuation -> True
    assert cat.is_punc is None
    assert WordType(txt=',').is_punc is True
    assert WordType(txt='...').is_punc is True

    # attrs surfaces num_forms + is_punc
    a = cat.attrs
    assert a['num_forms'] == 1
    assert a['is_punc'] is None

    # to_dict round-trips the text (WordType built via Word() has a parent, so
    # its key is resolvable)
    d = cat.to_dict()
    assert 'WordType' in d
    assert d['WordType']['txt'] == 'cat'


def test_wordtype_rime_distance():
    from prosodic.words.wordtype import Word

    # WordType.rime_distance delegates to its first WordForm's rime_distance.
    # Perfect rhymes score 0.0; a non-rhyme is not 0.0 (NaN under the default
    # binary max_dist=0, i.e. "no exact rime match").
    assert Word('cat').rime_distance(Word('hat')) == 0.0
    assert Word('cat').rime_distance(Word('mat')) == 0.0
    assert Word('cat').rime_distance(Word('dog')) != 0.0


def test_wordtype_unstress():
    from prosodic.words.wordtype import Word

    # "record" has two pronunciations (noun RE-cord / verb re-CORD).
    rec = Word('record')
    assert rec.num_forms >= 2
    min_stress = min(f.num_stressed_sylls for f in rec.forms)
    rec.unstress()
    # unstress() collapses a multi-form WordType down to the single least-stressed
    # form.
    assert rec.num_forms == 1
    assert rec.forms[0].num_stressed_sylls == min_stress

    # a single-form word is left untouched (the num_forms>1 guard is False)
    cat = Word('cat')
    cat.unstress()
    assert cat.num_forms == 1


def test_wordtoken_accessors():
    from prosodic.words.wordtoken import WordToken

    # a real token (built inside a TextModel) has a parent, so key/to_dict work
    tok = TextModel('cat sat').wordtoken1
    assert tok.txt == 'cat'
    assert tok.preterm is None            # no syntax parse -> no preterminal
    assert tok.has_wordform is True
    assert tok.is_punc is None            # ordinary word

    d = tok.to_dict()
    assert 'WordToken' in d
    assert d['WordToken']['txt'] == 'cat'
    assert 'key' in d['WordToken']

    # attrs carries the tokenizer-assigned positional numbers
    attrs = tok.attrs
    assert attrs['num'] == 1
    assert attrs['line_num'] == 1

    # a punctuation token: is_punc True, no wordform
    punc = WordToken(txt=',')
    assert punc.is_punc is True
    assert punc.has_wordform is False


def test_wordtoken_force_stress():
    from prosodic.words.wordtoken import WordToken

    # "today" is normally stressed on its second syllable (0 1).
    base = WordToken(txt='today')
    assert [f.num_stressed_sylls for f in base.wordtype.forms] == [1]

    # force_unstress() rebuilds the WordType with every syllable unstressed.
    tok = WordToken(txt='today')
    tok.force_unstress()
    assert tok.wordtype.num_forms == 1
    assert tok.wordtype.forms[0].num_stressed_sylls == 0

    # force_ambig_stress() offers BOTH an unstressed and a stressed variant, so
    # the parser may treat the word either way.
    tok2 = WordToken(txt='today')
    tok2.force_ambig_stress()
    stresses = sorted(f.num_stressed_sylls for f in tok2.wordtype.forms)
    assert tok2.wordtype.num_forms == 2
    assert stresses == [0, 1]


def test_wordtokenlist_basics():
    from prosodic.words.wordtokenlist import WordTokenList

    wtl = TextModel('the cat sat').wordtokens
    assert isinstance(wtl, WordTokenList)

    # .words returns the list itself; .txt joins the token texts
    assert wtl.words is wtl
    assert wtl.txt == 'the cat sat'

    # positional numbers of the tokens
    assert wtl.nums == [1, 2, 3]
    assert wtl.numset == {1, 2, 3}

    # every real word carries a wordform; punctuation does not
    assert wtl.num_with_forms == 3
    punc_wtl = TextModel('the, cat sat').wordtokens
    assert len(punc_wtl) == 4 and punc_wtl.num_with_forms == 3

    # the constructor rejects non-WordToken children
    try:
        WordTokenList(children=['not a token'])
        assert False, 'expected ValueError for non-WordToken child'
    except ValueError:
        pass

    # slicing preserves the list type
    assert isinstance(wtl[0:2], WordTokenList)
    assert len(wtl[0:2]) == 2

    # is_sent_parsed is False without a syntax parse (no preterminals); an empty
    # list short-circuits to False as well.
    assert wtl.is_sent_parsed is False
    assert WordTokenList().is_sent_parsed is False


def test_wordtokenlist_pickle_state():
    from prosodic.words.wordtokenlist import WordTokenList

    wtl = TextModel('hi there friend').wordtokens
    state = wtl.__getstate__()
    assert isinstance(state, dict)
    assert '_parse_results' in state and '_parses' in state

    # __setstate__ restores an equivalent list
    restored = WordTokenList.__new__(WordTokenList)
    restored.__setstate__(state)
    assert restored.txt == wtl.txt
    assert restored.nums == wtl.nums


def test_wordtokenlist_num_lines_and_render():
    # a two-line text: num_lines counts the lines under the token list
    wtl = TextModel('The cat is on the mat\nThe bat is in the vat').wordtokens
    assert wtl.num_lines == 2

    # best_parses yields one best parse per line
    bps = wtl.best_parses
    assert len(bps) == 2

    # render() / to_html() produce non-empty HTML strings
    html = wtl.to_html(as_str=True)
    assert isinstance(html, str) and 'cat' in html
    rendered = wtl.render(as_str=True)
    assert isinstance(rendered, str) and len(rendered) > 0

    # reset_meter() installs a fresh default Meter on the owning text
    wtl.reset_meter()
    from prosodic.parsing.meter import Meter
    assert isinstance(wtl.text._mtr, Meter)
