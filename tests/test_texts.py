from prosodic.imports import *

def test_Text():
    x = 'Hello world!?!?!?!? !? ?!? –––_  -—- — “‘‘’ ewr ewr ’'
    t = Text(x)
    assert t._txt == x
    assert t.txt == clean_text(x)
    

    y='This is a reasonably sized english text'
    assert Text(y).lang=='en'

    y='Dieser Text soll lang genug sein'
    assert Text(y).lang=='de'

    y='Ce texte est trop grande'
    assert Text(y).lang=='fr'