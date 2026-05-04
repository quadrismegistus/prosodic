"""Build a fresh README.ipynb for prosodic v3 with executed outputs.

The README notebook is canonical: this script is its source. Run it whenever
you change the API or the analysis module so the notebook (and the derived
README.md) stay in sync.

Usage::

    .venv/bin/python scripts/build_readme.py
    jupyter nbconvert --to markdown README.ipynb --output README

Outputs are written to ``<repo>/README.ipynb``. Requires ``nbformat`` and
``nbclient`` (``pip install jupyter`` covers both).
"""
from pathlib import Path

import nbformat
from nbclient import NotebookClient

REPO_ROOT = Path(__file__).resolve().parent.parent

nb = nbformat.v4.new_notebook()
cells = []

def md(text):
    cells.append(nbformat.v4.new_markdown_cell(text))

def code(src):
    cells.append(nbformat.v4.new_code_cell(src))


md("""# Prosodic 3

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/quadrismegistus/prosodic/blob/master/README.ipynb)
[![Demo](https://img.shields.io/badge/demo-prosodic.app-blue)](https://prosodic.app)
[![Code coverage](https://codecov.io/gh/quadrismegistus/prosodic/branch/master/graph/badge.svg)](https://codecov.io/gh/quadrismegistus/prosodic)

**Prosodic** is a Python library and web app for metrical-phonological analysis of poetry. It parses text into a linguistic hierarchy (text → stanza → line → word → syllable → phoneme), runs a constraint-satisfaction metrical parser, and identifies stress patterns (iambic, trochaic, anapestic, dactylic), foot/syllable schemes, and named rhyme schemes (sonnet variants, couplet, ballad, etc.).

Try the hosted version at **[prosodic.app](https://prosodic.app)** — paste a poem, see scansions, rhyme schemes, and form classification immediately. This notebook walks through the full Python API — from parsing a single line up to poem-level form classification. Click the **Open in Colab** badge above to run it in your browser.

Built by [Ryan Heuser](https://github.com/quadrismegistus), [Josh Falk](https://github.com/jsfalk), and [Arto Anttila](http://web.stanford.edu/~anttila/), with contributions from [Sam Bowman](https://github.com/sleepinyourhat).""")

md("""## Install

```bash
pip install prosodic
# or for development:
pip install git+https://github.com/quadrismegistus/prosodic
```

You'll also need [espeak](https://github.com/espeak-ng/espeak-ng) (free TTS) to phonemize words not in the CMU dictionary:

- **Mac**: `brew install espeak`
- **Linux**: `apt-get install espeak libespeak1 libespeak-dev`
- **Windows**: download from the [espeak-ng releases](https://github.com/espeak-ng/espeak-ng/releases/latest)""")

md("""### Setup (Colab only)

Skip this cell when running locally. It installs system + Python deps in a Colab runtime.""")

code("""# Auto-install dependencies if running in Google Colab.
# Locally this is a no-op.
import sys
IN_COLAB = "google.colab" in sys.modules
if IN_COLAB:
    import subprocess
    subprocess.run(
        ["apt-get", "-qq", "install", "-y",
         "espeak", "libespeak1", "libespeak-dev"],
        check=True,
    )
    subprocess.run(["pip", "install", "-q", "prosodic"], check=True)
    print("Colab setup complete.")
else:
    print("Local environment — skipping Colab setup.")""")

md("""## Quickstart

A complete tour of Prosodic in five lines.""")

code("""import prosodic

sonnet = prosodic.Text(\"\"\"When in the chronicle of wasted time
I see descriptions of the fairest wights,
And beauty making beautiful old rhyme
In praise of ladies dead and lovely knights,
Then, in the blazon of sweet beauty's best,
Of hand, of foot, of lip, of eye, of brow,
I see their antique pen would have express'd
Even such a beauty as you master now.
So all their praises are but prophecies
Of this our time, all you prefiguring;
And, for they look'd but with divining eyes,
They had not skill enough your worth to sing:
For we, which now behold these present days,
Had eyes to wonder, but lack tongues to praise.\"\"\")

sonnet.parse()
print(sonnet.summary())""")

md("""## Reading texts

You can build a `Text` from a string, a file, or just a single line.""")

code("""# from a string
short = prosodic.Text("A horse, a horse, my kingdom for a horse!")

# from a file
shaksonnets = prosodic.Text(fn='corpora/corppoetry_en/en.shakespeare.txt')

# a single line via .line1
line = prosodic.Text("Shall I compare thee to a summer's day?").line1

print(f"short: {len(short.lines)} line(s)")
print(f"sonnets: {len(shaksonnets.lines):,} lines, {len(shaksonnets.stanzas):,} stanzas")
print(f"single line: {line}")""")

md("""## The hierarchy: stanzas → lines → words → syllables → phonemes

Prosodic organizes text into a tree of linguistic entities. Children are constructed lazily on first access — the underlying source of truth is a per-syllable DataFrame.""")

code("""# tree access
print(f"sonnet has {len(sonnet.stanzas)} stanzas, {len(sonnet.lines)} lines")
print(f"line 1 has {len(sonnet.lines[0].wordtokens)} word tokens")
print(f"first word: {sonnet.lines[0].wordtokens[0]}")""")

code("""# attribute shortcut: text.line1 == text.lines[0]
sonnet.line1""")

code("""# wordform → syllable → phoneme
wordform = sonnet.line1.wordtokens[1].wordform
print(f"wordform: {wordform}")
for syll in wordform.syllables:
    print(f"  syllable: {syll}, IPA={syll.ipa!r}, stressed={syll.is_stressed}, heavy={syll.is_heavy}")
    for phon in syll.phonemes:
        print(f"    phon: {phon.txt!r}")""")

md("""## DataFrame view

The whole text is also accessible as a flat per-syllable DataFrame. This is the source of truth — entities are constructed from it on demand.""")

code("""# .df is the syllable-level DataFrame
sonnet.df.head(8)""")

code("""# columns
list(sonnet.df.columns)""")

md("""## Metrical parsing

`text.parse()` runs an exhaustive vectorized parser: it evaluates every possible scansion against a configurable set of metrical constraints (numpy on CPU, torch on GPU when available), then uses harmonic bounding to identify optimal parses. Constraints include `w_peak` (no peak in weak position), `w_stress` (no stress in weak), `s_unstress` (no unstress in strong), `unres_within`/`unres_across` (no unresolved disyllables), `foot_size`. See `prosodic/parsing/constraints.py` for the full list.""")

code("""# parse a single line
line = prosodic.Text("Shall I compare thee to a summer's day?").line1
line.parse()
print(line.best_parse)""")

code("""# inspect the parse
bp = line.best_parse
print(f"meter:     {bp.meter_str}    (- = weak, + = strong)")
print(f"stress:    {bp.stress_str}    (- = unstressed, + = stressed)")
print(f"score:     {bp.score}    (sum of weighted constraint violations)")
print(f"feet:      {bp.feet}")
print(f"foot_type: {bp.foot_type}    (per-parse classification)")
print(f"is_rising: {bp.is_rising}")""")

code("""# all unbounded parses for the line, sorted by score
for p in line.parses.unbounded:
    print(f"{p.meter_str}  score={p.score}")""")

code("""# parse the full sonnet
sonnet.parse()
for line in sonnet.lines[:6]:
    bp = line.best_parse
    print(f"L{line.num:2d}  {bp.meter_str}  score={bp.score:.1f}  ambig={len(line.parses.unbounded)}")""")

md("""## The parsed DataFrame

Per-syllable parse results across the whole text — useful for analysis, plotting, or export.""")

code("""sonnet.parsed_df.head(10)""")

code("""# every column you might want for analysis
list(sonnet.parsed_df.columns)""")

md("""## Custom meters

The default `Meter` allows up to 2-syllable strong/weak positions. You can change constraints, weights, position widths, or unit of parsing.""")

code("""# stricter binary meter
strict = prosodic.Meter(
    constraints=['w_peak', 'w_stress', 's_unstress', 'foot_size'],
    max_s=1, max_w=1,
)
print(strict)""")

code("""# parse with a custom meter
sonnet.parse(meter=strict)
print(sonnet.line1.best_parse)""")

md("""## Poem-level analysis

Prosodic 3 includes `prosodic/analysis/` (a port of the standalone [poesy](https://github.com/quadrismegistus/poesy) package) for higher-order summary statistics over a parsed text.""")

code("""# meter classification (iambic / trochaic / anapestic / dactylic)
sonnet.meter_type""")

code("""# repeating beat-length template (e.g. invariable pentameter, ballad meter)
print('feet  scheme:', sonnet.line_scheme)
print('syll  scheme:', sonnet.syllable_scheme)""")

md("""### Rhyme detection

Rhyme is computed via feature-weighted edit distance over IPA segments (panphon). 0 = perfect rhyme; higher = slant rhyme.""")

code("""# pairwise rime distance
sonnet.line1.rime_distance(sonnet.lines[2])  # 'time' vs 'rhyme'""")

code("""# every rhyming line in the text, with its closest partner
for line, (dist, partner) in list(sonnet.get_rhyming_lines().items())[:6]:
    print(f"L{line.num:2d} ↔ L{partner.num:2d}  dist={dist:.2f}  '{line.txt.strip()[:35]}' / '{partner.txt.strip()[:35]}'")""")

code("""# per-line rhyme group IDs (0 = no rhyme partner)
print('IDs:    ', sonnet.rhyme_ids)
from prosodic.analysis import nums_to_scheme
print('letters:', ''.join(nums_to_scheme(sonnet.rhyme_ids)))""")

md("""### Named rhyme scheme matching

Match observed rhyme groups against a 39-form catalog (Sonnet variants, Couplet, Sestet, Triplet, Rhyme Royal, Spenserian, etc.) by Jaccard similarity over rhyme-edge sets.""")

code("""rs = sonnet.rhyme_scheme
print(f"name:     {rs['name']}")
print(f"form:     {rs['form']}")
print(f"accuracy: {rs['accuracy']:.2f}")
print()
print("top candidates:")
for name, form, score in rs['candidates'][:5]:
    print(f"  {score:.2f}  {name:30s} {form}")""")

code("""# form predicates
print('is_sonnet:               ', sonnet.is_sonnet)
print('is_shakespearean_sonnet: ', sonnet.is_shakespearean_sonnet)""")

md("""### Tabular summary

`text.summary()` rolls everything together: per-line parse + rhyme letter + foot/syllable count + ambiguity, plus an estimated-schema block.""")

code("""print(sonnet.summary())""")

md("""## MaxEnt weight learning

`Meter.fit()` learns constraint weights from a target scansion (or annotated data) using L-BFGS-B Maximum Entropy optimization (Goldwater & Johnson 2003 / Hayes MaxEnt OT). The learned weights can be split by syllable position (`zones`) so positional sensitivity transfers to parsing.""")

code("""# Train weights to match an iambic pentameter target across all sonnet lines
import warnings
warnings.filterwarnings('ignore')

meter = prosodic.Meter()
meter.fit(sonnet, 'wswswswsws', zones=3)

print('top learned weights (zone × constraint):')
for name, w in sorted(meter.zone_weights.items(), key=lambda x: -abs(x[1]))[:8]:
    print(f"  {w:+.3f}  {name}")""")

md("""## Phrasal stress (optional)

With `syntax=True`, Prosodic uses spaCy's dependency parser to compute phrasal prominence (Liberman & Prince 1977) per word. This adds a `phrasal_stress` column to the syllable DataFrame and enables the `w_prom` and `s_demoted` constraints. Requires `pip install prosodic[syntax]`.

```python
t = prosodic.Text("...", syntax=True)
t.parse()
# phrasal_stress: 0 = sentence root, -1 = direct dependent, deeper = more embedded
```""")

md("""## Save and load

Parquet-backed save/load preserves the syllable DataFrame and any computed parse results — no need to re-parse on reload.""")

code("""import tempfile, os, shutil
out = tempfile.mkdtemp(prefix='prosodic_demo_')
sonnet.save(out)
print('saved files:')
for f in sorted(os.listdir(out)):
    print(f'  {f}')

# reload
loaded = prosodic.TextModel.load(out)
print(f'\\nreloaded: {len(loaded.lines)} lines, parse cached?',
      loaded._cached_parsed_df is not None)
shutil.rmtree(out)""")

md("""## Web app

A hosted instance is live at **[prosodic.app](https://prosodic.app)** — no install required. To run it locally:

```bash
prosodic web                     # http://127.0.0.1:8181
prosodic web --port 5111
prosodic web --dev               # auto-reload backend + frontend
```

Five tabs: **Parse** (text input + corpus dropdown + sortable, paginated results), **Line** (single-line scansion detail showing all candidates), **Meter** (constraint config + weights), **MaxEnt** (annotated-data training), **Settings**. See `prosodic/web/` for the implementation.""")

md("""## Remote client

If you have access to a Prosodic server (`prosodic web` or [prosodic.app](https://prosodic.app)), you can use the remote client to parse without installing torch / espeak / numpy locally — only `requests` is required.

```python
import prosodic
prosodic.set_server('https://prosodic.app')

t = prosodic.Text("From fairest creatures we desire increase")
t.parse()                            # delegates to /api/parse
print(t.lines[0].best_parse.meter_str)

result = t.fit(target_scansion='wswswswsws', zones=3)  # delegates to /api/maxent/fit
print(result.weights, result.accuracy)
```""")

md("""## Further reading

- [`prosodic/parsing/constraints.py`](prosodic/parsing/constraints.py): every metrical constraint, with a vectorized lambda for the parser
- [`prosodic/parsing/maxent.py`](prosodic/parsing/maxent.py): MaxEnt OT weight learner
- [`prosodic/analysis/`](prosodic/analysis/): poem-level form classification (this notebook's `meter_type` / `rhyme_scheme` / `summary`)
- [`prosodic/profiling.py`](prosodic/profiling.py): performance benchmarks (run `python -m prosodic.profiling`)
- [`CLAUDE.md`](CLAUDE.md): architectural overview and design notes""")

nb["cells"] = cells

# Execute
client = NotebookClient(nb, timeout=300, kernel_name="python3")
client.execute(cwd=str(REPO_ROOT))

# Save
out_path = REPO_ROOT / "README.ipynb"
with out_path.open("w") as f:
    nbformat.write(nb, f)

print(f"\nWrote {out_path} with {len(cells)} cells.")
