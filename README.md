# Prosodic 2

Prosodic is a metrical-phonological parser written in Python. Currently, it can parse English and Finnish text, but adding additional languages is easy with a pronunciation dictionary or a custom python function. Prosodic was built by [Ryan Heuser](https://github.com/quadrismegistus), [Josh Falk](https://github.com/jsfalk), and [Arto Anttila](http://web.stanford.edu/~anttila/). Josh also maintains [another repository](https://github.com/jsfalk/prosodic1b), in which he has rewritten the part of this project that does phonetic transcription for English and Finnish. [Sam Bowman](https://github.com/sleepinyourhat) has contributed to the codebase as well, adding several new metrical constraints.

"Prosodic 2", in this `develop` branch, is a near-total rewrite of Prosodic.

## Install

```
pip install git+https://github.com/quadrismegistus/prosodic@develop
```

## Usage

### Use in GUI

In a terminal, run:

```
prosodic
```

Then navigate to [http://127.0.0.1:5000/](http://127.0.0.1:5000/).

### Use in code

#### Texts


```python
# import prosodic
import prosodic as ps

# load a text
text = ps.Text("""
Those hours, that with gentle work did frame
The lovely gaze where every eye doth dwell,
Will play the tyrants to the very same
And that unfair which fairly doth excel;
For never-resting time leads summer on
To hideous winter, and confounds him there;
Sap checked with frost, and lusty leaves quite gone,
Beauty o’er-snowed and bareness every where:
Then were not summer’s distillation left,
A liquid prisoner pent in walls of glass,
Beauty’s effect with beauty were bereft,
Nor it, nor no remembrance what it was:
But flowers distill’d, though they with winter meet,
Leese but their show; their substance still lives sweet.
""")

# show text -- it will display the dataframe at (`text.df``)
text   
```




<div>
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
      <th>word_lang</th>
      <th>word_num_forms</th>
      <th>syll_is_stressed</th>
      <th>syll_is_heavy</th>
      <th>syll_is_strong</th>
      <th>syll_is_weak</th>
      <th>word_is_punc</th>
    </tr>
    <tr>
      <th>stanza_num</th>
      <th>line_num</th>
      <th>line_txt</th>
      <th>sent_num</th>
      <th>sentpart_num</th>
      <th>wordtoken_num</th>
      <th>wordtoken_txt</th>
      <th>wordform_num</th>
      <th>syll_num</th>
      <th>syll_txt</th>
      <th>syll_ipa</th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th rowspan="11" valign="top">1</th>
      <th rowspan="5" valign="top">1</th>
      <th rowspan="5" valign="top">Those hours, that with gentle work did frame</th>
      <th rowspan="5" valign="top">1</th>
      <th rowspan="5" valign="top">1</th>
      <th>1</th>
      <th>\nThose</th>
      <th>1</th>
      <th>1</th>
      <th>Those</th>
      <th>ðoʊz</th>
      <td>en</td>
      <td>1</td>
      <td>0</td>
      <td>1</td>
      <td></td>
      <td></td>
      <td></td>
    </tr>
    <tr>
      <th rowspan="3" valign="top">2</th>
      <th rowspan="3" valign="top">hours</th>
      <th rowspan="2" valign="top">1</th>
      <th>1</th>
      <th>ho</th>
      <th>'aʊ</th>
      <td>en</td>
      <td>2</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>2</th>
      <th>urs</th>
      <th>ɛːz</th>
      <td>en</td>
      <td>2</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>1</td>
      <td></td>
    </tr>
    <tr>
      <th>2</th>
      <th>1</th>
      <th>hours</th>
      <th>'aʊrz</th>
      <td>en</td>
      <td>2</td>
      <td>1</td>
      <td>1</td>
      <td></td>
      <td></td>
      <td></td>
    </tr>
    <tr>
      <th>3</th>
      <th>,</th>
      <th>0</th>
      <th>0</th>
      <th></th>
      <th></th>
      <td>en</td>
      <td>0</td>
      <td></td>
      <td></td>
      <td></td>
      <td></td>
      <td>1</td>
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
      <th>...</th>
      <th>...</th>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
    </tr>
    <tr>
      <th rowspan="5" valign="top">14</th>
      <th rowspan="5" valign="top">Leese but their show; their substance still lives sweet.</th>
      <th rowspan="5" valign="top">1</th>
      <th rowspan="5" valign="top">1</th>
      <th>7</th>
      <th>substance</th>
      <th>1</th>
      <th>2</th>
      <th>tance</th>
      <th>stəns</th>
      <td>en</td>
      <td>1</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>1</td>
      <td></td>
    </tr>
    <tr>
      <th>8</th>
      <th>still</th>
      <th>1</th>
      <th>1</th>
      <th>still</th>
      <th>'stɪl</th>
      <td>en</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td></td>
      <td></td>
      <td></td>
    </tr>
    <tr>
      <th>9</th>
      <th>lives</th>
      <th>1</th>
      <th>1</th>
      <th>lives</th>
      <th>'lɪvz</th>
      <td>en</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td></td>
      <td></td>
      <td></td>
    </tr>
    <tr>
      <th>10</th>
      <th>sweet</th>
      <th>1</th>
      <th>1</th>
      <th>sweet</th>
      <th>'swiːt</th>
      <td>en</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td></td>
      <td></td>
      <td></td>
    </tr>
    <tr>
      <th>11</th>
      <th>.</th>
      <th>0</th>
      <th>0</th>
      <th></th>
      <th></th>
      <td>en</td>
      <td>0</td>
      <td></td>
      <td></td>
      <td></td>
      <td></td>
      <td>1</td>
    </tr>
  </tbody>
</table>
<p>195 rows × 7 columns</p>
</div>




```python
# get lines
first_line = text.lines[0]
last_line = text.lines[-1]
random_line = text.line_r
random_line
```




<div>
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
      <th>word_lang</th>
      <th>word_num_forms</th>
      <th>syll_is_stressed</th>
      <th>syll_is_heavy</th>
      <th>syll_is_strong</th>
      <th>syll_is_weak</th>
      <th>word_is_punc</th>
    </tr>
    <tr>
      <th>line_num</th>
      <th>line_txt</th>
      <th>sent_num</th>
      <th>sentpart_num</th>
      <th>wordtoken_num</th>
      <th>wordtoken_txt</th>
      <th>wordform_num</th>
      <th>syll_num</th>
      <th>syll_txt</th>
      <th>syll_ipa</th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th rowspan="11" valign="top">5</th>
      <th rowspan="11" valign="top">For never-resting time leads summer on</th>
      <th rowspan="11" valign="top">1</th>
      <th rowspan="11" valign="top">1</th>
      <th>1</th>
      <th>\nFor</th>
      <th>1</th>
      <th>1</th>
      <th>For</th>
      <th>fɔːr</th>
      <td>en</td>
      <td>1</td>
      <td>0</td>
      <td>1</td>
      <td></td>
      <td></td>
      <td></td>
    </tr>
    <tr>
      <th rowspan="2" valign="top">2</th>
      <th rowspan="2" valign="top">never</th>
      <th rowspan="2" valign="top">1</th>
      <th>1</th>
      <th>ne</th>
      <th>'nɛ</th>
      <td>en</td>
      <td>1</td>
      <td>1</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>2</th>
      <th>ver</th>
      <th>vɛː</th>
      <td>en</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td></td>
    </tr>
    <tr>
      <th>3</th>
      <th>-</th>
      <th>0</th>
      <th>0</th>
      <th></th>
      <th></th>
      <td>en</td>
      <td>0</td>
      <td></td>
      <td></td>
      <td></td>
      <td></td>
      <td>1</td>
    </tr>
    <tr>
      <th rowspan="2" valign="top">4</th>
      <th rowspan="2" valign="top">resting</th>
      <th rowspan="2" valign="top">1</th>
      <th>1</th>
      <th>res</th>
      <th>'rɛ</th>
      <td>en</td>
      <td>1</td>
      <td>1</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>2</th>
      <th>ting</th>
      <th>stɪŋ</th>
      <td>en</td>
      <td>1</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>1</td>
      <td></td>
    </tr>
    <tr>
      <th>5</th>
      <th>time</th>
      <th>1</th>
      <th>1</th>
      <th>time</th>
      <th>'taɪm</th>
      <td>en</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td></td>
      <td></td>
      <td></td>
    </tr>
    <tr>
      <th>6</th>
      <th>leads</th>
      <th>1</th>
      <th>1</th>
      <th>leads</th>
      <th>'liːdz</th>
      <td>en</td>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td></td>
      <td></td>
      <td></td>
    </tr>
    <tr>
      <th rowspan="2" valign="top">7</th>
      <th rowspan="2" valign="top">summer</th>
      <th rowspan="2" valign="top">1</th>
      <th>1</th>
      <th>sum</th>
      <th>'sə</th>
      <td>en</td>
      <td>1</td>
      <td>1</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td></td>
    </tr>
    <tr>
      <th>2</th>
      <th>mer</th>
      <th>mɛː</th>
      <td>en</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td></td>
    </tr>
    <tr>
      <th>8</th>
      <th>on</th>
      <th>1</th>
      <th>1</th>
      <th>on</th>
      <th>ɑn</th>
      <td>en</td>
      <td>1</td>
      <td>0</td>
      <td>1</td>
      <td></td>
      <td></td>
      <td></td>
    </tr>
  </tbody>
</table>
</div>




```python
# show all known data under an entity
random_line.show()
```

    Line(num=5, txt='For never-resting time leads summer on')
    |
    |   WordToken(num=1, txt='\nFor', sent_num=1, sentpart_num=1)
    |       WordType(num=1, txt='For', lang='en', num_forms=1)
    |           WordForm(num=1, txt='For')
    |               Syllable(ipa='fɔːr', num=1, txt='For', is_stressed=False, is_heavy=True)
    |
    |   WordToken(num=2, txt=' never', sent_num=1, sentpart_num=1)
    |       WordType(num=1, txt='never', lang='en', num_forms=1)
    |           WordForm(num=1, txt='never')
    |               Syllable(ipa="'nɛ", num=1, txt='ne', is_stressed=True, is_heavy=False, is_strong=True, is_weak=False)
    |               Syllable(ipa='vɛː', num=2, txt='ver', is_stressed=False, is_heavy=False, is_strong=False, is_weak=True)
    |
    |   WordToken(num=3, txt='-', sent_num=1, sentpart_num=1)
    |       WordType(num=1, txt='-', lang='en', num_forms=0, is_punc=True)
    |
    |   WordToken(num=4, txt='resting', sent_num=1, sentpart_num=1)
    |       WordType(num=1, txt='resting', lang='en', num_forms=1)
    |           WordForm(num=1, txt='resting')
    |               Syllable(ipa="'rɛ", num=1, txt='res', is_stressed=True, is_heavy=False, is_strong=True, is_weak=False)
    |               Syllable(ipa='stɪŋ', num=2, txt='ting', is_stressed=False, is_heavy=True, is_strong=False, is_weak=True)
    |
    |   WordToken(num=5, txt=' time', sent_num=1, sentpart_num=1)
    |       WordType(num=1, txt='time', lang='en', num_forms=1)
    |           WordForm(num=1, txt='time')
    |               Syllable(ipa="'taɪm", num=1, txt='time', is_stressed=True, is_heavy=True)
    |
    |   WordToken(num=6, txt=' leads', sent_num=1, sentpart_num=1)
    |       WordType(num=1, txt='leads', lang='en', num_forms=1)
    |           WordForm(num=1, txt='leads')
    |               Syllable(ipa="'liːdz", num=1, txt='leads', is_stressed=True, is_heavy=True)
    |
    |   WordToken(num=7, txt=' summer', sent_num=1, sentpart_num=1)
    |       WordType(num=1, txt='summer', lang='en', num_forms=1)
    |           WordForm(num=1, txt='summer')
    |               Syllable(ipa="'sə", num=1, txt='sum', is_stressed=True, is_heavy=False, is_strong=True, is_weak=False)
    |               Syllable(ipa='mɛː', num=2, txt='mer', is_stressed=False, is_heavy=False, is_strong=False, is_weak=True)
    |
    |   WordToken(num=8, txt=' on', sent_num=1, sentpart_num=1)
    |       WordType(num=1, txt='on', lang='en', num_forms=1)
    |           WordForm(num=1, txt='on')
    |               Syllable(ipa='ɑn', num=1, txt='on', is_stressed=False, is_heavy=True)


#### Parsing


```python
# best to set the meter at top level but can be set elsewhre
text.set_meter(
    max_w=2,
    max_s=2,
    constraints=(
        'w_peak',
        's_trough',
        'w_stress',
        's_unstress',
        'unres_across',
        'unres_within',
        'foot_size',
    ),
    resolve_optionality=True
)
```

    [32m2023-12-10 22:44:41.267[0m | [36mget_meter[0m | [34m[1msetting meter to: Meter(constraints=('w_peak', 's_trough', 'w_stress', 's_unstress', 'unres_across', 'unres_within', 'foot_size'), categorical_constraints=(), max_s=2, max_w=2, resolve_optionality=True)[0m | [36mtexts.py[0m:[36m73[0m



```python
# parse a single line
first_line.parse()
```




<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th>parse_score</th>
      <th>parse_is_bounded</th>
      <th>meterpos_num_slots</th>
      <th>*w_peak</th>
      <th>meterslot_s_trough</th>
      <th>*w_stress</th>
      <th>*s_unstress</th>
      <th>*unres_across</th>
      <th>*unres_within</th>
      <th>*foot_size</th>
    </tr>
    <tr>
      <th>stanza_num</th>
      <th>line_num</th>
      <th>parse_rank</th>
      <th>parse_txt</th>
      <th>parse_meter</th>
      <th>parse_stress</th>
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
    </tr>
  </thead>
  <tbody>
    <tr>
      <th rowspan="3" valign="top">1</th>
      <th rowspan="3" valign="top">1</th>
      <th>1</th>
      <th>those HO urs THAT with GEN tle WORK did FRAME</th>
      <th>-+-+-+-+-+</th>
      <th>-+-+-+-+-+</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>10</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>2</th>
      <th>those HOURS that.with GEN tle WORK did FRAME</th>
      <th>-+--+-+-+</th>
      <th>-+--+-+-+</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>11</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>3</th>
      <th>those HOURS that.with GEN tle WORK did FRAME</th>
      <th>-+--+-+-+</th>
      <th>-+--+-+-+</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>11</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
  </tbody>
</table>
</div>




```python
# that shows its best (or unbounded) parses
assert first_line.parse() is first_line.parses is first_line.unbounded_parses
```


```python
# can also see the best parse directly
first_line.best_parse
```




Parse(stanza_num=1, line_num=1, txt='those HO urs THAT with GEN tle WORK did FRAME', rank=1, meter='-+-+-+-+-+', stress='-+-+-+-+-+', score=0, is_bounded=0)




```python
# or look at it by syll
first_line.best_parse.df
```




<div>
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
      <th>parse_score</th>
      <th>parse_is_bounded</th>
      <th>meterpos_num_slots</th>
      <th>*w_peak</th>
      <th>meterslot_s_trough</th>
      <th>*w_stress</th>
      <th>*s_unstress</th>
      <th>*unres_across</th>
      <th>*unres_within</th>
      <th>*foot_size</th>
    </tr>
    <tr>
      <th>stanza_num</th>
      <th>line_num</th>
      <th>parse_rank</th>
      <th>parse_txt</th>
      <th>parse_meter</th>
      <th>parse_stress</th>
      <th>meterpos_num</th>
      <th>meterpos_val</th>
      <th>meterslot_num</th>
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
    </tr>
  </thead>
  <tbody>
    <tr>
      <th rowspan="10" valign="top">1</th>
      <th rowspan="10" valign="top">1</th>
      <th rowspan="10" valign="top">1</th>
      <th rowspan="10" valign="top">those HO urs THAT with GEN tle WORK did FRAME</th>
      <th rowspan="10" valign="top">-+-+-+-+-+</th>
      <th rowspan="10" valign="top">-+-+-+-+-+</th>
      <th>1</th>
      <th>w</th>
      <th>1</th>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>2</th>
      <th>s</th>
      <th>2</th>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>3</th>
      <th>w</th>
      <th>3</th>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>4</th>
      <th>s</th>
      <th>4</th>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>5</th>
      <th>w</th>
      <th>5</th>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>6</th>
      <th>s</th>
      <th>6</th>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>7</th>
      <th>w</th>
      <th>7</th>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>8</th>
      <th>s</th>
      <th>8</th>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>9</th>
      <th>w</th>
      <th>9</th>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>10</th>
      <th>s</th>
      <th>10</th>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
  </tbody>
</table>
</div>




```python
# or look at all first line's best parses by syll
first_line.parses.df_syll
```




<div>
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
      <th>parselist_num_parses</th>
      <th>parselist_num_all_parses</th>
      <th>parse_score</th>
      <th>parse_is_bounded</th>
      <th>meterpos_num_slots</th>
      <th>*w_peak</th>
      <th>meterslot_s_trough</th>
      <th>*w_stress</th>
      <th>*s_unstress</th>
      <th>*unres_across</th>
      <th>*unres_within</th>
      <th>*foot_size</th>
    </tr>
    <tr>
      <th>stanza_num</th>
      <th>line_num</th>
      <th>parse_rank</th>
      <th>parse_txt</th>
      <th>parse_meter</th>
      <th>parse_stress</th>
      <th>meterpos_num</th>
      <th>meterpos_val</th>
      <th>meterslot_num</th>
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
    </tr>
  </thead>
  <tbody>
    <tr>
      <th rowspan="28" valign="top">1</th>
      <th rowspan="28" valign="top">1</th>
      <th rowspan="10" valign="top">1</th>
      <th rowspan="10" valign="top">those HO urs THAT with GEN tle WORK did FRAME</th>
      <th rowspan="10" valign="top">-+-+-+-+-+</th>
      <th rowspan="10" valign="top">-+-+-+-+-+</th>
      <th>1</th>
      <th>w</th>
      <th>1</th>
      <td>3</td>
      <td>3</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>2</th>
      <th>s</th>
      <th>2</th>
      <td>3</td>
      <td>3</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>3</th>
      <th>w</th>
      <th>3</th>
      <td>3</td>
      <td>3</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>4</th>
      <th>s</th>
      <th>4</th>
      <td>3</td>
      <td>3</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>5</th>
      <th>w</th>
      <th>5</th>
      <td>3</td>
      <td>3</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>6</th>
      <th>s</th>
      <th>6</th>
      <td>3</td>
      <td>3</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>7</th>
      <th>w</th>
      <th>7</th>
      <td>3</td>
      <td>3</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>8</th>
      <th>s</th>
      <th>8</th>
      <td>3</td>
      <td>3</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>9</th>
      <th>w</th>
      <th>9</th>
      <td>3</td>
      <td>3</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>10</th>
      <th>s</th>
      <th>10</th>
      <td>3</td>
      <td>3</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th rowspan="9" valign="top">2</th>
      <th rowspan="9" valign="top">those HOURS that.with GEN tle WORK did FRAME</th>
      <th rowspan="9" valign="top">-+--+-+-+</th>
      <th rowspan="9" valign="top">-+--+-+-+</th>
      <th>1</th>
      <th>w</th>
      <th>1</th>
      <td>3</td>
      <td>3</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>2</th>
      <th>s</th>
      <th>2</th>
      <td>3</td>
      <td>3</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th rowspan="2" valign="top">3</th>
      <th rowspan="2" valign="top">w</th>
      <th>3</th>
      <td>3</td>
      <td>3</td>
      <td>0</td>
      <td>0</td>
      <td>2</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>4</th>
      <td>3</td>
      <td>3</td>
      <td>0</td>
      <td>0</td>
      <td>2</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>4</th>
      <th>s</th>
      <th>5</th>
      <td>3</td>
      <td>3</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>5</th>
      <th>w</th>
      <th>6</th>
      <td>3</td>
      <td>3</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>6</th>
      <th>s</th>
      <th>7</th>
      <td>3</td>
      <td>3</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>7</th>
      <th>w</th>
      <th>8</th>
      <td>3</td>
      <td>3</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>8</th>
      <th>s</th>
      <th>9</th>
      <td>3</td>
      <td>3</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th rowspan="9" valign="top">3</th>
      <th rowspan="9" valign="top">those HOURS that.with GEN tle WORK did FRAME</th>
      <th rowspan="9" valign="top">-+--+-+-+</th>
      <th rowspan="9" valign="top">-+--+-+-+</th>
      <th>1</th>
      <th>w</th>
      <th>1</th>
      <td>3</td>
      <td>3</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>2</th>
      <th>s</th>
      <th>2</th>
      <td>3</td>
      <td>3</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th rowspan="2" valign="top">3</th>
      <th rowspan="2" valign="top">w</th>
      <th>3</th>
      <td>3</td>
      <td>3</td>
      <td>0</td>
      <td>0</td>
      <td>2</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>4</th>
      <td>3</td>
      <td>3</td>
      <td>0</td>
      <td>0</td>
      <td>2</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>4</th>
      <th>s</th>
      <th>5</th>
      <td>3</td>
      <td>3</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>5</th>
      <th>w</th>
      <th>6</th>
      <td>3</td>
      <td>3</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>6</th>
      <th>s</th>
      <th>7</th>
      <td>3</td>
      <td>3</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>7</th>
      <th>w</th>
      <th>8</th>
      <td>3</td>
      <td>3</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>8</th>
      <th>s</th>
      <th>9</th>
      <td>3</td>
      <td>3</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
  </tbody>
</table>
</div>




```python
# parse the whole sonnet and return the best parses
text.parse()
```

    Parsing lines: 100%|██████████| 14/14 [00:02<00:00,  5.45it/s]





<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th>parse_score</th>
      <th>parse_is_bounded</th>
      <th>meterpos_num_slots</th>
      <th>*w_peak</th>
      <th>meterslot_s_trough</th>
      <th>*w_stress</th>
      <th>*s_unstress</th>
      <th>*unres_across</th>
      <th>*unres_within</th>
      <th>*foot_size</th>
    </tr>
    <tr>
      <th>stanza_num</th>
      <th>line_num</th>
      <th>parse_rank</th>
      <th>parse_txt</th>
      <th>parse_meter</th>
      <th>parse_stress</th>
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
    </tr>
  </thead>
  <tbody>
    <tr>
      <th rowspan="14" valign="top">1</th>
      <th>1</th>
      <th>1</th>
      <th>those HO urs THAT with GEN tle WORK did FRAME</th>
      <th>-+-+-+-+-+</th>
      <th>-+-+-+-+-+</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>10</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>2</th>
      <th>1</th>
      <th>the LO vely GAZE where E very EYE doth DWELL</th>
      <th>-+-+-+-+-+</th>
      <th>-+-+-+-+-+</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>10</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>3</th>
      <th>1</th>
      <th>will PLAY the TY rants TO the VE ry SAME</th>
      <th>-+-+-+-+-+</th>
      <th>-+-+---+-+</th>
      <td>1.0</td>
      <td>0.0</td>
      <td>10</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>4</th>
      <th>1</th>
      <th>and THAT un FAIR which FAIR ly DOTH ex CEL</th>
      <th>-+-+-+-+-+</th>
      <th>-+-+-+---+</th>
      <td>1.0</td>
      <td>0.0</td>
      <td>10</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>5</th>
      <th>1</th>
      <th>for NE ver RES ting TIME leads SUM mer ON</th>
      <th>-+-+-+-+-+</th>
      <th>-+-+-+++--</th>
      <td>2.0</td>
      <td>0.0</td>
      <td>10</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>6</th>
      <th>1</th>
      <th>to HI deo.us WIN ter AND con FOUNDS him.there</th>
      <th>-+--+-+-+--</th>
      <th>-+--+---+--</th>
      <td>2.0</td>
      <td>0.0</td>
      <td>15</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
    </tr>
    <tr>
      <th>7</th>
      <th>1</th>
      <th>sap CHECKED with FROST and LUS ty LEAVES quite GONE</th>
      <th>-+-+-+-+-+</th>
      <th>++-+-+-+++</th>
      <td>2.0</td>
      <td>0.0</td>
      <td>10</td>
      <td>0</td>
      <td>0</td>
      <td>2</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>8</th>
      <th>1</th>
      <th>BEA uty.o'er SNOWED and BA reness E very WHERE</th>
      <th>+--+-+-+-+</th>
      <th>+--+-+-+-+</th>
      <td>2.0</td>
      <td>0.0</td>
      <td>12</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>2</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>9</th>
      <th>1</th>
      <th>THEN were.not SUM mer's DIS til LA tion LEFT</th>
      <th>+--+-+-+-+</th>
      <th>+--+-+-+-+</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>12</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>10</th>
      <th>1</th>
      <th>a LI quid PRI soner PENT in WALLS of GLASS</th>
      <th>-+-+-+-+-+</th>
      <th>-+-+-+-+-+</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>10</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>11</th>
      <th>1</th>
      <th>BEA uty's.ef FECT with BEA uty WERE be REFT</th>
      <th>+--+-+-+-+</th>
      <th>+--+-+---+</th>
      <td>3.0</td>
      <td>0.0</td>
      <td>12</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>2</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>12</th>
      <th>1</th>
      <th>nor IT nor NO re MEM brance WHAT it.was</th>
      <th>-+-+-+-+--</th>
      <th>-+-+-+-+--</th>
      <td>0.0</td>
      <td>0.0</td>
      <td>12</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>13</th>
      <th>1</th>
      <th>but FLO wers.dis TILL'D though THEY with WIN ter MEET</th>
      <th>-+--+-+-+-+</th>
      <th>-+--+-+-+-+</th>
      <td>2.0</td>
      <td>0.0</td>
      <td>13</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>2</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>14</th>
      <th>1</th>
      <th>LEESE but.their SHOW their SUBS tance STILL lives SWEET</th>
      <th>+--+-+-+-+</th>
      <th>+--+-+-+++</th>
      <td>1.0</td>
      <td>0.0</td>
      <td>12</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
  </tbody>
</table>
</div>




```python
# this is the same as what's now stored on text.best_parses
assert text.parse() is text.parses is text.best_parses
```

    Parsing lines: 100%|██████████| 14/14 [00:00<00:00, 56516.13it/s]



```python
# show the same data by syllable
text.parses.df_syll
```




<div>
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
      <th>parselist_num_parses</th>
      <th>parselist_num_all_parses</th>
      <th>parse_score</th>
      <th>parse_is_bounded</th>
      <th>meterpos_num_slots</th>
      <th>*w_peak</th>
      <th>meterslot_s_trough</th>
      <th>*w_stress</th>
      <th>*s_unstress</th>
      <th>*unres_across</th>
      <th>*unres_within</th>
      <th>*foot_size</th>
    </tr>
    <tr>
      <th>stanza_num</th>
      <th>line_num</th>
      <th>parse_rank</th>
      <th>parse_txt</th>
      <th>parse_meter</th>
      <th>parse_stress</th>
      <th>meterpos_num</th>
      <th>meterpos_val</th>
      <th>meterslot_num</th>
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
    </tr>
  </thead>
  <tbody>
    <tr>
      <th rowspan="11" valign="top">1</th>
      <th rowspan="5" valign="top">1</th>
      <th rowspan="5" valign="top">1</th>
      <th rowspan="5" valign="top">those HO urs THAT with GEN tle WORK did FRAME</th>
      <th rowspan="5" valign="top">-+-+-+-+-+</th>
      <th rowspan="5" valign="top">-+-+-+-+-+</th>
      <th>1</th>
      <th>w</th>
      <th>1</th>
      <td>14</td>
      <td>14</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>2</th>
      <th>s</th>
      <th>2</th>
      <td>14</td>
      <td>14</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>3</th>
      <th>w</th>
      <th>3</th>
      <td>14</td>
      <td>14</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>4</th>
      <th>s</th>
      <th>4</th>
      <td>14</td>
      <td>14</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>5</th>
      <th>w</th>
      <th>5</th>
      <td>14</td>
      <td>14</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
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
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
    </tr>
    <tr>
      <th rowspan="5" valign="top">14</th>
      <th rowspan="5" valign="top">1</th>
      <th rowspan="5" valign="top">LEESE but.their SHOW their SUBS tance STILL lives SWEET</th>
      <th rowspan="5" valign="top">+--+-+-+-+</th>
      <th rowspan="5" valign="top">+--+-+-+++</th>
      <th>5</th>
      <th>s</th>
      <th>6</th>
      <td>14</td>
      <td>14</td>
      <td>1</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>6</th>
      <th>w</th>
      <th>7</th>
      <td>14</td>
      <td>14</td>
      <td>1</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>7</th>
      <th>s</th>
      <th>8</th>
      <td>14</td>
      <td>14</td>
      <td>1</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>8</th>
      <th>w</th>
      <th>9</th>
      <td>14</td>
      <td>14</td>
      <td>1</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>9</th>
      <th>s</th>
      <th>10</th>
      <td>14</td>
      <td>14</td>
      <td>1</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
  </tbody>
</table>
<p>142 rows × 12 columns</p>
</div>




```python
# get parse statistics
df_stats = text.parses.stats()

# normalize line lengths by converting each value to a value-per-10syll
df_stats_norm = text.parses.stats(norm=True)
df_stats_norm.sort_values('n_viols')
```




<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th>bestparse_nsylls</th>
      <th>n_combo</th>
      <th>n_parse</th>
      <th>n_viols</th>
      <th>*w_peak</th>
      <th>*s_trough</th>
      <th>*w_stress</th>
      <th>*s_unstress</th>
      <th>*unres_across</th>
      <th>*unres_within</th>
      <th>*foot_size</th>
      <th>n_w_peak</th>
      <th>n_s_trough</th>
      <th>n_w_stress</th>
      <th>n_s_unstress</th>
      <th>n_unres_across</th>
      <th>n_unres_within</th>
      <th>n_foot_size</th>
    </tr>
    <tr>
      <th>stanza_num</th>
      <th>line_num</th>
      <th>line_txt</th>
      <th>bestparse_txt</th>
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
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th rowspan="14" valign="top">1</th>
      <th>1</th>
      <th>Those hours, that with gentle work did frame</th>
      <th>those HO urs THAT with GEN tle WORK did FRAME</th>
      <td>10</td>
      <td>12</td>
      <td>1</td>
      <td>0.000000</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>0.0</td>
    </tr>
    <tr>
      <th>9</th>
      <th>Then were not summer's distillation left,</th>
      <th>THEN were.not SUM mer's DIS til LA tion LEFT</th>
      <td>10</td>
      <td>4</td>
      <td>1</td>
      <td>0.000000</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>0.0</td>
    </tr>
    <tr>
      <th>12</th>
      <th>Nor it, nor no remembrance what it was:</th>
      <th>nor IT nor NO re MEM brance WHAT it.was</th>
      <td>10</td>
      <td>8</td>
      <td>1</td>
      <td>0.000000</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>0.0</td>
    </tr>
    <tr>
      <th>10</th>
      <th>A liquid prisoner pent in walls of glass,</th>
      <th>a LI quid PRI soner PENT in WALLS of GLASS</th>
      <td>10</td>
      <td>4</td>
      <td>1</td>
      <td>0.133929</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.000000</td>
      <td>0.312500</td>
      <td>0.000000</td>
      <td>0.312500</td>
      <td>0.000000</td>
      <td>0.312500</td>
      <td>0.0</td>
    </tr>
    <tr>
      <th>3</th>
      <th>Will play the tyrants to the very same</th>
      <th>will PLAY the TY rants TO the VE ry SAME</th>
      <td>10</td>
      <td>1</td>
      <td>1</td>
      <td>0.142857</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>1.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>1.000000</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>0.0</td>
    </tr>
    <tr>
      <th>4</th>
      <th>And that unfair which fairly doth excel;</th>
      <th>and THAT un FAIR which FAIR ly DOTH ex CEL</th>
      <td>10</td>
      <td>18</td>
      <td>1</td>
      <td>0.142857</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>1.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>1.000000</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>0.0</td>
    </tr>
    <tr>
      <th>14</th>
      <th>Leese but their show; their substance still lives sweet.</th>
      <th>LEESE but.their SHOW their SUBS tance STILL lives SWEET</th>
      <td>10</td>
      <td>4</td>
      <td>1</td>
      <td>0.142857</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>1.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>1.000000</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>0.0</td>
    </tr>
    <tr>
      <th>2</th>
      <th>The lovely gaze where every eye doth dwell,</th>
      <th>the LO vely GAZE where E very EYE doth DWELL</th>
      <td>10</td>
      <td>4</td>
      <td>1</td>
      <td>0.199336</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.5</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.000000</td>
      <td>0.232558</td>
      <td>0.000000</td>
      <td>0.465116</td>
      <td>0.465116</td>
      <td>0.232558</td>
      <td>0.0</td>
    </tr>
    <tr>
      <th>5</th>
      <th>For never-resting time leads summer on</th>
      <th>for NE ver RES ting TIME leads SUM mer ON</th>
      <td>10</td>
      <td>1</td>
      <td>1</td>
      <td>0.357143</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>1.0</td>
      <td>0.5</td>
      <td>1.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>1.000000</td>
      <td>0.500000</td>
      <td>1.000000</td>
      <td>0.000000</td>
      <td>0.0</td>
    </tr>
    <tr>
      <th>7</th>
      <th>Sap checked with frost, and lusty leaves quite gone,</th>
      <th>sap CHECKED with FROST and LUS ty LEAVES quite GONE</th>
      <td>10</td>
      <td>1</td>
      <td>1</td>
      <td>0.357143</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>1.5</td>
      <td>0.0</td>
      <td>1.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.000000</td>
      <td>0.000000</td>
      <td>1.500000</td>
      <td>0.000000</td>
      <td>1.000000</td>
      <td>0.000000</td>
      <td>0.0</td>
    </tr>
    <tr>
      <th>6</th>
      <th>To hideous winter, and confounds him there;</th>
      <th>to HI deo.us WIN ter AND con FOUNDS him.there</th>
      <td>11</td>
      <td>2</td>
      <td>1</td>
      <td>0.389610</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>2.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.000000</td>
      <td>0.303030</td>
      <td>0.000000</td>
      <td>1.515152</td>
      <td>0.606061</td>
      <td>0.303030</td>
      <td>0.0</td>
    </tr>
    <tr>
      <th>13</th>
      <th>But flowers distill'd, though they with winter meet,</th>
      <th>but FLO wers.dis TILL'D though THEY with WIN ter MEET</th>
      <td>11</td>
      <td>2</td>
      <td>1</td>
      <td>0.422078</td>
      <td>0.0</td>
      <td>1.0</td>
      <td>0.0</td>
      <td>1.0</td>
      <td>0.0</td>
      <td>0.5</td>
      <td>0.0</td>
      <td>0.227273</td>
      <td>0.681818</td>
      <td>0.227273</td>
      <td>0.909091</td>
      <td>0.454545</td>
      <td>0.454545</td>
      <td>0.0</td>
    </tr>
    <tr>
      <th>11</th>
      <th>Beauty's effect with beauty were bereft,</th>
      <th>BEA uty's.ef FECT with BEA uty WERE be REFT</th>
      <td>10</td>
      <td>2</td>
      <td>1</td>
      <td>0.500000</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>1.5</td>
      <td>1.0</td>
      <td>0.0</td>
      <td>0.0</td>
      <td>0.250000</td>
      <td>0.250000</td>
      <td>0.250000</td>
      <td>1.500000</td>
      <td>1.000000</td>
      <td>0.250000</td>
      <td>0.0</td>
    </tr>
    <tr>
      <th>8</th>
      <th>Beauty o'er-snowed and bareness every where:</th>
      <th>BEA uty.o'er SNOWED and BA reness E very WHERE</th>
      <td>10</td>
      <td>4</td>
      <td>1</td>
      <td>0.760534</td>
      <td>0.0</td>
      <td>1.0</td>
      <td>0.0</td>
      <td>2.0</td>
      <td>0.0</td>
      <td>1.0</td>
      <td>0.0</td>
      <td>0.503597</td>
      <td>0.647482</td>
      <td>0.863309</td>
      <td>1.654676</td>
      <td>1.007194</td>
      <td>0.647482</td>
      <td>0.0</td>
    </tr>
  </tbody>
</table>
</div>




```python
# forcefully parse a phrase
line_str = 'A horse, a horse, my kingdom for a horse!'
iambic_parse = ps.Parse(line_str, scansion='wswswsws')
trochaic_parse = ps.Parse(line_str, scansion='swswswswsw')

# assert iambic is a better fit
iambic_parse < trochaic_parse
```




    True




```python
# inspect iambic
iambic_parse
```




Parse(txt='a HORSE a HORSE my KING dom FOR', meter='-+-+-+-+', stress='-+-+-+--', score=1, is_bounded=0)




```python
# inspect trochaic
trochaic_parse
```




Parse(txt='A horse A horse MY king DOM for A horse', meter='+-+-+-+-+-', stress='-+-+-+---+', score=10, is_bounded=0)


