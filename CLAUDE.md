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

### Entity Hierarchy

All linguistic objects inherit from `Entity` (in `ents.py`), which extends `UserList`. Entities form a parent-child tree:

```
TextModel → Stanza → Line → WordToken → WordType → WordForm → Syllable → Phoneme
```

- **TextModel** (`texts/texts.py`): Root container. Created via `TextModel("some text")`. Key properties: `.stanzas`, `.lines`, `.wordtokens`, `.df` (DataFrame export).
- **Line** (`texts/lines.py`): The primary unit for metrical parsing. Call `.parse()` to get parses, `.best_parse` for optimal result.
- **WordToken** (`words/wordtoken.py`): A token in text; wraps a **WordType** (canonical form) which contains **WordForm** variants (pronunciations).
- **WordForm** (`words/wordform.py`): A specific pronunciation with IPA, stress, and weight info. Contains **Syllable** → **Phoneme** children.

### Metrical Parsing (`parsing/`)

- **Meter** (`meter.py`): Configuration object with constraints, max strong/weak positions (`max_s`, `max_w`).
- **Constraints** (`constraints.py`): Functions like `w_stress`, `s_unstress`, `unres_within`, `unres_across`, `w_peak`, `foot_size` that evaluate violations.
- **Parse** (`parses.py`): A single candidate parse. Ranked by violation count; `best_parse` = fewest violations.
- **ParseList** (`parselists.py`): Collection of all candidate parses for a line.

Parsing flow: `TextModel.parse()` → `Line.parse()` → generates candidate meter patterns → evaluates constraints → ranks by violations.

### Language Support (`langs/`)

- **English** (`langs/english/`): Uses CMU pronunciation dictionary + espeak TTS fallback.
- **Finnish** (`langs/finnish/`): Custom stress, weight, and sonority rules.
- Language detection via `langdetect`. Default language: `"en"`.

### Centralized Imports (`imports.py`)

All global constants, paths, and shared imports live in `imports.py`. Modules import from it via `from prosodic.imports import *`. Key constants: `DEFAULT_LANG`, `DEFAULT_METER`, `METER_MAX_S`, `METER_MAX_W`, `MAX_SYLL_IN_PARSE_UNIT`.

### Vectorized Parser (`parsing/vectorized.py`)

Optional numpy-based parser engine that evaluates all metrical constraints in batch. Enabled via `Meter(vectorized=True, parse_unit="line")`. About 3.6x faster than the default branch-and-bound parser on large texts. Uses `extract_features()` to convert syllable properties to numpy arrays, `encode_scansions()` to build scansion matrices, and `evaluate_constraints()` for batch constraint evaluation. Only constructs Parse objects for unbounded (non-dominated) scansions.

### Caching

Uses `HashStash` with pairtree engine, stored at `~/prosodic_data/data/cache/`. Caching is off by default (`USE_CACHE = False`). `enable_caching()` activates disk caching of parse results via `stash.map()`. Helps for small texts (<25 lines, ~6x speedup on warm cache), but deserialization overhead exceeds parsing cost for large texts, so `CACHE_LINE_LIMIT` (default 25) disables it above that threshold. Tests call `disable_caching()` at module level.

### Memory Management

- `OBJECTS` in `ents.py` is a `weakref.WeakValueDictionary` — entities are garbage-collected when no longer referenced.
- `DEFAULT_USE_REGISTRY` (in `imports.py`) gates all `register_objects()` calls. Set to `False` for batch workloads.
- `TextModel.cleanup()` explicitly clears parse results and cached properties.
- `Entity.clear_cached_properties()` removes all `@cached_property` values from an entity's `__dict__`.

### Web App (`web/`)

Flask + flask-socketio (WebSocket). Real-time parsing with progress updates.

## Testing Notes

- Tests import everything via `from prosodic.imports import *` and call `disable_caching()` at the top.
- Common test fixture: Shakespeare sonnets via `sonnet` variable.
- Web tests use Selenium with ChromeDriver; env var `NAPTIME=30` controls WebSocket timeouts.
- CI runs on Python 3.12.0 and requires espeak system package.
- Two pre-existing test failures: `test_wordform_rime_distance` (fixture mismatch) and `test_exhaustive` (hashstash cache error).

## Performance Improvement Plan

Prioritized list of future optimizations, roughly in order of impact vs effort:

### 1. Lazy TextModel Construction
**Impact: ~2x on TextModel build (6s → ~2s).** Currently TextModel eagerly constructs 160K Entity objects (WordToken → WordType → WordForm → Syllable → Phoneme) for every word. Most of this is unnecessary when the goal is just parsing. Store the tokenized DataFrame and build entity objects on demand when `.lines`, `.stanzas`, etc. are accessed. The vectorized parser could work directly from the DataFrame without materializing any Entity objects.

### 2. Cache `gruut_ipa.Phoneme.from_string()` Results
**Impact: saves ~1.8s on TextModel build.** The IPA phoneme parser (`gruut_ipa`) is called 72K+ times during Shakespeare construction. Results are deterministic — cache them with a simple dict keyed on IPA string.

### 3. Avoid pandas DataFrame in Tokenization
**Impact: saves ~0.6s on TextModel build.** `tokenize_sentwords_df()` returns a DataFrame, then `TextModel.__init__` iterates `df.iterrows()` (which creates a Series per row). A plain list of dicts would be faster.

### 4. Use `__slots__` on High-Volume Classes
**Impact: reduces memory and speeds up attribute access.** ParseSlot, ParsePosition, Syllable, and Phoneme are created in huge numbers. Adding `__slots__` eliminates per-instance `__dict__` overhead (~100 bytes per object). Requires careful migration since Entity uses `__dict__` for `cached_property`.

### 5. Vectorized Bounding
**Impact: saves ~2.5s on parsing.** `compute_bounding()` is O(n^2) pairwise comparison using Python loops over numpy arrays. Could be fully vectorized: compute `(S, S)` pairwise domination matrix in one broadcast operation.

### 6. Pre-filter Scansions by Syllable Count Feasibility
**Impact: reduces scansion count by ~30%.** Many generated scansions are immediately bounded. A fast pre-filter (e.g., skip scansions where strong positions outnumber stressed syllables by 2x) would reduce the constraint evaluation matrix size.
