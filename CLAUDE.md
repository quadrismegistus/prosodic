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

**`_syll_df` columns:** `word_num`, `line_num`, `para_num`, `sent_num`, `sentpart_num`, `linepart_num`, `word_txt`, `is_punc`, `form_idx`, `num_forms`, `syll_idx`, `syll_ipa`, `syll_text`, `is_stressed`, `is_heavy`, `is_strong`, `is_weak`, `is_functionword`

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
- **Constraints** (`constraints.py`): Functions like `w_stress`, `s_unstress`, `unres_within`, `unres_across`, `w_peak`, `foot_size` that evaluate violations.
- **Parse** (`parses.py`): A single candidate parse. Ranked by weighted violation score; `best_parse` = lowest score among unbounded.
- **LazyParseList** (`vectorized.py`): Stores numpy violation data. Parse objects built only on access. `.unbounded` returns sorted by score. `.best_parse` uses `argmin` — no sorting needed.

**Parsing flow:** `TextModel.parse()` → `parse_batch_from_df(syll_df, meter)` → groups by line, extracts features from numpy arrays → `evaluate_constraints_batch()` broadcasts features against scansion matrices → `compute_bounding_batch()` on GPU → results stored by line_num, attached to Entity lines lazily.

**Bounding optimization:** Lines with a perfect parse (0 violations) skip the O(S²) pairwise comparison entirely — the perfect scansion bounds everything else.

### Syllable DataFrame (`texts/syll_df.py`)

- `build_syll_df(token_dicts, lang)`: Builds the flat DataFrame from tokenized word dicts + `get_word()` output. Computes all syllable features (stress, weight, strong/weak, functionword) without constructing Entity objects.
- `SyllData`: Lightweight `__slots__` class that duck-types the Syllable interface for Parse/ParseSlot.
- `extract_features_from_df()`: Reads feature arrays from a DataFrame slice for one line.

### Language Support (`langs/`)

- **English** (`langs/english/`): Uses CMU pronunciation dictionary (2700/3206 Shakespeare words) + espeak TTS fallback (506 words, ~1.4s cold). `get_word()` cached via `@functools.cache`.
- **Finnish** (`langs/finnish/`): Custom stress, weight, and sonority rules.
- Language detection via `langdetect`. Default language: `"en"`.

### Centralized Imports (`imports.py`)

All global constants, paths, and shared imports live in `imports.py`. Modules import from it via `from prosodic.imports import *`. Key constants: `DEFAULT_LANG`, `DEFAULT_METER`, `METER_MAX_S`, `METER_MAX_W`, `MAX_SYLL_IN_PARSE_UNIT`.

### Memory Management

- `OBJECTS` in `ents.py` is a `weakref.WeakValueDictionary` — entities are garbage-collected when no longer referenced.
- `DEFAULT_USE_REGISTRY` (in `imports.py`) gates all `register_objects()` calls. Set to `False` for batch workloads.
- `TextModel.cleanup()` explicitly clears parse results and cached properties.
- `Entity.clear_cached_properties()` removes all `@cached_property` values from an entity's `__dict__`.
- TextModel children are lazy — if you only need parse results (no Entity access), ~280K objects are never created.

### Web App (`web/`)

Flask + flask-socketio (WebSocket). Real-time parsing with progress updates.

## Testing Notes

- Tests import everything via `from prosodic.imports import *` and call `disable_caching()` at the top (now a no-op).
- Common test fixture: Shakespeare sonnets via `sonnet` variable.
- Web tests use Selenium with ChromeDriver; env var `NAPTIME=30` controls WebSocket timeouts.
- CI runs on Python 3.12.0 and requires espeak system package.
- One pre-existing test failure: `test_wordform_rime_distance` (fixture mismatch).

## Performance (Shakespeare, 2155 lines, MPS GPU)

Cold start end-to-end: **~7.4s**
- Import: 1.1s (includes torch init)
- Init (tokenize + get_word + syll_df): 1.9s
- Parse (constraint eval + GPU bounding): 1.9s
- Lines (lazy entity build + attach): 2.5s

Without entity access (batch/corpus use): **~4.2s**

## Performance Improvement Plan

### Done
- ✅ Lazy TextModel construction (entities deferred)
- ✅ gruut_ipa cache (`_parse_ipa_cached`)
- ✅ Avoid pandas iterrows in tokenization
- ✅ Vectorized bounding (GPU-batched, perfect-parse shortcut)
- ✅ DataFrame-first architecture (syll_df)
- ✅ Batched constraint evaluation across lines
- ✅ Removed old branch-and-bound parser, hashstash parse caching

### Remaining
- **`__slots__` on high-volume classes** (SyllData already uses it; ParseSlot, ParsePosition could benefit)
- **Scansion prefiltering** (skip scansions where strong positions wildly mismatch stressed syllables)
- **Lazy phoneme construction** (Syllable creates Phoneme objects eagerly; could defer to IPA-on-demand)
