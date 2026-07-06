"""Which phonological features are determinative for rhyme classification?

Builds a 48-dim design matrix over Walker pairs: per-panphon-feature mean
|diff| computed separately for nucleus and coda (right-aligned; positions
without a counterpart contribute 1.0 on every feature). Fits standardized
L2 logistic regressions (sklearn): (a) perfect-vs-rest, (b) slant-vs-none,
plus a nucleus-only/coda-only ablation.

Findings (2026-07-06 run, seeds fixed):
  - slant-vs-none is a CODA-ONLY decision: coda-24 features alone give
    0.920 five-fold CV accuracy vs 0.678 for nucleus-24 (full 48: 0.924;
    majority baseline 0.571). Independently confirms the 2-D band result
    behind WordForm.rime_type.
  - within the coda, MANNER features are determinative (lat -2.9, nas
    -2.6, cont -2.2, voi -1.8 must match); place features (ant, cor)
    barely register - slant rhyme tolerates place drift, not manner drift.
  - for perfect-vs-rest (CV 0.850), the vowel features that must match
    are rounding and length (nuc_round -1.4, nuc_long -1.3).
  - caveat: coda_sg/cg/velaric/hitone/hireg show identical positive
    coefficients - a collinearity artifact of the empty-coda padding
    (those features are constant for real English codas).

Negative results (also 2026-07-06, recorded so they are not re-tried):
  - LEARNED PER-FEATURE WEIGHTS inside the band classifier LOSE to
    uniform: non-negative logistic weights per channel (fit_channel_
    weights below; coda top weights lab/lat/nas/cont/voi, nucleus
    long/lab/round/lo/hi - phonologically sensible) give Walker
    macro-F1 0.724 vs 0.758 uniform. Bands rely on near-IDENTITY
    thresholds; zero-weighted features (cor, ant) let different codas
    score ~0 and leak non-rhymes into the slant region.
  - A full 48-dim MULTINOMIAL model wins on Walker CV (macro-F1 0.822)
    but over-recalls on the sonnet-scheme validation in rime_eval.py
    (FPR 0.186 vs bands 0.041; F1 0.889 vs 0.912): it learns Walker's
    historical permissiveness, not real end-rhyme practice. Bands stay
    the default.

Requires scikit-learn (not a prosodic dependency; pip install scikit-learn).
Usage: python scripts/rime_feature_analysis.py
"""
import warnings; warnings.filterwarnings('ignore')
import sys, math, random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from rime_eval import load_walker, sample_pairs, get_wordform
from prosodic.words.phonemes import get_phoneme_featuretable
import numpy as np

ft = get_phoneme_featuretable()
FEATS = ['syl','son','cons','cont','delrel','lat','nas','strid','voi','sg',
         'cg','ant','cor','distr','lab','hi','lo','back','round','velaric',
         'tense','long','hitone','hireg']

_seg_cache = {}
def seg_vec(txt):
    if txt not in _seg_cache:
        segs = ft.ipa_segs(txt)
        _seg_cache[txt] = [np.array(ft.fts(s).numeric(), dtype=float) for s in segs]
    return _seg_cache[txt]

def parts(wf):
    phons = list(wf.rime)
    i = 0
    while i < len(phons) and phons[i].is_vowel:
        i += 1
    nuc = ''.join(p.txt for p in phons[:i])
    coda = ''.join(p.txt for p in phons[i:])
    return seg_vec(nuc), seg_vec(coda)

def part_feature_diffs(v1, v2):
    """Right-aligned per-feature mean |diff|; unmatched positions = 1.0."""
    n = max(len(v1), len(v2))
    if n == 0:
        return np.zeros(len(FEATS))
    total = np.zeros(len(FEATS))
    for k in range(1, n + 1):
        a = v1[-k] if k <= len(v1) else None
        b = v2[-k] if k <= len(v2) else None
        if a is None or b is None:
            total += 1.0
        else:
            total += np.abs(a - b) / 2.0  # features in {-1,0,1}: max diff 2
    return total / n

def pair_row(w1, w2):
    wf1, wf2 = get_wordform(w1), get_wordform(w2)
    if wf1 is None or wf2 is None or wf1.txt == wf2.txt:
        return None
    try:
        n1, c1 = parts(wf1); n2, c2 = parts(wf2)
    except Exception:
        return None
    return np.concatenate([part_feature_diffs(n1, n2),
                           part_feature_diffs(c1, c2)])

def fit_contrast(X, y):
    """Standardized L2 logistic regression + 5-fold CV accuracy."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import cross_val_score
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import make_pipeline
    pipe = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))
    cv = cross_val_score(pipe, X, y, cv=5).mean()
    pipe.fit(X, y)
    coefs = pipe.named_steps['logisticregression'].coef_[0]
    return coefs, cv


def fit_channel_weights(data_parts):
    """Fit non-negative per-feature weights per channel (substitution-only
    pairs, so no padding artifacts). Coda: slant-vs-none; nucleus:
    perfect-vs-slant. Returns (w_nuc, w_coda), mean-1 normalized."""
    from scipy.optimize import minimize

    def fit(Xp, Xn, l2=1.0):
        X = np.vstack([Xp, Xn])
        y = np.concatenate([np.ones(len(Xp)), np.zeros(len(Xn))])
        d = X.shape[1]

        def nll(params):
            b0, w = params[0], params[1:]
            z = b0 - X @ w
            pr = 1 / (1 + np.exp(-np.clip(z, -30, 30)))
            eps = 1e-12
            return -(y * np.log(pr + eps)
                     + (1 - y) * np.log(1 - pr + eps)).sum() + l2 * (w ** 2).sum()

        def grad(params):
            b0, w = params[0], params[1:]
            z = b0 - X @ w
            pr = 1 / (1 + np.exp(-np.clip(z, -30, 30)))
            r = pr - y
            return np.concatenate([[r.sum()], -X.T @ r + 2 * l2 * w])

        bounds = [(None, None)] + [(0, None)] * d
        res = minimize(nll, np.concatenate([[0.], np.ones(d)]), jac=grad,
                       method='L-BFGS-B', bounds=bounds)
        w = res.x[1:]
        return w / (w.mean() or 1.0)

    def sub_diffs(v1, v2):
        if not v1 or not v2:
            return None
        k = min(len(v1), len(v2))
        total = np.zeros(len(FEATS))
        for i in range(1, k + 1):
            total += np.abs(v1[-i] - v2[-i])
        return total / k

    def channel_X(pairs, channel):
        rows_ = [sub_diffs(p1[channel], p2[channel]) for p1, p2 in pairs]
        return np.array([r for r in rows_ if r is not None])

    w_coda = fit(channel_X(data_parts['slant'], 1),
                 channel_X(data_parts['none'], 1))
    w_nuc = fit(channel_X(data_parts['perfect'], 0),
                channel_X(data_parts['slant'], 0))
    return w_nuc, w_coda


def main():
    rows = load_walker()
    perfect, near, cross = sample_pairs(rows)
    rng = random.Random(7)
    MAXP = 4000
    data = {}
    for name, prs in (('perfect', perfect), ('slant', near), ('none', cross)):
        if len(prs) > MAXP:
            prs = rng.sample(prs, MAXP)
        X = [r for r in (pair_row(a, b) for a, b in prs) if r is not None]
        data[name] = np.array(X)
        print(f'{name}: {len(X)} pairs', file=sys.stderr)

    names = [f'nuc_{f}' for f in FEATS] + [f'coda_{f}' for f in FEATS]

    def contrast(pos_name, neg_names, title):
        Xp = data[pos_name]
        Xn = np.vstack([data[n] for n in neg_names])
        X = np.vstack([Xp, Xn])
        y = np.concatenate([np.ones(len(Xp)), np.zeros(len(Xn))])
        coefs, cv = fit_contrast(X, y)
        base = max(y.mean(), 1 - y.mean())
        print()
        print('=' * 64)
        print(f'{title}   (5-fold CV acc {cv:.3f}, majority baseline {base:.3f})')
        print('=' * 64)
        ranked = sorted(zip(names, coefs), key=lambda x: -abs(x[1]))
        print(f'{"feature":<14} {"coef":>8}   (negative = a DIFFERENCE in this feature argues AGAINST the class)')
        for nm, c in ranked[:14]:
            if abs(c) < 0.05:
                break
            print(f'{nm:<14} {c:>8.3f}')

    contrast('perfect', ['slant', 'none'], 'perfect vs rest')
    contrast('slant', ['none'], 'slant vs none')
    # nucleus-only vs coda-only ablation for slant-vs-none
    Xp, Xn = data['slant'], data['none']
    X = np.vstack([Xp, Xn])
    y = np.concatenate([np.ones(len(Xp)), np.zeros(len(Xn))])
    print()
    print('ablation (slant vs none, 5-fold CV acc):')
    for label, sl in (('full 48', slice(None)), ('nucleus 24', slice(0, 24)),
                      ('coda 24', slice(24, 48))):
        _, cv = fit_contrast(X[:, sl], y)
        print(f'  {label:<12} {cv:.3f}')

    # learned channel weights (see docstring: a NEGATIVE result for the
    # band classifier - reported here for the record/reuse)
    parts_data = {}
    for name, prs in (('perfect', perfect), ('slant', near), ('none', cross)):
        if len(prs) > MAXP:
            prs = rng.sample(prs, MAXP)
        pd_ = []
        for a, b in prs:
            wa, wb = get_wordform(a), get_wordform(b)
            if wa is None or wb is None or wa.txt == wb.txt:
                continue
            try:
                pd_.append((parts(wa), parts(wb)))
            except Exception:
                continue
        parts_data[name] = pd_
    w_nuc, w_coda = fit_channel_weights(parts_data)
    print()
    print('learned channel weights (mean-1; NEGATIVE result for bands - '
          'see docstring):')
    print('  coda:   ', {f: round(float(w), 2)
                         for f, w in zip(FEATS, w_coda) if w > 0.05})
    print('  nucleus:', {f: round(float(w), 2)
                         for f, w in zip(FEATS, w_nuc) if w > 0.05})

if __name__ == '__main__':
    main()
