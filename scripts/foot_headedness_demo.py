"""Prototype demo: principled headedness + foot delineation as a derived view.

Run: .venv/bin/python scripts/foot_headedness_demo.py

Part 1 reads a few single lines to show the machinery; Part 2 aggregates over the
Shakespeare corpus to check whether the delineation is principled-in-practice.
"""
import warnings; warnings.filterwarnings("ignore")
from collections import Counter
import prosodic


def scansion(bp):
    return " ".join(p.meter_val for p in bp.positions)


def show_line(text):
    t = prosodic.Text(text)
    t.parse()
    bp = t.lines[0].best_parse
    feet = bp.metrical_feet
    old = "rising" if bp.is_rising else "falling"          # the fragile position[0] read
    new = bp.head                                          # phase-count over all beats
    flag = "  <-- DISAGREE" if old != new.direction else ""
    print(f'\n"{text}"')
    print(f"  positions:  {scansion(bp)}   ({len(bp.positions)} positions)")
    print(f"  OLD is_rising (position[0] only): {old}{flag}")
    print(f"  NEW head (phase of all beats):    {new.direction}  (confidence {new.confidence:.2f})")
    print(f"  feet_str:   {bp.feet_str}      (* = inverts the line head)")
    for i, ft in enumerate(feet, 1):
        sub = "  SUBSTITUTED" if ft.is_substituted else ""
        sylls = "-".join(s.txt for s in ft.sylls)
        print(f"     foot {i}: {ft.pattern:<3} {ft.label:<9} head={ft.head:<9}{sub:<13} {sylls}")


print("=" * 70)
print("PART 1 — reading single lines")
print("=" * 70)
# a clean iamb, then two lines that open on a trochaic inversion (the classic
# place a fragile position[0] head-detector goes wrong)
for line in [
    "From fairest creatures we desire increase",
    "Pity the world, or else this glutton be",
    "Making a famine where abundance lies",
]:
    show_line(line)

# per-syllable view for one line: each syllable's foot + whether it's the beat
print("\n  per-syllable view of 'Pity the world, or else this glutton be':")
t = prosodic.Text("Pity the world, or else this glutton be"); t.parse()
bp = t.lines[0].best_parse
print(f"    {'syll':<10}{'foot':<6}{'beat? (is_head)'}")
for i, ft in enumerate(bp.metrical_feet, 1):
    for pos in ft.positions:
        for slot in pos.slots:
            print(f"    {slot.unit.txt:<10}{i:<6}{'yes' if pos.is_prom else 'no'}")

print("\n" + "=" * 70)
print("PART 2 — aggregate over the Shakespeare corpus (is it principled in practice?)")
print("=" * 70)
corpus = open("corpora/corppoetry_en/en.shakespeare.txt").read()
t = prosodic.Text(corpus)
t.parse()

from prosodic.analysis.feet import foot_head
line_data = []
for line in t.lines:
    bp = line.best_parse
    if not bp or not bp.positions:
        continue
    line_data.append((len(bp.positions), bp.head,
                      "rising" if bp.is_rising else "falling",
                      [ft.pattern for ft in bp.metrical_feet]))

total = len(line_data)
heads = Counter(d[1].direction for d in line_data)
confs = [d[1].confidence for d in line_data]
disagree = sum(1 for d in line_data if d[2] != d[1].direction)
poem_head = heads.most_common(1)[0][0]   # the poem-level prior = majority of lines

print(f"\nlines analyzed: {total}")
print(f"\nLINE headedness (each line's own phase):  "
      + "   ".join(f"{k}={v} ({v/total:.0%})" for k, v in heads.most_common()))
print(f"POEM head (majority of lines = the prior): {poem_head}")
print(f"mean line-head confidence: {sum(confs)/len(confs):.2f}   "
      f"(fully-regular, conf=1.0: {sum(1 for c in confs if c==1.0)/total:.0%})")
print(f"\nOLD is_rising vs NEW phase-count head DISAGREE on: "
      f"{disagree}/{total} lines ({disagree/total:.0%})  <- fragility of the position-based test")

# substitution = deviation from the POEM head (the coarse level is the prior)
sub_by_foot, n_penta, fully_flipped, partial = Counter(), 0, 0, 0
for npos, head, old, patterns in line_data:
    if npos != 10:
        continue
    n_penta += 1
    subs = [foot_head(p) not in (poem_head, "none", "ambiguous") for p in patterns]
    for i, s in enumerate(subs, 1):
        if s:
            sub_by_foot[i] += 1
    if all(subs):
        fully_flipped += 1
    elif any(subs):
        partial += 1

print(f"\nfeet SUBSTITUTED vs the POEM head ({poem_head}), pentameter lines (n={n_penta}):")
for i in range(1, 6):
    n = sub_by_foot[i]
    print(f"   foot {i}: {n:>4} ({n/n_penta:>4.0%})  {'#' * round(40 * n / n_penta)}")
print(f"\n   whole-line flips (ALL 5 feet substituted): {fully_flipped} ({fully_flipped/n_penta:.0%})")
print(f"   partial (some feet, a true within-line mix): {partial} ({partial/n_penta:.0%})")
print(f"   -> substitution is ~flat across positions & mostly whole-line: prosodic encodes")
print(f"      inversion as a line-level phase flip (or a violation), not a per-foot event.")
