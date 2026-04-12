"""Tests to improve coverage of Parse, ParseList, Entity, WordTokenList, Lines, and Stanzas."""
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from prosodic.imports import *
disable_caching()

# Shared fixtures
SONNET_LINE = "From fairest creatures we desire increase"
TWO_LINES = "From fairest creatures we desire increase\nThat thereby beauty's rose might never die"
FULL_SONNET = """Those hours, that with gentle work did frame
The lovely gaze where every eye doth dwell,
Will play the tyrants to the very same
And that unfair which fairly doth excel"""


# =============================================================================
# 1. Parse object tests
# =============================================================================

class TestParseConstructor:
    def test_parse_from_string(self):
        """Parse() can be constructed from a plain string."""
        from prosodic.parsing.parses import Parse
        p = Parse("hello world")
        assert p is not None
        assert p.num_sylls > 0

    def test_parse_from_string_with_scansion(self):
        """Parse() with explicit scansion string."""
        from prosodic.parsing.parses import Parse
        p = Parse("hello world", scansion="wsww")
        assert p is not None
        assert len(p.positions) > 0


class TestParseProperties:
    def setup_method(self):
        self.text = TextModel(SONNET_LINE)
        self.text.parse()
        self.line = self.text.lines[0]
        self.parse = self.line.best_parse

    def test_positions(self):
        assert len(self.parse.positions) > 0

    def test_slots(self):
        assert len(self.parse.slots) > 0
        assert self.parse.num_sylls == len(self.parse.slots)

    def test_score_is_numeric(self):
        assert isinstance(self.parse.score, (int, float))

    def test_scores_dict(self):
        scores = self.parse.scores
        assert isinstance(scores, dict)
        for k, v in scores.items():
            assert isinstance(v, (int, float))

    def test_num_viols(self):
        assert isinstance(self.parse.num_viols, int)
        assert self.parse.num_viols >= 0

    def test_meter_str(self):
        ms = self.parse.meter_str
        assert isinstance(ms, str)
        assert len(ms) == self.parse.num_sylls
        assert set(ms).issubset({'+', '-'})

    def test_stress_str(self):
        ss = self.parse.stress_str
        assert isinstance(ss, str)
        assert len(ss) == self.parse.num_sylls
        assert set(ss).issubset({'+', '-'})

    def test_txt(self):
        txt = self.parse.txt
        assert isinstance(txt, str)
        assert len(txt) > 0

    def test_is_rising(self):
        val = self.parse.is_rising
        assert val is True or val is False or val is None

    def test_nary_feet(self):
        n = self.parse.nary_feet
        assert n in (2, 3)

    def test_foot_type(self):
        ft = self.parse.foot_type
        assert ft in ("iambic", "trochaic", "anapestic", "dactylic", "")

    def test_is_complete(self):
        assert self.parse.is_complete is True


class TestParseBounds:
    def setup_method(self):
        self.text = TextModel(SONNET_LINE)
        self.text.parse()
        self.line = self.text.lines[0]
        self.parses = self.line.parses

    def test_bounds_method(self):
        """Parse.bounds() returns bool."""
        if len(self.parses) >= 2:
            p1 = self.parses[0]
            p2 = self.parses[1]
            result = p1.bounds(p2)
            assert isinstance(result, bool)

    def test_bounding_relation(self):
        """Parse.bounding_relation() returns a Bounding enum."""
        if len(self.parses) >= 2:
            p1 = self.parses[0]
            p2 = self.parses[1]
            rel = p1.bounding_relation(p2)
            assert rel in (Bounding.bounds, Bounding.bounded, Bounding.equal, Bounding.unequal)


class TestParseHtml:
    def setup_method(self):
        self.text = TextModel(SONNET_LINE)
        self.text.parse()
        self.line = self.text.lines[0]
        self.parse = self.line.best_parse

    def test_to_html_returns_string(self):
        html = self.parse.to_html(as_str=True)
        assert isinstance(html, str)
        assert len(html) > 0

    def test_repr_html(self):
        html = self.parse._repr_html_()
        assert isinstance(html, str)


class TestParseConcat:
    def test_concat_two_parses(self):
        """Parse.concat() combines multiple parses constructed from strings."""
        from prosodic.parsing.parses import Parse
        p1 = Parse("hello world")
        p2 = Parse("goodbye moon")
        combined = Parse.concat(p1, p2)
        assert combined is not None
        assert combined.num_sylls == p1.num_sylls + p2.num_sylls


class TestParseGetDf:
    def setup_method(self):
        self.text = TextModel(SONNET_LINE)
        self.text.parse()
        self.line = self.text.lines[0]
        self.parse = self.line.best_parse

    def test_get_df_returns_dataframe(self):
        df = self.parse.get_df()
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_get_df_has_columns(self):
        df = self.parse.get_df()
        # Should have meter/stress related columns
        cols = set(df.columns) | set(df.index.names)
        assert len(cols) > 0


class TestParseToFromDict:
    def setup_method(self):
        from prosodic.parsing.parses import Parse
        # Construct a parse directly so it has full wordtokens
        self.parse = Parse("hello world")

    def test_to_dict(self):
        """Parse.to_dict() works when parse has wordtokens."""
        d = self.parse.to_dict()
        assert isinstance(d, dict)
        assert "Parse" in d

    def test_round_trip(self):
        from prosodic.parsing.parses import Parse
        d = self.parse.to_dict()
        p2 = Parse.from_dict(d, use_registry=False)
        assert p2 is not None
        assert p2.meter_str == self.parse.meter_str
        assert p2.stress_str == self.parse.stress_str


# =============================================================================
# 2. ParseList tests
# =============================================================================

class TestParseList:
    def setup_method(self):
        self.text = TextModel(SONNET_LINE)
        self.text.parse()
        self.line = self.text.lines[0]
        self.parselist = self.line.parses

    def test_unbounded(self):
        ub = self.parselist.unbounded
        assert isinstance(ub, ParseList)
        assert all(not p.is_bounded for p in ub)

    def test_bounded(self):
        bd = self.parselist.bounded
        assert isinstance(bd, ParseList)
        assert all(p.is_bounded for p in bd)

    def test_best_parse(self):
        bp = self.parselist.best_parse
        assert bp is not None
        assert bp.is_bounded is False

    def test_repr_html(self):
        html = self.parselist._repr_html_()
        assert isinstance(html, str)
        assert len(html) > 0

    def test_stats_default(self):
        """ParseList.stats() returns a DataFrame."""
        df = self.parselist.stats()
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_stats_by_syll(self):
        """ParseList.stats(by='syll') returns syllable-level stats."""
        df = self.parselist.stats(by="syll")
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0


class TestParseListScansions:
    def test_scansions(self):
        """ParseList.scansions returns unique scansions."""
        t = TextModel(SONNET_LINE)
        t.parse()
        line = t.lines[0]
        pl = line.parses
        scans = pl.scansions
        assert scans is not None
        assert len(scans) >= 1

    def test_num_unbounded(self):
        """num_unbounded is at least 1 for a valid parse."""
        t = TextModel(SONNET_LINE)
        t.parse()
        line = t.lines[0]
        pl = line.parses
        assert pl.num_unbounded >= 1


# =============================================================================
# 3. Entity base tests
# =============================================================================

class TestEntityKey:
    def test_key_uniqueness(self):
        t = TextModel(TWO_LINES)
        keys = set()
        for line in t.lines:
            assert line.key not in keys
            keys.add(line.key)

    def test_key_is_string(self):
        t = TextModel("hello world")
        line = t.lines[0]
        assert isinstance(line.key, str)
        assert len(line.key) > 0


class TestEntityRoot:
    def test_root_is_text(self):
        t = TextModel(TWO_LINES)
        line = t.lines[0]
        assert line.root is t

    def test_root_of_root_is_self(self):
        t = TextModel("hello")
        assert t.root is t

    def test_deep_root(self):
        t = TextModel("hello world")
        sylls = t.syllables
        if sylls and len(sylls):
            assert sylls[0].root is t


class TestEntityGetList:
    def setup_method(self):
        self.text = TextModel(FULL_SONNET)

    def test_get_lines(self):
        lines = self.text.get_list("lines")
        assert lines is not None
        assert len(lines) == 4

    def test_get_stanzas(self):
        stanzas = self.text.get_list("stanzas")
        assert stanzas is not None
        assert len(stanzas) >= 1

    def test_get_wordtokens(self):
        wts = self.text.get_list("wordtokens")
        assert wts is not None
        assert len(wts) > 0

    def test_get_syllables(self):
        sylls = self.text.get_list("sylls")
        assert sylls is not None
        assert len(sylls) > 0

    def test_line_get_stanza(self):
        """A line can find its parent stanza."""
        line = self.text.lines[0]
        stanzas = line.get_list("stanza")
        assert stanzas is not None


class TestEntityToFromDict:
    def test_to_dict(self):
        t = TextModel("hello world")
        d = t.to_dict()
        assert isinstance(d, dict)
        assert "TextModel" in d

    def test_from_dict_round_trip(self):
        t = TextModel("hello world")
        d = t.to_dict()
        t2 = Entity.from_dict(d, use_registry=False)
        assert t2 is not None


class TestEntityClearCachedProperties:
    def test_clear_removes_cached(self):
        t = TextModel("hello world")
        # Access a cached_property to populate it - use 'root' which is cached on Entity
        _ = t.root
        assert "root" in t.__dict__
        t.clear_cached_properties()
        assert "root" not in t.__dict__

    def test_clear_on_line(self):
        t = TextModel(SONNET_LINE)
        line = t.lines[0]
        # Force a cached property
        _ = line.root  # root is cached_property
        assert "root" in line.__dict__
        line.clear_cached_properties()
        assert "root" not in line.__dict__


# =============================================================================
# 4. WordTokenList tests
# =============================================================================

class TestWordTokenList:
    def setup_method(self):
        self.text = TextModel(SONNET_LINE)

    def test_parse_returns_parses(self):
        line = self.text.lines[0]
        result = line.parse()
        assert result is not None

    def test_best_parse(self):
        line = self.text.lines[0]
        line.parse()
        bp = line.best_parse
        assert bp is not None

    def test_num_sylls(self):
        line = self.text.lines[0]
        assert line.num_sylls > 0

    def test_txt(self):
        wts = self.text.wordtokens
        assert isinstance(wts.txt, str)
        assert len(wts.txt) > 0


class TestIterWordtokenMatrix:
    def test_single_form_words(self):
        """Words with a single pronunciation yield one matrix entry."""
        t = TextModel("the cat")
        wts = t.wordtokens
        matrix = list(wts.iter_wordtoken_matrix())
        assert len(matrix) >= 1

    def test_matrix_entries_are_wordtokenlists(self):
        t = TextModel("the cat")
        wts = t.wordtokens
        for entry in wts.iter_wordtoken_matrix():
            assert hasattr(entry, 'wordforms')


# =============================================================================
# 5. Lines tests
# =============================================================================

class TestLineListFromWordtokens:
    def test_from_wordtokens(self):
        t = TextModel(TWO_LINES)
        wts = t.wordtokens
        lines = LineList.from_wordtokens(wts, text=t)
        assert lines is not None
        assert len(lines) == 2


class TestLineProperties:
    def setup_method(self):
        self.text = TextModel(TWO_LINES)

    def test_line_num(self):
        for i, line in enumerate(self.text.lines):
            assert line.num == i + 1

    def test_line_txt(self):
        lines = self.text.lines
        assert "fairest" in lines[0].txt
        assert "beauty" in lines[1].txt

    def test_line_parse(self):
        self.text.parse()
        line = self.text.lines[0]
        assert line._parses is not None

    def test_line_best_parse(self):
        self.text.parse()
        line = self.text.lines[0]
        bp = line.best_parse
        assert bp is not None
        assert bp.is_complete

    def test_line_repr(self):
        line = self.text.lines[0]
        r = repr(line)
        assert "Line" in r


# =============================================================================
# 6. Stanzas tests
# =============================================================================

class TestStanzaListFromWordtokens:
    def test_from_wordtokens(self):
        t = TextModel(FULL_SONNET)
        wts = t.wordtokens
        stanzas = StanzaList.from_wordtokens(wts, text=t)
        assert stanzas is not None
        assert len(stanzas) >= 1


class TestStanzaProperties:
    def setup_method(self):
        self.text = TextModel(FULL_SONNET)

    def test_stanza_lines(self):
        stanza = self.text.stanzas[0]
        lines = stanza.lines
        assert lines is not None
        assert len(lines) == 4

    def test_stanza_repr(self):
        stanza = self.text.stanzas[0]
        r = repr(stanza)
        assert "Stanza" in r

    def test_stanza_txt(self):
        stanza = self.text.stanzas[0]
        txt = stanza.txt
        assert isinstance(txt, str)
        assert len(txt) > 0


# =============================================================================
# Additional edge-case tests
# =============================================================================

class TestParseComparison:
    def test_sort_order(self):
        """Parses are sortable; best_parse is the minimum."""
        t = TextModel(SONNET_LINE)
        t.parse()
        line = t.lines[0]
        parses = list(line.parses)
        sorted_parses = sorted(parses)
        assert sorted_parses[0] is line.best_parse

    def test_parse_rank(self):
        """After ranking, parse_rank=1 is best."""
        t = TextModel(SONNET_LINE)
        t.parse()
        bp = t.lines[0].best_parse
        assert bp.parse_rank == 1


class TestParseAttrs:
    def test_attrs_dict(self):
        t = TextModel(SONNET_LINE)
        t.parse()
        p = t.lines[0].best_parse
        a = p.attrs
        assert isinstance(a, dict)
        assert "meter" in a
        assert "stress" in a
        assert "score" in a
        assert "num_viols" in a

    def test_stats_d(self):
        t = TextModel(SONNET_LINE)
        t.parse()
        p = t.lines[0].best_parse
        sd = p.stats_d()
        assert isinstance(sd, dict)
        assert "num_sylls" in sd
        assert "num_words" in sd


class TestParseViolations:
    def test_violset(self):
        t = TextModel(SONNET_LINE)
        t.parse()
        p = t.lines[0].best_parse
        vs = p.violset
        # violset is a Multiset
        assert isinstance(vs, Multiset)

    def test_viold(self):
        t = TextModel(SONNET_LINE)
        t.parse()
        p = t.lines[0].best_parse
        vd = p.viold
        assert isinstance(vd, Counter)
