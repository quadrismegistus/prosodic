import os,sys; sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from prosodic.imports import *
import tempfile

def test_phonet():
    lang = EnglishLanguage()
    assert type(lang) == type(English())


    ipa = lang.phonemize('dummywummy')
    assert "ˈʌ" in ipa

    sylls1 = lang.syllabify_ipa(ipa)

    osylls = lang.phoneticize('dummywummy')
    assert osylls
    sylls2 = osylls[0]

    assert len(sylls2) == 4
    assert sylls1 == sylls2

def test_espeak():
    with tempfile.TemporaryDirectory() as tdir:
        with open(os.path.join(tdir,'espeak-ng'),'w') as of: of.write('')
        assert get_espeak_env([tdir]) == tdir
    
    with tempfile.TemporaryDirectory() as tdir:
        opath=os.path.join(tdir,'a','b','c')
        os.makedirs(opath,exist_ok=True)
        lib_fn='libespeak.dylib'
        with open(os.path.join(opath,lib_fn),'w') as of: of.write('')
        assert get_espeak_env([tdir]) == os.path.join(opath,lib_fn)
    

def test_finnish():
    assert LANGS['fi']() is Finnish()
    assert isinstance(Finnish(), FinnishLanguage)
    wtype = Finnish().get('kalevala')
    assert isinstance(wtype,Entity)
    assert wtype.is_wordtype
    assert len(wtype.wordforms)==1
    assert len(wtype.syllables)==4
    assert wtype.wordforms[0].num_stressed_sylls == 2