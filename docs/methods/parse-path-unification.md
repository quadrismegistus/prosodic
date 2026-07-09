# Retiring the entity parse path (parse-path unification)

**Goal:** the parser has two implementations of the same job — `parse_batch_from_df`
(DF, entity-free) and `parse_batch` (entity) — that must be kept in lockstep and have
already drifted (the mixed-N variant-pooling fix lives only in the DF pooler; the
entity pooler has no ragged support and would crash on a co-optimal longer reading).
Unify on the DF path and delete the duplicate. Branch: `retire-entity-parser` (off
`develop`). Roadmap entry: `ROADMAP.md` § Parser.

**What this does NOT do:** it does not remove `Syllable`/`Phoneme` or any linguistic
entity. The `TextModel → … → Syllable → Phoneme` tree stays and is still built lazily
on access (rhyme, pronunciation, weight, `to_html`). Only a Parse's *slots* unify on
`SyllData` (the DF-path representation) instead of sometimes being real `Syllable`
entities. You can still reach the entities from a parse via the `word_num` bridge.

## The three "parse" mechanisms — only one is the duplicate

| mechanism | entry | slots | role |
|---|---|---|---|
| **DF batch parser** | `parse_batch_from_df` → `_pool_candidates` | `SyllData` | **keeper** — ragged/mixed-N, default for `text.parse()` |
| **entity batch parser** | `parse_batch` → `_pool_combo_parses` | `Syllable` | **duplicate — delete** |
| **manual constructor** | `Parse(line, "wsws")` → `Parse.__init__` | `Syllable` | reference / hand-built parse — *not* a duplicate |

## Phase 1 — retire the entity **batch** parser

### 1a. Callers of `parse_batch` to migrate

| site | context | migration |
|---|---|---|
| `parsing/meter.py:228` | `Meter.parse_text` — already DF-first; this is the fallback when no `_syll_df` | build a `_syll_df` in the fallback (or require one); drop the entity branch. **← start here** |
| `web/api.py:784` | lineparts in the streaming `parse_text` endpoint | linepart-scoped `parse_batch_from_df` |
| `web/api.py:1409` | lineparts in `parse_line` | same |
| `web/api.py:1017` | endpoint importing `parse_batch` | confirm + migrate |
| `web/api.py:1276` | `parse_line` — single-line branch already on DF (done); import remains for lineparts | drop when lineparts move |

The **lineparts** are the only real design work: they need a `syll_df` scoped to a
`LinePart` (a sub-span of a line's syllables), not a whole line.

### 1b. Entity-chain assumptions that break on `SyllData` slots

| site | assumes | action |
|---|---|---|
| `parsing/slots.py` `ParseSlot.wordform`/`.syll` | `unit.parent.parent` (Syllable→WordForm) | breaks on `SyllData` (parent None) → `word_num` bridge, or confirm unused on DF parses |
| `Parse.concat` (`parses.py:245`) | `parse.wordtokens` non-None | make DF-safe (concat is used for linepart aggregation) |
| render `_find_wordtoken` (`api.py:324`) | parent walk **with `word_num` fallback** | ✅ already DF-safe |
| `Parse.wordtoken2slots` (`parses.py:868`) | `word_num` on DF path | ✅ already DF-safe |

### 1c. Delete
`parse_batch` + `_pool_combo_parses` once 1a/1b are done.

### Sequencing finding (from a spike, 2026-07-09)
Migrating `Meter.parse_text`'s `Line` case to DF (so `line.parse()`/`best_parse`
use `SyllData` slots) **works for 672/675 tests and correctly unifies
`line.best_parse` with `text.parse()`** (the mixed-N discrepancy vanishes: both
report `[9,10]` for the temperate line). But it surfaced a hard coupling: three
tests (`from_combinations`, `parselistlist_get_df_and_stats`, `linepart_grid`) fail
because **`Parse.concat` and the `Parse.__init__` invariant
`num_with_forms == num_wordforms` require *resolved* (single-form) entity
wordtokens**, which a DF parse doesn't carry (its `SyllData` slots know `form_idx`
but there's no resolved `WordTokenList`). `scope`/`key`/render are cheap to satisfy
(hand the parse its line's raw `wordtokens` as context), but **`Parse.concat` — the
linepart→line aggregation — is the real blocker.**

**Corrected order:** do **`Parse.concat` DF-safety first** (rebuild a concatenated
parse from `SyllData`/`form_idx` rather than from resolved entity wordtokens, or
relax the invariant for DF-derived parses), *then* migrate `Meter.parse_text`'s
`Line` case. They must land together.

## Phase 2 — route `Parse(line, "wsws")` through the DF path

`Parse.__init__` builds entity slots via `TextModel(...).iter_wordtoken_matrix()`.
Heavily test-covered (`test_parsing`, `test_parselists`, `test_coverage`, `test_ents`,
`test_constraints`). Retiring the batch parser does NOT require touching it, so it's
deferred. Doing it later (build the line's `_syll_df`, slots = `SyllData`) removes the
*last* entity slots and lets `ParseSlot.wordform`/`.syll` simplify to the `word_num`
bridge — the full unification. Keep the public signature.

## Verification (every phase)
- Full test suite green.
- Web Playwright spot-check (table + Line View render, incl. a long/prose line).
- `cmp_prosodics` parity — `best_parse` byte-identical (scores never move; this guards
  against a slot/pooling regression).
- No perf regression on the Shakespeare sonnets profile.

## Progress (order corrected per the spike finding)
- [x] Step 0 — Line View single-line branch → DF path (`api.py`, merged in #175).
- [x] Audit + this doc.
- [x] **`Parse.concat` DF-safe** — `Parse.__init__` takes `slot_units` from `children`
      (positions) when supplied and skips the resolved-wordtokens assert; `concat`
      concats wordtokens only when all constituents carry them, else uses the context
      / None. Manual `Parse(text, scansion)` path unchanged.
- [x] **`Meter.parse_text` `Line`/`LinePart` case → DF** — reuses the parent text's
      `_syll_df` scoped to the unit. **`line.best_parse` now uses `SyllData` slots and
      unifies with `text.parse()`** (temperate reports `[9,10]` both ways). Fixed a
      `LazyParseList.stats` double-`line_num` (index vs column) surfaced by it.
- [ ] 1a — **bare `WordTokenList.parse()`** still hits the entity fallback (no parent
      `_syll_df`). Build a syll_df for it (or from its text). Narrow; rare.
- [ ] 1a — web linepart branches (`api.py:784`, `1409`) → DF (linepart-scoped syll_df).
- [ ] 1a — `api.py:1017` endpoint → DF.
- [ ] 1b — `ParseSlot.wordform`/`.syll` DF-safe (no real callers — low risk).
- [ ] 1c — delete `parse_batch` + `_pool_combo_parses` (blocked on the above callers).
- [ ] Phase 2 — `Parse(line, scansion)` → DF (removes the last entity slots).
