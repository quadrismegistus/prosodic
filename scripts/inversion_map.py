"""Inversion map: read every line AS strict iambic pentameter (wswswswsws) and
record, by line position, the two ways stress fights the template —

  * w_stress / w_peak  = a STRESSED syllable forced into a weak slot  -> INVERSION
  * s_unstress         = an UNSTRESSED syllable promoted to a strong slot -> PROMOTION

These separate the phenomena my foot-substitution counter conflated: a true
trochaic inversion (line-initial "Pity") vs a line-final falling ending. We read
the violations of the strict-iambic scansion straight from the parse's numpy — no
Parse objects, no re-parse.

Run: .venv/bin/python scripts/inversion_map.py
"""
import warnings; warnings.filterwarnings("ignore")
from collections import Counter
import numpy as np
import prosodic

TARGET = np.array([j % 2 == 1 for j in range(10)])  # wswswswsws: strong at odd 0-idx


def scansions(pl):
    """(meter_vals_1d, position_sizes_1d, viols_2d) per scansion — handles the
    ragged (mixed-position-count) case as well as the rectangular one."""
    if getattr(pl, "_ragged", False):
        for i in range(len(pl._all_viols)):
            yield np.asarray(pl._meter_vals[i]), np.asarray(pl._position_sizes[i]), pl._all_viols[i]
    else:
        mv, ps, av = pl._meter_vals, pl._position_sizes, pl._all_viols
        for i in range(av.shape[0]):
            yield mv[i], ps[i], av[i]


def iambic_viols(pl):
    """(10, C) per-position violations of the strict-iambic scansion, or None."""
    for mv, ps, av in scansions(pl):
        if len(mv) == 10 and np.all(ps == 1) and np.array_equal(np.asarray(mv, bool), TARGET):
            return av
    return None


corpus = open("corpora/corppoetry_en/en.shakespeare.txt").read()
t = prosodic.Text(corpus)
t.parse()

inv, prom, n = Counter(), Counter(), 0
cn = None
for line in t.lines:
    pl = line.parses
    if not pl or not getattr(pl, "_constraint_names", None):
        continue
    av = iambic_viols(pl)
    if av is None:
        continue
    if cn is None:
        cn = list(pl._constraint_names)
        wi = cn.index("w_stress")
        si = cn.index("s_unstress")
        pi = cn.index("w_peak") if "w_peak" in cn else None
    n += 1
    for p in range(10):
        if av[p, wi] > 0 or (pi is not None and av[p, pi] > 0):
            inv[p] += 1
        if av[p, si] > 0:
            prom[p] += 1

print(f"read {n} lines as strict iambic pentameter (wswswswsws)\n")
print("position:            " + "".join(f"{p+1:>5}" for p in range(10)))
print("weak/strong slot:    " + "".join(f"{'w' if p%2==0 else 's':>5}" for p in range(10)))
print("-" * 70)
print("INVERSION (w_stress): " + "".join(f"{inv[p]:>5}" for p in range(10)))
print("  as % of lines:      " + "".join(f"{round(100*inv[p]/n):>5}" for p in range(10)))
print("PROMOTION (s_unstr):  " + "".join(f"{prom[p]:>5}" for p in range(10)))
print("  as % of lines:      " + "".join(f"{round(100*prom[p]/n):>5}" for p in range(10)))
print()
top_inv = sorted(inv.items(), key=lambda kv: -kv[1])[:3]
top_prom = sorted(prom.items(), key=lambda kv: -kv[1])[:3]
print("inversions concentrate at positions: " + ", ".join(f"{p+1}({100*c//n}%)" for p, c in top_inv))
print("promotions concentrate at positions: " + ", ".join(f"{p+1}({100*c//n}%)" for p, c in top_prom))
