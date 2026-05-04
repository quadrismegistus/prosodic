# Prosodic 3

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/quadrismegistus/prosodic/blob/master/README.ipynb)
[![Demo](https://img.shields.io/badge/demo-prosodic.app-blue)](https://prosodic.app)
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

You'll also need [espeak](https://espeak.sourceforge.net) (free TTS) to phonemize words not in the CMU dictionary:

- **Mac**: `brew install espeak`
- **Linux**: `apt-get install espeak`
- **Windows**: download from the [espeak site](http://espeak.sourceforge.net/download.html)

### Setup (Colab only)

Skip this cell when running locally. It installs system + Python deps in a Colab runtime.


```python
# Auto-install dependencies if running in Google Colab.
# Locally this is a no-op.
import sys
IN_COLAB = "google.colab" in sys.modules
if IN_COLAB:
    import subprocess
    subprocess.run(["apt-get", "-qq", "install", "-y", "espeak"], check=True)
    subprocess.run(["pip", "install", "-q", "prosodic"], check=True)
    print("Colab setup complete.")
else:
    print("Local environment — skipping Colab setup.")
```

    Local environment — skipping Colab setup.


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

      #st    #ln  parse        rhyme      #feet    #syll    #parse
    -----  -----  -----------  -------  -------  -------  --------
        1      1  -+-+-+-+-+   a              5       10         2
        1      2  -+-+-+-+-+   b              5       10         1
        1      3  -+-+-+-+-+   a              5       10         3
        1      4  -+-+-+-+-+   b              5       10         1
        1      5  -+-+-+-+-+   -              5       10         8
        1      6  -+-+-+-+-+   c              5       10         1
        1      7  -+--++-+-+   -              4       10         8
        1      8  +-+-+-+-+-+  c              6       11         2
        1      9  -+-+-+-+--   -              4       10         3
        1     10  -+-+-+-+--   d              4       10         6
        1     11  -+-+-+-+-+   e              5       10         2
        1     12  -+-+-+-+-+   d              5       10         2
        1     13  -+-+-+-+-+   e              5       10         2
        1     14  -+-+-+-+-+   e              5       10         3
    
    
    estimated schema
    ----------
    meter: Iambic
    feet: Pentameter
    syllables: 10
    rhyme: Sonnet A (abab cdcd eefeff)


## Reading texts

You can build a `Text` from a string, a file, or just a single line.


```python
# from a string
short = prosodic.Text("A horse, a horse, my kingdom for a horse!")

# from a file
shaksonnets = prosodic.Text(fn='corpora/corppoetry_en/en.shakespeare.txt')

# a single line via .line1
line = prosodic.Text("Shall I compare thee to a summer's day?").line1

print(f"short: {len(short.lines)} line(s)")
print(f"sonnets: {len(shaksonnets.lines):,} lines, {len(shaksonnets.stanzas):,} stanzas")
print(f"single line: {line}")
```

    short: 1 line(s)


    [32m[0.66s] Building long text[0m:   0%|          | 0/20307 [00:00<?, ?it/s]

    [32m[0.66s] Building long text[0m:  16%|█▌        | 3188/20307 [00:00<00:00, 25089.11it/s]

    [32m[0.66s] Building long text[0m:  34%|███▍      | 6970/20307 [00:00<00:00, 31819.71it/s]

    [32m[0.66s] Building long text[0m:  50%|█████     | 10227/20307 [00:00<00:00, 28083.98it/s]

    [32m[0.66s] Building long text[0m:  69%|██████▉   | 14030/20307 [00:00<00:00, 31558.56it/s]

    [32m[0.66s] Building long text[0m:  85%|████████▌ | 17277/20307 [00:00<00:00, 27517.94it/s]

                                                                                        

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

    sonnet has 1 stanzas, 14 lines
    line 1 has 7 word tokens
    first word: WordToken(num=1, txt='When', lang='en', para_num=1, line_num=1, sent_num=1, sentpart_num=1, linepart_num=1)



```python
# attribute shortcut: text.line1 == text.lines[0]
sonnet.line1
```




<b>Line</b><br><div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th>wordtoken_is_punc</th>
    </tr>
    <tr>
      <th>stanza_num</th>
      <th>line_num</th>
      <th>linepart_num</th>
      <th>sent_num</th>
      <th>sentpart_num</th>
      <th>wordtoken_num</th>
      <th>wordtoken_txt</th>
      <th>wordtype_txt</th>
      <th>wordform_num</th>
      <th>wordform_ipa_origin</th>
      <th>syll_num</th>
      <th>syll_txt</th>
      <th>syll_ipa</th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th rowspan="11" valign="top">1</th>
      <th rowspan="11" valign="top">1</th>
      <th rowspan="11" valign="top">1</th>
      <th rowspan="11" valign="top">1</th>
      <th rowspan="11" valign="top">1</th>
      <th rowspan="2" valign="top">1</th>
      <th rowspan="2" valign="top">When</th>
      <th rowspan="2" valign="top">When</th>
      <th>1</th>
      <th>dict</th>
      <th>1</th>
      <th>When</th>
      <th>wɛn</th>
      <td>0</td>
    </tr>
    <tr>
      <th>2</th>
      <th>dict</th>
      <th>1</th>
      <th>When</th>
      <th>'wɛn</th>
      <td>0</td>
    </tr>
    <tr>
      <th rowspan="2" valign="top">2</th>
      <th rowspan="2" valign="top">in</th>
      <th rowspan="2" valign="top">in</th>
      <th>1</th>
      <th>dict</th>
      <th>1</th>
      <th>in</th>
      <th>ɪn</th>
      <td>0</td>
    </tr>
    <tr>
      <th>2</th>
      <th>dict</th>
      <th>1</th>
      <th>in</th>
      <th>'ɪn</th>
      <td>0</td>
    </tr>
    <tr>
      <th>3</th>
      <th>the</th>
      <th>the</th>
      <th>1</th>
      <th>dict</th>
      <th>1</th>
      <th>the</th>
      <th>ðə</th>
      <td>0</td>
    </tr>
    <tr>
      <th>...</th>
      <th>...</th>
      <th>...</th>
      <th>...</th>
      <th>...</th>
      <th>...</th>
      <th>...</th>
      <th>...</th>
      <td>...</td>
    </tr>
    <tr>
      <th>4</th>
      <th>chronicle</th>
      <th>chronicle</th>
      <th>1</th>
      <th>dict</th>
      <th>3</th>
      <th>cle</th>
      <th>kəl</th>
      <td>0</td>
    </tr>
    <tr>
      <th>5</th>
      <th>of</th>
      <th>of</th>
      <th>1</th>
      <th>dict</th>
      <th>1</th>
      <th>of</th>
      <th>ʌv</th>
      <td>0</td>
    </tr>
    <tr>
      <th rowspan="2" valign="top">6</th>
      <th rowspan="2" valign="top">wasted</th>
      <th rowspan="2" valign="top">wasted</th>
      <th rowspan="2" valign="top">1</th>
      <th rowspan="2" valign="top">dict</th>
      <th>1</th>
      <th>was</th>
      <th>'weɪ</th>
      <td>0</td>
    </tr>
    <tr>
      <th>2</th>
      <th>ted</th>
      <th>stəd</th>
      <td>0</td>
    </tr>
    <tr>
      <th>7</th>
      <th>time</th>
      <th>time</th>
      <th>1</th>
      <th>dict</th>
      <th>1</th>
      <th>time</th>
      <th>'taɪm</th>
      <td>0</td>
    </tr>
  </tbody>
</table>
<p>12 rows × 1 columns</p>
</div>




```python
# wordform → syllable → phoneme
wordform = sonnet.line1.wordtokens[1].wordform
print(f"wordform: {wordform}")
for syll in wordform.syllables:
    print(f"  syllable: {syll}, IPA={syll.ipa!r}, stressed={syll.is_stressed}, heavy={syll.is_heavy}")
    for phon in syll.phonemes:
        print(f"    phon: {phon.txt!r}")
```

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




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>word_num</th>
      <th>line_num</th>
      <th>para_num</th>
      <th>sent_num</th>
      <th>sentpart_num</th>
      <th>linepart_num</th>
      <th>word_txt</th>
      <th>is_punc</th>
      <th>form_idx</th>
      <th>num_forms</th>
      <th>syll_idx</th>
      <th>syll_ipa</th>
      <th>syll_text</th>
      <th>is_stressed</th>
      <th>is_heavy</th>
      <th>is_strong</th>
      <th>is_weak</th>
      <th>is_functionword</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>When</td>
      <td>0</td>
      <td>0</td>
      <td>2</td>
      <td>0</td>
      <td>wɛn</td>
      <td>When</td>
      <td>False</td>
      <td>True</td>
      <td>False</td>
      <td>False</td>
      <td>True</td>
    </tr>
    <tr>
      <th>1</th>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>When</td>
      <td>0</td>
      <td>1</td>
      <td>2</td>
      <td>0</td>
      <td>'wɛn</td>
      <td>When</td>
      <td>True</td>
      <td>True</td>
      <td>False</td>
      <td>False</td>
      <td>False</td>
    </tr>
    <tr>
      <th>2</th>
      <td>2</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>in</td>
      <td>0</td>
      <td>0</td>
      <td>2</td>
      <td>0</td>
      <td>ɪn</td>
      <td>in</td>
      <td>False</td>
      <td>True</td>
      <td>False</td>
      <td>False</td>
      <td>True</td>
    </tr>
    <tr>
      <th>3</th>
      <td>2</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>in</td>
      <td>0</td>
      <td>1</td>
      <td>2</td>
      <td>0</td>
      <td>'ɪn</td>
      <td>in</td>
      <td>True</td>
      <td>True</td>
      <td>False</td>
      <td>False</td>
      <td>False</td>
    </tr>
    <tr>
      <th>4</th>
      <td>3</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>the</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>ðə</td>
      <td>the</td>
      <td>False</td>
      <td>False</td>
      <td>False</td>
      <td>False</td>
      <td>True</td>
    </tr>
    <tr>
      <th>5</th>
      <td>4</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>chronicle</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>'krɑ</td>
      <td>chro</td>
      <td>True</td>
      <td>False</td>
      <td>True</td>
      <td>False</td>
      <td>False</td>
    </tr>
    <tr>
      <th>6</th>
      <td>4</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>chronicle</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>1</td>
      <td>nɪ</td>
      <td>ni</td>
      <td>False</td>
      <td>False</td>
      <td>False</td>
      <td>True</td>
      <td>False</td>
    </tr>
    <tr>
      <th>7</th>
      <td>4</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>chronicle</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>2</td>
      <td>kəl</td>
      <td>cle</td>
      <td>False</td>
      <td>True</td>
      <td>False</td>
      <td>False</td>
      <td>False</td>
    </tr>
  </tbody>
</table>
</div>




```python
# columns
list(sonnet.df.columns)
```




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

`text.parse()` runs an exhaustive vectorized parser: it evaluates every possible scansion against a configurable set of metrical constraints (numpy on CPU, torch on GPU when available), then uses harmonic bounding to identify optimal parses. Constraints include `w_peak` (no peak in weak position), `w_stress` (no stress in weak), `s_unstress` (no unstress in strong), `unres_within`/`unres_across` (no unresolved disyllables), `foot_size`. See `prosodic/parsing/constraints.py` for the full list.


```python
# parse a single line
line = prosodic.Text("Shall I compare thee to a summer's day?").line1
line.parse()
print(line.best_parse)
```

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

    meter:     -+-+-+-+-+    (- = weak, + = strong)
    stress:    ---+---+-+    (- = unstressed, + = stressed)
    score:     2.0    (sum of weighted constraint violations)
    feet:      ['ws', 'ws', 'ws', 'ws', 'ws']
    foot_type: iambic    (per-parse classification)
    is_rising: True



```python
# all unbounded parses for the line, sorted by score
for p in line.parses.unbounded:
    print(f"{p.meter_str}  score={p.score}")
```

    -+-+-+-+-+  score=2.0



```python
# parse the full sonnet
sonnet.parse()
for line in sonnet.lines[:6]:
    bp = line.best_parse
    print(f"L{line.num:2d}  {bp.meter_str}  score={bp.score:.1f}  ambig={len(line.parses.unbounded)}")
```

    L 1  -+-+-+-+-+  score=2.0  ambig=2
    L 2  -+-+-+-+-+  score=1.0  ambig=1
    L 3  -+-+-+-+-+  score=2.0  ambig=3
    L 4  -+-+-+-+-+  score=0.0  ambig=1
    L 5  -+-+-+-+-+  score=3.0  ambig=8
    L 6  -+-+-+-+-+  score=0.0  ambig=1


## The parsed DataFrame

Per-syllable parse results across the whole text — useful for analysis, plotting, or export.


```python
sonnet.parsed_df.head(10)
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>line_num</th>
      <th>word_num</th>
      <th>form_idx</th>
      <th>syll_idx</th>
      <th>line_syll_idx</th>
      <th>parse_idx</th>
      <th>parse_rank</th>
      <th>parse_score</th>
      <th>is_best</th>
      <th>is_bounded</th>
      <th>...</th>
      <th>pos_size</th>
      <th>meter_val</th>
      <th>syll_txt</th>
      <th>syll_ipa</th>
      <th>is_stressed</th>
      <th>*w_peak</th>
      <th>*w_stress</th>
      <th>*s_unstress</th>
      <th>*unres_across</th>
      <th>*unres_within</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>1</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>1</td>
      <td>2.0</td>
      <td>True</td>
      <td>False</td>
      <td>...</td>
      <td>1</td>
      <td>w</td>
      <td>When</td>
      <td>wɛn</td>
      <td>False</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>1</th>
      <td>1</td>
      <td>2</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>2.0</td>
      <td>True</td>
      <td>False</td>
      <td>...</td>
      <td>1</td>
      <td>s</td>
      <td>in</td>
      <td>ɪn</td>
      <td>False</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>2</th>
      <td>1</td>
      <td>3</td>
      <td>0</td>
      <td>0</td>
      <td>2</td>
      <td>1</td>
      <td>1</td>
      <td>2.0</td>
      <td>True</td>
      <td>False</td>
      <td>...</td>
      <td>1</td>
      <td>w</td>
      <td>the</td>
      <td>ðə</td>
      <td>False</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>3</th>
      <td>1</td>
      <td>4</td>
      <td>0</td>
      <td>0</td>
      <td>3</td>
      <td>1</td>
      <td>1</td>
      <td>2.0</td>
      <td>True</td>
      <td>False</td>
      <td>...</td>
      <td>1</td>
      <td>s</td>
      <td>chro</td>
      <td>'krɑ</td>
      <td>True</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>4</th>
      <td>1</td>
      <td>4</td>
      <td>0</td>
      <td>1</td>
      <td>4</td>
      <td>1</td>
      <td>1</td>
      <td>2.0</td>
      <td>True</td>
      <td>False</td>
      <td>...</td>
      <td>1</td>
      <td>w</td>
      <td>ni</td>
      <td>nɪ</td>
      <td>False</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>5</th>
      <td>1</td>
      <td>4</td>
      <td>0</td>
      <td>2</td>
      <td>5</td>
      <td>1</td>
      <td>1</td>
      <td>2.0</td>
      <td>True</td>
      <td>False</td>
      <td>...</td>
      <td>1</td>
      <td>s</td>
      <td>cle</td>
      <td>kəl</td>
      <td>False</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>6</th>
      <td>1</td>
      <td>5</td>
      <td>0</td>
      <td>0</td>
      <td>6</td>
      <td>1</td>
      <td>1</td>
      <td>2.0</td>
      <td>True</td>
      <td>False</td>
      <td>...</td>
      <td>1</td>
      <td>w</td>
      <td>of</td>
      <td>ʌv</td>
      <td>False</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>7</th>
      <td>1</td>
      <td>6</td>
      <td>0</td>
      <td>0</td>
      <td>7</td>
      <td>1</td>
      <td>1</td>
      <td>2.0</td>
      <td>True</td>
      <td>False</td>
      <td>...</td>
      <td>1</td>
      <td>s</td>
      <td>was</td>
      <td>'weɪ</td>
      <td>True</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>8</th>
      <td>1</td>
      <td>6</td>
      <td>0</td>
      <td>1</td>
      <td>8</td>
      <td>1</td>
      <td>1</td>
      <td>2.0</td>
      <td>True</td>
      <td>False</td>
      <td>...</td>
      <td>1</td>
      <td>w</td>
      <td>ted</td>
      <td>stəd</td>
      <td>False</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>9</th>
      <td>1</td>
      <td>7</td>
      <td>0</td>
      <td>0</td>
      <td>9</td>
      <td>1</td>
      <td>1</td>
      <td>2.0</td>
      <td>True</td>
      <td>False</td>
      <td>...</td>
      <td>1</td>
      <td>s</td>
      <td>time</td>
      <td>'taɪm</td>
      <td>True</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
  </tbody>
</table>
<p>10 rows × 21 columns</p>
</div>




```python
# every column you might want for analysis
list(sonnet.parsed_df.columns)
```




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

    Meter(constraints={'w_peak': 1.0, 'w_stress': 1.0, 's_unstress': 1.0, 'foot_size': 1.0}, max_s=1, max_w=1, resolve_optionality=True, parse_unit='line')



```python
# parse with a custom meter
sonnet.parse(meter=strict)
print(sonnet.line1.best_parse)
```

    Parse(txt='when IN the CHRO ni CLE of WAS ted TIME')


## Poem-level analysis

Prosodic 3 includes `prosodic/analysis/` (a port of the standalone [poesy](https://github.com/quadrismegistus/poesy) package) for higher-order summary statistics over a parsed text.


```python
# meter classification (iambic / trochaic / anapestic / dactylic)
sonnet.meter_type
```




    {'foot': 'binary',
     'head': 'final',
     'type': 'iambic',
     'mpos_freqs': {'w': 0.48175182481751827,
      's': 0.48905109489051096,
      'ww': 0.021897810218978103,
      'ss': 0.0072992700729927005},
     'perc_lines_starting': {'w': 0.9285714285714286, 's': 0.07142857142857142},
     'perc_lines_ending': {'s': 0.8571428571428571, 'w': 0.14285714285714285},
     'perc_lines_fourth': {'s': 0.8571428571428571, 'w': 0.14285714285714285},
     'ambiguity': 2.4793969867312335}




```python
# repeating beat-length template (e.g. invariable pentameter, ballad meter)
print('feet  scheme:', sonnet.line_scheme)
print('syll  scheme:', sonnet.syllable_scheme)
```

    feet  scheme: {'combo': (5,), 'diff': 8}
    syll  scheme: {'combo': (10,), 'diff': 1}


### Rhyme detection

Rhyme is computed via feature-weighted edit distance over IPA segments (panphon). 0 = perfect rhyme; higher = slant rhyme.


```python
# pairwise rime distance
sonnet.line1.rime_distance(sonnet.lines[2])  # 'time' vs 'rhyme'
```




    0.0




```python
# every rhyming line in the text, with its closest partner
for line, (dist, partner) in list(sonnet.get_rhyming_lines().items())[:6]:
    print(f"L{line.num:2d} ↔ L{partner.num:2d}  dist={dist:.2f}  '{line.txt.strip()[:35]}' / '{partner.txt.strip()[:35]}'")
```

    L 3 ↔ L 1  dist=0.00  'And beauty making beautiful old rhy' / 'When in the chronicle of wasted tim'
    L 8 ↔ L 6  dist=0.00  'Even such a beauty as you master no' / 'Of hand, of foot, of lip, of eye, o'
    L14 ↔ L13  dist=0.00  'Had eyes to wonder, but lack tongue' / 'For we, which now behold these pres'



```python
# per-line rhyme group IDs (0 = no rhyme partner)
print('IDs:    ', sonnet.rhyme_ids)
from prosodic.analysis import nums_to_scheme
print('letters:', ''.join(nums_to_scheme(sonnet.rhyme_ids)))
```

    IDs:     [1, 2, 1, 2, 0, 3, 0, 3, 0, 4, 5, 4, 5, 5]
    letters: abab-c-c-dedee


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

    name:     Sonnet A
    form:     abab cdcd eefeff
    accuracy: 0.70
    
    top candidates:
      0.70  Sonnet A                       abab cdcd eefeff
      0.56  Sonnet, Shakespearean          abab cdcd efefgg
      0.43  Sonnet E                       abab cbcd cdedee
      0.40  Sonnet B                       abab cdcd effegg
      0.36  Sonnet D                       ababbcdc ceceff



```python
# form predicates
print('is_sonnet:               ', sonnet.is_sonnet)
print('is_shakespearean_sonnet: ', sonnet.is_shakespearean_sonnet)
```

    is_sonnet:                True
    is_shakespearean_sonnet:  False


### Tabular summary

`text.summary()` rolls everything together: per-line parse + rhyme letter + foot/syllable count + ambiguity, plus an estimated-schema block.


```python
print(sonnet.summary())
```

      #st    #ln  parse        rhyme      #feet    #syll    #parse
    -----  -----  -----------  -------  -------  -------  --------
        1      1  -+-+-+-+-+   a              5       10         2
        1      2  -+-+-+-+-+   b              5       10         1
        1      3  -+-+-+-+-+   a              5       10         3
        1      4  -+-+-+-+-+   b              5       10         1
        1      5  -+-+-+-+-+   -              5       10         8
        1      6  -+-+-+-+-+   c              5       10         1
        1      7  -+--++-+-+   -              4       10         8
        1      8  +-+-+-+-+-+  c              6       11         2
        1      9  -+-+-+-+--   -              4       10         3
        1     10  -+-+-+-+--   d              4       10         6
        1     11  -+-+-+-+-+   e              5       10         2
        1     12  -+-+-+-+-+   d              5       10         2
        1     13  -+-+-+-+-+   e              5       10         2
        1     14  -+-+-+-+-+   e              5       10         3
    
    
    estimated schema
    ----------
    meter: Iambic
    feet: Pentameter
    syllables: 10
    rhyme: Sonnet A (abab cdcd eefeff)


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

    [93m[0.82s] prosodic.parsing.maxent.MaxEntTrainer._build_line_data(): 1/14 lines had no matching scansion among parser candidates (syllable count mismatch?)[0m


    top learned weights (zone × constraint):
      +6.162  s_unstress_z1
      +4.707  unres_within_z3
      +4.149  unres_across_z2
      +3.641  unres_across_z3
      +3.557  unres_within_z2
      +2.884  s_unstress_z3
      +2.374  unres_across_z1
      +2.075  w_stress_z2


## Phrasal stress (optional)

With `syntax=True`, Prosodic uses spaCy's dependency parser to compute phrasal prominence (Liberman & Prince 1977) per word. This adds a `phrasal_stress` column to the syllable DataFrame and enables the `w_prom` and `s_demoted` constraints. Requires `pip install prosodic[syntax]`.

```python
t = prosodic.Text("...", syntax=True)
t.parse()
# phrasal_stress: 0 = sentence root, -1 = direct dependent, deeper = more embedded
```

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

Five tabs: **Parse** (text input + corpus dropdown + sortable, paginated results), **Line** (single-line scansion detail showing all candidates), **Meter** (constraint config + weights), **MaxEnt** (annotated-data training), **Settings**. See `prosodic/web/` for the implementation.

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

- [`prosodic/parsing/constraints.py`](prosodic/parsing/constraints.py): every metrical constraint, with a vectorized lambda for the parser
- [`prosodic/parsing/maxent.py`](prosodic/parsing/maxent.py): MaxEnt OT weight learner
- [`prosodic/analysis/`](prosodic/analysis/): poem-level form classification (this notebook's `meter_type` / `rhyme_scheme` / `summary`)
- [`prosodic/profiling.py`](prosodic/profiling.py): performance benchmarks (run `python -m prosodic.profiling`)
- [`CLAUDE.md`](CLAUDE.md): architectural overview and design notes
