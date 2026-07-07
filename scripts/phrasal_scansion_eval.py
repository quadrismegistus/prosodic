"""Does phrasal stress help metrical scansion, and is the grid better than the tree?

Companion to docs/methods/phrasal-stress-scansion.qmd. Fits MaxEnt constraint
weights under three constraint sets — lexical baseline, +tree stress
(``w_stress_t``/``s_unstress_t``), +grid stress (``w_stress_g``/``s_unstress_g``)
— and measures held-out scansion accuracy (the model's argmax scansion matching
the gold), for both phrasal-stress engines (spaCy dependency / Stanza
constituency).

Two golds:
  - HUMAN: the Litlab-2016 tagged sample (data/tagged_samples/…) — 1736 lines,
    two annotators, four meters (iambic/trochaic/anapestic/dactylic).
  - TEMPLATE: Shakespeare's sonnets scored against strict iambic pentameter
    (masculine ``wswswswsws`` / feminine ``wswswswswsw``).

Run:  .venv/bin/python scripts/phrasal_scansion_eval.py [--engine spacy|stanza|both]

Notes / caveats (see the doc): MaxEnt here has a ~3% accuracy noise floor from a
collinearity ridge (w_peak entails w_stress); Milton is excluded because both
parsers fail on 17th-c. syntax; sentence segmentation is correct (not a
confound); positional zones do not help (slight overfit).
"""
import argparse
import os
import sys
import warnings

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd

PATH_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAGGED = os.path.join(PATH_REPO, "data/tagged_samples/tagged-sample-litlab-2016.txt")
SONNETS = os.path.join(PATH_REPO, "corpora/corppoetry_en/en.shakespeare.txt")
ENGINES = {"spacy": "en_core_web_sm", "stanza": "stanza"}
METERS = ["iambic", "trochaic", "anapestic", "dactylic"]
PENT = ["wswswswsws", "wswswswswsw"]  # iambic pentameter: masc + fem ending


def _load():
    from prosodic.imports import DEFAULT_CONSTRAINTS
    from prosodic.parsing.meter import Meter
    from prosodic.parsing.maxent import MaxEntTrainer
    return list(DEFAULT_CONSTRAINTS), Meter, MaxEntTrainer


def _tagged_df():
    df = pd.read_csv(TAGGED, sep="\t")
    df["ph2"] = df["parse_human2"].astype(str).str.replace("|", "", regex=False)
    df["line"] = df["line"].astype(str).str.strip()
    return df


def _annotations(df):
    """Both annotators as observed frequencies: (line, scansion, 1) rows."""
    rows = []
    for _, r in df.iterrows():
        for col in ("parse", "ph2"):
            s = str(r[col]).strip()
            if s and set(s) <= set("ws"):
                rows.append((r["line"], s, 1))
    return pd.DataFrame(rows, columns=["text", "scansion", "frequency"])


def _syntax_text(lines, model):
    import prosodic
    return prosodic.Text("\n".join(lines), syntax=True, syntax_model=model)


def _accuracy(trainer, by=None):
    """argmax(predicted) == argmax(observed), overall or grouped by ``by``
    (dict line->group)."""
    from collections import defaultdict
    cor, tot = defaultdict(int), defaultdict(int)
    for ld in trainer._line_data:
        if ld["observed"].sum() == 0:
            continue
        g = by.get(ld["text"].strip(), "?") if by else "all"
        tot[g] += 1
        p = trainer._softmax_probs(ld["viols"], trainer._weights)
        if int(np.argmax(p)) == int(np.argmax(ld["observed"])):
            cor[g] += 1
    return {g: (cor[g], tot[g]) for g in tot}


def _held_out(cons, data, stext, meter_by_line, MaxEntTrainer, Meter, zones=None):
    lines = list(dict.fromkeys(data["text"]))
    train = set(lines[0::2])
    tr_d = data[data.text.isin(train)]
    te_d = data[~data.text.isin(train)]
    tr = MaxEntTrainer(Meter(constraints=cons), zones=zones)
    tr.load_annotations(tr_d, text=stext)
    tr.train()
    te = MaxEntTrainer(Meter(constraints=cons), zones=zones)
    te.load_annotations(te_d, text=stext)
    te._weights, te.zones = tr._weights, tr.zones
    return _accuracy(te, by=meter_by_line), tr.learned_weights()


def run_grid_vs_tree(DEF, Meter, MaxEntTrainer, engines):
    """Held-out accuracy: lexical / +tree / +grid, per engine (tagged human gold)."""
    df = _tagged_df()
    data = _annotations(df)
    lines = list(dict.fromkeys(df["line"]))
    meter_by_line = dict(zip(df["line"], df["Meter Scheme"]))
    conds = {
        "lexical": DEF,
        "+tree": DEF + ["w_stress_t", "s_unstress_t"],
        "+grid": DEF + ["w_stress_g", "s_unstress_g"],
    }
    print("\n### Grid vs tree — held-out accuracy on human gold (overall / trochaic)\n")
    for eng, model in engines.items():
        stext = _syntax_text(lines, model)
        print(f"  {eng}:")
        for name, cons in conds.items():
            acc, _ = _held_out(cons, data, stext, meter_by_line, MaxEntTrainer, Meter)
            tc = sum(c for c, _ in acc.values())
            tt = sum(t for _, t in acc.values())
            tro = acc.get("trochaic", (0, 1))
            print(f"    {name:8} overall {tc/tt:5.1%}   trochaic {tro[0]/max(tro[1],1):5.1%}")


def run_shakespeare(DEF, Meter, MaxEntTrainer, engines, n=1500):
    """Held-out accuracy on the sonnets vs strict iambic pentameter."""
    lines = list(dict.fromkeys(
        l.strip() for l in open(SONNETS) if l.strip()))[:n]
    data = pd.DataFrame([(ln, t, 1) for ln in lines for t in PENT],
                        columns=["text", "scansion", "frequency"])
    print("\n### Shakespeare sonnets vs strict iambic pentameter — held-out\n")
    for eng, model in engines.items():
        stext = _syntax_text(lines, model)
        print(f"  {eng}:")
        for name, cons in {"lexical": DEF,
                           "+tree": DEF + ["w_stress_t", "s_unstress_t"],
                           "+grid": DEF + ["w_stress_g", "s_unstress_g"]}.items():
            acc, w = _held_out(cons, data, stext, None, MaxEntTrainer, Meter)
            c, t = acc.get("all", (0, 1))
            ph = {k: round(v, 2) for k, v in w.items() if k.endswith(("_t", "_g"))}
            print(f"    {name:8} {c/t:5.1%}   phrasal {ph}")


def run_per_meter_weights(DEF, Meter, MaxEntTrainer, engines):
    """Full learned weights per meter (DEF + tree + grid), per engine."""
    df = _tagged_df()
    lines = list(dict.fromkeys(df["line"]))
    cons = DEF + ["w_stress_t", "s_unstress_t", "w_stress_g", "s_unstress_g"]
    print("\n### Learned weights per meter (DEF + tree + grid phrasal)\n")
    for eng, model in engines.items():
        stext = _syntax_text(lines, model)
        W = {}
        for mtr in METERS:
            data = _annotations(df[df["Meter Scheme"] == mtr])
            tr = MaxEntTrainer(Meter(constraints=cons))
            tr.load_annotations(data, text=stext)
            tr.train()
            W[mtr] = tr.learned_weights()
        print(f"  {eng}:")
        print("    " + f"{'constraint':16}" + "".join(f"{m:>11}" for m in METERS))
        for c in cons:
            print("    " + f"{c:16}" + "".join(f"{round(W[m].get(c, 0), 2):>11}" for m in METERS))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", choices=["spacy", "stanza", "both"], default="both")
    ap.add_argument("--only", choices=["grid", "shakespeare", "weights"], default=None)
    args = ap.parse_args()
    engines = ENGINES if args.engine == "both" else {args.engine: ENGINES[args.engine]}
    DEF, Meter, MaxEntTrainer = _load()
    if args.only in (None, "grid"):
        run_grid_vs_tree(DEF, Meter, MaxEntTrainer, engines)
    if args.only in (None, "shakespeare"):
        run_shakespeare(DEF, Meter, MaxEntTrainer, engines)
    if args.only in (None, "weights"):
        run_per_meter_weights(DEF, Meter, MaxEntTrainer, engines)


if __name__ == "__main__":
    main()
