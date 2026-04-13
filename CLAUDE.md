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

# Web app
prosodic web

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

All global constants, paths, and shared imports live in `imports.py`. Modules import from it via `from prosodic.imports import *`. Key constants: `DEFAULT_LANG`, `DEFAULT_METER`, `METER_MAX_S`, `METER_MAX_W`, `MAX_SYLL_IN_PARSE_UNIT`.

### Memory Management

- `DEFAULT_USE_REGISTRY` is `False` — the OBJECTS registry (WeakValueDictionary, register_objects, find, match) has been removed.
- `TextModel.cleanup()` explicitly clears parse results and cached properties.
- `Entity.clear_cached_properties()` removes all `@cached_property` values from an entity's `__dict__`.
- TextModel children are lazy — if you only need parse results (no Entity access), ~280K objects are never created.

### Web App (`web/`)

Flask + flask-socketio (WebSocket). Mobile-friendly single-page app.
- `app.py`: Server with `parse` websocket handler. Uses `parse_batch()` with Entity-backed Syllables for HTML rendering (word boundaries, violation tooltips).
- `templates/index.html`: Responsive layout (sidebar stacks on mobile). Collapsible "Configure Meter" panel. Best-only / All-unbounded toggle. Violation tooltips on tap/hover. Ambiguity column.
- Run with `prosodic web` or `python -c "from prosodic.web.app import main; main(port=5111, host='0.0.0.0')"`

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

- 189 tests, all passing. Python 3.10 in `.venv`.
- Tests import everything via `from prosodic.imports import *` and call `disable_caching()` at the top (now a no-op).
- Common test fixture: Shakespeare sonnets via `sonnet` variable.
- Web tests use Flask test client + socketio test client (no browser needed). Selenium browser test skips gracefully if no driver. `NAPTIME` env var controls WebSocket timeouts.
- CI runs on Python 3.12.0 and requires espeak system package.

## Performance (Shakespeare sonnets, 2155 lines, Apple MPS GPU)

Run `python -m prosodic.profiling` to regenerate.

| Step | v2 | v3 | Speedup |
|---|---|---|---|
| Init (tokenize + pronunciations + entities) | 5.29s | 1.76s | 3x |
| Parse (CPU) | 72.97s | 5.02s | 15x |
| Parse (GPU) | — | 1.28s | 57x |
| **End-to-end (CPU)** | **78.3s** | **6.8s** | **12x** |
| **End-to-end (GPU)** | **78.3s** | **3.0s** | **26x** |
| + syntax (spaCy dep parse) | — | +1.2s | — |

v3 without entity access (batch/DF use only): **1.8s** (init 0.56s + GPU parse 1.28s) = **43x faster**.

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
- ✅ Web app rewrite (mobile-friendly, tooltips, ambiguity)
- ✅ MaxEnt weight learner (L-BFGS, vectorized, zone splitting, <1s training on 2K lines)
- ✅ Self-describing constraints (vectorized lambda on decorator, auto-dispatch)
- ✅ New constraints: clash, lapse, w_heavy, s_light, s_func, word_foot
- ✅ Phrasal stress from dependency parsing (spaCy, Liberman & Prince 1977)
- ✅ TTS pronunciation cache to disk (`~/prosodic_data/data/{lang}_cache.tsv`)
- ✅ Profiling module (`python -m prosodic.profiling`)

### Remaining
- **Scansion prefiltering** (skip scansions where strong positions wildly mismatch stressed syllables)
- **Lazy phoneme construction** (Syllable creates Phoneme objects eagerly; could defer to IPA-on-demand)
- **Ternary meter identification** (MaxEnt meter.fit works for binary iambic/trochaic but ternary anapestic/dactylic needs ternary-aware constraints or dynamic template matching)
- **Vectorize unres_within/unres_across** (last two constraints still use per-line Python loops in evaluate_constraints_batch; could be lifted to numpy with word boundary masking)
- **Rhyme detection threshold tuning** (RHYME_MAX_DIST=0 default is binary; gradient rime_distance works but no calibrated threshold for "slant rhyme" vs "not rhyme")
