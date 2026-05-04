"""Empirical evaluation of WordForm.rime_distance against Walker (1775).

Loads ``data/walker5.csv`` (a transcribed rhyming dictionary with perfect and
near/allowable rhyme groupings) and measures how well prosodic's
feature-weighted-edit rime distance separates the three classes:

    - perfect rhyme: same row, same `perfword` group
    - near rhyme:    same row, perfword × allowword
    - non-rhyme:     different rows (sampled)

Outputs distance histograms by class, a ROC curve for the "any rhyme vs
non-rhyme" binary task, and a suggested ``max_dist`` threshold based on the
F1-optimal operating point.

Usage::

    python scripts/rime_eval.py
    python scripts/rime_eval.py --n-cross 5000  # more non-rhyme samples
    python scripts/rime_eval.py --max-words 500 # quicker, smaller sample

Caveats: Walker's rhymes reflect 18th-century English. CMU/espeak provide
modern pronunciations, so some of his perfect rhymes won't rhyme to a modern
speaker. Useful noise for analyzing pre-1900 verse; misleading otherwise.
"""
from __future__ import annotations

import argparse
import csv
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import prosodic  # noqa: E402

DATA_PATH = REPO_ROOT / "data" / "walker5.csv"


def parse_words(cell: str) -> list[str]:
    """Split a Walker word-list cell on commas/semicolons; strip + lowercase."""
    return [w.strip().lower() for w in re.split(r"[,;]", cell) if w.strip()]


def load_walker(path: Path = DATA_PATH) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    out = []
    for i, r in enumerate(rows):
        perf = parse_words(r["perfword"])
        allow = parse_words(r["allowword"])
        if perf:  # rows with no perfect words are useless
            out.append({"row": i, "syll": r["syll"], "perf": perf, "allow": allow})
    return out


def get_wordform(word: str, _cache: dict = {}):
    """Return the first WordForm for a word (cached). None if unparseable."""
    if word in _cache:
        return _cache[word]
    try:
        t = prosodic.Text(word)
        wf = None
        if t.wordtokens and t.wordtokens[0].wordform is not None:
            wf = t.wordtokens[0].wordform
            if not wf.syllables:
                wf = None
        _cache[word] = wf
        return wf
    except Exception:
        _cache[word] = None
        return None


def sample_pairs(rows: list[dict],
                 max_words_per_row: int = 30,
                 n_cross: int = 3000,
                 seed: int = 17):
    """Build (class, w1, w2) triples for evaluation."""
    rng = random.Random(seed)
    perfect_pairs: list[tuple[str, str]] = []
    near_pairs: list[tuple[str, str]] = []

    for r in rows:
        perf = r["perf"][:max_words_per_row]
        allow = r["allow"][:max_words_per_row]
        # All within-perf pairs (without replacement, both orderings collapsed)
        for i in range(len(perf)):
            for j in range(i + 1, len(perf)):
                perfect_pairs.append((perf[i], perf[j]))
        # All perf × allow pairs
        for p in perf:
            for a in allow:
                near_pairs.append((p, a))

    # Cross-row: random words from distinct rows
    cross_pairs: list[tuple[str, str]] = []
    flat_by_row = [(r["row"], r["perf"][:max_words_per_row]) for r in rows
                   if r["perf"]]
    if len(flat_by_row) >= 2:
        for _ in range(n_cross):
            r1, r2 = rng.sample(flat_by_row, 2)
            cross_pairs.append((rng.choice(r1[1]), rng.choice(r2[1])))

    return perfect_pairs, near_pairs, cross_pairs


def compute_distances(pairs: list[tuple[str, str]],
                      label: str,
                      max_pairs: int = 4000) -> list[float]:
    """Return rime distances for as many pairs as possible (skipping
    unparseable words and NaN distances). Caps at ``max_pairs``."""
    import math
    rng = random.Random(7)
    if len(pairs) > max_pairs:
        pairs = rng.sample(pairs, max_pairs)
    out = []
    skipped = 0
    nan_count = 0
    for w1, w2 in pairs:
        wf1, wf2 = get_wordform(w1), get_wordform(w2)
        if wf1 is None or wf2 is None:
            skipped += 1
            continue
        try:
            d = wf1.rime_distance(wf2, max_dist=None)
        except Exception:
            skipped += 1
            continue
        if d is None:
            skipped += 1
            continue
        d = float(d)
        if math.isnan(d):
            nan_count += 1
            continue
        out.append(d)
    print(f"  {label:8s} n={len(out):5d}  "
          f"(skipped {skipped} unparseable, {nan_count} NaN)",
          file=sys.stderr)
    return out


def histogram(distances: list[float], bins: int = 20,
              width: int = 40) -> str:
    """ASCII histogram. Returns multi-line string."""
    if not distances:
        return "(empty)"
    lo, hi = 0.0, max(1.0, max(distances))
    counts = [0] * bins
    for d in distances:
        b = min(int((d - lo) / (hi - lo) * bins), bins - 1)
        counts[b] += 1
    peak = max(counts) or 1
    lines = []
    for i, c in enumerate(counts):
        edge = lo + (i / bins) * (hi - lo)
        bar = "#" * int(width * c / peak)
        lines.append(f"  {edge:5.2f} | {bar} {c}")
    return "\n".join(lines)


def roc(positives: list[float], negatives: list[float],
        thresholds: list[float] = None):
    """Return list of (threshold, tpr, fpr, precision, recall, f1)."""
    if thresholds is None:
        thresholds = [round(x * 0.05, 2) for x in range(0, 21)]
    out = []
    n_pos = len(positives) or 1
    n_neg = len(negatives) or 1
    for t in thresholds:
        tp = sum(1 for d in positives if d <= t)
        fp = sum(1 for d in negatives if d <= t)
        fn = n_pos - tp
        tpr = tp / n_pos
        fpr = fp / n_neg
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tpr
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        out.append({"t": t, "tpr": tpr, "fpr": fpr,
                    "prec": prec, "rec": rec, "f1": f1})
    return out


def auc(positives: list[float], negatives: list[float]) -> float:
    """AUC for the test 'distance <= threshold predicts rhyme'.

    Positives are rhymes (lower distance preferred); negatives are non-rhymes.
    AUC > 0.5 means the test discriminates correctly.
    """
    n_pos, n_neg = len(positives), len(negatives)
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    # Rank ascending so smaller distance = lower rank
    combined = [(d, 1) for d in positives] + [(d, 0) for d in negatives]
    combined.sort(key=lambda x: x[0])
    rank_sum_pos = 0
    i = 0
    while i < len(combined):
        j = i
        while j + 1 < len(combined) and combined[j + 1][0] == combined[i][0]:
            j += 1
        avg_rank = (i + j) / 2 + 1
        for k in range(i, j + 1):
            if combined[k][1] == 1:
                rank_sum_pos += avg_rank
        i = j + 1
    # Mann-Whitney U for "positives rank lower than negatives" =
    # n_pos*n_neg + n_pos*(n_pos+1)/2 - rank_sum_pos. Then AUC = U / (n_pos * n_neg).
    u = n_pos * n_neg + n_pos * (n_pos + 1) / 2 - rank_sum_pos
    return u / (n_pos * n_neg)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-words-per-row", type=int, default=30)
    ap.add_argument("--n-cross", type=int, default=3000)
    ap.add_argument("--max-pairs", type=int, default=4000,
                    help="cap on pairs per class for runtime")
    args = ap.parse_args()

    print(f"Loading Walker from {DATA_PATH} ...", file=sys.stderr)
    rows = load_walker()
    print(f"  {len(rows)} rows with at least one perfect rhyme",
          file=sys.stderr)

    perfect, near, cross = sample_pairs(
        rows,
        max_words_per_row=args.max_words_per_row,
        n_cross=args.n_cross,
    )
    print(f"\nSampled pairs:", file=sys.stderr)
    print(f"  perfect (same group): {len(perfect):6d}", file=sys.stderr)
    print(f"  near (perf x allow):  {len(near):6d}", file=sys.stderr)
    print(f"  cross (different):    {len(cross):6d}", file=sys.stderr)

    print(f"\nComputing rime distances ...", file=sys.stderr)
    d_perfect = compute_distances(perfect, "perfect", args.max_pairs)
    d_near = compute_distances(near, "near", args.max_pairs)
    d_cross = compute_distances(cross, "cross", args.max_pairs)

    def stats(name, ds):
        if not ds:
            return f"  {name:8s} n=0"
        ds_sorted = sorted(ds)
        n = len(ds_sorted)
        mean = sum(ds_sorted) / n
        median = ds_sorted[n // 2]
        p90 = ds_sorted[int(n * 0.9)]
        return (f"  {name:8s} n={n:5d}  mean={mean:.3f}  median={median:.3f}  "
                f"p90={p90:.3f}  min={ds_sorted[0]:.3f}  max={ds_sorted[-1]:.3f}")

    print()
    print("=" * 70)
    print("Rime distance distributions by Walker rhyme class")
    print("=" * 70)
    print(stats("perfect", d_perfect))
    print(stats("near", d_near))
    print(stats("cross", d_cross))
    print()

    print("Histogram (perfect):")
    print(histogram(d_perfect))
    print()
    print("Histogram (near/allowable):")
    print(histogram(d_near))
    print()
    print("Histogram (cross-row, presumed non-rhyme):")
    print(histogram(d_cross))
    print()

    def report_task(name, positives, negatives):
        print("=" * 70)
        print(f"Binary task: {name}")
        print("=" * 70)
        print(f"  AUC: {auc(positives, negatives):.4f}")
        print()
        print("  threshold |    TPR    FPR    prec    recall    F1")
        print("  ---------------------------------------------------")
        rows_roc = roc(positives, negatives)
        best_f1 = max(rows_roc, key=lambda r: r["f1"])
        for r in rows_roc:
            marker = "  <-- best F1" if r is best_f1 else ""
            print(f"   {r['t']:5.2f}      {r['tpr']:.3f}  {r['fpr']:.3f}  "
                  f"{r['prec']:.3f}  {r['rec']:.3f}  {r['f1']:.3f}{marker}")
        print()
        print(f"  F1-optimal threshold: {best_f1['t']:.2f}")
        # high-precision operating point
        hp = next((r for r in rows_roc if r["prec"] >= 0.95), None)
        if hp:
            print(f"  High-precision (>=95%) threshold: {hp['t']:.2f}  "
                  f"(TPR={hp['tpr']:.2f}, FPR={hp['fpr']:.2f})")
        print()

    report_task("perfect rhyme vs cross-row", d_perfect, d_cross)
    report_task("any rhyme (perfect + near) vs cross-row",
                d_perfect + d_near, d_cross)


if __name__ == "__main__":
    main()
