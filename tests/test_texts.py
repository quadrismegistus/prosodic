import os, sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from prosodic.imports import *
import tempfile
import pytest

disable_caching()


def test_Text():
    x = "Hello world!?!?!?!? !? ?!? –––_  -—- — “‘‘’ ewr ewr ’"
    t = TextModel(x, init=False)
    print([t._txt, t.txt])
    assert t._txt == clean_text(x)
    assert t.txt == clean_text(x)

    y = "This is a reasonably sized english text"
    assert TextModel(y, lang=None, init=False).lang == "en"

    y = "Dieser Text ist nicht so klug"
    assert TextModel(y, lang=None, init=False).lang == "de"
    assert TextModel(y, init=False).lang == DEFAULT_LANG

    with tempfile.TemporaryDirectory() as tdir:
        oline = "A slumber did my spirit seal"
        fn = os.path.join(tdir, "test.txt")
        with open(fn, "w", encoding='utf-8') as of:
            of.write(oline)
        assert TextModel(fn=fn)._txt == oline

    with pytest.raises(ValueError):
        TextModel()

    t = TextModel("    ererer e   e  ")
    assert t.txt == "ererer e   e"
    assert len(t.wordtokens) == 3
    assert t.attrs
