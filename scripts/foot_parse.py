"""Foot-parse a raw s/w scansion into a footed string — variable foot size AND
variable headedness within a line, no per-line k or head assumed. Spondees (ss)
and pyrrhics (ww) allowed as costed substitutions.

Uses the same DP as prosodic.analysis.feet (which Parse.metrical_feet calls).
Run: .venv/bin/python scripts/foot_parse.py
"""
import warnings; warnings.filterwarnings("ignore")
from prosodic.analysis.feet import foot_parse, FOOT_LABELS


def parse(scansion):
    proms = [c == "s" for c in scansion.lower() if c in "sw"]
    s = "".join("s" if p else "w" for p in proms)
    # (the word-boundary tiebreak was retired as a null result — human foot
    # boundaries hit word boundaries at chance rate; see foot-parsing.md §"negative
    # results" — so this is the pure foot-cost result.)
    spans = foot_parse(proms)
    feet = [s[a:b] for a, b in spans]
    return "|".join(feet), feet


TESTS = [
    ("s w w s w s w s w s", "your example 1"),
    ("w s w w s w w s w s", "your example 2"),
    ("w s w s w s w s w s", "clean iambic"),
    ("s w s w s w s w s w", "clean trochaic"),
    ("w w s w w s w w s w w s", "clean anapestic"),
    ("s w w s w w s w w", "clean dactylic"),
    ("w s s w s w s w s w", "spondee mid-line (ss)"),
    ("s s w s w s w s w s", "spondee line-initial"),
]
print("raw scansion                ->  footed                   feet")
print("-" * 80)
for raw, note in TESTS:
    footed, feet = parse(raw)
    labels = " ".join(FOOT_LABELS.get(f, f) for f in feet)
    print(f"{raw:<27} ->  {footed:<23}  {labels}    ({note})")
