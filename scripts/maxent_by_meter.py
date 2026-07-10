#!/usr/bin/env python
"""MaxEnt constraint-weight study over the hand-tagged foot gold, by meter.

Runs four analyses on data/tagged_samples/foot-gold.csv (30 lines x 4 meters):

  A. FLAT      — one MaxEnt fit per meter; the per-constraint weight signature.
  B. ZONES     — per-meter fit split into line thirds (initial/medial/final): does
                 binary verse's weak-position strictness concentrate at the edges?
  C. UNMATCHED — which gold lines the parser can't reproduce (elision syllable-count
                 mismatches), so the fits above are read on honest N.
  D. JOINT     — ONE partial-pooled model: per-meter weights shrunk toward a shared
                 grand mean (a hierarchical prior), so the meter contrasts are
                 estimated together on one scale rather than in four separate runs.

Usage:  .venv/bin/python scripts/maxent_by_meter.py [--reg 1.0] [--tau 0.3]
"""
import argparse
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

from prosodic.parsing.meter import Meter
from prosodic.parsing.maxent import MaxEntTrainer
from prosodic.texts.texts import TextModel

GOLD = "data/tagged_samples/foot-gold.csv"
METERS = ["iambic", "trochaic", "anapestic", "dactylic"]
_WS = str.maketrans("+-", "sw")


def _trainer(df_group, zones=None, reg=1.0):
    tr = MaxEntTrainer(Meter(), regularization=reg, zones=zones)
    tr.load_annotations(df_group)          # friendlier loader: line->text, freq->1.0
    return tr


def _matched(tr):
    return sum(1 for ld in tr._line_data if ld["observed"].sum() > 0), len(tr._line_data)


def run_flat(df, reg):
    print("\n=== A. FLAT — per-constraint weight by meter (higher = more enforced) ===")
    W, match = {}, {}
    for m in METERS:
        tr = _trainer(df[df.meter == m], reg=reg)
        tr.train()
        W[m] = tr.learned_weights()
        match[m] = _matched(tr)
    cons = list(W["iambic"].keys())
    print(f'{"":14s} ' + " ".join(f"{m[:9]:>9s}" for m in METERS))
    print(f'{"matched/30":14s} ' + " ".join(f'{match[m][0]:>9}' for m in METERS))
    for c in cons:
        print(f"{c:14s} " + " ".join(f"{W[m].get(c, 0):9.2f}" for m in METERS))


def run_zones(df, reg):
    print("\n=== B. ZONES — w_stress & s_unstress across line thirds (init|med|fin) ===")
    for m in METERS:
        tr = _trainer(df[df.meter == m], zones=3, reg=reg)
        tr.train()
        w = tr.learned_weights()
        def zvals(base):                       # keys look like "w_stress_z1".."_z3"
            zk = sorted((k for k in w if k.startswith(base + "_z")),
                        key=lambda k: int(k.rsplit("z", 1)[1]))
            return [w[k] for k in zk]
        fmt = lambda xs: " ".join(f"{x:5.2f}" for x in xs)
        print(f"  {m:10s}  w_stress [{fmt(zvals('w_stress'))}]   "
              f"s_unstress [{fmt(zvals('s_unstress'))}]")


def run_unmatched(df):
    print("\n=== C. COVERAGE — gold lines used per meter (mixed-N lines now train) ===")
    for m in METERS:
        g = df[df.meter == m]
        tr = _trainer(g, reg=1.0)
        used, in_data = _matched(tr)
        n_unique = g["line"].nunique()                  # duplicate lines fold (freq sums)
        dropped = n_unique - in_data                    # oversized/empty only, now
        not_cand = in_data - used                       # in _line_data but gold != a candidate
        print(f"  {m:10s}: {used}/{n_unique} unique lines used   ({dropped} dropped, "
              f"{not_cand} gold not among candidate scansions)")
        # name the mixed-N (elision) lines — previously skipped, now trained
        for _, r in g.iterrows():
            t = TextModel(r["line"])
            if t.lines and getattr(t.lines[0].parses, "_ragged", False):
                note = f"  ({r['note']})" if isinstance(r.get("note"), str) else ""
                print(f"        mixed-N (trained): {r['line'][:50]!r}{note}")


def run_joint(df, reg, tau):
    """Partial-pooled fit: per-meter weights w[m] shrunk toward a shared grand mean mu.
    tau = pooling scale (small -> all meters collapse to mu; large -> free/separate)."""
    print(f"\n=== D. JOINT partial-pool (tau={tau}): shared mean + per-meter deviation ===")
    from scipy.optimize import minimize

    # collect each meter's precomputed (S-grouped) viol/observed blocks
    blocks, cons = [], None
    for m in METERS:
        tr = _trainer(df[df.meter == m], reg=reg)
        tr._precompute()
        cons = tr._constraint_names
        blocks.append(list(tr._groups.values()))
    C, M = len(cons), len(METERS)

    def unpack(x):
        mu = x[:C]
        w = x[C:].reshape(M, C)
        return mu, w

    def obj(x):
        mu, w = unpack(x)
        nll = 0.0
        gmu = np.zeros(C)
        gw = np.zeros((M, C))
        for mi, groups in enumerate(blocks):
            wm = w[mi]
            for g in groups:
                v, obs = g["viols"], g["observed"]         # (L,S,C),(L,S)
                s = v @ wm
                s -= s.max(axis=-1, keepdims=True)
                p = np.exp(s); p /= p.sum(axis=-1, keepdims=True)
                nll -= (obs * np.log(np.clip(p, 1e-30, None))).sum()
                diff = obs - obs.sum(-1, keepdims=True) * p
                gw[mi] -= np.einsum("ls,lsc->c", diff, v)
            # shrink meter -> mu
            nll += ((wm - mu) ** 2).sum() / (2 * tau)
            gw[mi] += (wm - mu) / tau
            gmu -= (wm - mu) / tau
        # weak prior on the shared mean
        nll += (mu ** 2).sum() / (2 * reg)
        gmu += mu / reg
        return nll, np.concatenate([gmu, gw.ravel()])

    x0 = np.zeros(C * (M + 1))
    bounds = [(-np.inf, 0.0)] * (C * (M + 1))     # HG convention: weights <= 0
    res = minimize(obj, x0, jac=True, method="L-BFGS-B", bounds=bounds,
                   options={"maxiter": 10000})
    mu, w = unpack(res.x)
    # report as positive magnitudes (like learned_weights)
    print(f'{"constraint":14s} {"SHARED":>8s} | ' + " ".join(f"{m[:8]:>8s}" for m in METERS))
    for ci, c in enumerate(cons):
        base = -mu[ci]
        devs = " ".join(f"{-w[mi][ci] - base:+8.2f}" for mi in range(M))
        print(f"{c:14s} {base:8.2f} | {devs}")
    print("  (columns = each meter's DEVIATION from the shared mean; + = more enforced)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reg", type=float, default=1.0)
    ap.add_argument("--tau", type=float, default=0.3)
    args = ap.parse_args()

    df = pd.read_csv(GOLD)
    print(f"foot gold: {len(df)} lines, {df.meter.nunique()} meters "
          f"({', '.join(f'{m}={n}' for m, n in df.meter.value_counts().items())})")
    run_flat(df, args.reg)
    run_zones(df, args.reg)
    run_unmatched(df)
    run_joint(df, args.reg, args.tau)


if __name__ == "__main__":
    main()
