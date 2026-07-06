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
- **Lazy phoneme construction** — `Syllable.__init__` eagerly builds
  Phoneme children (`words/syllables.py`); could defer to IPA-on-demand
  via cached_property. Only matters on the entity path (DF path never
  builds them). Profile first: init is 2.1s on the sonnets, most of it
  espeak/dict, so the win may be small. Watch `rime_distance` (needs
  phonemes) and `to_dict`/save-load round-trips.
- **Scansion prefiltering** — skip scansions where strong positions wildly
  mismatch stressed syllables before constraint evaluation. Deprioritized:
  after the bounding elite screen, constraint evaluation is a minor cost;
  profile before bothering. NOTE: unlike the elite screen this would change
  `parses.bounded` contents (user-visible) unless done as an exact
  dominance screen — scrutinize before building.

## Analysis & display

- **Web app: grid in Line View + parse table polish** (deferred to last by
  design — Ryan's call, 2026-07-05). The API half is done: `grid_data()` /
  `phrasal_values()` in `analysis/grid.py` give per-syllable rows incl.
  phrasal levels. Remaining: render in the web frontend — either
  server-side HTML from `/api/parse/line` (follow `render_parse_html` in
  `web/api.py`, which walks `line.wordtokens` for punctuation) or ship
  grid_data JSON to a Svelte component (`frontend/src/lib/components/
  LineViewTab.svelte`). `syntax`/`syntax_model` already flow through all
  parse endpoints via the settings store. Check the AUDIT note that the
  web path may restrict the constraint list before assuming parity.
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
- **Learned per-feature rhyme weights** — next step suggested by both
  our own regression (`scripts/rime_feature_analysis.py`: slant-vs-none
  is coda-only, CV 0.924; manner features determinative, place ~ignored)
  and the literature (Yoon et al. 2007; Lakretz et al. 2018 — learned
  feature weights beat hand-set and are language-specific; Hirjee &
  Brown 2009 — corpus-mined phoneme-confusion weights for rap rhyme).
  Sketch: replace the uniform mean-|diff| substitution cost in
  `feature_edit_distance` with per-feature weights fit per channel
  (nucleus vs coda) on Walker — but NOTE this changes the metric under
  `rime_distance` and would churn `rhyme_ids`; either gate behind a
  flag or re-calibrate the 0.35 in the same PR. Also worth building
  first: a true-negative eval set mined from non-rhyming sonnet line
  pairs (Walker is positive-only; German rhyme corpora show ~1/3 of
  real stanzas don't rhyme). Longer-horizon: per-period weights (Walker
  1775 vs modern), positional within-coda weighting (edge-proximal
  consonants matter more — Woods et al.), corpus-mined confusion
  signal. SOTA survey (Reddy & Knight 2011 unsupervised schemes; Haider
  & Kuhn 2018 Siamese nets + German gold corpus; 2026 Greek hybrid
  LLM+phonological-verifier) confirms explicit calibrated phonological
  modeling remains the reliable core; our continuous calibrated
  distance is a novelty vs the discrete taxonomies in the literature.

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
- **Esperanto** — community-requested (issue #36, 2021; the asker wanted it
  for MA research). Easiest possible language: fully phonemic orthography,
  invariant penultimate stress, elision (final `-o` apostrophe) as the one
  wrinkle. Pure `get_sylls_ll_rule()` implementation, no dictionary needed.
  Reply to #36 when shipped.

## Infrastructure

- ✅ **PyPI Trusted Publishing** — shipped for both repos (prosodic
  `release.yml` OIDC via the `pypi` environment; publisher added on PyPI).
  REMAINING: after the next successful `v*` tag release verifies the OIDC
  path end-to-end, delete the now-unused `PYPI_API_TOKEN` secret.
- **Docs freeze refresh** — whenever API output shown in
  `docs/index.qmd` / `docs/explorations/*.qmd` changes (e.g. new syllable
  labels, changed scores), re-execute locally and commit `_freeze/`;
  stale freezes silently publish stale numbers. `grep -rn` the frozen
  JSONs for old values when in doubt.
- **README/docs sync** — `scripts/build_readme.py` (GitHub/Colab artifact)
  and `docs/index.qmd` (docs home) are siblings; when the API tour
  changes, update both (each file's header comment says so).
