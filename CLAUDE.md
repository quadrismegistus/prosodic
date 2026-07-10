# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Prosodic is a Python library and web app for metrical-phonological analysis of poetry. It parses text into a linguistic hierarchy (text → stanza → line → word → syllable → phoneme) and performs constraint-satisfaction metrical parsing to identify stress patterns (iambic, trochaic, anapestic, dactylic).

## Commands

```bash
# Install (espeak required: brew install espeak on Mac;
#   apt-get install espeak libespeak1 libespeak-dev on Linux)
pip install -e .

# Run tests
pytest
pytest tests/test_parsing.py              # single file
pytest tests/test_parsing.py::test_feet   # single test
pytest --cov=prosodic --cov-report=xml    # with coverage

# Web app (FastAPI + uvicorn)
prosodic web                              # starts on 127.0.0.1:8181
prosodic web --host 0.0.0.0 --port 5111  # custom host/port
prosodic web --dev                        # auto-reload backend + frontend on change

# Frontend dev (requires Node.js)
cd prosodic/web/frontend && npm install && npm run dev  # dev server with hot reload
cd prosodic/web/frontend && npm run build               # build to ../static_build/

# Code formatting
yapf --style .style.yapf -i <file>

# Rebuild README.ipynb + README.md (after API or analysis-module changes)
.venv/bin/python scripts/build_readme.py            # executes cells → README.ipynb AND clean README.md
#   (requires: pip install nbconvert nbclient)

# Recalibrate rhyme threshold against Walker (1775)
.venv/bin/python scripts/rime_eval.py               # ROC, AUC, suggested max_dist
```

`scripts/build_readme.py` is the single source: it executes the cells, writes `README.ipynb` (canonical, Colab-runnable), then converts to a clean `README.md` in the same run — no separate `nbconvert` step. Executed outputs are scrubbed of terminal noise (stderr streams dropped, ANSI/tqdm frames stripped — hashstash's progress bars render into notebook outputs because ipykernel pretends to be a TTY) before saving either artifact. The conversion drops the Colab-only bootstrap cell (tagged `remove_cell`), strips pandas `<style>` blocks, round-trips DataFrame `<table>` HTML into GitHub-native markdown tables, and inserts a standalone `↓` between each code block and its output so the boundary is unambiguous. Edit `build_readme.py`, not `README.ipynb` directly. nbformat regenerates cell UUIDs on every run, so a fresh build always produces a UUID-only `.ipynb` diff — discard it unless content actually changed.

## Architecture

### DataFrame-First Design (v3)

TextModel stores a flat syllable-level DataFrame (`_syll_df`) as the source of truth. Entity objects (WordToken, Syllable, etc.) are constructed lazily only when accessed. The vectorized parser works entirely from the DataFrame without building Entity objects.

**Key flow:**
1. `TextModel.__init__` tokenizes text → calls `get_word()` per unique word → builds `_syll_df`
2. `text.parse()` → `parse_batch_from_df()` reads features from `_syll_df`, evaluates constraints in numpy, bounds on GPU
3. `text.lines` (first access) triggers lazy Entity construction + attaches parse results

**`_syll_df` columns:** `word_num`, `line_num`, `para_num`, `sent_num`, `sentpart_num`, `linepart_num`, `word_txt`, `is_punc`, `form_idx`, `num_forms`, `syll_idx`, `syll_ipa`, `syll_text`, `is_stressed`, `is_heavy`, `is_strong`, `is_weak`, `is_functionword`; with `syntax=True` also `phrasal_stress` (discrete), `pstress`, `tstress` (tree/cumulative), `gstress` (grid/RPPR), `pstrength`

### Entity Hierarchy

All linguistic objects inherit from `Entity` (in `ents.py`), which extends `UserList`. Entities form a parent-child tree:

```
TextModel → Stanza → Line → WordToken → WordType → WordForm → Syllable → Phoneme
```

- **TextModel** (`texts/texts.py`): Root container. Created via `TextModel("some text")`. `children` is a lazy property — entities built on first access. Key properties: `.stanzas`, `.lines`, `.wordtokens`.
- **Line** (`texts/lines.py`): The primary unit for metrical parsing. Call `.parse()` to get parses, `.best_parse` for optimal result.
- **WordToken** (`words/wordtoken.py`): A token in text; wraps a **WordType** (canonical form) which contains **WordForm** variants (pronunciations).
- **WordForm** (`words/wordform.py`): A specific pronunciation with IPA, stress, and weight info. Contains **Syllable** → **Phoneme** children.
- **SyllData** (`texts/syll_df.py`): Lightweight syllable stand-in used by the DF parse path. Duck-types Syllable for Parse construction without Entity overhead.

### Metrical Parsing (`parsing/`)

Theory + implementation write-up: [`docs/methods/metrical-parsing.qmd`](docs/methods/metrical-parsing.qmd).

The parser is always vectorized and exhaustive — it evaluates ALL possible scansions via numpy and uses harmonic bounding to identify optimal parses.

- **Meter** (`meter.py`): Configuration object with constraints, max strong/weak positions (`max_s`, `max_w`). The `exhaustive` and `vectorized` params are accepted but ignored (always both). `pool_forms` (default `True`, `METER_POOL_FORMS`) and `resolve_optionality` (default `True`) are in the meter cache key.
- **Pronunciation-variant pooling (`pool_forms`, default on)**: when a word has multiple pronunciations, `resolve_optionality=True` enumerates the cartesian product of wordform combos; `pool_forms=True` then reports the scansions optimal under **ANY** pronunciation (Prosodic v1/v2 semantics — parses resolve word-forms in situ), deduped by meter string keeping the min-score representative. `pool_forms=False` reports only the single best-scoring combo (the v3-rewrite behavior, an unintended regression). Implemented in `vectorized.py`: `_pool_candidates` (cross-bounds each combo's unbounded parses in pure numpy — within-combo-bounded stays bounded by transitivity — then dedups combo-0-base + overlay so ties keep the canonical pronunciation; the entity-path twin `_pool_combo_parses` was retired with the entity parser in PR #176). Returns a concatenated `LazyParseList` with per-scansion `sylls_by_scansion` (so an alt-pronunciation parse reports its own `form_idx`/stress); `get_parses_df` stays numpy-only. Builds `LazyParseList`s lazily (fast path builds only combo 0), ~15% over no-pool. `num_parses` is a distinct-meter-string count matching v1's reported count.
- **Constraints** (`constraints.py`): Each constraint has a `@constraint` decorator with `desc`, `scope`, and optional `vectorized` lambda. The vectorized lambda receives broadcast feature arrays and returns `(L, S, N)` int8 violations — this is what runs during parsing. The entity-based function body is a reference implementation used only by manually-constructed Parse objects. Default constraints: `w_stress`, `s_unstress`, `unres_within`, `unres_across`, `w_peak`, `foot_size`. Additional: `s_trough`, `clash`, `lapse`, `w_heavy`, `s_light`, `s_func`, `word_foot`. Phrasal stress constraints (require `syntax=True`): `w_prom`, `s_demoted` (discrete depth), `w_stress_p`/`s_unstress_p` (local phrasal `pstress`), `w_stress_t`/`s_unstress_t` (tree/cumulative `tstress`), `w_stress_g`/`s_unstress_g` (grid/RPPR `gstress`), `w_peak_p`/`s_trough_p` (local peak/valley `pstrength`). Adding a new constraint = one decorated function in `constraints.py` with a `vectorized` lambda; no changes to `vectorized.py` needed.
- **Parse** (`parses.py`): A single candidate parse. Ranked by weighted violation score; `best_parse` = lowest score among unbounded, with **co-optimal ties broken deterministically** by `LazyParseList._order` — a pure-scansion comparator (fewest resolutions `ss` → period-k regularity → distinct pseudo-feet → fewest dips `ww` → canonical `w`-onset content key), decoupled from the foot DP. `num_cooptimal`/`is_tied` surface how many distinct scansions tied.
- **LazyParseList** (`vectorized.py`): Stores numpy violation data. Parse objects built only on access. `.unbounded`/`get_parses_df`/`parse_rank` all rank via `_order` (so they agree). `.best_parse` **short-circuits to `argmin` when the min score is strictly unique** (~half of lines — the tie-break is irrelevant there); only a genuine score tie runs the full `_order`. (`_order`'s per-scansion keys are cheap/cached; the rectangular-path `ss`/`ww`/content keys are vectorized.)

**Parsing flow:** `TextModel.parse()` → `parse_batch_from_df(syll_df, meter)` → groups by line, extracts features from numpy arrays → `evaluate_constraints_batch()` broadcasts features against scansion matrices → `compute_bounding_batch()` on GPU → results stored by line_num, attached to Entity lines lazily.

**Bounding optimization:** Lines with a perfect parse (0 violations) skip the O(S²) pairwise comparison entirely — the perfect scansion bounds everything else. Non-perfect lines go through an **elite pre-screen** first: candidates dominated by one of the K=16 lowest-total candidates are eliminated in O(K·S) (mean ~3 survivors of ~180 on the sonnets), and the exact pairwise kernel runs only on the survivors. Exact by transitivity of dominance — byte-identical to full pairwise (tested). CPU parse is now ≈ GPU parse; the GPU is no longer needed for parsing.

### MaxEnt Weight Learning (`parsing/maxent.py`)

`MaxEntTrainer` learns constraint weights from annotated data or a target scansion using Maximum Entropy (log-linear) optimization. Based on Goldwater & Johnson (2003) / Hayes MaxEnt OT.

- **`MaxEntTrainer(meter, regularization=100.0, zones=None)`**: zones splits the violation matrix by syllable position before training. `"initial"` = first 2 syllables vs rest. `3` = three equal zones. `"foot"` = per foot.
- **`load_annotations(data)`**: accepts `[(text, scansion, frequency), ...]` or DataFrame with those columns. Parses all lines via `parse_batch_from_df`, matches annotations to candidate scansions.
- **`load_text(text, "wswswswsws")`**: assigns a target scansion to all lines — no annotation file needed. Also accepts a LIST of targets for meters whose line length varies (ternary verse: `["wwswwswwswws", "wswwswwswws"]` = anapestic tetrameter ± iamb-initial foot); each line matches the target(s) of its syllable count.
- **`train()`**: L-BFGS-B optimization (scipy). Converges in <1s on 2000+ lines. Vectorized gradient via `einsum` over groups of same-length lines.
- **`learned_weights()`** / **`apply_to_meter()`**: extract or apply learned weights.

**Key design**: operates on the `(S, N, C)` violation matrices already produced by the parser. Zone splitting is post-hoc feature engineering — partitions the N (syllable) axis into zones before summing, creating `C * n_zones` features. No parser changes needed.

**`meter.fit()` pipeline**: `Meter.fit(text, "wswswswsws", zones=3)` trains MaxEnt weights on a corpus and stores `meter.zone_weights` (dict of zone-expanded constraint names → weights) and `meter.zones` on the meter. `LazyParseList` scoring uses learned weights whenever `zone_weights` is set — with `zones=None` this degrades to flat weighted scoring (`zone_split` just sums over N), so `fit(zones=None)` weights are honored too. This means learned positional sensitivity transfers to parsing unseen text. Also `meter.fit_annotations(data)` for annotated data (list of tuples or DataFrame).

**Ternary meters**: nothing parser-side is binary-specific — anapestic feet are `ww` positions + `s` positions, already in the candidate space (`max_w=2`). Default weights scan regular anapestic lines correctly (Byron/Browning corpus files + `tests/test_ternary.py`); `fit()` with a target list learns the ternary signature (strict `s_unstress`/`unres_within`, free `w_stress`/`unres_across` — Hanson & Kiparsky 1996). See `docs/methods/metrical-parsing.qmd` § Ternary meters.

**Shared utilities**: `zone_split(viols_3d, zones)`, `zone_boundaries(zones, N)`, `make_zone_names(base_names, nsylls, zones)` — used by both MaxEntTrainer and LazyParseList.

**Constraint entailment**: w_peak entails w_stress (100% co-occurrence). In MaxEnt/HG, overlapping constraints stack: w_peak violation costs w_peak + w_stress. This is how the model makes w_peak effectively inviolable (Kiparsky) without infinite weight.

### Phrasal Stress (`texts/phrasal_stress.py`, `analysis/metrical_lp.py`)

Theory + lineage: [`docs/methods/phrasal-stress.qmd`](docs/methods/phrasal-stress.qmd) (MetricalTree), [`docs/methods/constituency-backend.qmd`](docs/methods/constituency-backend.qmd) (faithful L&P + the two-backend validation).

Optional phrasal prominence (Liberman & Prince 1977) from `TextModel("...", syntax=True)`. **Two interchangeable engines**, a one-parameter swap producing the same `_syll_df` columns — they differ only in the parse:

- **spaCy** (default, `syntax_model="en_core_web_sm"`): Dozat's MetricalTree over a dependency projection. Fast.
- **Stanza** (opt-in, `syntax_model="stanza"`): faithful L&P over a real constituency parse (`metrical_lp.py`) — the binary metrical tree, DTE, and RPPR grid the dep projection can't represent.

**Columns** (all [0,1], 1.0 = nuclear, NaN = punct; both engines):
- **`phrasal_stress`**: discrete depth (0 = root/most prominent, negative = embedded).
- **`tstress`** = **tree stress** (cumulative, L&P eq-12 / Dozat total) — fine-grained. spaCy: Dozat native; Stanza: `stress_numbers()` over the LP tree.
- **`gstress`** = **grid stress** (RPPR grid height, L&P's preferred, coarse). Stanza: `grid_heights()` native; spaCy: `_mt_grid` binarizes the projection (NSR/CSR) and runs the *same* `grid_heights`. Grids agree closely across engines; tree stresses differ more.
- **`pstress`** = local phrasal peak (1.0 if strong child of parent), **`pstrength`** = local peaks/valleys.

**spaCy tokenization (default `spacy_free=True`)**: parse the full sentence text WITH punctuation (so clitics split — `beauty's`→`beauty`+`'s`→`poss` not `compound`, fixing a real possessive bug — and clauses attach), but flatten newlines to spaces first (verse line breaks, not punctuation, confuse a dep parser) and DROP punctuation before the gradient (a sentence-final period attaches to the root and would inflate its cumulative stress). `spacy_free=False` = legacy pre-tokenized path.

**Sentence scoping**: both engines group by prosodic `sent_num`; Stanza runs `tokenize_no_ssplit=True` so 1 prosodic sentence = 1 tree, same normalization unit as spaCy.

**Tree export**: `text.syntax_trees()` is engine-aware — dep-projection `nltk.Tree` (preterminals `TAG/tstress`) under spaCy, faithful L&P binary s/w tree (`R`/`s`/`w` nodes, `role/tstress` leaves, via `lp_nltk_trees`) under stanza. `import svgling` renders either.

**Grid integration**: `line.grid_str()/grid_df()/grid_plot()` render `gstress` (the actual RPPR grid; falls back to `tstress` for old data) — height 4 = phrasally prominent, 5 = nuclear. `SyllData.word_num` bridges DF-path slots to word-level values.

**Constraints** (all inert when `syntax=False` via `has_phrasal`/`has_gradient`): `w_prom`/`s_demoted` (discrete `phrasal_stress`); gradient `w_stress_p`/`s_unstress_p` (pstress), `w_stress_t`/`s_unstress_t` (**tree** stress), `w_stress_g`/`s_unstress_g` (**grid** stress), `w_peak_p`/`s_trough_p` (pstrength). Adding one = a decorated function reading `f["gstress"]` etc.; the feature is plumbed in `vectorized.py` (−1 sentinel = absent).

**Stanza caching**: `_stanza_parse()` caches serialized `stanza.Document` objects (`to_serialized()`/`from_serialized()`) in a HashStash under `~/prosodic_data/data/cache/stanza_constituency`, keyed by `(lang, config-version, text)`. Cold ~3.5s/sonnet → warm ~0.01s (267×). Caches the RAW parse, so improving the L&P tree/grid logic never invalidates it; bump `_STANZA_CACHE_VERSION` only on a pipeline-config change. Stanza is an extra dependency (`pip install prosodic[syntax]` covers spaCy; Stanza installed separately).

- **Config**: `DEFAULT_SYNTAX = False`, `DEFAULT_SYNTAX_MODEL = "en_core_web_sm"` in `imports.py`.
- **MaxEnt integration**: `meter.fit_annotations(data, text=text_with_syntax)` passes a pre-built syntax-enabled TextModel through to the trainer.
- **Empirical notes**: (a) on Shakespeare sonnets with `wswswswsws`, phrasal constraints are redundant with lexical stress (69.2% with or without) — no signal for fixed-template scansion. (b) The possessive advantage once attributed to constituency was a *tokenization artifact*; once both engines split clitics they agree ~91% on sonnet nuclear placement. Constituency retains only a marginal structural edge (see `constituency-backend.qmd`).

### Syllable DataFrame (`texts/syll_df.py`)

- `build_syll_df(token_dicts, lang)`: Builds the flat DataFrame from tokenized word dicts + `get_word()` output. Computes all syllable features (stress, weight, strong/weak, functionword) without constructing Entity objects.
- `SyllData`: Lightweight `__slots__` class that duck-types the Syllable interface for Parse/ParseSlot.
- `_phone_is_vowel()`, `_syll_is_heavy_from_ipa()`: Compute phonological features from IPA without Entity objects.

### Language Support (`langs/`)

- **English** (`langs/english/`): Uses CMU pronunciation dictionary (2700/3206 Shakespeare words) + espeak TTS fallback (506 words, ~1.4s cold). `get_word()` cached via `@functools.cache`.
- **Verse elision** (`langs/english/english.py`, `EnglishLanguage.use_elision`, default on): 12 English synaeresis rules (`ELISION_RULES`, ported from v1's `add_elisions`) add a reduced-syllable pronunciation variant — flower→flour, heaven→heav'n, fire→fi'r, seven→sev'n, opening→op'ning, gardener→gard'ner, etc. Each rule maps a 2-syllable IPA sequence (`.` = syllable boundary) to its 1-syllable form; applied in `LanguageModel.get_sylls_ipa_ll` after formatting (base language elides nothing). It's an OPTION, not a forcing: `pool_forms` uses the elided reading only where it scans better ("sweet as love which overflows her bow'r" → clean pentameter). Because elided variants differ in syllable count, they exercise **mixed-N pooling** (below).
- **Mixed-syllable-count pooling**: when a word's variants differ in syllable count (fire 1~2, flower 1~2), `pool_forms` cross-bounds unbounded parses ACROSS lengths (the bounding vector is N-independent) and keeps co-optimal parses of **all** lengths — matching v1. A single `(P,N,C)` array can't hold varying-length scansions, so mixed-N results use a **ragged `LazyParseList`**: `_all_viols` is a *list* of per-scansion `(N_k,C)` arrays (with `_meter_vals`/`_position_ids`/`_position_sizes` parallel lists) and `_ragged=True`. The fast rectangular path is untouched for same-length lines; only per-scansion consumers special-case ragged — `_build_single_parse` takes the per-parse 2D viols slice, `get_parses_df` uses `_ragged_chunk` (each parse reports its own pronunciation's `form_idx`), and MaxEnt skips ragged lines. ~5% of lines are ragged; ~1.3× no-pool.
- **Finnish** (`langs/finnish/`): Custom stress, weight, and sonority rules.
- **German** (`langs/german/`): espeak-driven — espeak-ng's German lexical stress is highly reliable (validated on prefix/compound/loanword classes, `tests/test_german.py`), so no rule engine; `german.tsv` overrides the one systematic miss (-ur loanwords: Natur), `unstressed_words.txt`/`ambig_stress_words.txt` mark function words. Schiller Blankvers corpus at `corpora/corppoetry_de/`; 20/30 monologue lines scan strict iambic at defaults.
- **TTS syllabifier** (`langs.py syllabify_ipa`): espeak tokens are aligned to panphon segs per-token — diphthongs (`aʊ`) and affricates (`dʒ`) are one espeak token but two panphon segs, and the old naive zip shifted every boundary flag after the first such token (wrong counts/weights for TTS-fallback words in all languages). Rules: vocalic token = first-seg flag + forced boundary between adjacent nuclei; consonantal token = any-seg flag splits before the token. Differentially verified over all 5294 cached English TTS words.
- **Syllable text labels** (`langs/g2p_align.py`): orthographic syllable splits come from grapheme-to-phoneme DP alignment against the IPA syllabification ("within" → wi|thin, not NLTK's wit|hin — issue #47). 99.8% of dictionary words align; failures (letter-by-letter initialisms) fall back to the legacy NLTK sonority split. English-only via `EnglishLanguage.use_g2p_alignment = True`.
- Language detection via `langdetect`. Default language: `"en"`.

### Centralized Imports (`imports.py`)

All global constants, paths, and shared imports live in `imports.py`. Modules import from it via `from prosodic.imports import *`. Key constants: `DEFAULT_LANG`, `DEFAULT_METER`, `METER_MAX_S`, `METER_MAX_W`, `MAX_SYLL_IN_PARSE_UNIT` (18, bumped from 14 — 50ms GPU, 2.1s CPU at this cap). `SEPS_PHRASE` defines punctuation that triggers linepart boundaries; ASCII `--` is normalized to em-dash in the tokenizer.

### Memory Management

- `DEFAULT_USE_REGISTRY` is `False` — the OBJECTS registry (WeakValueDictionary, register_objects, find, match) has been removed.
- `TextModel.cleanup()` explicitly clears parse results and cached properties.
- `Entity.clear_cached_properties()` removes all `@cached_property` values from an entity's `__dict__`.
- TextModel children are lazy — if you only need parse results (no Entity access), ~280K objects are never created.

### Web App (`web/`)

FastAPI backend + SvelteKit frontend (compiled to static files). PWA-ready, mobile-friendly.

**Backend** (`api.py`):
- FastAPI JSON API with endpoints: `/api/meter/defaults`, `/api/parse`, `/api/parse/stream` (SSE), `/api/parse/line` (single-line detail), `/api/parse/export` (CSV/TSV/JSON download), `/api/maxent/fit`, `/api/maxent/fit-annotations`, `/api/maxent/reparse`, `/api/corpora`, `/api/corpora/read`
- `/api/parse/line` returns ALL scansions (unbounded + bounded) for a single line, with per-position violation details and violation summaries
- `render_parse_html(parse, line)` returns server-rendered HTML strings with CSS classes for meter/stress/violation styling. When `line` is passed, walks `line.wordtokens` to interleave punctuation tokens. Parent chain from syllable to WordToken is 5 hops (use `_find_wordtoken` which walks up by class name).
- `serialize_parse()` removed — Pydantic SlotData objects were too slow for 10K+ line texts
- Serves built SvelteKit frontend from `static_build/` directory
- Streaming parse results via SSE in batches of 50 lines for progressive rendering
- MaxEnt accuracy computed from trainer: `_compute_accuracy()` checks predicted vs observed best scansion per line
- **Prose handling**: `_long_line_nums(t)` detects lines > `MAX_SYLL_IN_PARSE_UNIT` (canonical syllable count via `form_idx==0`). Those lines fall back to linepart-level parsing; short lines stay on the normal line path. `_aggregate_lineparts()` stitches linepart results back per line_num with `<br>` line breaks in both Parse and Meter columns. Punctuation-only lineparts (0 sylls) render as plain interstitial text; content lineparts that couldn't parse (>MAX) render as italic. When `syntax=True`, oversized lineparts are further sub-split at dep-tree clause boundaries via `_syntax_subsplit()`.
- **Data export**: `/api/parse/export` returns per-line CSV/TSV/JSON with best-parse stats + `_unbounded` averages (sum across unbounded / total syllables). Frontend Export button with format dropdown in ParseResults.
- **`--dev` mode**: `prosodic web --dev` runs uvicorn as subprocess with `--reload` watching `prosodic/` + spawns `npm run build --watch` for frontend. Uvicorn run as subprocess (not in-process) to avoid macOS multiprocessing spawn issues.
- **Settings store**: shared persisted store in `stores.js`; `syntax`/`syntax_model` flow through to all parse endpoints. Settings tab reads/writes the shared store.

**Frontend** (`frontend/` → builds to `static_build/`):
- SvelteKit with `adapter-static`, builds to ~180KB (replaced 13MB of jQuery/DataTables)
- **Component-based tabs with URL routing**: all tabs stay mounted, preserving state and scroll position. `goTab()` uses `pushState` for shallow routing (`/`, `/line`, `/meter`, `/maxent`, `/settings`) — back/forward works. Active tab in `activeTab` persisted store. Lucide icons on both top nav (desktop) and bottom nav (mobile).
- 5 tabs: **Parse** (text input + corpus dropdown + results), **Line** (single-line detail with all scansions), **Meter** (constraint config + weights), **MaxEnt** (file upload + training), **Settings** (global options)
- Parse tab: clicking a line navigates to Line View with full scansion detail (unbounded + bounded)
- Line View: text input for manual line entry, shows all scansions sorted by score with violation badges, bounded parses grayed out. Also renders a combined Liberman & Prince (1977)-style figure (`MetricalGridTree.svelte`, one SVG, single shared x-axis): the metrical grid (colored boxes by prominence level, matching `grid_plot()`'s palette) stacked above the syllables, and — when `syntax=True` — the dependency-projection syntax tree hanging below (root at the bottom, leaves pinned to the word row; a multi-syllable word's leaf is centered over its own syllable columns via `word_num`, which `grid_data()` rows and `tree_to_dict()` leaves both now carry). Click a table row to switch which candidate's grid/tree is shown. No charting/tree-layout npm dependency — hand-rolled inline SVG. Fed by `/api/parse/line`'s `grid`/`syntax_trees`/`grid_palette`/`grid_level_names` fields; `tree_to_dict()` in `texts/phrasal_stress.py` converts `nltk.Tree` to JSON for this.
- Settings tab: syntax toggle, spaCy model, language, max syllables, parse timeout
- Parse results: sortable columns (Line, Meter, Score, Ambig), pagination (50/100/250/500 per page), best-only / all-unbounded toggle
- MaxEnt zone weights saved to Meter config and used for zone-aware scoring in Parse
- All config persisted in localStorage (meter config, weights, zone weights, last text, maxent params, active tab, settings)
- Corpus dropdown loads texts from `corpora/` directory

**Pydantic models** (`models.py`): `MaxEntFitRequest/Response`, `MaxEntReparseRequest/Response`, `MeterDefaultsResponse`, `CorpusFile/ListResponse`, `WeightEntry`

**Weight system**: Two modes of scoring:
1. **Manual weights**: per-constraint weight boxes on Meter page (default 1.0), sent as `name/weight` format
2. **Zone weights**: learned by MaxEnt, stored as `meter.zone_weights` dict (zone-expanded names → weights). When active, override manual weights for scoring. Reset via "Reset Weights" button.

- Run with `prosodic web` or `python -c "from prosodic.web.api import main; main(port=8181, host='0.0.0.0')"`

### Remote Client (`client.py`)

`prosodic.client` provides a remote API client that duck-types the local `TextModel`/`Line`/`Parse` interfaces. Only requires `requests` — no numpy, espeak, or prosodic internals.

**Usage:**
```python
import prosodic
prosodic.set_server("https://prosodic.app")  # or "http://localhost:8181"

t = prosodic.Text("From fairest creatures we desire increase")  # returns RemoteText
t.parse()                           # calls /api/parse
for line in t.lines:
    print(line.best_parse.meter_str, line.best_parse.score)

t.parse_lines()                     # calls /api/parse/line per line (all scansions)
for p in t.lines[0].parses.bounded:
    print(p.meter_str, p.score)

result = t.fit(target_scansion='wswswswsws', zones=3)  # calls /api/maxent/fit
print(result.weights, result.accuracy)
```

**Key design:** `Text()` factory checks `get_server()` — if set, returns `RemoteText`; otherwise returns local `TextModel`. Downstream code using `.lines`, `.parse()`, `.best_parse` works identically.

**Proxy objects:** `RemoteText`, `RemoteLine`, `RemoteParse`, `RemoteParseList` duck-type their local equivalents. `_HttpTransport` wraps either `requests` (URL string) or FastAPI `TestClient` (for tests).

**Save/load:** `t.save(path)` saves parse results as JSON (`remote_parse.json`) + optional parquet. `RemoteText.load(path)` reconstructs from JSON without a server.

### Deployment (`deploy/`)

Server deployment config for running prosodic.app (and optionally lltk.net) on a single VPS.

- `nginx-prosodic.conf`: Nginx vhost config for prosodic.app. TLS added by certbot on first setup.
- `prosodic.service`: systemd unit file for the FastAPI server.
- `setup.sh`: One-shot provisioning script (apt, venv, clone, build, start).

Target: Hetzner CCX33 (~$35/mo), CPU-only (GPU not needed for serving).

### Desktop App (removed)

A Tauri v2 desktop scaffold (Python backend as PyInstaller sidecar with bundled espeak) lived in `desktop/` but was never built into a shipped artifact and was removed 2026-07-05 to retire its maintenance surface. Restore with `git checkout desktop-scaffold -- desktop/` (the tag points at its last, dependency-patched state).

## The Parse Path (one, DF)

Parsing goes through a single path — the DF path — since the duplicate entity parser (`parse_batch`/`_pool_combo_parses`) was retired in PR #176 (see `docs/methods/parse-path-unification.md`). It works entirely from `_syll_df`; Parse objects contain `SyllData` slots (lightweight, no parent chain). Two entry points:

1. **`parse_batch_from_df(syll_df, meter, line_col=...)`**: batch-parses a whole `_syll_df` grouped by `line_col`. Used by `text.parse()`. Good for batch processing, `text.parsed_df`, `text.save()`.
2. **`parse_units_from_df(units, syll_df, meter)`**: parses arbitrary `WordTokenList` units (a single Line/LinePart, lineparts, syntax sub-splits, bare token lists) by scoping the parent `syll_df` to each unit's `word_num`s (entity-agnostic — never a `df_col` derived from `meter.parse_unit`). Used by `line.parse()`/`line.best_parse` (via `Meter.parse_text_iter`) and the web linepart passes. This is why `line.best_parse` now matches `text.parse()`.

The `TextModel → … → Syllable → Phoneme` entity tree still exists and is built lazily on access (rhyme, pronunciation, weight, `to_html`); only Parse *slots* are `SyllData`. Reach entities from a parse via the `word_num` bridge (`SyllData.word_num == WordToken.num`). The one place that still builds *entity* Parse slots is the manual constructor `Parse(line, "wsws")` — a reference/hand-built parse, deliberately not routed through the DF path (it hand-builds one parse from a given scansion; it is not a bulk parser).

**Gotchas:**
- DF-path parses have `slot.unit.parent = None` — can't traverse to wordtoken/wordform; use `slot.unit.word_num`.
- `text.parse()` stores results in `text._line_parse_results[meter_key]`. When `text.lines` is first accessed, results are attached to line entities via line_num matching. A `line.best_parse` accessed *without* a prior `text.parse()` parses that single line on demand via `parse_units_from_df`.
- `parse.wordforms` is the raw (multi-variant) WordTokenList on the line path and `None` on `text.parse()` — do NOT count words with `len(parse.wordforms)`; `parse.num_words` counts distinct `word_num` across slots for exactly this reason.
- `LazyParseList` defers Parse object construction. `best_parse` builds exactly 1 Parse (argmin when the min score is unique, else the `_order` tie-break among the co-optimal set). Iterating builds all.
- `text.parsed_df` is a cached property (default meter). Use `text.get_parsed_df(**kwargs)` for custom meters.

### Rhyme Detection (`words/wordform.py`, `words/phonemes.py`)

- `WordForm.rime_distance(other, max_dist)` computes distance between word rimes.
- Uses **feature-weighted edit distance** on IPA segments via panphon: aligns phonemes via DP where substitution cost = normalized feature distance. Returns 0-1 (0 = perfect rhyme).
- `max_dist=0` (default, `RHYME_MAX_DIST`): binary exact match. `max_dist=None`: no limit, returns gradient distance.
- `WordForm.rime_distance_nc(other)`: 2-D decomposition — (nucleus, coda) feature-edit distances, where nucleus = leading vowel run of the rime and coda = everything after incl. unstressed tail. Separates what the scalar conflates: gone/alone (0.58, 0.00) vs day/night (0.08, 1.00).
- `WordForm.rime_type(other)` / `Line.rime_type(line2)`: classification in the 2-D space, regions Walker-calibrated (`scripts/rime_eval.py` 2-D section, macro-F1 0.758 vs 0.679 for 1-D): `'perfect'` (dn ≤ 0.05 ∧ dc ≤ 0.15), `'slant'` = consonance (dc ≤ 0.05, nucleus free — the calibration independently recovered the classical definition), `'assonance'` (dn ≤ 0.05, coda mismatch; linguistically real but Walker has no assonance class to validate against), else `None`. Constants `RHYME_PERFECT_NUC_MAX` etc. in imports.py. `compute_rhyme_ids` now uses these bands by default too (see below).
- `scripts/rime_feature_analysis.py` (needs sklearn): per-feature logistic regression over Walker. Slant-vs-none is coda-only (0.920 CV from coda features alone); within the coda, manner features (lat/nas/cont/voi) are determinative while place (ant/cor) barely matters; perfect requires vowel rounding+length match.
- **Validated on real verse** (`rime_eval.py` sonnet-scheme section: scheme pairs = positives, within-quatrain non-scheme pairs = TRUE negatives): bands F1 0.912/FPR 0.041 vs 1-D scalar FPR 0.226. **Negative results, recorded so they're not re-tried**: (a) learned per-feature channel weights lose to uniform under the bands (0.724 vs 0.758 Walker macro-F1 — identity thresholds leak when features are zero-weighted); (b) a 48-dim multinomial wins Walker CV (0.822) but over-recalls on real verse (FPR 0.186) — it learns Walker's historical permissiveness. `feature_edit_distance(weights=...)` param exists for future per-language/period weight experiments.
- `PhonemeList.feature_edit_distance(other)`: the core DP alignment. `PhonemeList.feature_distance(other)`: legacy euclidean on averaged features (still available but not used by rime_distance).
- `Line.rime_distance(line2)`: delegates to final wordform's rime_distance.
- `Text.get_rhyming_lines()`, `Text.is_rhyming`, `Text.num_rhyming_lines`: aggregate rhyme detection.

### Poem-Level Analysis (`analysis/`)

Higher-order summary statistics over a parsed text. Surfaced as TextModel properties; ported from the standalone `poesy` package (Heuser et al., Stanford LitLab) into prosodic v3.

- **`text.meter_type`**: dict with `foot` (binary/ternary), `head` (initial/final), `type` (iambic/trochaic/anapestic/dactylic), and per-position frequencies. Aggregates across all best parses; uses fraction of `ww` positions > 17.5% threshold to detect ternary verse, and 4th-syllable strong/weak frequency to detect head direction.
- **`text.line_scheme`**: repeating beat-length template (e.g. `(5,)` for invariable pentameter, `(4,3)` for ballad meter). `analysis/line_scheme.py:detect_line_scheme()` searches divisor-length cycles, prefers shorter (less overfit) templates.
- **`text.syllable_scheme`**: same as above but counted in canonical (form_idx==0) syllables.
- **`text.rhyme_ids`**: per-line integer IDs grouping rhyming lines. Algorithm: candidate pairs within ±4-line window gated by the 2-D band classifier (`rime_type` in perfect/slant), ranked perfect-first then by nucleus distance; perfect pairs union even without mutuality, slant pairs require mutual nearest neighbors. 0 = no rhyme partner. On the sonnets this lifted scheme detection from 137/154 to 149/154 Shakespearean (fixing sonnet 106's slant-rhyme quatrain). Legacy 1-D scalar mode via `compute_rhyme_ids(text, max_dist=0.35)` (the old Walker F1-optimal threshold). See `scripts/rime_eval.py` to regenerate calibrations.
- **`text.rhyme_scheme`**: best-fit named scheme via Jaccard similarity on rhyme-edge sets. Schemes catalog at `analysis/data/rhyme_schemes.txt` (39 named forms: Sonnet variants, Couplet, Sestet, Triplet, etc.). Returns `{name, form, accuracy, candidates}`.
- **`text.is_sonnet` / `text.is_shakespearean_sonnet`**: 14 lines + median 9–11 sylls + scheme matches a sonnet variant.
- **`text.summary()`**: tabulated per-line annotations + estimated schema block (uses `tabulate`).

### Foot delineation (`analysis/feet.py`)

Theory + write-up: [`docs/methods/foot-parsing.md`](docs/methods/foot-parsing.md). A first-class **`Foot`/`FootList`** view layer over a parse's scansion, cut by a line-local DP (variable foot size + headedness, one head per interior foot, extrametrical anacrusis/feminine edges — 97.5% exact vs a hand-tagged gold). Surfaced on `Parse`: `metrical_feet` (cached `FootList`), `feet`/`feet_str`/`footed_scansion` (`'wws|wws|wws|w'`), `foot_counts`/`nary_feet`/`foot_type`/`is_rising`/`head`; `Line.metrical_parse` = `best_parse`. Deliberately **line-scoped** (no poem context; the `parse_feet(head=…)`/`foot_parse(pref_size=…)` hooks stay dormant). Decoupled from `best_parse`'s tie-break by design (that uses cheap scansion statistics, not the DP).

The `_syll_df`-backed canonical syllable count is essential for line/syllable scheme detection — `line.num_sylls` includes all pronunciation variants and inflates counts.

## Testing Notes

- 219 tests, all passing. Python 3.10 in `.venv`.
- Tests import everything via `from prosodic.imports import *` and call `disable_caching()` at the top (now a no-op).
- Common test fixture: Shakespeare sonnets via `sonnet` variable.
- Web tests use FastAPI TestClient (httpx-based). 12 tests covering meter defaults, parse, maxent, corpora, and static files. Selenium browser test skips gracefully if no driver.
- Client tests (`test_client.py`): 28 tests for remote API client. Uses FastAPI TestClient (no running server needed). Covers parsing, line-level detail, bounded/unbounded, MaxEnt, save/load roundtrips, and `Text()` factory dispatch.
- CI runs on Python 3.12.0 and requires espeak system package.

## Performance (Shakespeare sonnets, 2155 lines, Apple MPS GPU)

Run `python -m prosodic.profiling` to regenerate.

| Step | v1 (1.3.8) | v2 | v3 | v3 vs v2 |
|---|---|---|---|---|
| Init (tokenize + pronunciations + entities) | 1.4s | 5.29s | 2.2s | 2x |
| Parse (CPU) | 36.6s | 72.97s | 6.4s | 11x |
| Parse (GPU) | 36.6s | 72.97s | 4.1s | 18x |
| **End-to-end (CPU)** | **38.0s** | **78.3s** | **8.6s** | **9x** |
| **End-to-end (GPU)** | **38.0s** | **78.3s** | **6.3s** | **12x** |
| **DF-only (no entities, GPU)** | **38.0s** | **78.3s** | **5.1s** | **15x** |
| Syntax (dep parse) | — | 160.2s | 3.3s | 49x |

v1 measured 2026-07-10 via the `cmp_prosodics` harness (same machine, whole-sonnets
Text + parse, dict warm; `v1_3_8/profile_v1_sonnets.py` there). Note the shape of the
history: **v1's pruned branch-and-bound was ~2× faster than the 2024 v2 rewrite** —
the oft-quoted "78s legacy" figure is v2, not v1. v3 is ~9× v1, ~18× v2 on parse (GPU).

An earlier revision of this table showed Parse at 1.9s — that predates the v1-semantics
restoration (PRs #164–169): variant pooling × verse elision means ~89% of sonnet lines
now carry multiple pronunciation combos (mean 9/line), each evaluated and cross-bounded,
plus mixed-N dominated-length retention. That ~3× is purchased semantics (parity ρ
0.9475 vs the 2020 v1 data), not regression. Two vectorization passes clawed most of it
back, each verified byte-identical by a full before/after dump diff: (1) the pooling
overlay (`build_for_N`) — same-N combos share one scansion enumeration, so
dedup-by-meter-string ≡ per-index argmin (was 4.0s of Python loops, now 1.8s); (2) the
elite bounding pre-screen runs on the torch device when available
(`_elite_screen_torch`, 15x over numpy on MPS — the pooled combos push its input to
~15K rows/call; any sound screen yields the same final mask by transitivity of
dominance). GPU beats CPU again at this workload — the old "CPU edges out GPU" note
flipped back when pooling re-inflated the kernels' inputs.

**TTS pronunciation cache**: espeak results cached to `~/prosodic_data/data/{lang}_cache.tsv`. First run phonemizes ~671 words via espeak; subsequent runs load from cache. Cold init 1.9s → warm 0.56s.

## Performance Improvement Plan

### Done
- ✅ Lazy TextModel construction (entities deferred)
- ✅ gruut_ipa cache (`_parse_ipa_cached`)
- ✅ Avoid pandas iterrows in tokenization
- ✅ Vectorized bounding (GPU-batched, perfect-parse shortcut)
- ✅ DataFrame-first architecture (syll_df)
- ✅ Batched constraint evaluation across lines
- ✅ Removed old branch-and-bound parser, hashstash parse caching
- ✅ Removed OBJECTS registry, register_objects, find, match, equals
- ✅ Dead code removal (old MaxEnt.py, lexconvert.py, SimpleCache, branch/copy)
- ✅ Save/load to parquet (text.save(), TextModel.load())
- ✅ Web app rewrite: Flask+HTMX → FastAPI+SvelteKit (PWA, 3 tabs, streaming, sortable, paginated, localStorage, 180KB vs 13MB)
- ✅ MaxEnt weight learner (L-BFGS, vectorized, zone splitting, <1s training on 2K lines)
- ✅ Self-describing constraints (vectorized lambda on decorator, auto-dispatch)
- ✅ New constraints: clash, lapse, w_heavy, s_light, s_func, word_foot
- ✅ Phrasal stress from dependency parsing (spaCy, Liberman & Prince 1977)
- ✅ TTS pronunciation cache to disk (`~/prosodic_data/data/{lang}_cache.tsv`)
- ✅ Profiling module (`python -m prosodic.profiling`)
- ✅ Web app: component-based tabs (state/scroll preserved across switches), Line View tab, Settings tab
- ✅ Remote client API (`prosodic.client`): same interface as local, delegates to HTTP API, save/load support
- ✅ Desktop app scaffold (Tauri v2 + PyInstaller sidecar; removed 2026-07-05, restore via `desktop-scaffold` tag)
- ✅ Server deployment config (nginx + certbot + systemd + setup script for prosodic.app, co-hosts with lltk.net)
- ✅ prosodic.app deployed LIVE (2026-04-14, app3 branch, 65.109.29.122)
- ✅ Prose handling: auto-fallback to linepart parsing for long lines, syntax-based sub-splitting
- ✅ Dash normalization (`--` → em-dash in tokenizer)
- ✅ MAX_SYLL_IN_PARSE_UNIT bumped 14 → 18 (50ms GPU, 2.1s CPU)
- ✅ Data export (CSV/TSV/JSON per-line with best + unbounded averages)
- ✅ URL routing with back/forward, lucide icons, two-column desktop layout
- ✅ `--dev` flag for prosodic web (auto-reload backend + frontend)
- ✅ Punctuation preserved in parse HTML via render_parse_html(parse, line)
- ✅ Poesy port: meter type / line scheme / rhyme scheme / sonnet detection / summary table now in `prosodic/analysis/` (was a separate `poesy` package; poesy ≥0.4 is now a thin shim over prosodic ≥3.5)
- ✅ Rhyme calibrated against Walker (1775) rhyming dictionary (`data/walker5.csv`, `scripts/rime_eval.py`): 2-D (nucleus, coda) band classification (`rime_type`), band-gated `compute_rhyme_ids` (sonnets 137→149/154), sonnet-scheme true-negative validation.
- ✅ Auto-deploy on push (`stable-release.yml`: tests → SSH deploy → health check; self-healing `git reset --hard` + `npm ci`)
- ✅ Merge app3 → master (master is the deployed branch)
- ✅ Windows in CI test matrix (espeak-ng MSI; validates the #62/#74 fixes on every push)
- ✅ G2P-aligned orthographic syllable labels (`langs/g2p_align.py`, fixes #47)
- ✅ cadence fork superseded and archived (prose rhythm now via `syntax=True`; its unique capabilities catalogued in ROADMAP.md)
- ✅ Web app: combined Liberman & Prince-style grid+tree figure in Line View (`MetricalGridTree.svelte`); `grid_plot()` redesigned with colored boxes instead of star marks

### Remaining

See [ROADMAP.md](ROADMAP.md) — the single source for planned work (parser
optimizations, grid stress view, cadence ports, languages, infrastructure).
