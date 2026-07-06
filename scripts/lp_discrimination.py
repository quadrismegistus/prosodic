"""Hard-case discrimination: faithful Stanza constituency vs spaCy MetricalTree.

Compares the nuclear-stress placement of the two backends against
hand-derived gold, on cases chosen to probe where a dependency projection
and real constituency should diverge (compounds, possessives, proper-noun
modifiers). Nuclear = argmax prominence, so BOTH backends produce it (spaCy
via argmax tstress; the faithful pipeline via the tree DTE) — no structure
needed for the comparison itself.

CAVEATS (read before trusting the totals):
  - The sentences and gold are the author's linguistic judgments, not an
    independently annotated corpus. Possessive gold is uncontroversial;
    proper-modifier gold is genuinely debatable (see below).
  - The faithful pipeline's possessive / common-noun-compound handling was
    designed during this work knowing these distinctions matter — principled,
    but a mild teaching-to-the-test risk.

    Run: .venv/bin/python scripts/lp_discrimination.py
"""
import warnings

warnings.filterwarnings("ignore")

# (category, text, gold_nuclear, gold_is_solid)
#   gold_is_solid=False marks cases where the gold itself is contestable —
#   e.g. "Boston terrier" is a breed name and is plausibly fore-stressed
#   (BOSTON terrier), so spaCy's "boston" may be correct and the phrasal
#   reading "terrier" wrong. Excluded from the "solid" score.
CASES = [
    # N+N compounds: fore-stress (LEFT) — CSR
    ("compound", "apple pie", "apple", True),
    ("compound", "computer science", "computer", True),
    ("compound", "kitchen table", "kitchen", True),
    ("compound", "credit card", "credit", True),
    ("compound", "police officer", "police", True),
    ("compound", "birthday party", "birthday", True),
    ("compound", "coffee cup", "coffee", True),
    ("compound", "railroad station", "railroad", True),
    # Adj+N phrases: end-stress (RIGHT) — NSR
    ("adj-phrase", "hot coffee", "coffee", True),
    ("adj-phrase", "old house", "house", True),
    ("adj-phrase", "red car", "car", True),
    ("adj-phrase", "tall building", "building", True),
    ("adj-phrase", "black cat", "cat", True),
    # proper/place + noun: phrasal reading (RIGHT) — but breed/idiom readings
    # are fore-stressed, so these golds are DEBATABLE
    ("proper-mod", "Boston terrier", "terrier", False),
    ("proper-mod", "Chicago winters", "winters", False),
    ("proper-mod", "Sunday dinner", "dinner", False),
    # simple sentences: NSR rightmost content
    ("sentence", "the dog barked", "barked", True),
    ("sentence", "she read the book", "book", True),
    ("sentence", "they painted the fence", "fence", True),
    ("sentence", "the children were playing", "playing", True),
    # PP / ditransitive: rightmost
    ("pp", "the cat on the mat", "mat", True),
    ("pp", "a glass of water", "water", True),
    ("pp", "the man in the moon", "moon", True),
    ("ditrans", "she gave him a book", "book", True),
    # relative clause: rightmost content in the clause
    ("relcl", "the house that Jack built", "built", True),
    ("relcl", "the book that she wrote", "wrote", True),
    # possessive: head noun (RIGHT) — uncontroversial; spaCy's documented weak spot
    ("poss", "John's car", "car", True),
    ("poss", "my brother's house", "house", True),
    ("poss", "the queen's crown", "crown", True),
    # particle verb: object nuclear
    ("particle", "turn off the light", "light", True),
    ("particle", "pick up the phone", "phone", True),
]


def _norm(w):
    w = w.lower()
    return w[:-2] if w.endswith("'s") else w


def _spacy_nuclear(txt):
    import prosodic
    df = prosodic.Text(txt, syntax=True)._syll_df
    sub = (df[(df.form_idx == 0) & (~df.is_punc.astype(bool))]
           .drop_duplicates("word_num").dropna(subset=["tstress"]))
    if not len(sub):
        return "?"
    return _norm(sub.loc[sub.tstress.idxmax()].word_txt.strip())


def main():
    from collections import defaultdict
    from prosodic.analysis.metrical_lp import parse_lptree

    by_cat = defaultdict(lambda: [0, 0, 0])         # [n, stanza, spacy]
    solid = [0, 0, 0]
    for cat, txt, gold, is_solid in CASES:
        st = _norm(parse_lptree(txt).dte.label)
        sp = _spacy_nuclear(txt)
        a, b = st == gold, sp == gold
        by_cat[cat][0] += 1
        by_cat[cat][1] += a
        by_cat[cat][2] += b
        if is_solid:
            solid[0] += 1
            solid[1] += a
            solid[2] += b
        flagS = "OK " if a else "** "
        flagP = "OK " if b else "** "
        note = "" if is_solid else "  (gold debatable)"
        print(f"[{cat:10}] {txt:26} gold={gold:9} "
              f"stanza={flagS}{st:12} spacy={flagP}{sp}{note}")

    print(f"\n{'category':12} {'n':>3} {'Stanza':>8} {'spaCy':>8}")
    for cat, (n, a, b) in by_cat.items():
        print(f"{cat:12} {n:>3} {a:>8} {b:>8}")
    n = len(CASES)
    print(f"{'TOTAL':12} {n:>3} "
          f"{sum(t[1] for t in by_cat.values()):>8} "
          f"{sum(t[2] for t in by_cat.values()):>8}")
    print(f"{'SOLID only':12} {solid[0]:>3} {solid[1]:>8} {solid[2]:>8}")


if __name__ == "__main__":
    main()
