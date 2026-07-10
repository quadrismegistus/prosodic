# Prosodic 3

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/quadrismegistus/prosodic/blob/master/README.ipynb)
[![Demo](https://img.shields.io/badge/demo-prosodic.app-blue)](https://prosodic.app)
[![Docs](https://img.shields.io/badge/docs-prosodic.app%2Fdocs-blue)](https://prosodic.app/docs/)
[![Code coverage](https://codecov.io/gh/quadrismegistus/prosodic/branch/master/graph/badge.svg)](https://codecov.io/gh/quadrismegistus/prosodic)

**Prosodic** is a Python library and web app for metrical-phonological analysis of poetry. It parses text into a linguistic hierarchy (text → stanza → line → word → syllable → phoneme), runs a constraint-satisfaction metrical parser, and identifies stress patterns (iambic, trochaic, anapestic, dactylic), foot/syllable schemes, and named rhyme schemes (sonnet variants, couplet, ballad, etc.).

Try the hosted version at **[prosodic.app](https://prosodic.app)** — paste a poem, see scansions, rhyme schemes, and form classification immediately. This notebook walks through the full Python API — from parsing a single line up to poem-level form classification. Click the **Open in Colab** badge above to run it in your browser.

Built by [Ryan Heuser](https://github.com/quadrismegistus), [Josh Falk](https://github.com/jsfalk), and [Arto Anttila](http://web.stanford.edu/~anttila/), with contributions from [Sam Bowman](https://github.com/sleepinyourhat).

## Install

```bash
pip install prosodic
# or for development:
pip install git+https://github.com/quadrismegistus/prosodic
```

You'll also need [espeak](https://github.com/espeak-ng/espeak-ng) (free TTS) to phonemize words not in the CMU dictionary:

- **Mac**: `brew install espeak`
- **Linux**: `apt-get install espeak libespeak1 libespeak-dev`
- **Windows**: download from the [espeak-ng releases](https://github.com/espeak-ng/espeak-ng/releases/latest)

## Quickstart

A complete tour of Prosodic in five lines.

```python
import prosodic

sonnet = prosodic.Text("""When in the chronicle of wasted time
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
Had eyes to wonder, but lack tongues to praise.""")

sonnet.parse()
print(sonnet.summary())
```

↓

      #st    #ln  parse        rhyme      #feet    #syll    #parse
    -----  -----  -----------  -------  -------  -------  --------
        1      1  -+-+-+-+-+   a              5       10         2
        1      2  -+-+-+-+-+   b              5       10         1
        1      3  -+-+-+-+-+   a              5       10         3
        1      4  -+-+-+-+-+   b              5       10         1
        1      5  -+-+-+-+-+   -              5       10         8
        1      6  -+-+-+-+-+   c              5       10         1
        1      7  +-+-++-+-+   -              5       10         7
        1      8  +-+-+-+-+-+  c              6       11         3
        1      9  -+-+-+-+-+   -              5       10         3
        1     10  -+-+-+-+-+   d              5       10         6
        1     11  -+-+-+-+-+   -              5       10         3
        1     12  -+-+-+-+-+   d              5       10         2
        1     13  -+-+-+-+-+   e              5       10         1
        1     14  -+-+-+-+-+   e              5       10         3
    
    
    estimated schema
    ----------
    meter: Iambic
    feet: Pentameter
    syllables: 10
    rhyme: Sonnet, Shakespearean (abab cdcd efefgg)

## Reading texts

You can build a `Text` from a string, a file, or just a single line.

```python
# from a string
short = prosodic.Text("A horse, a horse, my kingdom for a horse!")

# from a file (local path or URL)
shaksonnets = prosodic.Text(fn='https://raw.githubusercontent.com/quadrismegistus/prosodic/refs/heads/master/corpora/corppoetry_en/en.shakespeare.txt')

# a single line via .line1
line = prosodic.Text("Shall I compare thee to a summer's day?").line1

print(f"short: {len(short.lines)} line(s)")
print(f"sonnets: {len(shaksonnets.lines):,} lines, {len(shaksonnets.stanzas):,} stanzas")
print(f"single line: {line}")
```

↓

    short: 1 line(s)
    sonnets: 2,155 lines, 154 stanzas
    single line: Line(num=1, txt="Shall I compare thee to a summer's day?")

## The hierarchy: stanzas → lines → words → syllables → phonemes

Prosodic organizes text into a tree of linguistic entities. Children are constructed lazily on first access — the underlying source of truth is a per-syllable DataFrame.

```python
# tree access
print(f"sonnet has {len(sonnet.stanzas)} stanzas, {len(sonnet.lines)} lines")
print(f"line 1 has {len(sonnet.lines[0].wordtokens)} word tokens")
print(f"first word: {sonnet.lines[0].wordtokens[0]}")
```

↓

    sonnet has 1 stanzas, 14 lines
    line 1 has 7 word tokens
    first word: WordToken(num=1, txt='When', lang='en', para_num=1, line_num=1, sent_num=1, sentpart_num=1, linepart_num=1)

```python
# attribute shortcut: text.line1 == text.lines[0]
sonnet.line1
```

↓

**Line**

|   stanza_num |   line_num |   linepart_num |   sent_num |   sentpart_num | wordtoken_num   | wordtoken_txt   | wordtype_txt   | wordform_num   | wordform_ipa_origin   | syll_num   | syll_txt   | syll_ipa   | wordtoken_is_punc   |
|-------------:|-----------:|---------------:|-----------:|---------------:|:----------------|:----------------|:---------------|:---------------|:----------------------|:-----------|:-----------|:-----------|:--------------------|
|            1 |          1 |              1 |          1 |              1 | 1               | When            | When           | 1              | dict                  | 1          | When       | wɛn        | 0                   |
|            1 |          1 |              1 |          1 |              1 | 1               | When            | When           | 2              | dict                  | 1          | When       | 'wɛn       | 0                   |
|            1 |          1 |              1 |          1 |              1 | 2               | in              | in             | 1              | dict                  | 1          | in         | ɪn         | 0                   |
|            1 |          1 |              1 |          1 |              1 | 2               | in              | in             | 2              | dict                  | 1          | in         | 'ɪn        | 0                   |
|            1 |          1 |              1 |          1 |              1 | 3               | the             | the            | 1              | dict                  | 1          | the        | ðə         | 0                   |
|            1 |          1 |              1 |          1 |              1 | ...             | ...             | ...            | ...            | ...                   | ...        | ...        | ...        | ...                 |
|            1 |          1 |              1 |          1 |              1 | 4               | chronicle       | chronicle      | 1              | dict                  | 3          | cle        | kəl        | 0                   |
|            1 |          1 |              1 |          1 |              1 | 5               | of              | of             | 1              | dict                  | 1          | of         | ʌv         | 0                   |
|            1 |          1 |              1 |          1 |              1 | 6               | wasted          | wasted         | 1              | dict                  | 1          | wa         | 'weɪ       | 0                   |
|            1 |          1 |              1 |          1 |              1 | 6               | wasted          | wasted         | 1              | dict                  | 2          | sted       | stəd       | 0                   |
|            1 |          1 |              1 |          1 |              1 | 7               | time            | time           | 1              | dict                  | 1          | time       | 'taɪm      | 0                   |
*12 rows × 1 columns*
```python
# wordform → syllable → phoneme
wordform = sonnet.line1.wordtokens[1].wordform
print(f"wordform: {wordform}")
for syll in wordform.syllables:
    print(f"  syllable: {syll}, IPA={syll.ipa!r}, stressed={syll.is_stressed}, heavy={syll.is_heavy}")
    for phon in syll.phonemes:
        print(f"    phon: {phon.txt!r}")
```

↓

    wordform: WordForm(num=1, txt='in', force_ambig_stress=True, ipa_origin='dict')
      syllable: Syllable(num=1, txt='in', ipa='ɪn'), IPA='ɪn', stressed=False, heavy=True
        phon: 'ɪ'
        phon: 'n'

## DataFrame view

The whole text is also accessible as a flat per-syllable DataFrame. This is the source of truth — entities are constructed from it on demand.

```python
# .df is the syllable-level DataFrame
sonnet.df.head(8)
```

↓

|    |   word_num |   line_num |   para_num |   sent_num |   sentpart_num |   linepart_num | word_txt   |   is_punc |   form_idx |   num_forms |   syll_idx | syll_ipa   | syll_text   | is_stressed   | is_heavy   | is_strong   | is_weak   | is_functionword   |
|---:|-----------:|-----------:|-----------:|-----------:|---------------:|---------------:|:-----------|----------:|-----------:|------------:|-----------:|:-----------|:------------|:--------------|:-----------|:------------|:----------|:------------------|
|  0 |          1 |          1 |          1 |          1 |              1 |              1 | When       |         0 |          0 |           2 |          0 | wɛn        | When        | False         | True       | False       | False     | True              |
|  1 |          1 |          1 |          1 |          1 |              1 |              1 | When       |         0 |          1 |           2 |          0 | 'wɛn       | When        | True          | True       | False       | False     | False             |
|  2 |          2 |          1 |          1 |          1 |              1 |              1 | in         |         0 |          0 |           2 |          0 | ɪn         | in          | False         | True       | False       | False     | True              |
|  3 |          2 |          1 |          1 |          1 |              1 |              1 | in         |         0 |          1 |           2 |          0 | 'ɪn        | in          | True          | True       | False       | False     | False             |
|  4 |          3 |          1 |          1 |          1 |              1 |              1 | the        |         0 |          0 |           1 |          0 | ðə         | the         | False         | False      | False       | False     | True              |
|  5 |          4 |          1 |          1 |          1 |              1 |              1 | chronicle  |         0 |          0 |           1 |          0 | 'krɑ       | chro        | True          | False      | True        | False     | False             |
|  6 |          4 |          1 |          1 |          1 |              1 |              1 | chronicle  |         0 |          0 |           1 |          1 | nɪ         | ni          | False         | False      | False       | True      | False             |
|  7 |          4 |          1 |          1 |          1 |              1 |              1 | chronicle  |         0 |          0 |           1 |          2 | kəl        | cle         | False         | True       | False       | False     | False             |
```python
# columns
list(sonnet.df.columns)
```

↓

    ['word_num',
     'line_num',
     'para_num',
     'sent_num',
     'sentpart_num',
     'linepart_num',
     'word_txt',
     'is_punc',
     'form_idx',
     'num_forms',
     'syll_idx',
     'syll_ipa',
     'syll_text',
     'is_stressed',
     'is_heavy',
     'is_strong',
     'is_weak',
     'is_functionword']

## Metrical parsing

`text.parse()` runs an exhaustive vectorized parser: it evaluates every possible scansion against a configurable set of metrical constraints (numpy on CPU, torch on GPU when available), then uses harmonic bounding to identify optimal parses. Constraints include `w_peak` (no peak in weak position), `w_stress` (no stress in weak), `s_unstress` (no unstress in strong), `unres_within`/`unres_across` (no unresolved disyllables), `foot_size`. Turning on `syntax=True` (below) adds gradient phrasal-stress constraints (`w_stress_p`/`s_unstress_p`/`w_stress_t`/`s_unstress_t`). See `prosodic/parsing/constraints.py` for the full list, or [the write-up on metrical parsing](docs/methods/metrical-parsing.qmd) for the theory.

```python
# parse a single line
line = prosodic.Text("Shall I compare thee to a summer's day?").line1
line.parse()
print(line.best_parse)
```

↓

    Parse(txt="shall I com PARE thee TO a SUM mer's DAY")

```python
# inspect the parse
bp = line.best_parse
print(f"meter:     {bp.meter_str}    (- = weak, + = strong)")
print(f"stress:    {bp.stress_str}    (- = unstressed, + = stressed)")
print(f"score:     {bp.score}    (sum of weighted constraint violations)")
print(f"feet:      {bp.feet}")
print(f"foot_type: {bp.foot_type}    (per-parse classification)")
print(f"is_rising: {bp.is_rising}")
```

↓

    meter:     -+-+-+-+-+    (- = weak, + = strong)
    stress:    -+-+---+-+    (- = unstressed, + = stressed)
    score:     1.0    (sum of weighted constraint violations)
    feet:      ['ws', 'ws', 'ws', 'ws', 'ws']
    foot_type: iambic    (per-parse classification)
    is_rising: True

```python
# all unbounded parses for the line, sorted by score
for p in line.parses.unbounded:
    print(f"{p.meter_str}  score={p.score}")
```

↓

    -+-+-+-+-+  score=1.0
    -+-++--+-+  score=1.0
    -+--+--+-+  score=3.0

```python
# parse the full sonnet
sonnet.parse()
for line in sonnet.lines[:6]:
    bp = line.best_parse
    print(f"L{line.num:2d}  {bp.meter_str}  score={bp.score:.1f}  ambig={len(line.parses.unbounded)}")
```

↓

    L 1  -+-+-+-+-+  score=1.0  ambig=2
    L 2  -+-+-+-+-+  score=1.0  ambig=1
    L 3  -+-+-+-+-+  score=2.0  ambig=3
    L 4  -+-+-+-+-+  score=0.0  ambig=1
    L 5  -+-+-+-+-+  score=2.0  ambig=8
    L 6  -+-+-+-+-+  score=0.0  ambig=1

## The metrical grid

`line.grid_str()` renders the best parse as a **Hayes-style metrical grid** (Liberman & Prince 1977; Hayes 1983): marks stacked over each syllable, where column height encodes prominence — every syllable gets one mark, lexically stressed syllables a second, primary-stressed syllables a third. The `w`/`s` row beneath is the metrical template, so a stress–meter mismatch shows up as a tall column standing over a `w` (a `*` after the meter letter flags a position that incurred a violation). This works on any parsed line — no spaCy required.

```python
# Hayes-style metrical grid of the best parse (lexical rows only)
print(sonnet.line1.grid_str())
```

↓

         *      *              *       *
         *      *              *       *
    *    *  *   *    *  *   *  *  *    *
    when IN the CHRO ni CLE of WA sted TIME
    w    s  w   s    w  s*  w  s  w    s

## Feet

Prosodic parses **positions** (weak/strong), not feet — but a derived *foot layer* groups a parse's syllables into classical feet (iamb, trochee, anapest, dactyl, …) via a dynamic program with extrametrical edge handling, validated at 97.5% exact against a hand-tagged gold. `parse.scansion` is the per-syllable `w`/`s` string; `footed_scansion` cuts it at foot boundaries; `metrical_feet` returns first-class `Foot` objects (a `*` in `feet_str` marks a foot that inverts the line's head — a substitution). See [the foot-parsing write-up](docs/methods/foot-parsing.md).

```python
bp = prosodic.Text("Pity the world, or else this glutton be").line1.best_parse
print(f"scansion:        {bp.scansion}")
print(f"footed_scansion: {bp.footed_scansion}")
print(f"feet_str:        {bp.feet_str}   (* = substituted foot)")
```

↓

    scansion:        swwswswsws
    footed_scansion: sw|ws|ws|ws|ws
    feet_str:        (s w*)(w s)(w s)(w s)(w s)   (* = substituted foot)

```python
# metrical_feet: first-class Foot objects (label, pattern, headedness)
for ft in bp.metrical_feet:
    print(f"{ft.label:10s} {ft.pattern:4s} head={ft.head:8s} substituted={ft.is_substituted}")
```

↓

    trochee    sw   head=falling  substituted=True
    iamb       ws   head=rising   substituted=False
    iamb       ws   head=rising   substituted=False
    iamb       ws   head=rising   substituted=False
    iamb       ws   head=rising   substituted=False

## The parsed DataFrame

Per-syllable parse results across the whole text — useful for analysis, plotting, or export.

```python
sonnet.parsed_df.head(10)
```

↓

|    |   line_num |   word_num |   form_idx |   syll_idx |   line_syll_idx |   parse_idx |   parse_rank |   parse_score | is_best   | is_bounded   | ...   |   pos_size | meter_val   | syll_txt   | syll_ipa   | is_stressed   |   *w_peak |   *w_stress |   *s_unstress |   *unres_across |   *unres_within |
|---:|-----------:|-----------:|-----------:|-----------:|----------------:|------------:|-------------:|--------------:|:----------|:-------------|:------|-----------:|:------------|:-----------|:-----------|:--------------|----------:|------------:|--------------:|----------------:|----------------:|
|  0 |          1 |          1 |          0 |          0 |               0 |           0 |            1 |             1 | True      | False        | ...   |          1 | w           | When       | wɛn        | False         |         0 |           0 |             0 |               0 |               0 |
|  1 |          1 |          2 |          1 |          0 |               1 |           0 |            1 |             1 | True      | False        | ...   |          1 | s           | in         | 'ɪn        | True          |         0 |           0 |             0 |               0 |               0 |
|  2 |          1 |          3 |          0 |          0 |               2 |           0 |            1 |             1 | True      | False        | ...   |          1 | w           | the        | ðə         | False         |         0 |           0 |             0 |               0 |               0 |
|  3 |          1 |          4 |          0 |          0 |               3 |           0 |            1 |             1 | True      | False        | ...   |          1 | s           | chro       | 'krɑ       | True          |         0 |           0 |             0 |               0 |               0 |
|  4 |          1 |          4 |          0 |          1 |               4 |           0 |            1 |             1 | True      | False        | ...   |          1 | w           | ni         | nɪ         | False         |         0 |           0 |             0 |               0 |               0 |
|  5 |          1 |          4 |          0 |          2 |               5 |           0 |            1 |             1 | True      | False        | ...   |          1 | s           | cle        | kəl        | False         |         0 |           0 |             1 |               0 |               0 |
|  6 |          1 |          5 |          0 |          0 |               6 |           0 |            1 |             1 | True      | False        | ...   |          1 | w           | of         | ʌv         | False         |         0 |           0 |             0 |               0 |               0 |
|  7 |          1 |          6 |          0 |          0 |               7 |           0 |            1 |             1 | True      | False        | ...   |          1 | s           | wa         | 'weɪ       | True          |         0 |           0 |             0 |               0 |               0 |
|  8 |          1 |          6 |          0 |          1 |               8 |           0 |            1 |             1 | True      | False        | ...   |          1 | w           | sted       | stəd       | False         |         0 |           0 |             0 |               0 |               0 |
|  9 |          1 |          7 |          0 |          0 |               9 |           0 |            1 |             1 | True      | False        | ...   |          1 | s           | time       | 'taɪm      | True          |         0 |           0 |             0 |               0 |               0 |
*10 rows × 21 columns*
```python
# every column you might want for analysis
list(sonnet.parsed_df.columns)
```

↓

    ['line_num',
     'word_num',
     'form_idx',
     'syll_idx',
     'line_syll_idx',
     'parse_idx',
     'parse_rank',
     'parse_score',
     'is_best',
     'is_bounded',
     'pos_idx',
     'pos_size',
     'meter_val',
     'syll_txt',
     'syll_ipa',
     'is_stressed',
     '*w_peak',
     '*w_stress',
     '*s_unstress',
     '*unres_across',
     '*unres_within']

## Custom meters

The default `Meter` allows up to 2-syllable strong/weak positions. You can change constraints, weights, position widths, or unit of parsing.

```python
# stricter binary meter
strict = prosodic.Meter(
    constraints=['w_peak', 'w_stress', 's_unstress', 'foot_size'],
    max_s=1, max_w=1,
)
print(strict)
```

↓

    Meter(constraints={'w_peak': 1.0, 'w_stress': 1.0, 's_unstress': 1.0, 'foot_size': 1.0}, max_s=1, max_w=1, resolve_optionality=True, pool_forms=True, parse_unit='line')

```python
# parse with a custom meter
sonnet.parse(meter=strict)
print(sonnet.line1.best_parse)
```

↓

    Parse(txt='when IN the CHRO ni CLE of WA sted TIME')

## Poem-level analysis

Prosodic 3 includes `prosodic/analysis/` (a port of the standalone [poesy](https://github.com/quadrismegistus/poesy) package) for higher-order summary statistics over a parsed text.

```python
# meter classification (iambic / trochaic / anapestic / dactylic)
sonnet.meter_type
```

↓

    {'foot': 'binary',
     'head': 'final',
     'type': 'iambic',
     'mpos_freqs': {'w': 0.49645390070921985, 's': 0.5035460992907801},
     'perc_lines_starting': {'w': 0.9285714285714286, 's': 0.07142857142857142},
     'perc_lines_ending': {'s': 1.0},
     'perc_lines_fourth': {'s': 0.9285714285714286, 'w': 0.07142857142857142},
     'ambiguity': 1.0}

```python
# repeating beat-length template (e.g. invariable pentameter, ballad meter)
print('feet  scheme:', sonnet.line_scheme)
print('syll  scheme:', sonnet.syllable_scheme)
```

↓

    feet  scheme: {'combo': (5,), 'diff': 2}
    syll  scheme: {'combo': (10,), 'diff': 1}

### Rhyme detection

Rhyme is detected from sound, not spelling. Each line-final rime splits into nucleus (vowel) and coda feature-edit distances, and pairs classify as `'perfect'`, `'slant'` (consonance: identical coda, free vowel), `'assonance'`, or `None` — bands calibrated against Walker's 1775 rhyming dictionary.

```python
# classify rhyme pairs ('time'/'rhyme'; 'prophecies'/'eyes')
print('time/rhyme:     ', sonnet.line1.rime_type(sonnet.lines[2]))
print('prophecies/eyes:', sonnet.lines[8].rime_type(sonnet.lines[10]))
```

↓

    time/rhyme:      perfect
    prophecies/eyes: slant

```python
# gradient pairwise rime distance (0 = identical rime)
sonnet.line1.rime_distance(sonnet.lines[2])  # 'time' vs 'rhyme'
```

↓

    0.0

```python
# every rhyming line in the text, with its closest partner
for line, (dist, partner) in list(sonnet.get_rhyming_lines().items())[:6]:
    print(f"L{line.num:2d} ↔ L{partner.num:2d}  dist={dist:.2f}  '{line.txt.strip()[:35]}' / '{partner.txt.strip()[:35]}'")
```

↓

    L 3 ↔ L 1  dist=0.00  'And beauty making beautiful old rhy' / 'When in the chronicle of wasted tim'
    L 8 ↔ L 6  dist=0.00  'Even such a beauty as you master no' / 'Of hand, of foot, of lip, of eye, o'
    L14 ↔ L13  dist=0.00  'Had eyes to wonder, but lack tongue' / 'For we, which now behold these pres'

```python
# per-line rhyme group IDs (0 = no rhyme partner)
print('IDs:    ', sonnet.rhyme_ids)
from prosodic.analysis import nums_to_scheme
print('letters:', ''.join(nums_to_scheme(sonnet.rhyme_ids)))
```

↓

    IDs:     [1, 2, 1, 2, 0, 3, 0, 3, 0, 4, 0, 4, 5, 5]
    letters: abab-c-c-d-dee

### Named rhyme scheme matching

Match observed rhyme groups against a 39-form catalog (Sonnet variants, Couplet, Sestet, Triplet, Rhyme Royal, Spenserian, etc.) by Jaccard similarity over rhyme-edge sets.

```python
rs = sonnet.rhyme_scheme
print(f"name:     {rs['name']}")
print(f"form:     {rs['form']}")
print(f"accuracy: {rs['accuracy']:.2f}")
print()
print("top candidates:")
for name, form, score in rs['candidates'][:5]:
    print(f"  {score:.2f}  {name:30s} {form}")
```

↓

    name:     Sonnet, Shakespearean
    form:     abab cdcd efefgg
    accuracy: 0.71
    
    top candidates:
      0.71  Sonnet, Shakespearean          abab cdcd efefgg
      0.50  Sonnet A                       abab cdcd eefeff
      0.50  Sonnet B                       abab cdcd effegg
      0.42  Sonnet D                       ababbcdc ceceff
      0.33  Sonnet, Spenserian             abab bcbc cdcdee

```python
# form predicates
print('is_sonnet:               ', sonnet.is_sonnet)
print('is_shakespearean_sonnet: ', sonnet.is_shakespearean_sonnet)
```

↓

    is_sonnet:                True
    is_shakespearean_sonnet:  True

### Tabular summary

`text.summary()` rolls everything together: per-line parse + rhyme letter + foot/syllable count + ambiguity, plus an estimated-schema block.

```python
print(sonnet.summary())
```

↓

      #st    #ln  parse        rhyme      #feet    #syll    #parse
    -----  -----  -----------  -------  -------  -------  --------
        1      1  -+-+-+-+-+   a              5       10         1
        1      2  -+-+-+-+-+   b              5       10         1
        1      3  -+-+-+-+-+   a              5       10         1
        1      4  -+-+-+-+-+   b              5       10         1
        1      5  -+-+-+-+-+   -              5       10         1
        1      6  -+-+-+-+-+   c              5       10         1
        1      7  -+-+-+-+-+   -              5       10         1
        1      8  +-+-+-+-+-+  c              6       11         1
        1      9  -+-+-+-+-+   -              5       10         1
        1     10  -+-+-+-+-+   d              5       10         1
        1     11  -+-+-+-+-+   -              5       10         1
        1     12  -+-+-+-+-+   d              5       10         1
        1     13  -+-+-+-+-+   e              5       10         1
        1     14  -+-+-+-+-+   e              5       10         1
    
    
    estimated schema
    ----------
    meter: Iambic
    feet: Pentameter
    syllables: 10
    rhyme: Sonnet, Shakespearean (abab cdcd efefgg)

## Other languages and meters

Everything above is English iambic pentameter, but neither is required. `lang="de"` swaps in German pronunciations (espeak-ng-driven — see [the write-up on languages](docs/methods/languages.qmd)) and the same constraints score this line of Schiller's *Wilhelm Tell* as strict alternating stress:

```python
de = prosodic.Text("Durch diese hohle Gasse muß er kommen", lang="de")
de.parse()
bp = de.line1.best_parse
print(bp.txt)
print(f"meter:  {bp.meter_str}   (- weak, + strong)")
print(f"stress: {bp.stress_str}   (- unstressed, + stressed)")
```

↓

    durch DIE se HO hle GAS se MUSS er KOM men
    meter:  -+-+-+-+-+-   (- weak, + strong)
    stress: -+-+-+-+-+-   (- unstressed, + stressed)

Ternary meter needs no special mode either — anapestic feet (`ww` + `s`) are already in the candidate space, so `meter_type` classifies Byron's anapestic tetrameter correctly at default weights:

```python
byron = prosodic.Text(fn='https://raw.githubusercontent.com/quadrismegistus/prosodic/refs/heads/master/corpora/corppoetry_en/en.byron.sennacherib.txt')
byron.parse()
mt = byron.meter_type

line = byron.lines[1]
bp = line.best_parse
print(bp.txt)
print(f"meter:  {bp.meter_str}   (- weak, + strong)")
print({k: mt[k] for k in ('foot', 'head', 'type')})
```

↓

    and.his CO horts.were GLEA ming.in PUR ple.and GOLD
    meter:  --+--+--+--+   (- weak, + strong)
    {'foot': 'ternary', 'head': 'final', 'type': 'anapestic'}

## MaxEnt weight learning

`Meter.fit()` learns constraint weights from a target scansion (or annotated data) using L-BFGS-B Maximum Entropy optimization (Goldwater & Johnson 2003 / Hayes MaxEnt OT). The learned weights can be split by syllable position (`zones`) so positional sensitivity transfers to parsing.

```python
# Train weights to match an iambic pentameter target across all sonnet lines
import warnings
warnings.filterwarnings('ignore')

meter = prosodic.Meter()
meter.fit(sonnet, 'wswswswsws', zones=3)

print('top learned weights (zone × constraint):')
for name, w in sorted(meter.zone_weights.items(), key=lambda x: -abs(x[1]))[:8]:
    print(f"  {w:+.3f}  {name}")
```

↓

    top learned weights (zone × constraint):
      +5.939  unres_across_z2
      +5.106  unres_within_z3
      +4.257  unres_across_z3
      +3.975  unres_within_z2
      +3.652  s_unstress_z1
      +2.766  w_stress_z3
      +2.263  unres_across_z1
      +1.500  w_stress_z1

```python
# or learn from hand-annotated scansions — a CSV with line/scansion columns
# (extra columns ignored; mixed-syllable-count elision lines train too)
from prosodic.parsing.maxent import MaxEntTrainer
trainer = MaxEntTrainer(prosodic.Meter())
trainer.load_annotations('data/tagged_samples/foot-gold.csv')
trainer.train()
{k: round(v, 2) for k, v in trainer.learned_weights().items()}
```

↓

    {'w_peak': 0.51,
     'w_stress': 0.67,
     's_unstress': 2.13,
     'unres_across': 1.42,
     'unres_within': 1.5,
     'foot_size': 0.0}

## Phrasal stress (optional)

With `syntax=True`, Prosodic runs spaCy's dependency parser to compute sentence-level prominence per word (Liberman & Prince 1977). It adds two kinds of column to the syllable DataFrame:

- **`phrasal_stress`** — a discrete dependency-tree depth (`0` = sentence root, more negative = more deeply embedded), enabling the `w_prom` and `s_demoted` constraints.
- **`pstress` / `tstress`** — gradient prominence in `[0, 1]`, ported from Dozat's MetricalTree algorithm (`tstress == 1.0` marks the sentence's nuclear stress), enabling the gradient constraints `w_stress_p` / `s_unstress_p` / `w_stress_t` / `s_unstress_t`.

When `syntax=True`, `grid_str()` extends the grid *above* the word level using `tstress`, so the nuclear-stress word becomes the tallest column. Requires `pip install prosodic[syntax]`. See [the write-up on phrasal stress](docs/methods/phrasal-stress.qmd) for the full method and its lineage.

```python
# nuclear stress ("day") becomes the tallest column
phrasal = prosodic.Text("Shall I compare thee to a summer's day", syntax=True)
phrasal.parse()
print(phrasal.line1.grid_str())
```

↓

                                         *
                                         *
          *     *              *         *
          *     *              *         *
    *     * *   *    *    *  * *   *     *
    shall I com PARE thee TO a SUM mer's DAY
    w     s w   s    w    s* w s   w     s

```python
# the gradient phrasal columns (one value per word, broadcast onto its syllables)
cols = ['word_txt', 'syll_text', 'is_stressed', 'pstress', 'tstress']
phrasal.df[phrasal.df.form_idx == 0][cols]
```

↓

|    | word_txt   | syll_text   | is_stressed   |   pstress |   tstress |
|---:|:-----------|:------------|:--------------|----------:|----------:|
|  0 | Shall      | Shall       | False         |  0        |  0.583333 |
|  2 | I          | I           | False         |  0.333333 |  0.416667 |
|  4 | compare    | com         | False         |  0        |  0.75     |
|  5 | compare    | pare        | True          |  0        |  0.75     |
|  6 | thee       | thee        | False         |  0.333333 |  0.416667 |
|  8 | to         | to          | False         |  0        |  0.583333 |
|  9 | a          | a           | False         |  0        |  0        |
| 10 | summer's   | sum         | True          |  1        |  0.5      |
| 11 | summer's   | mer's       | False         |  1        |  0.5      |
| 12 | day        | day         | True          |  1        |  1        |
## Save and load

Parquet-backed save/load preserves the syllable DataFrame and any computed parse results — no need to re-parse on reload.

```python
import tempfile, os, shutil
out = tempfile.mkdtemp(prefix='prosodic_demo_')
sonnet.save(out)
print('saved files:')
for f in sorted(os.listdir(out)):
    print(f'  {f}')

# reload
loaded = prosodic.TextModel.load(out)
print(f'\nreloaded: {len(loaded.lines)} lines, parse cached?',
      loaded._cached_parsed_df is not None)
shutil.rmtree(out)
```

↓

    saved files:
      meta.json
      parsed.parquet
      syll.parquet
      text.txt.gz
    
    reloaded: 14 lines, parse cached? True

## Web app

A hosted instance is live at **[prosodic.app](https://prosodic.app)** — no install required. To run it locally:

```bash
prosodic web                     # http://127.0.0.1:8181
prosodic web --port 5111
prosodic web --dev               # auto-reload backend + frontend
```

Five tabs: **Parse** (text input + corpus dropdown + sortable, paginated results), **Line** (single-line scansion detail showing all candidates), **Meter** (constraint config + weights), **MaxEnt** (annotated-data training), **Settings**. Results are **shareable via permalink**, exportable as CSV/TSV/JSON, and long/prose lines fall back to phrase-level parsing automatically. See `prosodic/web/` for the implementation.

## Remote client

If you have access to a Prosodic server (`prosodic web` or [prosodic.app](https://prosodic.app)), you can use the remote client to parse without installing torch / espeak / numpy locally — only `requests` is required.

```python
import prosodic
prosodic.set_server('https://prosodic.app')

t = prosodic.Text("From fairest creatures we desire increase")
t.parse()                            # delegates to /api/parse
print(t.lines[0].best_parse.meter_str)

result = t.fit(target_scansion='wswswswsws', zones=3)  # delegates to /api/maxent/fit
print(result.weights, result.accuracy)
```

## Further reading

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
- [`CLAUDE.md`](CLAUDE.md): architectural overview and design notes
