"""Test: are non-line-initial trochaic inversions in iambic pentameter generally
after a caesura (a punctuation phrase boundary)?

For each line read as strict iambic, a mid-line inversion = w_stress/w_peak at a
weak slot (positions 3,5,7,9). "After a caesura" = the inverted syllable starts a
new linepart (SEPS_PHRASE punctuation boundary before it). We compare the caesura
rate at inversions to the baseline caesura rate at the same positions.
"""
import warnings; warnings.filterwarnings("ignore")
from collections import Counter
import numpy as np
import prosodic

TARGET = np.array([j % 2 == 1 for j in range(10)])


def iambic_viols(pl):
    def scans():
        if getattr(pl, "_ragged", False):
            for i in range(len(pl._all_viols)):
                yield np.asarray(pl._meter_vals[i]), np.asarray(pl._position_sizes[i]), pl._all_viols[i]
        else:
            for i in range(pl._all_viols.shape[0]):
                yield pl._meter_vals[i], pl._position_sizes[i], pl._all_viols[i]
    for mv, ps, av in scans():
        if len(mv) == 10 and np.all(ps == 1) and np.array_equal(np.asarray(mv, bool), TARGET):
            return av
    return None


t = prosodic.Text(open("corpora/corppoetry_en/en.shakespeare.txt").read())
t.parse()
sdf0 = t._syll_df[t._syll_df.form_idx == 0]

cn = None
inv_caes, inv_tot, base_caes, base_tot = Counter(), Counter(), Counter(), Counter()
for line in t.lines:
    pl = line.parses
    if not getattr(pl, "_constraint_names", None):
        continue
    av = iambic_viols(pl)
    if av is None:
        continue
    if cn is None:
        cn = list(pl._constraint_names)
        wi = cn.index("w_stress")
        pi = cn.index("w_peak") if "w_peak" in cn else None
    lp = sdf0[sdf0.line_num == line.num].sort_values(["word_num", "syll_idx"]).linepart_num.tolist()
    if len(lp) != 10:
        continue
    for p in (2, 4, 6, 8):  # mid-line weak slots, 0-indexed -> positions 3,5,7,9
        caesura = lp[p] != lp[p - 1]        # inverted syllable starts a new phrase
        base_tot[p] += 1
        base_caes[p] += caesura
        if av[p, wi] > 0 or (pi is not None and av[p, pi] > 0):
            inv_tot[p] += 1
            inv_caes[p] += caesura

print("mid-line trochaic inversions vs caesura (punctuation phrase break before them)\n")
print(f"{'pos':>4} {'#inv':>6} {'inv after caesura':>18} {'baseline at pos':>16}")
for p in (2, 4, 6, 8):
    ip = 100 * inv_caes[p] / inv_tot[p] if inv_tot[p] else 0
    bp = 100 * base_caes[p] / base_tot[p] if base_tot[p] else 0
    print(f"{p+1:>4} {inv_tot[p]:>6} {ip:>16.0f}% {bp:>14.0f}%")
ti, tic = sum(inv_tot.values()), sum(inv_caes.values())
tb, tbc = sum(base_tot.values()), sum(base_caes.values())
print(f"\nALL mid-line inversions: {100*tic/ti:.0f}% fall after a caesura   "
      f"vs baseline {100*tbc/tb:.0f}%   (enrichment {tic/ti/(tbc/tb):.1f}x)")
