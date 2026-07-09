"""Prototype demo: principled headedness + foot delineation as a derived view.

Run: .venv/bin/python scripts/foot_headedness_demo.py

Part 1 reads a few single lines to show the machinery; Part 2 aggregates over the
Shakespeare corpus to check whether the delineation is principled-in-practice.
"""
import warnings; warnings.filterwarnings("ignore")
from collections import Counter
import prosodic


def scansion(bp):
    return " ".join("s" if sl.is_prom else "w" for sl in bp.slots)


def show_line(text):
    t = prosodic.Text(text)
    t.parse()
    bp = t.lines[0].best_parse
    feet = bp.metrical_feet
    old = "rising" if bp.is_rising else "falling"          # the fragile position[0] read
    new = bp.head                                          # phase-count over all beats
    flag = "  <-- DISAGREE" if old != new.direction else ""
    print(f'\n"{text}"')
    print(f"  syllables:  {scansion(bp)}   ({len(bp.slots)} syllables, {len(feet)} feet)")
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
    for slot in ft.slots:
        print(f"    {slot.unit.txt:<10}{i:<6}{'yes' if slot.is_prom else 'no'}")

print("\n" + "=" * 70)
print("PART 2 — aggregate over the Shakespeare corpus (is it principled in practice?)")
print("=" * 70)
corpus = open("corpora/corppoetry_en/en.shakespeare.txt").read()
t = prosodic.Text(corpus)
t.parse()

line_data = []
for line in t.lines:
    bp = line.metrical_parse   # regularity-selected co-optimal parse (poem-level)
    if not bp or not bp.slots:
        continue
    feet = bp.metrical_feet
    line_data.append((bp.head, "rising" if bp.is_rising else "falling",
                      [(ft.label, len(ft.pattern), ft.is_substituted) for ft in feet]))

total = len(line_data)
heads = Counter(d[0].direction for d in line_data)
disagree = sum(1 for d in line_data if d[1] != d[0].direction)
foot_types = Counter(lbl for _, _, feet in line_data for lbl, _, _ in feet)
n_feet = sum(foot_types.values())
mixed = sum(1 for _, _, feet in line_data if len({sz for _, sz, _ in feet if sz in (2, 3)}) > 1)
spondee_lines = sum(1 for _, _, feet in line_data if any(l == "spondee" for l, _, _ in feet))
sub_lines = sum(1 for _, _, feet in line_data if any(sub for _, _, sub in feet))

print(f"\nlines analyzed: {total}   (all foot-parsed by DP — size + head derived, not assumed)")
print(f"\nLINE headedness (majority direction of each line's feet):  "
      + "   ".join(f"{k}={v} ({v/total:.0%})" for k, v in heads.most_common()))
print(f"OLD is_rising vs DP head DISAGREE on: {disagree}/{total} ({disagree/total:.0%})")
print(f"\nFOOT inventory ({n_feet} feet):")
for lbl, c in foot_types.most_common():
    print(f"   {lbl:<11} {c:>6} ({c/n_feet:>4.0%})  {'#' * round(60 * c / n_feet)}")
print(f"\nmixed-size lines (binary AND ternary feet): {mixed} ({mixed/total:.0%})")
print(f"lines with a spondee:                       {spondee_lines} ({spondee_lines/total:.0%})  <- rare, as expected")
print(f"lines with >=1 substituted foot (inversion): {sub_lines} ({sub_lines/total:.0%})")
