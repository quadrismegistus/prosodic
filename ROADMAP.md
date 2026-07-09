# Prosodic Roadmap

Planned and potential work, roughly ordered by value within each section.
Items graduate to CLAUDE.md's Done list when they ship. History: `analysis/`
absorbed [poesy](https://github.com/quadrismegistus/poesy) (now a thin shim
over prosodic ≥3.5); [cadence](https://github.com/quadrismegistus/cadence)
(prose-rhythm fork, archived 2026-07) was superseded by v3's `syntax=True`
prose handling — everything it did that prosodic doesn't is preserved below.

## How to work this list

Conventions that produced the 2026-07-05 sprint (PRs #126–#148), kept here
so any future session can continue cold:

- **Flow**: branch → PR → CI green (6 legs incl. Windows) → merge. Master
  pushes auto-deploy prosodic.app (self-healing script) and, for `docs/**`,
  auto-publish the docs site to BOTH ryanheuser.com/prosodic/ and
  prosodic.app/docs/. PyPI releases are deliberate tag pushes (`git tag
  vX.Y.Z && git push origin vX.Y.Z`), published via OIDC trusted publishing.
- **Verification habit**: derive expected outputs by hand or against a
  reference implementation BEFORE trusting your own tests (the MetricalTree
  port's unit tests were self-consistently wrong until a differential vs
  cadence caught the topology bug). Prefer byte-identity checks for
  optimizations (see the bounding elite screen, `tests/test_parsing.py`).
- **Docs are executable**: exploration pages under `docs/explorations/` run
  real `{python}` cells; re-execute locally (main venv), commit `_freeze/`,
  and verify a no-execution render before pushing. Never `gh run rerun` the
  docs workflow — fresh `gh workflow run docs.yml` only.
- **House rule**: no Claude session links in anything public.
- New constraints = one decorated function in `parsing/constraints.py` with
  a `vectorized` lambda; features flow from `_syll_df` columns through
  `parse_batch_from_df` → `evaluate_constraints_batch` (see the pstress/
  tstress/pstrength plumbing, PRs #137/#145, for the pattern to copy).

## From cadence — COMPLETE

All unique cadence capabilities are ported (grid API #136, gradient
MetricalTree #137, `*_p`/`*_t` constraints #138, pstrength + `w_peak_p`/
`s_trough_p` #145, nltk.Tree export #146), cross-validated against cadence
as reference implementation (9-sentence differential, exact agreement, one
documented deliberate divergence on coordination — see
`docs/methods/phrasal-stress.qmd`). Not ported, deliberately:

- **Multi-engine comparison** — never shipped in cadence (vestigial `ENGINE`
  constant); the idea survives in its `notebooks/engines.ipynb` scratch
  harness. Low priority unless a second engine actually lands.
- **Reference notebooks** — before relying on memory of the algorithms, see
  cadence's `notebooks/test-bounding.ipynb` (cleanest statement of the
  harmonic-bounding algorithm) and `engines.ipynb`.

Possible refinements to the MetricalTree port (only if dep projections
prove too coarse in practice): constituency-backed trees via benepar/Stanza
as an optional extra; dictionary-derived lexical stress classes (cadence's
own refinement — replace/augment the tag-list lstress classes in
`_mt_lstress_base` with prosodic's own per-word stress data, incl. graded
values for words with stress-ambiguous pronunciation variants).

## Parser

- ✅ **Ternary meter identification** — shipped 2026-07-06. The gap was
  indeed smaller than assumed: anapestic scansions were already in the
  candidate space and default weights already scan Byron/Browning
  correctly (`meter_type` → anapestic). What shipped: `load_text`/`fit()`
  accept a LIST of targets (line-length-matched — ternary verse varies
  line length via iamb-initial feet); fixed a real bug where
  `fit(zones=None)` learned weights were silently ignored by
  `LazyParseList` scoring; corpus files `en.byron.sennacherib.txt` +
  `en.browning.goodnews.txt`; `tests/test_ternary.py` (8 tests,
  hand-verified scansions); docs § Ternary meters.
- ✅ **Lazy phoneme construction — PROFILED, REJECTED** (2026-07-06,
  measured, never built). `cProfile` + a monkeypatched A/B on the full
  Shakespeare corpus (2155 lines, 24947 syllables, 72280 phonemes) put a
  hard ceiling on the win: fully deleting phoneme construction AND
  stubbing `is_heavy` saved only 0.26s of 1.13s entity-build time (~23%
  of that step, ~10-12% of total init) — and that's unrealistically
  generous, since it assumes syllable weight is never needed. Worse: the
  ceiling is unreachable as sketched. `WordForm.__init__`
  (`words/wordform.py:69-70`) eagerly forces `syll.weight`/`.stress` for
  every syllable immediately after construction — `weight` → `is_heavy`
  → `has_consonant_ending` reads the syllable's last *Phoneme* child, so
  a `cached_property` on `Syllable` alone gets forced open one line
  later for free, saving nothing. A real win needs deferring
  `WordForm.weight`/`.stress` too, plus `Syllable.children` (the
  `Entity`/`UserList` base itself) has no separate `.phonemes` accessor
  to lazily wrap — laziness would mean the shared `Entity`/`UserList`
  base populating `children` on first access, not a one-class patch.
  Not worth a two-layer base-class refactor for a ~0.2s ceiling. Only
  worth revisiting if `Entity`/`UserList` gets reworked for unrelated
  reasons.
- ✅ **Scansion prefiltering — REJECTED** (2026-07-06, rejected on design
  grounds, never built). The idea was to skip scansions where strong
  positions wildly mismatch stressed syllables before constraint
  evaluation. But this prunes the candidate space itself, not just
  `parses.bounded`'s presentation of it — and MaxEnt training needs the
  FULL exhaustive scansion set (violation counts over every candidate) to
  fit weights correctly. Silently dropping candidates pre-evaluation would
  bias the log-linear model in a way that wouldn't surface until training
  accuracy quietly degraded. Not worth that risk for a cost center that's
  likely already minor after the bounding elite screen. Do not revisit
  unless it can be proven an exact dominance screen (byte-identical
  candidate set, like the elite screen already is) — if parse speed needs
  another pass, optimize `evaluate_constraints_batch` itself instead.

## Analysis & display

- 🚧 **Foot delineation & headedness** — a derived foot layer (iamb/trochee/
  anapest/dactyl) over the position scansion, on branch `feet-headedness`
  (PR #175, not merged). Write-up + roadmap:
  [`docs/methods/foot-parsing.md`](docs/methods/foot-parsing.md). Shipped on the
  branch: a DP foot-parser (`analysis/feet.py`, one head per foot, spondee =
  resolution, period-based size, catalexis), `Parse.metrical_feet`/`head`/
  `feet_str`, `Line.metrical_parse`, and a regularity-ranked `best_parse`
  (`_order` = score → period-k regularity → pseudo-feet → position, all cheap and
  computed from the scansion, **deliberately decoupled** from the DP so best_parse
  stays stable while feet evolve). Validated: 98% vs `meter_type`, 85% meter
  recovery across 4 meters, 32%/51% vs the human `parse_human2` foot boundaries
  (gap = the annotator's poem-meter conventions). **Next** (see the doc):
  poem-meter-aware footing (head + size) + anacrusis — the biggest gap-closers —
  then word/phrase boundaries. Foot-annotated corpora are essentially nonexistent
  (only Haider's small set + `parse_human2` + classical quantitative), so this
  fills a real derivation gap.

- ✅ **Web app: combined grid + syntax tree in Line View** — shipped
  2026-07-06 (PR #155, then combined same day). `grid_plot()` redesigned
  first (boxes filled by prominence level, not star marks —
  `LEVEL_NAMES`/`LEVEL_COLORS`/`LEVEL_PALETTE` in `analysis/grid.py` are
  now the shared source of truth). Line View first got the grid and tree
  as two separate components, then combined into one Liberman & Prince
  (1977)-style figure (`MetricalGridTree.svelte`, single SVG, shared
  x-axis): grid boxes stacked above the syllables, dependency-projection
  tree hanging below with root at the bottom and leaves pinned to the
  word row — matching L&P's own convention, and apt beyond style, since
  the grid's "phrasal"/"nuclear" levels are literally projected from the
  tree's tstress values already. Grid columns are per-syllable, tree
  leaves are per-word, so `word_num` was threaded through both
  (`grid_data()` rows, `tree_to_dict()` leaves — `_find_word_num()` in
  `analysis/grid.py`, `tree._word_nums` set by `syntax_trees()`) to
  center a multi-syllable word's leaf over its own syllable-column span.
  No new npm dependency — hand-rolled inline SVG throughout; `svgling`
  was never a real dependency and stays that way. Found and fixed along
  the way: `LineViewTab.svelte` wasn't sending `syntax`/`syntax_model` to
  the backend at all, and `/api/parse/line` dropped `syntax_model` even
  when `syntax` was on. Remaining polish (not blocking): parse-table
  sort/column tweaks if Ryan wants them later.
- ✅ **Rhyme slant-band calibration** — shipped 2026-07-06, upgraded
  same-day from 1-D to a 2-D (nucleus, coda) decomposition after the 1-D
  scalar proved unable to separate gone/alone (real slant) from
  day/night (not a rhyme) — both 0.389. `WordForm.rime_distance_nc()` +
  `rime_type()` classify in the 2-D space (Walker-calibrated, macro-F1
  0.758 vs 0.679 1-D; `scripts/rime_eval.py` 2-D section). The
  calibration independently recovered the classical taxonomy: slant =
  coda identity (consonance), nucleus free; assonance = the mirror
  quadrant (shipped as a label, Walker-unvalidated). Deliberately NOT
  changed: `compute_rhyme_ids`' binary 0.35 (no churn to
  `text.rhyme_ids`, docs freezes untouched). Remaining known limit:
  wordform[0]-only comparison makes noun/verb stress variants
  (IN-crease vs in-CREASE) read as non-rhymes — min-over-forms would
  fix it if it ever matters.
- ✅ **Learned per-feature rhyme weights — INVESTIGATED, REJECTED**
  (2026-07-06, same PR as the 2-D bands; recorded so it isn't re-tried).
  Both follow-ups from the regression/SOTA survey were built and
  measured: (a) non-negative per-channel feature weights (coda fit on
  slant-vs-none, nucleus on perfect-vs-slant; weights phonologically
  sensible) LOSE under the band classifier — Walker macro-F1 0.724 vs
  0.758 uniform, because bands rely on near-identity thresholds and
  zero-weighted features (cor/ant) let different codas score ~0;
  (b) a full 48-dim multinomial wins Walker CV (0.822) but over-recalls
  on the NEW sonnet-scheme validation set (FPR 0.186 vs bands 0.041,
  F1 0.889 vs 0.912) — it learns Walker's 18th-c. permissiveness, not
  real end-rhyme practice. What shipped instead: the sonnet-scheme
  validation itself (`rime_eval.py` — real positives AND true
  negatives, the eval Walker can't provide), the
  `feature_edit_distance(weights=...)` hook, and the fitting code in
  `rime_feature_analysis.py` for future per-language/period weight
  experiments (Lakretz et al. 2018: optimal weights are
  language-specific — relevant once German rhyme data exists).
  Still-open leads if revisited: positional within-coda weighting
  (Woods et al.), corpus-mined confusion signal (Hirjee & Brown 2009).
- ✅ **Band-gated `compute_rhyme_ids`** — shipped 2026-07-06 (follow-up
  PR to the bands). Candidates gated by `rime_type` (perfect/slant),
  ranked perfect-first then nucleus distance; perfect unions without
  mutuality, slant requires MNN. Sonnet scheme detection 137→149/154
  (sonnet 106 fixed — its slant quatrain is consonance the bands hear);
  all churn surfaces updated in the same PR (tests, docs freezes for
  index + sonnets exploration, README rebuild). Legacy scalar mode kept
  via `max_dist=0.35`. poesy consumes `text.rhyme_ids` — notify
  poesy-claude on merge (behavioral improvement, no API change).

## Languages

- ✅ **German (Blankvers)** — shipped 2026-07-06, and much lighter than
  sketched: espeak-ng's German lexical stress turned out highly reliable
  (prefixes, compounds, loanwords hand-verified), so `langs/german/` is a
  thin `LanguageModel` subclass + word lists + a 6-row `german.tsv`
  override for -ur loanwords — no rule engine. The enabling work was a
  latent cross-language TTS syllabifier bug (espeak-token/panphon-seg
  misalignment on diphthongs & affricates) fixed in `syllabify_ipa` and
  differentially verified over all 5294 cached English TTS words.
  Schiller corpus + `tests/test_german.py` (8 tests). Possible follow-ups:
  German g2p spelling table for aligned syllable labels (now NLTK
  fallback); a Goethe/other-meter corpus; grow the word lists from usage.
- **Esperanto — DEFERRED** (2026-07-06, deliberately not picked up by
  Ryan or this session: neither reads Esperanto well enough to hand-verify
  the stress battery the recipe requires — unlike German, where that
  verification was doable firsthand). Community-requested (issue #36,
  2021; the asker wanted it for MA research). Otherwise well-specified
  and easy: fully phonemic orthography, invariant penultimate stress,
  elision (final `-o` apostrophe) as the one wrinkle. Pure
  `get_sylls_ll_rule()` implementation, no dictionary needed. Best suited
  to a contributor (or future session) who can actually read Esperanto to
  check the hand-derived test cases before trusting espeak's output — the
  German port's whole methodology depended on that step. NOTE: consider
  the German (TTS-first) path too — espeak has an `eo` voice; measure it
  first per the recipe in `docs/methods/languages.qmd`. Reply to #36 when
  shipped.

## Docs follow-ups (well-specified; any model)

- ✅ **Surface German + ternary meter in the user-facing tour** — shipped
  2026-07-06. Both siblings (`docs/index.qmd`, `scripts/build_readme.py`)
  got an "Other languages and meters" section: the Schiller `lang="de"`
  line scoring as strict alternation, and Byron's anapestic tetrameter
  with `meter_type` classifying it ternary/anapestic. Freeze re-executed
  and committed; README rebuilt.
- **Optional: a German/Blankvers exploration page** under
  `docs/explorations/` (Schiller corpus is in the repo; follow
  sonnets.qmd's structure: executed cells + committed freeze). Add a
  navbar menu entry in `docs/_quarto.yml`.

## Infrastructure

- ✅ **PyPI Trusted Publishing** — COMPLETE. Shipped for both repos;
  v3.6.0 (2026-07-06) published via OIDC end-to-end and the obsolete
  `PYPI_API_TOKEN` secret is deleted. Releases are `git tag vX.Y.Z &&
  git push origin vX.Y.Z` (bump `_version.py` first); no secrets involved.
- **Docs freeze refresh** — whenever API output shown in
  `docs/index.qmd` / `docs/explorations/*.qmd` changes (e.g. new syllable
  labels, changed scores), re-execute locally and commit `_freeze/`;
  stale freezes silently publish stale numbers. `grep -rn` the frozen
  JSONs for old values when in doubt.
- **README/docs sync** — `scripts/build_readme.py` (GitHub/Colab artifact)
  and `docs/index.qmd` (docs home) are siblings; when the API tour
  changes, update both (each file's header comment says so).
