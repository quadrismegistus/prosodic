"""Tests for v3 DataFrame-first architecture.

Covers: syll_df construction, lazy entity construction, DF-only parse path,
parse_df/parsed_df, save/load, linepart parsing, SyllData, sorted parses,
bounding optimizations, and the full entity-free workflow.
"""
import os
import sys
import shutil
import tempfile

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from prosodic.imports import *

disable_caching()

sonnet = """Those hours, that with gentle work did frame
The lovely gaze where every eye doth dwell,
Will play the tyrants to the very same
And that unfair which fairly doth excel:
For never-resting time leads summer on
To hideous winter and confounds him there;
Sap check'd with frost and lusty leaves quite gone,
Beauty o'ersnow'd and bareness every where:
Then, were not summer's distillation left,
A liquid prisoner pent in walls of glass,
Beauty's effect with beauty were bereft,
Nor it nor no remembrance what it was:
But flowers distill'd though they with winter meet,
Leese but their show; their substance still lives sweet."""


# --- syll_df construction ---

class TestSyllDf:
    def test_build_basic(self):
        t = TextModel("hello world")
        assert t._syll_df is not None
        assert len(t._syll_df) > 0

    def test_columns(self):
        t = TextModel("From fairest creatures we desire increase")
        df = t.df
        expected_cols = {
            'word_num', 'line_num', 'para_num', 'sent_num', 'sentpart_num',
            'linepart_num', 'word_txt', 'is_punc', 'form_idx', 'num_forms',
            'syll_idx', 'syll_ipa', 'syll_text', 'is_stressed', 'is_heavy',
            'is_strong', 'is_weak', 'is_functionword',
        }
        assert expected_cols.issubset(set(df.columns))

    def test_multiline(self):
        t = TextModel("hello world\ngoodbye moon")
        df = t.df
        assert set(df['line_num'].unique()) == {1, 2}

    def test_punctuation_rows(self):
        t = TextModel("hello, world!")
        df = t.df
        punc = df[df['is_punc'] == 1]
        assert len(punc) >= 1  # comma or exclamation

    def test_ambiguous_words(self):
        t = TextModel("desire increase")
        df = t.df
        # these words have multiple pronunciations
        assert (df['num_forms'] > 1).any()
        assert len(df[df['form_idx'] > 0]) > 0

    def test_stress_features(self):
        t = TextModel("hello")
        df = t.df[t.df['is_punc'] == 0]
        # "hello" has stressed and unstressed syllables
        assert df['is_stressed'].any()
        assert not df['is_stressed'].all()

    def test_functionword(self):
        t = TextModel("the cat")
        df = t.df[(t.df['is_punc'] == 0) & (t.df['form_idx'] == 0)]
        # "the" is a function word (1 syll, unstressed)
        the_rows = df[df['word_txt'].str.strip() == 'the']
        assert the_rows['is_functionword'].all()

    def test_df_property(self):
        t = TextModel("test text")
        assert t.df is t._syll_df


# --- Lazy entity construction ---

class TestLazyEntities:
    def test_children_not_built_on_init(self):
        t = TextModel("hello world")
        assert t._children_built is False

    def test_children_built_on_access(self):
        t = TextModel("hello world")
        _ = t.children
        assert t._children_built is True
        assert len(t.children) == 2

    def test_lines_triggers_children(self):
        t = TextModel("hello world\ngoodbye moon")
        assert t._children_built is False
        lines = t.lines
        assert t._children_built is True
        assert len(lines) == 2

    def test_parse_does_not_build_entities(self):
        t = TextModel("From fairest creatures we desire increase")
        t.parse()
        assert t._children_built is False

    def test_children_setter(self):
        t = TextModel("hello world")
        assert t._children_built is False
        t.children = [1, 2, 3]
        assert t._children_built is True


# --- DF-only parse path ---

class TestDfParsePath:
    def test_basic_parse(self):
        t = TextModel("From fairest creatures we desire increase")
        t.parse()
        assert t._children_built is False
        assert len(t._line_parse_results) > 0

    def test_best_parse_without_entities(self):
        t = TextModel("From fairest creatures we desire increase")
        t.parse()
        # access best_parse via _line_parse_results without building entities
        for meter_key, results in t._line_parse_results.items():
            for line_num, pl in results.items():
                bp = pl.best_parse
                assert bp is not None
                assert bp.meter_str == "-+-+-+-+-+"

    def test_multiline_parse(self):
        t = TextModel(sonnet)
        t.parse()
        assert t._children_built is False
        for mk, results in t._line_parse_results.items():
            assert len(results) == 14

    def test_parse_attaches_to_lines(self):
        t = TextModel("hello world\ngoodbye moon")
        t.parse()
        lines = t.lines  # triggers entity build + attachment
        for line in lines:
            assert line._parses is not None

    def test_linepart_parse(self):
        t = TextModel("To be or not to be, that is the question.")
        pl = t.parse(parse_unit='linepart', combine_by=None)
        assert len(pl) == 2
        bp1 = pl[0].best_parse
        bp2 = pl[1].best_parse
        assert bp1 is not None
        assert bp2 is not None

    def test_linepart_no_entities(self):
        t = TextModel("To be or not to be, that is the question.")
        t.parse(parse_unit='linepart', combine_by=None)
        assert t._children_built is False


# --- parsed_df / get_parsed_df ---

class TestParsedDf:
    def test_parsed_df_cached_property(self):
        t = TextModel("From fairest creatures we desire increase")
        pdf = t.parsed_df
        assert len(pdf) > 0
        assert 'line_num' in pdf.columns
        assert 'meter_val' in pdf.columns
        assert 'syll_txt' in pdf.columns
        # cached
        assert t.parsed_df is pdf

    def test_parsed_df_columns(self):
        t = TextModel("From fairest creatures we desire increase")
        pdf = t.parsed_df
        assert 'is_stressed' in pdf.columns
        assert 'is_prom' in pdf.columns
        assert 'score' in pdf.columns

    def test_parsed_df_no_entities(self):
        t = TextModel("From fairest creatures we desire increase")
        _ = t.parsed_df
        assert t._children_built is False

    def test_get_parsed_df_custom_meter(self):
        t = TextModel("a horse a horse my kingdom for a horse")
        df1 = t.get_parsed_df()
        df2 = t.get_parsed_df(max_s=1, max_w=1)
        # different meter configs should produce different results
        assert len(df1) > 0
        assert len(df2) > 0

    def test_parsed_df_multiline(self):
        t = TextModel(sonnet)
        pdf = t.parsed_df
        assert pdf['line_num'].nunique() == 14


# --- Save / Load ---

class TestSaveLoad:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.tmpdir)

    def test_save_creates_files(self):
        t = TextModel("From fairest creatures we desire increase")
        path = t.save(os.path.join(self.tmpdir, "test1"))
        assert os.path.exists(os.path.join(path, "syll.parquet"))
        assert os.path.exists(os.path.join(path, "parsed.parquet"))
        assert os.path.exists(os.path.join(path, "meta.json"))

    def test_meta_json_contents(self):
        t = TextModel("hello world")
        path = t.save(os.path.join(self.tmpdir, "test2"))
        import json
        with open(os.path.join(path, "meta.json")) as f:
            meta = json.load(f)
        assert meta['txt'] == "hello world"
        assert meta['lang'] == "en"
        assert 'num_lines' in meta

    def test_load_returns_textmodel(self):
        t = TextModel("From fairest creatures we desire increase")
        path = t.save(os.path.join(self.tmpdir, "test3"))
        t2 = TextModel.load(path)
        assert isinstance(t2, TextModel)
        assert t2._txt == t._txt
        assert t2.lang == t.lang

    def test_load_has_syll_df(self):
        t = TextModel("From fairest creatures we desire increase")
        path = t.save(os.path.join(self.tmpdir, "test4"))
        t2 = TextModel.load(path)
        assert t2._syll_df is not None
        assert len(t2.df) == len(t.df)

    def test_load_has_cached_parsed_df(self):
        t = TextModel("From fairest creatures we desire increase")
        path = t.save(os.path.join(self.tmpdir, "test5"))
        t2 = TextModel.load(path)
        pdf = t2.parsed_df
        assert len(pdf) > 0
        assert t2._children_built is False  # no entities needed

    def test_load_can_reparse(self):
        t = TextModel("From fairest creatures we desire increase")
        path = t.save(os.path.join(self.tmpdir, "test6"))
        t2 = TextModel.load(path)
        t2.parse()  # uses cached syll_df
        assert t2._children_built is False

    def test_load_can_build_entities(self):
        t = TextModel("From fairest creatures we desire increase\nThat thereby beauty rose might never die")
        path = t.save(os.path.join(self.tmpdir, "test7"))
        t2 = TextModel.load(path)
        lines = t2.lines
        assert len(lines) == 2
        assert t2._children_built is True

    def test_load_entities_have_parses(self):
        t = TextModel("From fairest creatures we desire increase")
        path = t.save(os.path.join(self.tmpdir, "test8"))
        t2 = TextModel.load(path)
        t2.parse()
        line = t2.lines[0]
        bp = line.best_parse
        assert bp is not None
        assert bp.meter_str == "-+-+-+-+-+"

    def test_round_trip_shakespeare(self):
        txt = open('corpora/corppoetry_en/en.shakespeare.txt').read()
        t = TextModel(txt)
        path = t.save(os.path.join(self.tmpdir, "shak"))
        t2 = TextModel.load(path)
        # syll_df should match
        assert len(t2.df) == len(t.df)
        # parsed_df should match
        pdf1 = t.parsed_df
        pdf2 = t2.parsed_df
        assert len(pdf1) == len(pdf2)


# --- SyllData ---

class TestSyllData:
    def test_sylldata_properties(self):
        from prosodic.texts.syll_df import SyllData
        sd = SyllData(ipa="'hɛ", txt="hel", is_stressed=True,
                      is_heavy=False, is_strong=True, is_weak=False)
        assert sd.ipa == "'hɛ"
        assert sd.txt == "hel"
        assert sd.is_stressed is True
        assert sd.is_heavy is False
        assert sd.is_strong is True
        assert sd.is_weak is False
        assert sd.stress == "P"

    def test_sylldata_in_parse(self):
        t = TextModel("From fairest creatures we desire increase")
        t.parse()
        # DF path uses SyllData, not real Syllable
        for mk, results in t._line_parse_results.items():
            for ln, pl in results.items():
                bp = pl.best_parse
                slot = bp.children[0][0]
                # slot.unit should be SyllData (DF path)
                assert hasattr(slot.unit, 'ipa')
                assert hasattr(slot.unit, 'is_stressed')


# --- Sorted parses ---

class TestSortedParses:
    def test_unbounded_sorted_by_score(self):
        t = TextModel("a horse a horse my kingdom for a horse")
        t.parse(max_s=2, max_w=2)
        pl = list(t._line_parse_results.values())[0][1]
        unbounded = pl.unbounded
        if len(unbounded) > 1:
            scores = [p.score for p in unbounded]
            assert scores == sorted(scores)

    def test_data_sorted_by_score(self):
        t = TextModel("a horse a horse my kingdom for a horse")
        t.parse(max_s=2, max_w=2)
        pl = list(t._line_parse_results.values())[0][1]
        all_parses = pl.data
        scores = [pl._all_scores[i] for i in range(len(pl._all_scansions))]
        data_scores = [p.score for p in all_parses]
        assert data_scores == sorted(data_scores)

    def test_best_parse_is_minimum(self):
        t = TextModel("From fairest creatures we desire increase")
        t.parse()
        pl = list(t._line_parse_results.values())[0][1]
        bp = pl.best_parse
        for p in pl.unbounded:
            assert bp.score <= p.score


# --- Bounding optimizations ---

class TestBounding:
    def test_perfect_parse_bounds_all(self):
        # "embrace" x5 is perfect iambic — 0 violations
        t = TextModel("embrace " * 5)
        t.parse()
        pl = list(t._line_parse_results.values())[0][1]
        bp = pl.best_parse
        assert bp.score == 0
        # perfect parse should bound everything
        assert pl.num_unbounded == 1

    def test_bounding_batch(self):
        from prosodic.parsing.vectorized import compute_bounding_batch
        import numpy as np
        # 10 lines, 5 scansions, 3 constraints
        v = np.array([
            [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0], [0, 0, 1]],
        ] * 10, dtype=np.int8)
        masks = compute_bounding_batch(v)
        assert masks.shape == (10, 5)
        # first scansion (all zeros) should be unbounded, bound everything else
        assert masks[:, 0].all()


# --- Edge cases ---

class TestEdgeCases:
    def test_single_word(self):
        t = TextModel("hello")
        t.parse()
        assert t._children_built is False

    def test_empty_parse_result(self):
        t = TextModel("I")  # single syllable, too short to parse
        t.parse()
        # should not crash

    def test_finnish(self):
        t = TextModel("hyvaa paivaa", lang="fi")
        assert t.df is not None
        assert len(t.df) > 0

    def test_multiple_stanzas(self):
        t = TextModel(sonnet)
        pdf = t.parsed_df
        assert pdf['line_num'].nunique() == 14
