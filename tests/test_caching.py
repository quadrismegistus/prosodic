import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from prosodic.imports import *

disable_caching()

lstr = 'I am monarch of all I survey'


def test_cache_text():
    with caching_enabled():
        t = Text(lstr)
        t2 = Text(lstr)
        assert t2.children_from_cache()

    with caching_disabled():
        t = Text(lstr)
        assert not t.children_from_cache()


def test_cache_parses():
    with caching_enabled():
        # t = Text(lstr)
        t = Line(lstr)
        t.parse(force=True)
        # t2 = Text(lstr)
        t2 = Line(lstr)
        assert t2.parses_from_cache()

    with caching_disabled():
        # t = Text(lstr)
        t = Line(lstr)
        assert not t.parses_from_cache()


# trying tests again
