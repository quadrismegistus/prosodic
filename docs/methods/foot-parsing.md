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

**One head per foot.** `#feet = #strong-runs`. Each maximal run of strongs is one
head (one beat); the weak runs between/around them are distributed to neighbouring
feet by the DP. So there is **no pyrrhic** (0-head foot) and **no two-head
spondee**: an `ss` is a *strong resolution* (a disyllabic head, still one beat),
because `max_s = max_w = 2` and positions alternate, so adjacent strong *syllables*
are always one position.

**Cost function** (`_foot_cost`):

| factor | rule |
|---|---|
| foot size | free at the line's **dominant size** (period-2 vs period-3 self-similarity); other well-formed sizes cost more — so a genuinely ternary line isn't broken into cheaper binary feet |
| bare foot | degenerate mid-line (10); **catalexis** at the line end (0.5) — a truncated final foot is legitimate |
| medial head | amphibrach/cretic penalised (+2) |
| word boundary | a foot boundary that splits a word costs a small tiebreak (`MIDWORD`) |

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
(score,  period-k regularity,  distinct pseudo-feet,  stable position)
```

routed through *every* ranking site (`best_parse`, `unbounded`, `parse_rank`,
`get_parses_df`, …) so they all agree (`best_parse == unbounded[0] == rank 1`).

**Crucially, all three tie-break keys are computed from the scansion string — NOT
the DP foot-parser.** `best_parse` is load-bearing (web, `parsed_df`, `meter_type`,
save/load, the `cmp_prosodics` calibration all read it) and must stay *stable*
while the foot layer keeps evolving. The foot-parser is the higher-fidelity view in
`metrical_feet`; it is intentionally kept out of the core ranking.

### Sort-key exploration

| key | agreement w/ foot-based pick | notes |
|---|---|---|
| unique **bigrams** | 86% | but binary-biased (2 bigrams for iamb, 3 for anapest) — broke ternary detection (Browning) |
| **period-k** self-similarity | 80% | meter-agnostic (iamb period-2, anapest period-3 both score maximal); **secondary key** |
| **pseudo-feet** (cut after each strong-run) | 77% alone | cheap, deterministic, foot-flavored; as **tertiary** resolves 39% of residual ties |

Residual ties cascade: **52% → 7%** (after period-k) **→ 4%** (after pseudo-feet)
→ the rest fall to the stable position order, so the sort is fully deterministic.
`_meter_vals` is computed in `__init__` so the entity and DF paths agree.

## 4. Validation

**Against `meter_type`** (the v1 `ww%` + 4th-syllable heuristic): the line-local
footing agrees with it on **98%** of sonnets (the disagreements are the
feminine-ending sonnets, where the 4th-syllable test is more robust).

**Meter recovery across four meters** (litlab tagged sample, 33 poems): **85%** —
anapestic 9/9, iambic 8/9, trochaic 5/6, dactylic 6/9. Misses are genuinely hard
(Blake's *Tyger* is a real trochaic/iambic dispute; *Charge of the Light Brigade*
is irregular).

**Against human foot boundaries** (`parse_human2`, 1731 lines, self-consistency:
strip `|` → re-foot → compare): **32% exact / 51% boundary**. The gap is *not*
delineation but the annotator's **poem-meter conventions** — anacrusis (a leading
upbeat as its own foot), a consistent head across the poem, and catalexis. The same
scansion `wswwswws` is *dactylic + anacrusis* (`w|sww|sww|s`, human) **or**
*anapestic* (`ws|wws|wws`, ours); the human picks by the poem's known meter, which
a line-local parser can't see.

## 5. Roadmap

The foot-parser is now **decoupled from `best_parse`**, so it can be made as rich
(and slow) as needed without destabilizing anything. In rough priority:

1. **Poem-meter awareness (head + size)** — the biggest `parse_human2` gap-closer.
   Detect the poem's (head, size) via the period/phase machinery, then foot each
   line *into* it. Would likely lift agreement into the 60s–70s.
2. **Anacrusis** — a leading upbeat as its own foot (`w|sww|…`) for falling meters;
   pairs with (1).
3. **Word boundaries** — promote the `MIDWORD` tiebreak to a real, tunable cost
   (weak-distribution + word-foot alignment, Kiparsky). Needs a `line`→scansion
   word-alignment (syllabify each word, map to scansion positions) — reusable for
   everything else. *Note:* feet cross words freely in pentameter, so this is a
   moderate preference, not a dominant one.
4. **Phrase boundaries** (`linepart_num` / syntax) — where inversions cluster; ties
   back to the caesura analysis.

**Two models, both defensible.** The current foot-parser is a *mechanical,
line-local* delineation (one head per foot, meter-agnostic). `parse_human2` is
*poem-meter-informed hand scansion*. Matching the human fully means re-encoding the
annotator's convention, which is a different goal from mechanical delineation.
Either is a legitimate destination; (1)–(2) move toward the human one.

**Sort-key determinism (optional):** the position fallback is deterministic given
the (deterministic) candidate order; a scansion-content final key would make it
independent of generation order too.

## Files

- `analysis/feet.py` — `foot_parse` (DP), `head_of`, `line_head`, `parse_feet`, `foot_str`, `_foot_cost`.
- `parsing/vectorized.py` — `LazyParseList._order` (comparator), `_regularity_key`, `_pseudo_foot_key`.
- `parsing/parses.py` — `Parse.metrical_feet`, `Parse.head`, `Parse.feet_str`.
- `texts/lines.py` — `Line.metrical_parse`.
- `scripts/` — `foot_parse.py`, `foot_headedness_demo.py`, `foot_examples.py`, `inversion_map.py`, `caesura_test.py`.
- Validation data — `parse_human2` in `data/tagged_samples/tagged-sample-litlab-2016.txt`.
