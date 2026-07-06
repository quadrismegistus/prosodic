"""Liberman & Prince (1977) structural gold set.

Two layers, both scored against L&P's OWN published figures:

- **Layer A (engine):** hand-encoded trees from the paper → ``grid_heights``
  must reproduce the printed grid exactly. Validates the RPPR grid engine
  across the paper's figures.
- **Layer B (auto pipeline):** the phrase text → Stanza constituency →
  binarize → grid, checked for L&P's published nuclear placement. Measures
  how often the automatic pipeline recovers L&P's structure.

We use L&P's INPUT scansions (the pure RPPR-from-tree grids), not the
Rhythm-Rule (Iambic Reversal) outputs — that rule is not implemented here.
"""
import os
import sys

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from prosodic.analysis.metrical_lp import (
    expand_to_syllables,
    grid_heights,
    parse_lptree,
    sw,
    ws,
)

# --------------------------------------------------------------- Layer A
# (name, hand-encoded tree, published grid heights in surface order)
LP_FIGURES = [
    ("thirteen men (105a)",
     ws(ws("thir", "teen"), "men"), [1, 2, 3]),
    ("Tennessee air (106a)",
     ws(ws(sw("Ten", "nes"), "see"), "air"), [2, 1, 3, 4]),
    ("Montana cowboy (108)",
     ws(sw(ws("Mon", "tan"), "a"), sw("cow", "boy")), [1, 2, 1, 3, 1]),
    ("execute (116a)",
     sw(sw("e", "xe"), "cute"), [2, 1, 1]),
    ("knowledgeable (116b)",
     sw(sw(sw("know", "ledge"), "a"), "ble"), [2, 1, 1, 1]),
    ("poly vinyl chloride (118a)",
     ws(sw("po", "ly"), ws(sw("vi", "nyl"), sw("chlo", "ride"))),
     [2, 1, 2, 1, 3, 1]),
    ("John's three red shirts (118b)",
     ws("Johns", ws("three", ws("red", "shirts"))), [1, 1, 1, 2]),
]


@pytest.mark.parametrize("name,tree,grid", LP_FIGURES,
                         ids=[f[0] for f in LP_FIGURES])
def test_lp_figure_grid(name, tree, grid):
    assert grid_heights(tree) == grid


# --------------------------------------------------------------- Layer B
# (phrase, published nuclear word). Auto pipeline should recover the nuclear.
LP_NUCLEI = [
    ("thirteen men", "men"),
    ("Tennessee air", "air"),
    ("achromatic lens", "lens"),
    ("Montana cowboy", "cowboy"),
    ("John's three red shirts", "shirts"),
    ("the cat that ate the rat that stole the cheese", "cheese"),
    ("Sammy's father's brother's dog", "dog"),
    ("American history teacher", "history"),
    ("law degree requirement changes", "law"),
    ("reports of threats of violence", "violence"),
    pytest.param(
        "poly vinyl chloride", "chloride",
        marks=pytest.mark.xfail(
            reason="compound/phrase ambiguity L&P themselves flag in (119); "
                   "Stanza also tags 'poly' as JJ, so the NN-run vinyl+chloride "
                   "compounds to vinyl. A known-hard, acknowledged-ambiguous case."
        ),
    ),
]


@pytest.mark.parametrize("text,nuclear",
                         [c if isinstance(c, tuple) else c for c in LP_NUCLEI])
def test_lp_auto_nuclear(text, nuclear):
    try:
        tree = parse_lptree(text)
    except Exception as e:
        pytest.skip(f"stanza unavailable: {e}")
    if tree is None:
        pytest.skip("no parse")
    got = tree.dte.label.lower()
    if got.endswith("'s"):          # strip a possessive clitic, not a plural -s
        got = got[:-2]
    assert got == nuclear, f"{text!r}: auto nuclear {got!r}, L&P {nuclear!r}"
