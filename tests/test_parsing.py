import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from prosodic.imports import *
from pandas.testing import assert_frame_equal

disable_caching()

def test_feet():
    # iambic test
    tstr = "embrace " * 5
    l = TextModel(tstr).line1.parse()
    assert l.unbounded.num_parses == 1
    assert l.best_parse.is_rising == True
    assert l.best_parse.nary_feet == 2
    assert l.best_parse.foot_type == "iambic"

    # trochaic test
    tstr = "dungeon " * 5
    l = TextModel(tstr).line1.parse()
    assert l.num_parses == 1
    assert l.best_parse.is_rising == False
    assert l.best_parse.nary_feet == 2
    assert l.best_parse.foot_type == "trochaic"

    # anapestic
    tstr = "disembark " * 4
    l = TextModel(tstr).line1.parse()
    assert l.best_parse.is_rising == True
    assert l.best_parse.nary_feet == 3
    assert l.best_parse.foot_type == "anapestic"

    # dactylic test
    tstr = "dangerous " * 4
    l = TextModel(tstr).line1.parse()
    assert l.best_parse.is_rising == False
    assert l.best_parse.nary_feet == 3
    assert l.best_parse.foot_type == "dactylic"

    lx = TextModel(tstr).line1
    assert not lx._parses
    mopts1 = dict(max_s=1, max_w=1)
    lx.parse(**mopts1)
    assert lx._parses
    p1 = lx._parses
    m1 = lx.meter
    lx.parse(**mopts1)
    m2 = lx.meter
    assert m1 is m2
    assert lx._parses is p1

    lx.parse(max_s=2, max_w=2)
    m3 = lx.meter
    p2 = lx._parses
    assert m2 is not m3
    assert p1 is not p2


def test_text_parsing():
    t = TextModel(sonnet)
    print(t)
    assert len(t.lines) == 14
    t.parse(num_proc=1)
    assert len([p for pl in t.parses.unbounded for p in pl]) >= 14
    assert t.parses.num_lines == 14
    assert len(t.parses.stats(by="line")) == 14
    assert len(t.parses.stats(by="syll")) > 14


def test_exhaustive():
    # vectorized parser is always exhaustive — exhaustive param is a no-op
    t = TextModel(sonnet)
    parses1 = t.line1.parse(exhaustive=True)
    parses2 = t.line1.parse(exhaustive=True)
    assert parses1 is parses2  # same meter config, cached

    line = TextModel("A horse, a horse, my kingdom for a horse!").line1
    line.parse(max_s=10, max_w=10)
    assert line.parses.num_all == 1024
    assert line.parses.num_unbounded < 1024

    # ?
    # assert len(parses1.unbounded) < len(parses2.unbounded)


def test_bounding():
    s = "A horse a horse my kingdom for a horse"
    p1 = Parse(s, "ws" * 5)
    p2 = Parse(s, "sw" * 5)
    assert p1.bounds(p2)


def test_html():
    html = TextModel("disaster disaster disaster").line1.best_parse.to_html(
        as_str=True
    )
    assert "mtr_s" in html
    assert "viol_y" in html



def test_standalone_parsing():
    p1 = Parse("my horse my horse my kingdom for a horse")
    assert p1.num_peaks == 5
    p2 = Parse("the horse the horse the kingdom for a horse")
    assert p2.num_peaks == 5
    assert set(p1.violset) == {"s_unstress"}  # my is currently stressed!?
    assert set(p2.violset) == {"s_unstress"}

    p6 = Parse("my horse my horse my kingdom for a horse", "sw" * 5)
    assert p1 < p6
    assert p1.score < p6.score

    p7 = Parse("my horse my horse my kingdom for a horse", "ww" * 5)
    assert p7.foot_type == ""


def test_parselist():
    parses = TextModel("a horse " * 5).line1.parse()
    # assert parses.bounded # @todo fix this
    assert parses.unbounded
    assert len(parses) == len(parses.all)
    # assert len(parses.bounded) < len(parses) # @todo fix this

    ps1 = parses.stats_d(norm=False, incl_bounded=True)
    ps2 = parses.stats_d(norm=True, incl_bounded=True)
    print(ps1)
    print(ps2)
    assert set(ps1.keys()) == set(ps2.keys())
    assert set(ps1.values()) != set(ps2.values())

    html = parses._repr_html_()
    assert "</table>" in html

    l = TextModel("my horse my horse my kingdom for a horse").line1
    l.parse()
    assert l.best_parse.meter_str == "-+" * 5

    l = TextModel("my horse my horse my kingdom for a horse").line1
    # assert len(l.parses.unbounded)==1
    # assert len(l.bounded_parses)>1
    assert l.best_parse.meter_str == "-+" * 5


def test_constraints():
    l = TextModel("hello world " * 3).line1
    ckey = tuple(DEFAULT_CONSTRAINTS)
    l.parse(constraints=ckey)
    assert len(l.parses.unbounded)


def test_parse_iter():
    text = TextModel(sonnet)
    for parse_list in text.parse_iter():
        break
    # assert parsed_line.is_parseable
    parsed_line = parse_list.line
    assert parsed_line._parses
    assert parsed_line is text.lines[0]


def test_scansion():
    t = TextModel("into " * 2).line1
    t.parse(exhaustive=True, force=True)
    # vectorized parser picks best wordform variant, so all scansions are unique
    # original parser generates duplicates from multiple wordform combos
    assert len(t.parses.data) >= len(t.parses.scansions.data)


def test_vectorized_parser():
    """Test that vectorized parser matches original parser results."""
    from prosodic.parsing.meter import Meter
    m_vec = Meter(vectorized=True, parse_unit="line")

    cases = [
        ("embrace " * 5, "iambic"),
        ("dungeon " * 5, "trochaic"),
        ("disembark " * 4, "anapestic"),
        ("dangerous " * 4, "dactylic"),
        ("a horse a horse my kingdom for a horse", "iambic"),
        ("Shall I compare thee to a summers day", None),
        ("To be or not to be that is the question", None),
    ]

    for txt, expected_foot in cases:
        t_orig = TextModel(txt)
        t_orig.parse()
        orig = t_orig.lines[0].best_parse

        t_vec = TextModel(txt)
        t_vec.parse(meter=m_vec, combine_by=None)
        vec = t_vec.lines[0].best_parse

        # violations must match (exact meter_str may differ on ties)
        assert orig.num_viols == vec.num_viols, (
            f"{txt!r}: viols mismatch {orig.num_viols} vs {vec.num_viols}"
        )
        assert orig.score == vec.score, (
            f"{txt!r}: score mismatch {orig.score} vs {vec.score}"
        )

        # foot type must match
        if expected_foot:
            assert vec.foot_type == expected_foot, (
                f"{txt!r}: expected {expected_foot}, got {vec.foot_type}"
            )
        assert orig.foot_type == vec.foot_type, (
            f"{txt!r}: foot mismatch {orig.foot_type} vs {vec.foot_type}"
        )


def test_vectorized_bounding():
    """Test that iambic bounds trochaic for 'a horse...'"""
    from prosodic.parsing.meter import Meter
    m_vec = Meter(vectorized=True, parse_unit="line")

    txt = "a horse a horse my kingdom for a horse"
    t = TextModel(txt)
    t.parse(meter=m_vec, combine_by=None)
    bp = t.lines[0].best_parse

    assert bp.foot_type == "iambic"
    assert bp.meter_str == "-+-+-+-+-+"


def test_entity_path_evaluates_all_constraints():
    """Regression: parse_batch (the entity/web parse path) must evaluate every
    constraint via the vectorized dispatch, agreeing with parse_batch_from_df.

    Before the two paths were unified, parse_batch used a single-line evaluator
    that hardcoded only 7 constraints, so clash/lapse/s_func/w_heavy/s_light/
    word_foot were silently all-zero on the entity path (which every web
    endpoint uses)."""
    from prosodic.parsing.meter import Meter
    from prosodic.parsing.vectorized import parse_batch, parse_batch_from_df

    m = Meter(constraints=["w_stress", "s_unstress", "clash", "s_func",
                           "w_heavy", "word_foot"])
    names = list(m.constraints.keys())
    line = "And dig deep trenches in thy beautys field"

    ent_mass = parse_batch(TextModel(line).lines, m)[0][1]._all_viols.sum(axis=(0, 1))
    by = {n: int(ent_mass[i]) for i, n in enumerate(names)}
    # these previously-ignored constraints all fire on this line
    for n in ["clash", "s_func", "w_heavy", "word_foot"]:
        assert by[n] > 0, f"{n} not evaluated on the entity path (mass={by[n]})"

    # entity path must agree with the DF path on constraint totals
    t = TextModel(line)
    df_mass = list(parse_batch_from_df(t._syll_df, m).values())[0]._all_viols.sum(axis=(0, 1))
    assert [int(x) for x in df_mass] == [int(x) for x in ent_mass], \
        "DF and entity paths disagree on constraint totals"


def _reference_bounding(viol_sums):
    """Straightforward, un-tiled harmonic bounding. A scansion j is bounded iff
    some scansion i dominates it (<= on every constraint, < on at least one).
    Used as the ground truth the chunked/tiled implementation must match."""
    import numpy as np
    L, S, C = viol_sums.shape
    if S <= 1:
        return np.ones((L, S), dtype=bool)
    diff = viol_sums[:, :, None, :] - viol_sums[:, None, :, :]  # (L, S, S, C)
    i_leq_j = (diff <= 0).all(axis=3)
    i_lt_j = i_leq_j & (diff < 0).any(axis=3)
    bounded = i_lt_j.any(axis=1)
    return ~bounded


def test_bounding_tiled_equals_reference():
    """Memory-budgeted (chunked over L, tiled over S x S) harmonic bounding must
    return the exact same unbounded mask as the plain O(S^2 C) reference, for
    inputs of varied L / S / C and at several memory budgets that force real
    tiling. This guards the C6/F4 optimization: a memory win that changed which
    parses are bounded would be a silent correctness bug."""
    import numpy as np
    from prosodic.parsing import vectorized as V

    rng = np.random.default_rng(12345)
    dev = V.get_device()

    cases = []
    # (L, S, C, make_perfect)
    for L, S, C in [(1, 1, 4), (2, 2, 3), (3, 10, 5), (4, 25, 6),
                    (2, 40, 4), (3, 64, 7), (1, 128, 8), (5, 30, 5),
                    (2, 200, 6)]:
        # non-perfect: shift up by 1 so no all-zero row (forces pairwise path)
        cases.append((rng.integers(0, 3, size=(L, S, C)) + 1).astype(np.int64))
        # binary values -> many ties / duplicate rows (dominance edge cases)
        cases.append(rng.integers(0, 2, size=(L, S, C)).astype(np.int64))

    # a case with duplicate rows (equal vectors must NOT bound each other)
    dup = (rng.integers(0, 3, size=(2, 50, 4)) + 1).astype(np.int64)
    dup[:, 1, :] = dup[:, 0, :]
    dup[:, 7, :] = dup[:, 0, :]
    cases.append(dup)

    # budgets small enough to force multi-tile / multi-chunk decomposition,
    # plus the module default (no forced tiling for small S).
    budgets = [4096, 50_000, 500_000, None]

    for arr in cases:
        ref = _reference_bounding(arr)
        for budget in budgets:
            got = V._compute_bounding_batch_numpy(arr.copy(), budget=budget)
            assert np.array_equal(ref, got), (
                f"numpy tiled != reference (shape={arr.shape}, budget={budget})")
            if dev is not None:
                got_t = V._compute_bounding_batch_torch(arr.copy(), dev, budget=budget)
                assert np.array_equal(ref, got_t), (
                    f"torch tiled != reference (shape={arr.shape}, budget={budget})")

        # single-line entry points must agree with the batch reference too
        for li in range(arr.shape[0]):
            v_sc = arr[li]
            exp = ref[li]
            got_sl = V._compute_bounding_numpy(v_sc.copy(), budget=4096)
            assert np.array_equal(exp, got_sl), "single-line numpy tiled mismatch"
            if dev is not None:
                got_slt = V._compute_bounding_torch(v_sc.copy(), dev, budget=4096)
                assert np.array_equal(exp, got_slt), "single-line torch tiled mismatch"

    # block-size helper never exceeds the requested element budget
    Lc, Ti, Tj = V._bounding_block_sizes(4, 8362, 14, bytes_per_elem=8, budget=V.BOUNDING_MEM_BUDGET)
    assert Lc * Ti * Tj * 14 * 8 <= V.BOUNDING_MEM_BUDGET
    # small problems are not tiled (single-shot, identical to the old path)
    assert V._bounding_block_sizes(3, 20, 6, bytes_per_elem=8) == (3, 20, 20)


def test_df_and_entity_paths_agree_on_ambiguous_lines():
    """The DF/vector path (text.parse) must explore the full cartesian product
    of pronunciation variants, like the entity path, so it finds the true best
    parse on ambiguous lines. Regression for AUDIT C9/M3: the DF path used to
    build only 'diagonal' form combos and returned worse-than-optimal parses on
    ~18% of Shakespeare lines (once missing a perfect parse, reporting 3 viols)."""
    from prosodic.parsing.meter import Meter
    from prosodic.parsing.vectorized import parse_batch, parse_batch_from_df
    lines = [
        "More than that tongue that more hath more express'd.",
        "Shall I compare thee to a summers day",
        "When forty winters shall besiege thy brow",
        "That thereby beautys rose might never die",
    ]
    t = TextModel("\n".join(lines))
    m = Meter()
    df = parse_batch_from_df(t._syll_df, m)
    ent = {(wt[0].line_num if len(wt) else None): pl
           for wt, pl in parse_batch(t.lines, m)
           if pl is not None and hasattr(pl, "_all_viols")}
    for ln, dpl in df.items():
        epl = ent.get(ln)
        assert epl is not None, f"line {ln} missing from entity path"
        assert abs(dpl.best_parse.score - epl.best_parse.score) < 1e-9, (
            f"line {ln}: DF best score {dpl.best_parse.score} != "
            f"entity {epl.best_parse.score} — DF under-explored variants"
        )


def test_df_path_finds_optimal_on_ambiguous_line():
    # A perfect (0-violation) parse of this line exists only in a non-diagonal
    # pronunciation combination; the DF path must find it.
    t = TextModel("More than that tongue that more hath more express'd.")
    assert t.parse()[0].best_parse.score == 0


def test_best_parse_cooptimal_signal():
    """best_parse exposes num_cooptimal / is_tied so a co-optimal tie among
    equally-scoring scansions is visible instead of being silently resolved.
    The tiebreak itself stays metrically neutral; this only reports how many
    DISTINCT best meter strings were equally optimal (given the chosen
    pronunciation)."""
    unique_line = "Shall I compare thee to a summers day"
    tied_line = "Were an all-eating shame and thriftless praise"
    t = TextModel(unique_line + "\n" + tied_line)
    res = t.parse()
    for pl in res:
        bp = pl.best_parse
        assert bp is not None
        assert bp.num_cooptimal >= 1
        assert bp.is_tied == (bp.num_cooptimal > 1)
        # num_cooptimal == number of DISTINCT co-optimal meter strings among the
        # unbounded parses (resolution ties on the same +/- pattern count once)
        n = len({p.meter_str for p in pl.unbounded if abs(p.score - bp.score) < 1e-9})
        assert bp.num_cooptimal == n

    assert res[0].best_parse.is_tied is False
    assert res[0].best_parse.num_cooptimal == 1
    assert res[1].best_parse.is_tied is True
    assert res[1].best_parse.num_cooptimal >= 2
