import os,sys; sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from prosodic.imports import *
import tempfile

def test_Text():
    x = 'Hello world!?!?!?!? !? ?!? –––_  -—- — “‘‘’ ewr ewr ’'
    t = Text(x,init=False)
    assert t._txt == x
    assert t.txt == clean_text(x)

    y='This is a reasonably sized english text'
    assert Text(y,lang=None,init=False).lang=='en'

    y='Dieser Text ist nicht so klug'
    assert Text(y,lang=None,init=False).lang=='de'
    assert Text(y,init=False).lang==DEFAULT_LANG

    y='Ce texte est trop grande'
    assert Text(y,lang=None,init=False).lang=='fr'


    with tempfile.TemporaryDirectory() as tdir:
        oline='A slumber did my spirit seal'
        fn=os.path.join(tdir,'test.txt')
        with open(fn,'w') as of: of.write(oline)
        assert Text(filename=fn)._txt==oline