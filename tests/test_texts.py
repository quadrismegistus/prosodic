import os, sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from prosodic.imports import *
import tempfile

disable_caching()


def test_Text():
    x = "Hello world!?!?!?!? !? ?!? –––_  -—- — “‘‘’ ewr ewr ’"
    t = Text(x, init=False)
    print([t._txt, t.txt])
    assert t._txt == x
    assert t.txt == clean_text(x)

    y = "This is a reasonably sized english text"
    assert Text(y, lang=None, init=False).lang == "en"

    y = "Dieser Text ist nicht so klug"
    assert Text(y, lang=None, init=False).lang == "de"
    assert Text(y, init=False).lang == DEFAULT_LANG

    y = "Ce texte est trop grande"
    assert Text(y, lang=None, init=False).lang == "fr"

    with tempfile.TemporaryDirectory() as tdir:
        oline = "A slumber did my spirit seal"
        fn = os.path.join(tdir, "test.txt")
        with open(fn, "w", encoding='utf-8') as of:
            of.write(oline)
        assert Text(fn=fn)._txt == oline

    try:
        Text()
        assert 0  # ought to fail
    except Exception:
        assert 1  # pass

    try:
        Stanza()
        assert 0  # ought to fail
    except Exception:
        assert 1  # pass

    try:
        Line()
        assert 0  # ought to fail
    except Exception:
        assert 1  # pass

    t = Text("    ererer e   e  ").txt == "ererer e   e"

    l1 = Line("test\n")
    assert l1._txt == "test"
    assert l1.txt == "test"
    l2 = Line("ing two")
    t = Stanza(children=[l1, l2])
    assert t.txt == "test\ning two"

    assert len(t.lines) == 2
    assert len(t.lines.df) == 3  # 3 sylls
    assert len(t.wordtokens) == 3
    assert t.attrs
