# Foot parsing

Prosodic parses verse into metrical **positions** (weak/strong), not **feet**.
This document describes the *foot layer* — a derived view that groups syllables
into feet (iamb, trochee, anapest, dactyl, …) — how it is delineated, how it feeds
(and is deliberately kept out of) `best_parse` ranking, how it was validated
against human annotation, and what remains.

> **Why this is hard, and why it's worth it.** A survey of the multilingual
> scansion landscape (Spanish ADSO/DISCO, Russian RNC/RIFMA/PoeTree, German
> DLK/Metricalizer, HuggingFace Arabic/Persian/Sanskrit, ELTeC) found that
> **almost nothing annotates feet.** Scansion is stored as a per-syllable stress
> string and/or a per-line meter *label*, in which the classical foot survives
> only as the meter's *name* (iambic) and *count* (pentameter). The only genuine
> foot-boundary gold sets are Haider's *Metrical Tagging in the Wild* (~150 German
> + 64 English poems), the classical quantitative corpora (Latin Pedecerto/MQDQ,
> Greek hexameter, Czech CCV), and — conveniently — the `parse_human2` column of
> our own `data/tagged_samples/tagged-sample-litlab-2016.txt`. Feet must be
> **derived** from (meter template + realized stress); that derivation is exactly
> what this layer provides.

## 1. The foot-parser (`analysis/feet.py`)

Footing is a **segmentation problem**: cut the per-syllable `s`/`w` string into
feet, minimizing a small cost, solved exactly by **dynamic programming**.

**Read over syllables, not positions.** Feet are read over *syllable slots*, not
metrical positions. Prosodic can't store the traditional `S w | w S` juncture of a
trochaic inversion (two weak *positions* can't be adjacent), so it resolves it into
one weak position — which, footed over positions, hides the inversion. Over
syllables the inversion reappears (`Pi-ty | the-world` = trochee + iamb).

**One head per interior foot.** `#interior feet = #strong-runs`. Each maximal run of
strongs is one head (one beat); the weak runs between/around them are distributed to
neighbouring feet by the DP. So there is **no pyrrhic** (0-head foot) *interior* and
**no two-head spondee**: an `ss` is a *strong resolution* (a disyllabic head, still
one beat), because `max_s = max_w = 2` and positions alternate, so adjacent strong
*syllables* are always one position.

**Extrametrical edges (`w|…`, `…|w`).** The one exception to "every foot has a head"
is at the line edges: a line-initial lone weak (**anacrusis**) or line-final lone
weak (**feminine ending**) may split off as its own *headless* foot. These are
*extrametrical* — not beats — and the DP takes them only when doing so lets the
interior feet be cleaner (recovers `wws|wws|wws|w` over the head-forced
`wws|wws|wwsw`). Note the asymmetry: a lone **`s`** is *not* extrametrical — it is a
catalectic foot, a real beat that counts. A lone **`w`** is.

**Cost function** (`_foot_cost` + `EXTRAMETRICAL`):

| factor | rule |
|---|---|
| foot size | free at the line's **dominant size** (period-2 vs period-3 self-similarity); other well-formed sizes cost more — so a genuinely ternary line isn't broken into cheaper binary feet |
| bare foot | degenerate mid-line (10); **catalexis** at the line end (0.5) — a truncated final foot (a lone `s`) is a legitimate beat |
| medial head | amphibrach/cretic penalised (+2) |
| extrametrical edge | anacrusis `w|…` / feminine `…|w` cost `EXTRAMETRICAL` = 1.0 (tuned on the gold: <0.5 over-peels to 67%, ~1.0–1.5 is the 97.5% plateau) |

**Headedness is an output, not an input.** Each foot's direction (rising/falling)
is read from where its head sits; the line head is the *majority* direction; the
meter's foot size is the majority foot length. Surfaced as `Parse.head`,
`Parse.metrical_feet`, `Parse.feet_str`.

## 2. `Line.metrical_parse` — selecting the reading

Among the co-optimal (equal-score) parses of a line, `metrical_parse` picks the
one with the **fewest distinct full feet** (a regular line is metrically *uniform*
— all iambs, all trochees), line-locally and meter-agnostically. This recovers the
regular reading (`His tender heir…` → 5 iambs) even for a single line in isolation.
`best_parse` tie-breaks *arbitrarily* among co-optimal parses; `metrical_parse`
does not.

## 3. `best_parse` ranking — decoupled from the foot-parser

**52% of Shakespeare sonnet lines have a co-optimal tie**, and `best_parse`'s pick
differs from the regular reading on **23%** — so the tie-break is pervasive, not a
corner case. The shared comparator `LazyParseList._order` ranks by:

```
(score,  fewest ss,  period-k regularity,  distinct pseudo-feet,  fewest ww,  scansion-content [w-onset])
```

routed through *every* ranking site (`best_parse`, `unbounded`, `parse_rank`,
`get_parses_df`, …) so they all agree (`best_parse == unbounded[0] == rank 1`).

**Crucially, all three tie-break keys are computed from the scansion string — NOT
the DP foot-parser.** `best_parse` is load-bearing (web, `parsed_df`, `meter_type`,
save/load, the `cmp_prosodics` calibration all read it) and must stay *stable*
while the foot layer keeps evolving. The foot-parser is the higher-fidelity view in
`metrical_feet`; it is intentionally kept out of the core ranking.

### Sort-key exploration

Every key is a pure scansion statistic (no foot-parser call), so `best_parse` stays
decoupled from the churning DP. In order of discovery:

| key | notes |
|---|---|
| unique **bigrams** | 86% match to a foot pick, but binary-biased (2 bigrams for iamb, 3 for anapest) — broke ternary detection (Browning). Dropped. |
| **period-k** self-similarity | meter-agnostic (iamb period-2, anapest period-3 both maximal); secondary key. |
| **pseudo-feet** (cut after each strong-run) | cheap, deterministic, foot-flavored; resolves ~39% of residual ties. |
| **fewest `ss`** (resolutions) | **primary tie-break** (right after score) — see below. |
| **fewest `ww`** (dips) | last key; putting it *early* costs ~7 pts (`ss,ww`-first = 49.6% vs human). |

**Why `ss` is the primary tie-break, validated against humans.** Ranked against the
human per-syllable scansions in the litlab tagged sample (1597 comparable lines, 4
meters), `ss`-first exact-matches **57.1%** vs **56.3%** for a regularity-first
order — +1% on iambic/trochaic/dactylic, tied on anapestic, never worse. (This
briefly looked *worse* — 89.5% vs 93.1% — but only against `metrical_parse` as the
yardstick, and `metrical_parse` is itself wrong on these ties, so that metric was
rewarding the wrong pick. Against real humans, `ss`-first wins.) A resolution crams
two stresses into one beat — the most marked departure from `wsws…` — so minimising
it *first* is the right markedness ordering.

This is what fixes forced initial inversions **under uniform weights** (every
constraint weight is 1; we do not hand-tune). *"Pity the world, or else this glutton
be"* is a genuine 1–1 tie: the dip `swwswswsws` puts `{ty, the}` in one weak
position → a single `unres_across` (an across-word disyllabic weak may hold only
function words, and "ty" is content-word material); the resolution `sswswswsws` puts
`{Pi, ty}` in one strong position → a single `s_unstress` (unstressed "ty" under a
beat). Both score 1.0 — the grammar cannot separate them, and reweighting to force
it shifts 27% of sonnet parses (not viable). `ss`-first selects the truer dip
`(s w*)(w s)(w s)(w s)(w s)` = trochaic inversion + 4 iambs; regularity-first took
the spondaic `(s s)(w s)…`, stressing "ty", for its cleaner *tail*.

**Fully determinative, honestly.** The last key is the **scansion-content key**
(`_content_key`), not the old generation-order position: a binary fraction of the
scansion with the first syllable most significant and `w`=0/`s`=1, so ascending
order prefers a **`w`-onset** (unmarked weak start) over an initial inversion, and
breaks toward `w` at the earliest diverging position. This drops the sonnet residual
(parses tied on *every* prior key) from ~35 lines falling to enumeration order to
**0** — the winner is now a fixed function of the scansions, refactor-proof, not an
accident of how candidates were enumerated. It does *not* make those genuinely
co-equal readings *meaningfully* distinct (~29 of the 35 differ only in where an
equally-cross-word dip sits — real ambiguity, no signal left); it just makes the
forced last-resort a canonical `w`-leaning convention rather than a fragile one. The
full order (score → ss → period-k → pseudo-feet → ww → content) is total.
`_meter_vals` is computed in `__init__` so the entity and DF paths agree.

## 4. Validation

**Against `meter_type`** (the v1 `ww%` + 4th-syllable heuristic): the line-local
footing agrees with it on **98%** of sonnets (the disagreements are the
feminine-ending sonnets, where the 4th-syllable test is more robust).

**Meter recovery across four meters** (litlab tagged sample, 33 poems): **85%** —
anapestic 9/9, iambic 8/9, trochaic 5/6, dactylic 6/9. Misses are genuinely hard
(Blake's *Tyger* is a real trochaic/iambic dispute; *Charge of the Light Brigade*
is irregular).

**Against a hand-tagged foot gold** (`data/tagged_samples/foot-gold.csv`, 120 lines,
30/meter, `scripts/foot_gold_eval.py`): **97.5% exact / 96.2% boundary** — iambic
100%, trochaic 100%, dactylic 96.7%, anapestic 93.3%.

*`parse_human2` is not a foot gold, which misled an earlier "32%/51%".* The `|` in
the litlab sample is a mix of conventions: iambic is annotated syllable-by-syllable
(`w|s|w|s`, 83% of its lines), anapestic marks upbeat-vs-beat (`ww|s|ww|s`), and
only trochaic is real feet — so we were scoring *correct* feet against a *beat grid*.
Re-tagged by foot (incl. the anacrusis/feminine edges), the same footer scores 97.5%.
Foot-annotated gold sets essentially don't exist in the wild (multilingual survey +
this file), so this 120-line set is the target.

The one real residual is the ternary **rising-vs-falling tie**: `wswwswwsw` foots as
*anacrusis + dactyls* (`w|sww|sww|sw`) **or** *iamb + anapests + feminine*
(`ws|wws|wws|w`) at *identical* cost (one edge foot + a clean interior, 2.0 either
way). Breaking it needs the poem head (falling→anacrusis), which a line-local parser
can't see — and here the gold lines are *labelled* anapestic yet hand-footed falling,
so it isn't even cleanly winnable from the label.

## 5. Roadmap

The foot-parser is **decoupled from `best_parse`**, so it can be made as rich as
needed without destabilizing anything. Against the hand-tagged gold it is already at
97.5%. Remaining work:

1. **Phrase boundaries** (`linepart_num` / syntax) — where inversions cluster; ties
   back to the caesura analysis. Still line-scoped (a line's own syntax), so it fits
   the design below.

**Deliberately *not* done — poem-level footing.** The one real residual (the ternary
rising/falling tie, §4) needs the *poem's* head to break — anacrusis in falling
meters, feminine in rising. The hooks exist (`foot_parse` takes `pref_size`/
`pref_head`; feeding `meter_type` in would likely resolve most of it), and it stays
un-merged on purpose. **Prosodic is line-scoped by design — to a fault:** every unit
(parse, scansion, `best_parse`, footing) is computed from a single line in isolation,
with no cross-line or poem-level state. Wiring a poem→line dependency into footing
would breach that consistency to recover ~2% of ternary lines, so it stays an
*accepted limitation*, not a planned feature. (If it's ever wanted, it should be an
opt-in `pref_head=` argument the caller supplies, never an implicit poem lookup, so
the line-local default is preserved.)

**Done, and recorded as negative results so they aren't re-tried:**
- ✅ **Anacrusis + feminine ending** — headless extrametrical edges (`w|…`, `…|w`),
  cost `EXTRAMETRICAL` tuned on the gold. This was the 93.3%→97.5% lift.
- ❌ **Word-boundary footing** — human foot boundaries land on word boundaries at the
  *chance* rate (`P(foot|word-gap) ≈ P(foot|mid-word)`, sign even flips by meter), so
  the `MIDWORD` tiebreak was retired. No consistent signal to align to.

**Sort-key determinism — done.** The last key is now the `w`-onset-preferring
scansion-content key (§3), so the order is total and independent of generation
order; the remaining residual is genuine metrical ambiguity, not an undecided sort.

## Files

- `analysis/feet.py` — `foot_parse` (DP + extrametrical edges), `_foot_dp`, `line_head`, `parse_feet`, `foot_str`, `_foot_cost`, `EXTRAMETRICAL`.
- `parsing/vectorized.py` — `LazyParseList._order` (comparator), `_regularity_key`, `_pseudo_foot_key`, `_doubled_keys`, `_content_key`.
- `parsing/parses.py` — `Parse.metrical_feet`, `Parse.head`, `Parse.feet_str`.
- `texts/lines.py` — `Line.metrical_parse`.
- `scripts/` — `foot_gold_eval.py` (gold validation), `foot_parse.py`, `foot_headedness_demo.py`, `foot_examples.py`, `inversion_map.py`, `caesura_test.py`.
- **Gold** — `data/tagged_samples/foot-gold.csv` (120 hand-tagged lines). *Not* `parse_human2` in the litlab sample, which is a beat/syllable grid, not feet.
