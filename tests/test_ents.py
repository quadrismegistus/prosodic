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


def test_getattr_underscore_raises():
    # Underscore-prefixed attrs must raise AttributeError, not return None,
    # so IPython's introspection (t.save?) and pickle/copy machinery work.
    t = TextModel('hello')
    assert not hasattr(t, '_ipython_canary_method_should_not_exist_')
    assert not hasattr(t, '_some_private_thing')
    # But non-underscored missing attrs still fall through to None (legacy).
    assert t.missing_thing is None


def test_getattr_property_error_propagates():
    # A property whose getter raises AttributeError must propagate it, not have
    # it masked to None by the plural/singular fallback (which caused silent
    # None returns and a RecursionError in TextModel.load().lineparts). AUDIT T13.
    class Boom(Entity):
        prefix = "boom"
        nice_type_name = "boom"

        @property
        def kaboom(self):
            raise AttributeError("real error inside getter: _missing")

    with pytest.raises(AttributeError):
        _ = Boom().kaboom

    # The dynamic plural/singular magic must still work (not caught by the guard).
    t = TextModel("Shall I compare thee to a summers day\nRough winds do shake")
    assert len(t.lines) == 2
    assert t.lines[0].wordforms[0].syllables[0].lines is not None


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


# ---------------------------------------------------------------------------
# The tests below target Entity/EntityList base-class methods in ents.py that
# were previously uncovered. Each builds a small TextModel and asserts concrete
# tree structure/behavior. See module-level notes on genuinely-dead branches.
# ---------------------------------------------------------------------------


def test_copy_entity_and_list():
    # copy() has two branches: children is an EntityList vs a plain list.
    t = TextModel('hello bright world')
    tc = t.copy()
    assert tc is not t
    assert type(tc) is TextModel
    assert tc.txt == t.txt
    # copy is a distinct object graph
    assert tc.children is not t.children

    # A Stanza's children is a plain list -> exercises the else branch.
    st = t.stanzas[0]
    stc = st.copy()
    assert stc is not st
    assert stc.txt == st.txt
    assert type(stc) is type(st)


def test_clear_cached_properties():
    t = TextModel('hello world')
    line = t.lines[0]
    # Populate some cached_property values.
    _ = line.root
    _ = line.ancestors
    assert 'root' in line.__dict__
    assert 'ancestors' in line.__dict__
    line.clear_cached_properties()
    assert 'root' not in line.__dict__
    assert 'ancestors' not in line.__dict__
    # Recomputable afterwards.
    assert line.root is t


def test_list_type_and_type_name_and_type():
    t = TextModel('hello world')
    line = t.lines[0]
    # Entity.list_type (base) resolves the *List class for a non-list entity.
    assert t.syllables[0].list_type is SyllableList
    # A Line is itself an EntityList, so it uses the override (own class).
    assert line.list_type is Line
    # EntityList.list_type returns its own class.
    assert t.stanzas.list_type is StanzaList
    # type_name: plain lowercase; list classes get pluralized.
    assert line.type_name == 'line'
    assert t.stanzas.type_name == 'stanzas'
    # .type returns the concrete class.
    assert line.type is Line
    # nice_type_name strips Model/Class.
    assert t.nice_type_name == 'Text'


def test_get_class_and_child_type():
    assert Entity._get_class('line') is Line
    assert Entity._get_class('stanza') is Stanza
    t = TextModel('hello world')
    # A list class exposes its singular child_type name; a non-list -> None.
    assert t.stanzas.child_type == 'Stanza'
    assert t.lines[0].child_type is None


def test_is_wordtokenlist():
    t = TextModel('hello world')
    assert t.wordtokens.is_wordtokenlist is True
    # A Line *is* a WordTokenList subclass in this architecture.
    assert t.lines[0].is_wordtokenlist is True
    # A Syllable is not.
    assert t.syllables[0].is_wordtokenlist is False


def test_getitem_slice_sets_metadata():
    # Slicing an EntityList returns a same-class instance; __getitem__ then
    # copies over _text/parent (lines 197-198).
    t = TextModel('hello there big world')
    sl = t.wordtokens[0:2]
    assert type(sl) is WordTokenList
    assert len(sl) == 2
    assert sl is not t.wordtokens


def test_getattr_dynamic_magic():
    t = TextModel('hello world foo bar')
    # digit-suffixed singular -> nth child (1-based).
    assert t.line1 is t.lines[0]
    assert t.syll2 is t.syllables[1]
    # out-of-range digit index -> None (IndexError branch).
    assert t.line999 is None
    # <name>_r -> a random one of that type.
    assert type(t.syllable_r) is Syllable
    # <name>_span -> (first.num, last.num).
    assert t.syllable_span == (t.syllables[0].num, t.syllables[-1].num)
    # num_<type> -> count.
    assert t.num_lines == 1
    assert t.num_syllables == len(t.syllables)


def test_get_list_branches():
    t = TextModel('hello world foo')
    line = t.lines[0]
    # Unknown type -> None (list_class is None).
    assert line.get_list('nonexistenttype') is None
    # Asking a list for its own type returns self.
    assert t.stanzas.get_list('stanza') is t.stanzas
    # An entity whose children ARE the requested list returns those children.
    wt = t.wordtokens[0]
    assert wt.get_list('wordtype') is wt.children
    # A punctuation token has no syllable descendants -> None.
    t2 = TextModel('hello, world!')
    puncs = [w for w in t2.wordtokens if w.is_punc]
    assert puncs, 'expected punctuation tokens'
    assert puncs[0].get_list('syllable') is None


def test_children_keys_set_and_descendants():
    t = TextModel('hello world')
    assert isinstance(t.children_keys, set)
    assert len(t.children_keys) == len(t.children)
    assert isinstance(t.children_set, set)
    assert len(t.children_set) == len(t.children)
    # descendants maps key -> obj and includes self.
    desc = t.descendants
    assert isinstance(desc, dict)
    assert t.key in desc
    assert isinstance(t.descendant_keys, set)
    assert t.descendant_keys == set(desc.keys())


def test_get_ancestor_and_descendants_helpers():
    t = TextModel('hello world')
    syll = t.syllables[0]
    # Ancestors that exist above the syllable in the parent chain.
    wt = syll._get_ancestor('wordtoken')
    assert wt is not None and type(wt) is WordToken
    assert syll._get_ancestor('text') is t
    # A type that is NOT an ancestor (deeper than syllable) -> None.
    assert syll._get_ancestor('phoneme') is None
    # get_descendants of a deeper type returns entities; of a shallower/absent
    # type returns an empty list.
    assert len(t.get_descendants('phoneme')) == len(t.phonemes)
    assert t.get_descendants('stanza') == []


def test_contains_branches():
    t = TextModel('hello world\nfoo bar baz')
    line0, line1 = t.lines[0], t.lines[1]
    # self contains self.
    assert t.contains(t) is True
    # Text contains a descendant line (key-prefix match).
    assert t.contains(line0) is True
    # Text contains a descendant EntityList.
    assert t.contains(t.stanzas) is True
    # A deeper entity does not contain a shallower one.
    assert t.wordtokens[0].contains(line0) is False
    assert t.syllables[0].contains(line0) is False
    # Two sibling lines: one does not contain a wordtoken of the other.
    other_wt = line1.wordtokens[0]
    assert line0.contains(other_wt) is False


def test_get_random_and_get_one():
    t = TextModel('hello world foo bar')
    assert type(t.get_random('line')) is Line
    assert t.get_random('nonexistenttype') is None
    assert t.get_one('line') is t.lines[0]
    assert t.get_one('nonexistenttype') is None


def test_wordforms_helpers():
    t = TextModel('hello, world!')
    first = t.wordforms_first
    assert type(first) is WordFormList
    # wordforms_first: the first form of each wordtype that HAS forms
    # (punctuation wordtypes have no forms and are skipped).
    assert len(first) == len([w for w in t.wordtypes if w.children])
    # nopunc keeps only non-punctuation forms.
    nopunc = t.wordforms_nopunc
    assert type(nopunc) is WordFormList
    assert len(nopunc) == len([wf for wf in first if not wf.is_punc])
    assert all(not wf.is_punc for wf in nopunc)
    # wordforms_all: list of per-wordtype form lists.
    allforms = t.wordforms_all
    assert type(allforms) is list
    assert all(type(x) is WordFormList for x in allforms)
    # Counts.
    assert t.num_wordforms_all == sum(len(wt.children) for wt in t.wordtypes)
    assert t.num_wordforms_nopunc == len(
        [wf for wf in t.wordforms if not wf.parent.is_punc])


def test_hash_id_equality():
    t = TextModel('hello world')
    line = t.lines[0]
    # to_hash / hash / id are stable strings; __hash__ is an int.
    assert isinstance(line.to_hash(), str) and line.to_hash()
    assert isinstance(line.hash, str) and line.hash
    assert isinstance(line.id, str) and line.id
    assert isinstance(hash(line), int)
    # Identity-based equality.
    assert line == line
    assert line == t.lines[0]  # same underlying object (cached)
    assert not (line == t)
    assert line != t.wordtokens[0]
    # Hashable + usable in a set.
    assert line in {line}


def test_serialization_roundtrip_properties():
    t = TextModel('hello world')
    line = t.lines[0]
    assert isinstance(line.stuffed, dict)
    assert line.unstuffed is not None
    assert isinstance(line.serialized, (bytes, bytearray))
    d = line.deserialized
    assert type(d) is Line and d.key == line.key
    # classmethod deserialize on serialized bytes.
    d2 = Entity.deserialize(line.serialized)
    assert type(d2) is Line and d2.key == line.key


def test_ancestors_root_grandparent_prefixkey_id():
    t = TextModel('hello world')
    line = t.lines[0]
    # ancestors walk up to (but excluding) self, ending at the root text.
    anc = line.ancestors
    assert anc[-1] is t
    assert t in anc
    assert line.root is t
    # grandparent = parent.parent.
    assert line.grandparent is t
    # grandparent on the root text -> None (parent is None).
    assert t.grandparent is None
    # prefix_key resolves from the class registry.
    assert line.prefix_key == 'Line'


def test_key_without_parent_raises():
    # A parentless entity with no explicit key cannot form a key.
    e = Entity()
    assert e.parent is None
    with pytest.raises(AttributeError):
        _ = e.key


def test_wordspan_and_txt_join():
    t = TextModel('hello world foo')
    line = t.lines[0]
    span = line.wordspan
    assert span == (line.wordtokens[0].num, line.wordtokens[-1].num)
    # Entity.txt lazily joins children when _txt is unset.
    syll = t.syllables[0]
    syll._txt = None
    joined = syll.txt
    assert joined == ''.join(p.txt for p in syll.children)
    assert joined


def test_to_dict_variants_and_save_and_reduce():
    t = TextModel('hello world')
    line = t.lines[0]
    # incl_txt + extra kwargs land in the payload.
    d = line.to_dict(incl_txt=True, extra='xyz')
    payload = d['Line']
    assert payload['txt'] == line._txt
    assert payload['extra'] == 'xyz'
    assert 'children' in payload
    # incl_children=False omits children.
    d2 = line.to_dict(incl_children=False)
    assert 'children' not in d2['Line']
    # incl_attrs=True copies _attrs into the payload.
    line._attrs = {'foo': 'bar'}
    d3 = line.to_dict(incl_attrs=True)
    assert d3['Line']['foo'] == 'bar'
    # save() delegates to to_dict (returns a dict, does not raise).
    assert isinstance(line.save('unused.json'), dict)
    # __reduce__ returns (Entity.from_dict, (dict,)) and round-trips.
    fn, args = line.__reduce__()
    assert fn.__func__ is Entity.from_dict.__func__
    assert isinstance(args[0], dict)
    rebuilt = fn(*args)
    assert rebuilt.key == line.key


def test_from_dict_dispatch_and_multi_raises():
    t = TextModel('hello world')
    line = t.lines[0]
    # Entity.from_dict dispatches to the concrete subclass named in the dict.
    obj = Entity.from_dict(line.to_dict(), use_registry=False)
    assert type(obj) is Line
    assert obj.key == line.key
    # More than one top-level class key is an error.
    with pytest.raises(AssertionError):
        Entity.from_dict({'Line': {}, 'Stanza': {}})


def test_html_and_render_after_parse():
    t = TextModel('hello world')
    line = t.lines[0]
    line.parse()
    # html property delegates to to_html().
    assert line.html is not None
    # Base Entity.render delegates to to_html(as_str=...). Line overrides
    # render, so call the base implementation directly.
    rendered = Entity.render(line, as_str=True)
    assert isinstance(rendered, str)
    assert '<' in rendered
    assert rendered == line.to_html(as_str=True)


def test_repr_and_reprhtml_and_ld_df_helpers():
    t = TextModel('hello world')
    line = t.lines[0]
    # __repr__ includes num/txt-style kwargs.
    r = repr(line)
    assert r.startswith('Line(')
    # EntityList __repr__ is the multi-line indented form. A StanzaList's
    # items are themselves EntityLists (recursive branch); a WordTokenList's
    # items are plain entities (the repr(item) branch).
    rl = repr(t.stanzas)
    assert rl.startswith('StanzaList([')
    assert '\n' in rl
    rw = repr(t.wordtokens)
    assert rw.startswith('WordTokenList([')
    assert 'WordToken(' in rw
    # ld / data / l / df accessors.
    assert isinstance(line.ld, list) and line.ld
    assert line.data is line.children
    assert line.l is line.children
    assert isinstance(line.df, pd.DataFrame)
    # child_class resolves the singular child entity class of a list.
    assert t.stanzas.child_class is Stanza
    # _repr_html_ with a custom df exercises the blank(None) path (object
    # dtype preserves the literal None the blank() helper checks for).
    df = pd.DataFrame({'a': ['x', None]}, dtype=object)
    html = line._repr_html_(df=df)
    assert '<table' in html


def test_get_df_unbool_and_badcols():
    t = TextModel('hello world')
    # get_df runs bool->int coercion via unbool over syllable feature columns.
    df = t.get_df(incl_phons=False, incl_sylls=True)
    import numpy as _np
    vals = set(_np.ravel(df.values).tolist())
    # Booleans are coerced to 0/1.
    assert 0 in vals or 1 in vals
    assert not any(v is True or v is False for v in vals)


def test_inspect_maxlines_truncates():
    import io
    import contextlib
    t = TextModel('hello world\nfoo bar baz')
    # Top-level inspect() prints and returns None.
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ret = t.inspect(maxlines=2)
    assert ret is None
    out = buf.getvalue().rstrip('\n')
    assert len(out.split('\n')) <= 2


def test_sibling_navigation_and_index():
    t = TextModel('one two here\nthree four there')
    line0, line1 = t.lines[0], t.lines[1]
    # next / prev link siblings; boundaries return None.
    assert line0.next is line1
    assert line1.prev is line0
    assert line0.prev is None
    assert line1.next is None
    # i / num relationships.
    assert line0.i == 0 and line0.num == 1
    assert line1.i == 1 and line1.num == 2
    # The root text has no parent -> i/num/next/prev are None.
    assert t.i is None
    assert t.num is None
    assert t.next is None
    assert t.prev is None


def test_meter_get_set_inherit():
    from prosodic.parsing.meter import Meter
    t = TextModel('one two three')
    line = t.lines[0]
    # Explicitly set a meter object.
    m = Meter(max_s=2)
    assert line.get_meter(m) is m
    # No args -> unchanged.
    assert line.get_meter() is m
    # Different kwargs -> a new meter.
    m2 = line.get_meter(max_s=3)
    assert m2 is not m and m2.max_s == 3
    # Same kwargs again -> no change.
    assert line.get_meter(max_s=3) is m2
    # set_meter / meter property.
    line.set_meter(max_w=2)
    assert line.meter.max_w == 2
    # Sibling entities inherit the text-level meter.
    t2 = TextModel('alpha beta gamma')
    ml = t2.lines[0].get_meter()
    assert t2.wordtokens[0].get_meter() is ml


def test_entitylist_bool_txt_istextlist_children_type():
    t = TextModel('hello world')
    # __bool__: non-empty vs empty.
    assert bool(t.stanzas) is True
    assert bool(StanzaList(parent=t)) is False
    # Base EntityList.txt is None (StanzaList does not override it).
    assert t.stanzas.txt is None
    # is_text_list: a list whose parent is the text.
    assert t.stanzas.is_text_list
    # children_type property runs (a class or None).
    ct = t.stanzas.children_type
    assert ct is None or isinstance(ct, type)


def test_entitylist_append_sets_parent():
    t = TextModel('hello world')
    sl = StanzaList(parent=t)
    st = TextModel('foo bar').stanzas[0]
    # st has a parent already; append should not steal it, only add.
    n = len(sl.children)
    sl.append(st)
    assert len(sl.children) == n + 1
    assert sl.children[-1] is st
    # Appending a parentless entity adopts the list as its parent.
    orphan = Stanza()
    sl.append(orphan)
    assert orphan.parent is sl


def test_module_get_class():
    from prosodic.ents import get_class
    assert get_class('Line') is Line
    assert get_class('Stanza') is Stanza