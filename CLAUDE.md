# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Prosodic is a Python library and web app for metrical-phonological analysis of poetry. It parses text into a linguistic hierarchy (text → stanza → line → word → syllable → phoneme) and performs constraint-satisfaction metrical parsing to identify stress patterns (iambic, trochaic, anapestic, dactylic).

## Commands

```bash
# Install (espeak required: brew install espeak on Mac, apt-get install espeak on Linux)
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
```

## Architecture

### DataFrame-First Design (v3)

TextModel stores a flat syllable-level DataFrame (`_syll_df`) as the source of truth. Entity objects (WordToken, Syllable, etc.) are constructed lazily only when accessed. The vectorized parser works entirely from the DataFrame without building Entity objects.

**Key flow:**
1. `TextModel.__init__` tokenizes text → calls `get_word()` per unique word → builds `_syll_df`
2. `text.parse()` → `parse_batch_from_df()` reads features from `_syll_df`, evaluates constraints in numpy, bounds on GPU
3. `text.lines` (first access) triggers lazy Entity construction + attaches parse results

**`_syll_df` columns:** `word_num`, `line_num`, `para_num`, `sent_num`, `sentpart_num`, `linepart_num`, `word_txt`, `is_punc`, `form_idx`, `num_forms`, `syll_idx`, `syll_ipa`, `syll_text`, `is_stressed`, `is_heavy`, `is_strong`, `is_weak`, `is_functionword`, `phrasal_stress` (optional, only with `syntax=True`)

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

The parser is always vectorized and exhaustive — it evaluates ALL possible scansions via numpy and uses harmonic bounding to identify optimal parses.

- **Meter** (`meter.py`): Configuration object with constraints, max strong/weak positions (`max_s`, `max_w`). The `exhaustive` and `vectorized` params are accepted but ignored (always both).
- **Constraints** (`constraints.py`): Each constraint has a `@constraint` decorator with `desc`, `scope`, and optional `vectorized` lambda. The vectorized lambda receives broadcast feature arrays and returns `(L, S, N)` int8 violations — this is what runs during parsing. The entity-based function body is a reference implementation used only by manually-constructed Parse objects. Default constraints: `w_stress`, `s_unstress`, `unres_within`, `unres_across`, `w_peak`, `foot_size`. Additional: `s_trough`, `clash`, `lapse`, `w_heavy`, `s_light`, `s_func`, `word_foot`. Phrasal stress constraints (require `syntax=True`): `w_prom`, `s_demoted`. Adding a new constraint = one decorated function in `constraints.py` with a `vectorized` lambda; no changes to `vectorized.py` needed.
- **Parse** (`parses.py`): A single candidate parse. Ranked by weighted violation score; `best_parse` = lowest score among unbounded.
- **LazyParseList** (`vectorized.py`): Stores numpy violation data. Parse objects built only on access. `.unbounded` returns sorted by score. `.best_parse` uses `argmin` — no sorting needed.

**Parsing flow:** `TextModel.parse()` → `parse_batch_from_df(syll_df, meter)` → groups by line, extracts features from numpy arrays → `evaluate_constraints_batch()` broadcasts features against scansion matrices → `compute_bounding_batch()` on GPU → results stored by line_num, attached to Entity lines lazily.

**Bounding optimization:** Lines with a perfect parse (0 violations) skip the O(S²) pairwise comparison entirely — the perfect scansion bounds everything else.

### MaxEnt Weight Learning (`parsing/maxent.py`)

`MaxEntTrainer` learns constraint weights from annotated data or a target scansion using Maximum Entropy (log-linear) optimization. Based on Goldwater & Johnson (2003) / Hayes MaxEnt OT.

- **`MaxEntTrainer(meter, regularization=100.0, zones=None)`**: zones splits the violation matrix by syllable position before training. `"initial"` = first 2 syllables vs rest. `3` = three equal zones. `"foot"` = per foot.
- **`load_annotations(data)`**: accepts `[(text, scansion, frequency), ...]` or DataFrame with those columns. Parses all lines via `parse_batch_from_df`, matches annotations to candidate scansions.
- **`load_text(text, "wswswswsws")`**: assigns a uniform target scansion to all lines — no annotation file needed.
- **`train()`**: L-BFGS-B optimization (scipy). Converges in <1s on 2000+ lines. Vectorized gradient via `einsum` over groups of same-length lines.
- **`learned_weights()`** / **`apply_to_meter()`**: extract or apply learned weights.

**Key design**: operates on the `(S, N, C)` violation matrices already produced by the parser. Zone splitting is post-hoc feature engineering — partitions the N (syllable) axis into zones before summing, creating `C * n_zones` features. No parser changes needed.

**`meter.fit()` pipeline**: `Meter.fit(text, "wswswswsws", zones=3)` trains MaxEnt weights on a corpus and stores `meter.zone_weights` (dict of zone-expanded constraint names → weights) and `meter.zones` on the meter. `LazyParseList` scoring checks for these and uses zone-aware scoring when available — splits `(S, N, C)` violations by syllable position before weighting. This means learned positional sensitivity transfers to parsing unseen text. Also `meter.fit_annotations(data)` for annotated data (list of tuples or DataFrame).

**Shared utilities**: `zone_split(viols_3d, zones)`, `zone_boundaries(zones, N)`, `make_zone_names(base_names, nsylls, zones)` — used by both MaxEntTrainer and LazyParseList.

**Constraint entailment**: w_peak entails w_stress (100% co-occurrence). In MaxEnt/HG, overlapping constraints stack: w_peak violation costs w_peak + w_stress. This is how the model makes w_peak effectively inviolable (Kiparsky) without infinite weight.

### Phrasal Stress (`texts/phrasal_stress.py`)

Optional dependency-parse-based phrasal prominence (Liberman & Prince 1977). Uses spaCy dep-only parsing — no constituency trees needed.

- **`TextModel("...", syntax=True)`**: enables phrasal stress computation. Adds `phrasal_stress` column to `_syll_df`.
- **Algorithm**: vectorized depth in dependency tree + NSR/CSR adjustments. No tree objects — just numpy arrays over head/deprel/POS. Converges in O(max_depth) iterations.
- **Values**: 0 = sentence root (most prominent), -1 = direct dependent, -2 to -6 = deeper embedding. `<NA>` for punctuation.
- **Constraints**: `w_prom` (prominent word on weak position, `phrasal_stress >= -1`), `s_demoted` (deeply embedded word on strong position, `phrasal_stress <= -2`). Both are inert when `syntax=False` (check `has_phrasal` flag).
- **Performance**: ~1s overhead for 2155 lines (spaCy dep parse). Model loads once, cached.
- **Config**: `DEFAULT_SYNTAX = False`, `DEFAULT_SYNTAX_MODEL = "en_core_web_sm"` in `imports.py`. spaCy is an optional dependency (`pip install prosodic[syntax]`).
- **MaxEnt integration**: `meter.fit_annotations(data, text=text_with_syntax)` passes a pre-built syntax-enabled TextModel through to the trainer. Without this, the trainer creates its own TextModel without syntax.
- **Empirical note**: on Shakespeare sonnets with `wswswswsws` target, phrasal constraints are redundant with lexical stress features (69.2% accuracy with or without). They add no signal for fixed-template scansion but may help for prose rhythm or naturalness ranking.

### Syllable DataFrame (`texts/syll_df.py`)

- `build_syll_df(token_dicts, lang)`: Builds the flat DataFrame from tokenized word dicts + `get_word()` output. Computes all syllable features (stress, weight, strong/weak, functionword) without constructing Entity objects.
- `SyllData`: Lightweight `__slots__` class that duck-types the Syllable interface for Parse/ParseSlot.
- `_phone_is_vowel()`, `_syll_is_heavy_from_ipa()`: Compute phonological features from IPA without Entity objects.

### Language Support (`langs/`)

- **English** (`langs/english/`): Uses CMU pronunciation dictionary (2700/3206 Shakespeare words) + espeak TTS fallback (506 words, ~1.4s cold). `get_word()` cached via `@functools.cache`.
- **Finnish** (`langs/finnish/`): Custom stress, weight, and sonority rules.
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
- Line View: text input for manual line entry, shows all scansions sorted by score with violation badges, bounded parses grayed out
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

### Desktop App (`desktop/`)

Tauri v2 desktop app scaffold. Bundles the Python backend via PyInstaller as a sidecar, including espeak. No Python installation required for end users.

- `build.sh`: Builds frontend → PyInstaller sidecar → Tauri `.app` bundle.
- `src-tauri/src/main.rs`: Launches sidecar on random port, passes port to webview via `window.__PROSODIC_PORT__`.
- `scripts/prosodic_server.py`: Server entry point for PyInstaller with port negotiation and bundled espeak path setup.
- `scripts/prosodic_server.spec`: PyInstaller spec bundling Python + prosodic + espeak (~300MB).
- GPU (torch) and spaCy excluded from bundle to keep size manageable.

## Two Parse Paths

There are two ways parsing happens, and it matters which one you're in:

1. **DF path** (`parse_batch_from_df`): Used by `text.parse()`. Works entirely from `_syll_df`. Parse objects contain `SyllData` (lightweight, no parent chain). `parse.wordtokens` is None. Good for batch processing, `text.parsed_df`, `text.save()`. No entities built.

2. **Entity path** (`parse_batch`): Used by the web app and when you call `parse_batch(text.lines, meter)` directly. Parse objects contain real `Syllable` entities with parent chains (wordform → wordtype → wordtoken). Needed for HTML rendering (word boundaries, `line.to_html()`).

**Gotchas:**
- DF-path parses have `slot.unit.parent = None` — can't traverse to wordtoken/wordform.
- `text.parse()` stores results in `text._line_parse_results[meter_key]`. When `text.lines` is first accessed, results are attached to line entities via line_num matching.
- `LazyParseList` defers Parse object construction. `best_parse` builds exactly 1 Parse via `argmin`. Iterating builds all.
- `text.parsed_df` is a cached property (default meter). Use `text.get_parsed_df(**kwargs)` for custom meters.

### Rhyme Detection (`words/wordform.py`, `words/phonemes.py`)

- `WordForm.rime_distance(other, max_dist)` computes distance between word rimes.
- Uses **feature-weighted edit distance** on IPA segments via panphon: aligns phonemes via DP where substitution cost = normalized feature distance. Returns 0-1 (0 = perfect rhyme).
- `max_dist=0` (default, `RHYME_MAX_DIST`): binary exact match. `max_dist=None`: no limit, returns gradient distance.
- `PhonemeList.feature_edit_distance(other)`: the core DP alignment. `PhonemeList.feature_distance(other)`: legacy euclidean on averaged features (still available but not used by rime_distance).
- `Line.rime_distance(line2)`: delegates to final wordform's rime_distance.
- `Text.get_rhyming_lines()`, `Text.is_rhyming`, `Text.num_rhyming_lines`: aggregate rhyme detection.

## Testing Notes

- 219 tests, all passing. Python 3.10 in `.venv`.
- Tests import everything via `from prosodic.imports import *` and call `disable_caching()` at the top (now a no-op).
- Common test fixture: Shakespeare sonnets via `sonnet` variable.
- Web tests use FastAPI TestClient (httpx-based). 12 tests covering meter defaults, parse, maxent, corpora, and static files. Selenium browser test skips gracefully if no driver.
- Client tests (`test_client.py`): 28 tests for remote API client. Uses FastAPI TestClient (no running server needed). Covers parsing, line-level detail, bounded/unbounded, MaxEnt, save/load roundtrips, and `Text()` factory dispatch.
- CI runs on Python 3.12.0 and requires espeak system package.

## Performance (Shakespeare sonnets, 2155 lines, Apple MPS GPU)

Run `python -m prosodic.profiling` to regenerate.

| Step | v2 | v3 | Speedup |
|---|---|---|---|
| Init (tokenize + pronunciations + entities) | 5.29s | 1.80s | 3x |
| Parse (CPU) | 72.97s | 5.0s | 15x |
| Parse (GPU) | 72.97s | 1.3s | 57x |
| **End-to-end (CPU)** | **78.3s** | **6.8s** | **12x** |
| **End-to-end (GPU)** | **78.3s** | **3.1s** | **26x** |
| **DF-only (no entities, GPU)** | **78.3s** | **1.8s** | **42x** |
| Syntax (dep parse) | 160.2s | 2.7s | 58x |

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
- ✅ Desktop app scaffold (Tauri v2 + PyInstaller sidecar + bundled espeak)
- ✅ Server deployment config (nginx + certbot + systemd + setup script for prosodic.app, co-hosts with lltk.net)
- ✅ prosodic.app deployed LIVE (2026-04-14, app3 branch, 65.109.29.122)
- ✅ Prose handling: auto-fallback to linepart parsing for long lines, syntax-based sub-splitting
- ✅ Dash normalization (`--` → em-dash in tokenizer)
- ✅ MAX_SYLL_IN_PARSE_UNIT bumped 14 → 18 (50ms GPU, 2.1s CPU)
- ✅ Data export (CSV/TSV/JSON per-line with best + unbounded averages)
- ✅ URL routing with back/forward, lucide icons, two-column desktop layout
- ✅ `--dev` flag for prosodic web (auto-reload backend + frontend)
- ✅ Punctuation preserved in parse HTML via render_parse_html(parse, line)

### Remaining
- **Parse table design polish** (grid stress view — Hayes-style metrical grid over syllables)
- **Scansion prefiltering** (skip scansions where strong positions wildly mismatch stressed syllables)
- **Lazy phoneme construction** (Syllable creates Phoneme objects eagerly; could defer to IPA-on-demand)
- **Ternary meter identification** (MaxEnt meter.fit works for binary iambic/trochaic but ternary anapestic/dactylic needs ternary-aware constraints or dynamic template matching)
- **Vectorize unres_within/unres_across** (last two constraints still use per-line Python loops in evaluate_constraints_batch; could be lifted to numpy with word boundary masking)
- **Rhyme detection threshold tuning** (RHYME_MAX_DIST=0 default is binary; gradient rime_distance works but no calibrated threshold for "slant rhyme" vs "not rhyme")
- **Grid stress view** (Hayes-style metrical grid visualization for Line View tab — asterisks stacked over syllables by stress level)
- **Auto-deploy on push** (GitHub Actions SSH workflow: `git pull && pip install -e . && npm run build && systemctl restart prosodic`)
- **GPU/CPU dispatch optimization** (CPU wins for n<11 single-line, GPU wins for n≥11 or batched; auto-dispatch by total work per nsylls group)
- **Merge app3 → master** (app3 currently ahead; deployment is on app3 branch)
