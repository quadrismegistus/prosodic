"""Build a fresh README.ipynb for prosodic v3 with executed outputs.

The README notebook is canonical: this script is its source. Run it whenever
you change the API or the analysis module so the notebook (and the derived
README.md) stay in sync.

Sibling: ``docs/index.qmd`` is the docs-site edition of this same API tour
(a quarto-native executable page with frozen outputs in ``docs/_freeze/``).
When the tour changes here, update it too — see the comment at the top of
that file.

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

def md(text, tags=None):
    cell = nbformat.v4.new_markdown_cell(text)
    if tags:
        cell.metadata["tags"] = tags
    cells.append(cell)

def code(src, tags=None):
    cell = nbformat.v4.new_code_cell(src)
    if tags:
        cell.metadata["tags"] = tags
    cells.append(cell)


md("""# Prosodic 3

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/quadrismegistus/prosodic/blob/master/README.ipynb)
[![Demo](https://img.shields.io/badge/demo-prosodic.app-blue)](https://prosodic.app)
[![Docs](https://img.shields.io/badge/docs-prosodic.app%2Fdocs-blue)](https://prosodic.app/docs/)
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

Skip this cell when running locally. It installs system + Python deps in a Colab runtime.""",
   tags=["remove_cell"])

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
    print("Local environment — skipping Colab setup.")""",
     tags=["remove_cell"])

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

# from a file (local path or URL)
shaksonnets = prosodic.Text(fn='https://raw.githubusercontent.com/quadrismegistus/prosodic/refs/heads/master/corpora/corppoetry_en/en.shakespeare.txt')

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

`text.parse()` runs an exhaustive vectorized parser: it evaluates every possible scansion against a configurable set of metrical constraints (numpy on CPU, torch on GPU when available), then uses harmonic bounding to identify optimal parses. Constraints include `w_peak` (no peak in weak position), `w_stress` (no stress in weak), `s_unstress` (no unstress in strong), `unres_within`/`unres_across` (no unresolved disyllables), `foot_size`. Turning on `syntax=True` (below) adds gradient phrasal-stress constraints (`w_stress_p`/`s_unstress_p`/`w_stress_t`/`s_unstress_t`). See `prosodic/parsing/constraints.py` for the full list, or [the write-up on metrical parsing](docs/methods/metrical-parsing.qmd) for the theory.""")

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

md("""## The metrical grid

`line.grid_str()` renders the best parse as a **Hayes-style metrical grid** (Liberman & Prince 1977; Hayes 1983): marks stacked over each syllable, where column height encodes prominence — every syllable gets one mark, lexically stressed syllables a second, primary-stressed syllables a third. The `w`/`s` row beneath is the metrical template, so a stress–meter mismatch shows up as a tall column standing over a `w` (a `*` after the meter letter flags a position that incurred a violation). This works on any parsed line — no spaCy required.""")

code("""# Hayes-style metrical grid of the best parse (lexical rows only)
print(sonnet.line1.grid_str())""")

md("""## Feet

Prosodic parses **positions** (weak/strong), not feet — but a derived *foot layer* groups a parse's syllables into classical feet (iamb, trochee, anapest, dactyl, …) via a dynamic program with extrametrical edge handling, validated at 97.5% exact against a hand-tagged gold. `parse.scansion` is the per-syllable `w`/`s` string; `footed_scansion` cuts it at foot boundaries; `metrical_feet` returns first-class `Foot` objects (a `*` in `feet_str` marks a foot that inverts the line's head — a substitution). See [the foot-parsing write-up](docs/methods/foot-parsing.md).""")

code("""bp = prosodic.Text("Pity the world, or else this glutton be").line1.best_parse
print(f"scansion:        {bp.scansion}")
print(f"footed_scansion: {bp.footed_scansion}")
print(f"feet_str:        {bp.feet_str}   (* = substituted foot)")""")

code("""# metrical_feet: first-class Foot objects (label, pattern, headedness)
for ft in bp.metrical_feet:
    print(f"{ft.label:10s} {ft.pattern:4s} head={ft.head:8s} substituted={ft.is_substituted}")""")

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

Rhyme is detected from sound, not spelling. Each line-final rime splits into nucleus (vowel) and coda feature-edit distances, and pairs classify as `'perfect'`, `'slant'` (consonance: identical coda, free vowel), `'assonance'`, or `None` — bands calibrated against Walker's 1775 rhyming dictionary.""")

code("""# classify rhyme pairs ('time'/'rhyme'; 'prophecies'/'eyes')
print('time/rhyme:     ', sonnet.line1.rime_type(sonnet.lines[2]))
print('prophecies/eyes:', sonnet.lines[8].rime_type(sonnet.lines[10]))""")

code("""# gradient pairwise rime distance (0 = identical rime)
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

md("""## Other languages and meters

Everything above is English iambic pentameter, but neither is required. `lang="de"` swaps in German pronunciations (espeak-ng-driven — see [the write-up on languages](docs/methods/languages.qmd)) and the same constraints score this line of Schiller's *Wilhelm Tell* as strict alternating stress:""")

code("""de = prosodic.Text("Durch diese hohle Gasse muß er kommen", lang="de")
de.parse()
bp = de.line1.best_parse
print(bp.txt)
print(f"meter:  {bp.meter_str}   (- weak, + strong)")
print(f"stress: {bp.stress_str}   (- unstressed, + stressed)")""")

md("""Ternary meter needs no special mode either — anapestic feet (`ww` + `s`) are already in the candidate space, so `meter_type` classifies Byron's anapestic tetrameter correctly at default weights:""")

code("""byron = prosodic.Text(fn='https://raw.githubusercontent.com/quadrismegistus/prosodic/refs/heads/master/corpora/corppoetry_en/en.byron.sennacherib.txt')
byron.parse()
mt = byron.meter_type

line = byron.lines[1]
bp = line.best_parse
print(bp.txt)
print(f"meter:  {bp.meter_str}   (- weak, + strong)")
print({k: mt[k] for k in ('foot', 'head', 'type')})""")

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

code("""# or learn from hand-annotated scansions — a CSV with line/scansion columns
# (extra columns ignored; mixed-syllable-count elision lines train too)
from prosodic.parsing.maxent import MaxEntTrainer
trainer = MaxEntTrainer(prosodic.Meter())
trainer.load_annotations('data/tagged_samples/foot-gold.csv')
trainer.train()
{k: round(v, 2) for k, v in trainer.learned_weights().items()}""")

md("""## Phrasal stress (optional)

With `syntax=True`, Prosodic runs spaCy's dependency parser to compute sentence-level prominence per word (Liberman & Prince 1977). It adds two kinds of column to the syllable DataFrame:

- **`phrasal_stress`** — a discrete dependency-tree depth (`0` = sentence root, more negative = more deeply embedded), enabling the `w_prom` and `s_demoted` constraints.
- **`pstress` / `tstress`** — gradient prominence in `[0, 1]`, ported from Dozat's MetricalTree algorithm (`tstress == 1.0` marks the sentence's nuclear stress), enabling the gradient constraints `w_stress_p` / `s_unstress_p` / `w_stress_t` / `s_unstress_t`.

When `syntax=True`, `grid_str()` extends the grid *above* the word level using `tstress`, so the nuclear-stress word becomes the tallest column. Requires `pip install prosodic[syntax]`. See [the write-up on phrasal stress](docs/methods/phrasal-stress.qmd) for the full method and its lineage.""")

code("""# Phrasal stress needs spaCy + a model: pip install "prosodic[syntax]".
# In Colab we install them on demand; locally this is a no-op.
import sys, importlib.util
if importlib.util.find_spec("spacy") is None and "google.colab" in sys.modules:
    import subprocess
    subprocess.run(["pip", "install", "-q", "prosodic[syntax]"], check=True)
    subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"], check=True)""",
     tags=["remove_cell"])

code("""# nuclear stress ("day") becomes the tallest column
phrasal = prosodic.Text("Shall I compare thee to a summer's day", syntax=True)
phrasal.parse()
print(phrasal.line1.grid_str())""")

code("""# the gradient phrasal columns (one value per word, broadcast onto its syllables)
cols = ['word_txt', 'syll_text', 'is_stressed', 'pstress', 'tstress']
phrasal.df[phrasal.df.form_idx == 0][cols]""")

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

Five tabs: **Parse** (text input + corpus dropdown + sortable, paginated results), **Line** (single-line scansion detail showing all candidates), **Meter** (constraint config + weights), **MaxEnt** (annotated-data training), **Settings**. Results are **shareable via permalink**, exportable as CSV/TSV/JSON, and long/prose lines fall back to phrase-level parsing automatically. See `prosodic/web/` for the implementation.""")

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

**Methods write-ups** (theory + implementation):

- [Metrical parsing](docs/methods/metrical-parsing.qmd): generative-metrics background, the constraint-based model, harmonic bounding, and the vectorized parser
- [Phrasal stress](docs/methods/phrasal-stress.qmd): the Nuclear Stress Rule, Dozat's MetricalTree, and our dependency-projection port (`pstress`/`tstress`)
- [Foot parsing](docs/methods/foot-parsing.md): the DP foot delineation (extrametrical edges, headedness), the deterministic `best_parse` tie-break, and the hand-tagged foot gold
- [Rhyme detection](docs/methods/rhyme.qmd): feature-edit distance on IPA rimes, the 2-D (nucleus, coda) bands, and the Walker (1775) calibration

**Source**:

- [`prosodic/parsing/constraints.py`](prosodic/parsing/constraints.py): every metrical constraint, with a vectorized lambda for the parser
- [`prosodic/parsing/maxent.py`](prosodic/parsing/maxent.py): MaxEnt OT weight learner
- [`prosodic/analysis/`](prosodic/analysis/): poem-level form classification (this notebook's `meter_type` / `rhyme_scheme` / `summary`)
- [`prosodic/profiling.py`](prosodic/profiling.py): performance benchmarks (run `python -m prosodic.profiling`)
- [`CLAUDE.md`](CLAUDE.md): architectural overview and design notes""")

nb["cells"] = cells

# Execute
client = NotebookClient(nb, timeout=300, kernel_name="python3")
client.execute(cwd=str(REPO_ROOT))


def scrub_outputs(nb):
    """Remove terminal noise from executed cell outputs.

    hashstash's progress_bar passes disable=None to tqdm (auto-off when not a
    TTY), but ipykernel's stream pretends to be a TTY so the bars render into
    cell outputs as ANSI-colored carriage-return frames. Drop stderr streams
    wholesale (progress + log noise, never README content) and strip ANSI
    escapes / stray tqdm frames from what remains. Cleans both the saved
    README.ipynb and the markdown derived from it.
    """
    import re

    ansi = re.compile(r"\x1b\[[0-9;]*m")
    tqdm_frame = re.compile(r"^.*\d+%\|.*(\||\])\s*(\[.*it/s\]?)?\s*$")

    for cell in nb["cells"]:
        if cell.get("cell_type") != "code":
            continue
        kept = []
        for out in cell.get("outputs", []):
            if out.get("output_type") == "stream":
                if out.get("name") == "stderr":
                    continue
                text = ansi.sub("", "".join(out.get("text", "")))
                lines = [
                    ln for ln in text.split("\n")
                    if not tqdm_frame.match(ln.replace("\r", ""))
                ]
                text = "\n".join(lines)
                if not text.strip():
                    continue
                out["text"] = text
                # coalesce with a preceding stdout chunk (removing the
                # interleaved stderr leaves stdout split mid-block, which
                # renders with spurious blank lines)
                if (
                    kept
                    and kept[-1].get("output_type") == "stream"
                    and kept[-1].get("name") == "stdout"
                ):
                    kept[-1]["text"] = kept[-1]["text"].rstrip("\n") + "\n" + text
                    continue
            kept.append(out)
        cell["outputs"] = kept


scrub_outputs(nb)

# Save notebook (canonical, Colab-runnable)
out_path = REPO_ROOT / "README.ipynb"
with out_path.open("w") as f:
    nbformat.write(nb, f)
print(f"Wrote {out_path} with {len(cells)} cells.")


def write_readme_md(nb):
    """Convert the executed notebook to a clean README.md.

    nbconvert alone leaves junk in the markdown: the Colab-only bootstrap cell,
    pandas DataFrame ``<style scoped>`` CSS blocks (which GitHub strips anyway),
    and raw ``<table>`` HTML. We drop the tagged Colab cells, strip the CSS, and
    round-trip the DataFrame tables back through pandas into GitHub-native
    markdown tables.
    """
    import copy
    import io
    import re
    import pandas as pd
    from nbconvert import MarkdownExporter
    from traitlets.config import Config

    # Mark code→output boundaries (hashstash-README style): inject a sentinel
    # stream line as each cell's first output, then rewrite it to a standalone
    # "↓" after conversion. Without it, indented output blocks are visually
    # ambiguous with the code fence above them.
    ARROW = "@@OUTPUT-ARROW@@"
    nb = copy.deepcopy(nb)
    for cell in nb["cells"]:
        if cell.get("cell_type") == "code" and cell.get("outputs"):
            cell["outputs"].insert(
                0,
                nbformat.v4.new_output("stream", name="stdout", text=ARROW + "\n"),
            )

    cfg = Config()
    cfg.TagRemovePreprocessor.remove_cell_tags = ("remove_cell",)
    cfg.TagRemovePreprocessor.enabled = True
    cfg.MarkdownExporter.preprocessors = [
        "nbconvert.preprocessors.TagRemovePreprocessor"
    ]
    body, _ = MarkdownExporter(config=cfg).from_notebook_node(nb)

    # sentinel (rendered as an indented output line) -> standalone arrow
    body = re.sub(rf"\n( {{4}}{ARROW}\n+|{ARROW}\n+)", "\n\n↓\n\n", body)

    # pandas DataFrame CSS is dead weight (GitHub ignores <style>)
    body = re.sub(r"<style.*?</style>", "", body, flags=re.DOTALL)

    # entity _repr_html_ labels ("<b>Line</b><br>...") -> a bold markdown line
    body = re.sub(r"<b>(.*?)</b>\s*<br\s*/?>", r"**\1**\n\n", body, flags=re.DOTALL)

    def _clean_col(c):
        # flatten MultiIndex headers and drop pandas' "Unnamed: N_level" filler
        if isinstance(c, tuple):
            parts = [str(x) for x in c if not str(x).startswith("Unnamed")]
            return " ".join(parts).strip()
        return "" if str(c).startswith("Unnamed") else str(c)

    # DataFrame HTML tables -> markdown tables
    def _table_to_md(match):
        try:
            df = pd.read_html(io.StringIO(match.group(0)))[0]
            df.columns = [_clean_col(c) for c in df.columns]
            return df.to_markdown(index=False)
        except Exception:
            return match.group(0)

    body = re.sub(r"<table.*?</table>", _table_to_md, body, flags=re.DOTALL)
    body = re.sub(r"</?div>\s*", "", body)      # unwrap leftover df <div>s
    body = re.sub(r"<p>(.*?)</p>", r"*\1*", body, flags=re.DOTALL)  # "N rows × M cols" footer
    body = re.sub(r"\n{3,}", "\n\n", body)      # collapse blank-line runs
    body = body.rstrip() + "\n"

    md_path = REPO_ROOT / "README.md"
    md_path.write_text(body)
    print(f"Wrote {md_path} ({body.count(chr(10))} lines).")


write_readme_md(nb)
