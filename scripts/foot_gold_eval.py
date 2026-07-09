"""Evaluate foot delineation against the hand-tagged foot-gold set.

Foots each gold line's scansion with prosodic's `foot_parse` and reports exact +
boundary agreement with the human foot boundaries, by meter. Re-run after any
change to `analysis/feet.py`.

Gold: `data/tagged_samples/foot-gold.csv` — 120 lines (30/meter) sampled from the
litlab tagged sample and hand-tagged by foot, including anacrusis (`w|…`) and
feminine (`…|w`) extrametrical edges. The `parse_human2` column of the original
sample is NOT a foot gold (it is a mix of syllable/beat-grid conventions); this is.

    python scripts/foot_gold_eval.py
"""
import pandas as pd
from collections import defaultdict
from prosodic.analysis.feet import foot_parse


def _bounds(feetstr):
    """Inter-foot boundary indices (after-syllable positions) from a `|`-string."""
    parts, b, p = feetstr.split("|"), set(), 0
    for f in parts[:-1]:
        p += len(f)
        b.add(p - 1)
    return b


def ours(scan):
    """Our footing of a w/s scansion as a `|`-delimited string."""
    return "|".join(scan[a:b] for a, b in foot_parse([c == "s" for c in scan]))


def main(path="data/tagged_samples/foot-gold.csv"):
    df = pd.read_csv(path)
    D = defaultdict(lambda: [0, 0, 0, 0])  # exact, n, inter, union
    misses = []
    for _, r in df.iterrows():
        gold = str(r["feet"]).strip().replace(" ", "")
        if not gold or set(gold) - set("sw|"):
            continue
        o = ours(gold.replace("|", ""))
        gb, ob = _bounds(gold), _bounds(o)
        for k in (str(r["meter"]), "ALL"):
            D[k][0] += o == gold
            D[k][1] += 1
            D[k][2] += len(gb & ob)
            D[k][3] += len(gb | ob)
        if o != gold:
            misses.append((r["meter"], gold, o))
    for k in ["ALL", "iambic", "trochaic", "anapestic", "dactylic"]:
        if k in D:
            e, n, i, u = D[k]
            print(f"{k:10} exact {e / n:6.1%}  boundary {i / max(u, 1):6.1%}  (n={n})")
    print(f"\n{len(misses)} misses:")
    for m, g, o in misses:
        print(f"  [{m}] gold {g}  ours {o}")


if __name__ == "__main__":
    main()
