import os,sys; sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from prosodic.imports import *

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

    