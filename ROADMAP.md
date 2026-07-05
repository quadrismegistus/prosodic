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
- **Rhyme detection threshold tuning** — `RHYME_MAX_DIST=0` default is
  binary; `analysis/` uses the calibrated 0.35 (Walker 1775, F1-optimal;
  see `scripts/rime_eval.py` + `data/walker5.csv`). Open question: a
  calibrated "slant rhyme" BAND (e.g. perfect < 0.05 < slant < 0.35 < none)
  for the user-facing default. The eval harness exists; extend it to
  three-way classification and pick boundaries by F1 per class. Changing
  the default changes `text.rhyme_ids` everywhere — check the sonnets
  exploration numbers (137 Shakespearean, sonnet 106 → Sonnet A) still
  hold or update them deliberately (re-freeze the docs page).

## Languages

- **German (Blankvers)** — validates the "flexible languages" claim.
  Path: `langs/langs.py` `LanguageModel` subclass like Finnish
  (`langs/finnish/` is the template for rule-based `get_sylls_ll_rule()`);
  espeak has `de` support for the TTS fallback. German needs: syllable
  weight rules, fixed-ish root-initial stress with prefix exceptions
  (be-/ge-/ver-/er-/zer-/ent- unstressed), compound handling. Corpus:
  Schiller/Goethe Blankvers (public domain). The g2p syllable-label
  aligner (`langs/g2p_align.py`) is English-only — German would need its
  own spelling table or fall back to NLTK labels (fine).
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
