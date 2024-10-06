import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from prosodic.imports import *
disable_caching()
import pytest

def test_show():
    t = TextModel('in hello world')
    x = t.inspect()
    assert x is None
    x = t.inspect(indent=1)
    assert x is not None
    assert 'TextModel(' in x

    html = t._repr_html_()
    assert '<table' in html


def test_get_ld():
    t = TextModel('in hello world')

    ld1 = t.get_ld(incl_phons=False, incl_sylls=False,
                   multiple_wordforms=False)
    ld2 = t.get_ld(incl_phons=False, incl_sylls=False, multiple_wordforms=True)
    ld3 = t.get_ld(incl_phons=False, incl_sylls=True, multiple_wordforms=True)
    ld4 = t.get_ld(incl_phons=True, incl_sylls=True, multiple_wordforms=True)

    assert len(ld1) < len(ld2) < len(ld3) < len(ld4)


def test_get_df():
    t = TextModel('in hello world')

    df1 = t.get_df(incl_phons=False, incl_sylls=False,
                   multiple_wordforms=False)
    df2 = t.get_df(incl_phons=False, incl_sylls=False, multiple_wordforms=True)
    df3 = t.get_df(incl_phons=False, incl_sylls=True, multiple_wordforms=True)
    df4 = t.get_df(incl_phons=True, incl_sylls=True, multiple_wordforms=True)

    assert len(df1) < len(df2) < len(df3) < len(df4)


def test_get_children():
    t = TextModel(sonnet + '\n\n' + sonnet)
    assert len(t.stanzas) == 2
    assert len(t.lines) == (14*2)
    assert len(t.syllables) >= (14*2*10)
    assert len(t.phonemes) >= (14*2*10)

    assert type(t.stanzas) == StanzaList
    assert type(t.lines) == LineList
    assert type(t.wordtokens) == WordTokenList
    assert type(t.wordtypes) == WordTypeList
    assert type(t.wordforms) == WordFormList
    assert type(t.wordforms_all) == list
    assert type(t.syllables) == SyllableList
    assert type(t.phonemes) == PhonemeList

    w = TextModel('hello').wordtypes[0]
    syll = w.syllables[0]
    assert syll.wordtype is w
    assert len(w.syllables) == 2
    assert len(w.phonemes) == 5

    w = TextModel('hello').wordtypes[0]
    assert len(w.syllables) == 2
    assert len(w.phonemes) == 5

    t = TextModel('hello')
    stanza = t.stanzas[0]
    assert stanza.parent.nice_type_name == 'StanzaList'
    assert stanza.text is t
    assert stanza.stanzas.data == [stanza]

    line = t.lines[0]
    assert line.parent.nice_type_name == 'LineList'
    assert line.stanza is stanza
    assert line.text is t

    wordtoken = t.wordtokens[0]
    assert wordtoken.parent.nice_type_name == 'WordTokenList'
    assert wordtoken.line is line
    assert wordtoken.stanza is stanza
    assert wordtoken.text is t

    wordtype = t.wordtypes[0]
    assert wordtype.wordtoken is wordtoken
    assert wordtype.line is line
    assert wordtype.stanza is stanza
    assert wordtype.text is t
    assert wordtype.children

    wordform = t.wordforms[0]
    assert wordform.wordtype is wordtype

    syll = t.syllables[0]
    assert syll.wordform is wordform
    assert syll.wordtype is wordtype

    phon = t.phonemes[0]
    assert phon.syll is syll
    assert phon.syllable is syll
    assert phon.wordform is wordform
    assert phon.wordtype is wordtype


def test_i():
    t = TextModel('hello')
    wf = t.wordforms[0]
    syll = wf.children[0]
    assert syll.i is not None
    assert syll.num is not None
    assert syll.next is not None
    assert syll.prev is None
    syll = wf.children[1]
    assert syll.next is None
    assert syll.prev is not None



def test_types():
    text = TextModel('ok')
    stanza = text.stanza1
    line = text.line1
    wtoken = text.children[0]
    wtype = wtoken.children[0]
    wform = wtype.children[0]
    syll = wform.children[0]
    phon = syll.children[0]

    assert text.is_text
    assert not stanza.is_text
    assert not line.is_text
    assert not wtoken.is_text
    assert not wtype.is_text
    assert not wform.is_text
    assert not syll.is_text
    assert not phon.is_text

    assert not text.is_stanza
    assert stanza.is_stanza
    assert not line.is_stanza
    assert not wtoken.is_stanza
    assert not wtype.is_stanza
    assert not wform.is_stanza
    assert not syll.is_stanza
    assert not phon.is_stanza

    assert not text.is_line
    assert not stanza.is_line
    assert line.is_line
    assert not wtoken.is_line
    assert not wtype.is_line
    assert not wform.is_line
    assert not syll.is_line
    assert not phon.is_line

    assert not text.is_wordtoken
    assert not stanza.is_wordtoken
    assert not line.is_wordtoken
    assert wtoken.is_wordtoken
    assert not wtype.is_wordtoken
    assert not wform.is_wordtoken
    assert not syll.is_wordtoken
    assert not phon.is_wordtoken

    assert not text.is_wordtype
    assert not stanza.is_wordtype
    assert not line.is_wordtype
    assert not wtoken.is_wordtype
    assert wtype.is_wordtype
    assert not wform.is_wordtype
    assert not syll.is_wordtype
    assert not phon.is_wordtype

    assert not text.is_wordform
    assert not stanza.is_wordform
    assert not line.is_wordform
    assert not wtoken.is_wordform
    assert not wtype.is_wordform
    assert wform.is_wordform
    assert not syll.is_wordform
    assert not phon.is_wordform

    assert not text.is_syll
    assert not stanza.is_syll
    assert not line.is_syll
    assert not wtoken.is_syll
    assert not wtype.is_syll
    assert not wform.is_syll
    assert syll.is_syll
    assert not phon.is_syll

    assert not text.is_phon
    assert not stanza.is_phon
    assert not line.is_phon
    assert not wtoken.is_phon
    assert not wtype.is_phon
    assert not wform.is_phon
    assert not syll.is_phon
    assert phon.is_phon


def test_exceptions():
    with pytest.raises(ValueError):
        WordTokenList(children=[1, 2])

    with pytest.raises(ValueError):
        TextModel(children=[Entity()])


def test_new_parent_system():
    t = TextModel('hello')
    assert t.parent is None
    obj = t
    while obj.children:
        assert obj.children.parent is obj
        assert obj.children[0].parent is obj.children
        obj = obj.children[0]
    
    obj = Parse(t.linepart1)
    assert obj.parent is None   # wait for parselist
    while obj.children:
        assert obj.children.parent is obj
        assert obj.children[0].parent is obj.children
        obj = obj.children[0]


def test_serialize():
    t = TextModel('hello world')

    def do(x):
        for obj in x.iter_all():
            obj2 = Entity.from_dict(obj.to_dict(), use_registry=False)
            assert obj.key == obj2.key
            attrd1 = {k:v for k,v in obj.attrs.items() if k not in {'num', 'txt'}}
            attrd2 = {k:v for k,v in obj2.attrs.items() if k not in {'num', 'txt'}}
            assert attrd1 == attrd2

    do(t)