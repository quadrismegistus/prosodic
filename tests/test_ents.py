import os,sys; sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from prosodic.imports import *

def test_show():
    t = Text('the hello world')
    x = t.show()
    assert x is None
    x = t.show(indent=1)
    assert x is not None
    assert 'Text(' in x

    html=t._repr_html_()
    assert '<table' in html

    ld1 = t.get_ld(incl_phons=False, incl_sylls=False, multiple_wordforms=False)
    ld2 = t.get_ld(incl_phons=False, incl_sylls=False, multiple_wordforms=True)
    ld3 = t.get_ld(incl_phons=False, incl_sylls=True, multiple_wordforms=True)
    ld4 = t.get_ld(incl_phons=True, incl_sylls=True, multiple_wordforms=True)

    assert len(ld1) < len(ld2)
    assert len(ld2) < len(ld3)
    assert len(ld3) < len(ld4)