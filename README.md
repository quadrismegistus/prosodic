# Prosodic

[![codecov](https://codecov.io/github/quadrismegistus/prosodic/graph/badge.svg?token=t8VZMSMR4u)](https://codecov.io/github/quadrismegistus/prosodic)

Prosodic is a metrical-phonological parser written in Python. Currently, it can parse English and Finnish text, but adding additional languages is easy with a pronunciation dictionary or a custom python function. Prosodic was built by [Ryan Heuser](https://github.com/quadrismegistus), [Josh Falk](https://github.com/jsfalk), and [Arto Anttila](http://web.stanford.edu/~anttila/). Josh also maintains [another repository](https://github.com/jsfalk/prosodic1b), in which he has rewritten the part of this project that does phonetic transcription for English and Finnish. [Sam Bowman](https://github.com/sleepinyourhat) has contributed to the codebase as well, adding several new metrical constraints.

This version, Prosodic 2.x, is a near-total rewrite of the original Prosodic.

Supports Python>=3.9.

## [Demo](https://prosodic.dev/)

You can view and use a web app demo of the current Prosodic app at **[prosodic.dev](https://prosodic.dev/)**.


## Install

### 1. Install python package

Install from pypi:

```
pip install prosodic
```


### 2. Install espeak

Install [espeak](https://espeak.sourceforge.net), free text-to-speak (TTS) software, to ‘sound out’ unknown words.

* *Mac*: `brew install espeak`. (First install [homebrew](brew.sh) if not already installed.)

* *Linux*: `apt-get install espeak libespeak1 libespeak-dev`

* *Windows*: Download and install from [github](https://github.com/espeak-ng/espeak-ng/releases/latest)

## Usage

### Web app

Prosodic has a new GUI (graphical user interface) in a web app. After installing, run:

```
prosodic web
```

Then navigate to [http://127.0.0.1:8181/](http://127.0.0.1:8181/). It should look like this:

<img width="900" alt="prosodic-web-preview-3" src="https://github.com/user-attachments/assets/d34278fd-a28e-4337-9bcf-8c3c57992bc2">


### Python

#### Read texts


```python
# import prosodic
import prosodic

# load a text
sonnet = prosodic.Text("""
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

# can also load by filename
shaksonnets = prosodic.Text(fn='corpora/corppoetry_en/en.shakespeare.txt')
```

#### Stanzas, lines, words, syllables, phonemes

Texts in prosodic are organized into a tree structure. The `.children` of a `Text` object is a list of `Stanza`'s, whose `.parent` objects point back to the `Text`. In turn, in each stanza's `.children` is a list of `Line`'s, whose `.parent`'s point back to the stanza; so on down the tree.


```python
# Take a peek at this tree structure 
# and the features particular entities have
sonnet.show(maxlines=30, incl_phons=True)
```

    Text()
    |   Stanza(num=1)
    |       Line(num=1, txt='Those hours, that with gentle work did frame')
    |           WordToken(num=1, txt='Those', sent_num=1, sentpart_num=1)
    |               WordType(num=1, txt='Those', lang='en', num_forms=1)
    |                   WordForm(num=1, txt='Those')
    |                       Syllable(ipa='ðoʊz', num=1, txt='Those', is_stressed=False, is_heavy=True)
    |                           Phoneme(num=1, txt='ð', syl=-1, son=-1, cons=1, cont=1, delrel=-1, lat=-1, nas=-1, strid=0, voi=1, sg=-1, cg=-1, ant=1, cor=1, distr=1, lab=-1, hi=-1, lo=-1, back=-1, round=-1, velaric=-1, tense=0, long=-1, hitone=0, hireg=0)
    |                           Phoneme(num=3, txt='o', syl=1, son=1, cons=-1, cont=1, delrel=-1, lat=-1, nas=-1, strid=0, voi=1, sg=-1, cg=-1, ant=0, cor=-1, distr=0, lab=-1, hi=-1, lo=-1, back=1, round=1, velaric=-1, tense=1, long=-1, hitone=0, hireg=0)
    |                           Phoneme(num=3, txt='ʊ', syl=1, son=1, cons=-1, cont=1, delrel=-1, lat=-1, nas=-1, strid=0, voi=1, sg=-1, cg=-1, ant=0, cor=-1, distr=0, lab=-1, hi=1, lo=-1, back=1, round=1, velaric=-1, tense=-1, long=-1, hitone=0, hireg=0)
    |                           Phoneme(num=4, txt='z', syl=-1, son=-1, cons=1, cont=1, delrel=-1, lat=-1, nas=-1, strid=0, voi=1, sg=-1, cg=-1, ant=1, cor=1, distr=-1, lab=-1, hi=-1, lo=-1, back=-1, round=-1, velaric=-1, tense=0, long=-1, hitone=0, hireg=0)
    |           WordToken(num=2, txt=' hours', sent_num=1, sentpart_num=1)
    |               WordType(num=1, txt='hours', lang='en', num_forms=2)
    |                   WordForm(num=1, txt='hours')
    |                       Syllable(ipa="'aʊ", num=1, txt='ho', is_stressed=True, is_heavy=True, is_strong=True, is_weak=False)
    |                           Phoneme(num=2, txt='a', syl=1, son=1, cons=-1, cont=1, delrel=-1, lat=-1, nas=-1, strid=0, voi=1, sg=-1, cg=-1, ant=0, cor=-1, distr=0, lab=-1, hi=-1, lo=1, back=-1, round=-1, velaric=-1, tense=1, long=-1, hitone=0, hireg=0)
    |                           Phoneme(num=3, txt='ʊ', syl=1, son=1, cons=-1, cont=1, delrel=-1, lat=-1, nas=-1, strid=0, voi=1, sg=-1, cg=-1, ant=0, cor=-1, distr=0, lab=-1, hi=1, lo=-1, back=1, round=1, velaric=-1, tense=-1, long=-1, hitone=0, hireg=0)
    |                       Syllable(ipa='ɛːz', num=2, txt='urs', is_stressed=False, is_heavy=True, is_strong=False, is_weak=True)
    |                           Phoneme(num=2, txt='ɛː', syl=1, son=1, cons=-1, cont=1, delrel=-1, lat=-1, nas=-1, strid=0, voi=1, sg=-1, cg=-1, ant=0, cor=-1, distr=0, lab=-1, hi=-1, lo=-1, back=-1, round=-1, velaric=-1, tense=-1, long=1, hitone=0, hireg=0)
    |                           Phoneme(num=4, txt='z', syl=-1, son=-1, cons=1, cont=1, delrel=-1, lat=-1, nas=-1, strid=0, voi=1, sg=-1, cg=-1, ant=1, cor=1, distr=-1, lab=-1, hi=-1, lo=-1, back=-1, round=-1, velaric=-1, tense=0, long=-1, hitone=0, hireg=0)
    |                   WordForm(num=2, txt='hours')
    |                       Syllable(ipa="'aʊrz", num=1, txt='hours', is_stressed=True, is_heavy=True)
    |                           Phoneme(num=2, txt='a', syl=1, son=1, cons=-1, cont=1, delrel=-1, lat=-1, nas=-1, strid=0, voi=1, sg=-1, cg=-1, ant=0, cor=-1, distr=0, lab=-1, hi=-1, lo=1, back=-1, round=-1, velaric=-1, tense=1, long=-1, hitone=0, hireg=0)
    |                           Phoneme(num=3, txt='ʊ', syl=1, son=1, cons=-1, cont=1, delrel=-1, lat=-1, nas=-1, strid=0, voi=1, sg=-1, cg=-1, ant=0, cor=-1, distr=0, lab=-1, hi=1, lo=-1, back=1, round=1, velaric=-1, tense=-1, long=-1, hitone=0, hireg=0)
    |                           Phoneme(num=4, txt='r', syl=-1, son=1, cons=1, cont=1, delrel=0, lat=-1, nas=-1, strid=0, voi=1, sg=-1, cg=-1, ant=1, cor=1, distr=-1, lab=-1, hi=0, lo=0, back=0, round=-1, velaric=-1, tense=0, long=-1, hitone=0, hireg=0)
    |                           Phoneme(num=4, txt='z', syl=-1, son=-1, cons=1, cont=1, delrel=-1, lat=-1, nas=-1, strid=0, voi=1, sg=-1, cg=-1, ant=1, cor=1, distr=-1, lab=-1, hi=-1, lo=-1, back=-1, round=-1, velaric=-1, tense=0, long=-1, hitone=0, hireg=0)
    |           WordToken(num=3, txt=',', sent_num=1, sentpart_num=1)
    |               WordType(num=1, txt=',', lang='en', num_forms=0, is_punc=True)
    |           WordToken(num=4, txt=' that', sent_num=1, sentpart_num=1)
    |               WordType(num=1, txt='that', lang='en', num_forms=3)



```python
# take a peek at it in dataframe form
sonnet.df   # by-syllable dataframe representation
sonnet      # ...which will also be shown when text object displayed (in a notebook)
```





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
      <th>word_lang</th>
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
      <th>Those</th>
      <th>en</th>
      <th>1</th>
      <th>1</th>
      <th>Those</th>
      <th>ðoʊz</th>
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
      <th rowspan="3" valign="top">en</th>
      <th rowspan="2" valign="top">1</th>
      <th>1</th>
      <th>ho</th>
      <th>'aʊ</th>
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
      <th>en</th>
      <th>0</th>
      <th>0</th>
      <th></th>
      <th></th>
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
      <th>...</th>
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
      <th>en</th>
      <th>1</th>
      <th>2</th>
      <th>tance</th>
      <th>stəns</th>
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
      <th>en</th>
      <th>1</th>
      <th>1</th>
      <th>still</th>
      <th>'stɪl</th>
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
      <th>en</th>
      <th>1</th>
      <th>1</th>
      <th>lives</th>
      <th>'lɪvz</th>
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
      <th>en</th>
      <th>1</th>
      <th>1</th>
      <th>sweet</th>
      <th>'swiːt</th>
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
      <th>en</th>
      <th>0</th>
      <th>0</th>
      <th></th>
      <th></th>
      <td>0</td>
      <td></td>
      <td></td>
      <td></td>
      <td></td>
      <td>1</td>
    </tr>
  </tbody>
</table>
<p>195 rows × 6 columns</p>
</div>




```python
# you can loop over this directly if you want
for stanza in shaksonnets.stanzas:
    for line in sonnet:
        for wordtoken in line:
            for wordtype in wordtoken:
                for wordform in wordtype:
                    for syllable in wordform:
                        for phoneme in syllable:
                            # ...
                            pass
```


```python
# or directly access components
print(f'''
Shakespeare's sonnets have:
  * {len(shaksonnets.stanzas):,} "stanzas"        (in this text, each one a sonnet)
  * {len(shaksonnets.lines):,} lines
  * {len(shaksonnets.wordtokens):,} wordtokens    (including punctuation)
  * {len(shaksonnets.wordtypes):,} wordtypes     (each token has one wordtype object)
  * {len(shaksonnets.wordforms):,} wordforms     (a word + IPA pronunciation; no punctuation)
  * {len(shaksonnets.syllables):,} syllables
  * {len(shaksonnets.phonemes):,} phonemes
''')
```

    
    Shakespeare's sonnets have:
      * 154 "stanzas"        (in this text, each one a sonnet)
      * 2,155 lines
      * 20,317 wordtokens    (including punctuation)
      * 20,317 wordtypes     (each token has one wordtype object)
      * 17,601 wordforms     (a word + IPA pronunciation; no punctuation)
      * 21,915 syllables
      * 63,614 phonemes
    



```python
# access lines

# text.line{num} will return text.lines[num-1]
assert sonnet.line1 is sonnet.lines[0]
assert sonnet.line10 is sonnet.lines[9]

# show the line
sonnet.line1
```





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
      <th>word_lang</th>
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
    </tr>
  </thead>
  <tbody>
    <tr>
      <th rowspan="11" valign="top">1</th>
      <th rowspan="11" valign="top">Those hours, that with gentle work did frame</th>
      <th rowspan="11" valign="top">1</th>
      <th rowspan="11" valign="top">1</th>
      <th>1</th>
      <th>Those</th>
      <th>en</th>
      <th>1</th>
      <th>1</th>
      <th>Those</th>
      <th>ðoʊz</th>
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
      <th rowspan="3" valign="top">en</th>
      <th rowspan="2" valign="top">1</th>
      <th>1</th>
      <th>ho</th>
      <th>'aʊ</th>
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
      <th>en</th>
      <th>0</th>
      <th>0</th>
      <th></th>
      <th></th>
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
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
    </tr>
    <tr>
      <th>6</th>
      <th>gentle</th>
      <th>en</th>
      <th>1</th>
      <th>2</th>
      <th>tle</th>
      <th>təl</th>
      <td>1</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>1</td>
      <td></td>
    </tr>
    <tr>
      <th>7</th>
      <th>work</th>
      <th>en</th>
      <th>1</th>
      <th>1</th>
      <th>work</th>
      <th>'wɛːk</th>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td></td>
      <td></td>
      <td></td>
    </tr>
    <tr>
      <th rowspan="2" valign="top">8</th>
      <th rowspan="2" valign="top">did</th>
      <th rowspan="2" valign="top">en</th>
      <th>1</th>
      <th>1</th>
      <th>did</th>
      <th>dɪd</th>
      <td>2</td>
      <td>0</td>
      <td>1</td>
      <td></td>
      <td></td>
      <td></td>
    </tr>
    <tr>
      <th>2</th>
      <th>1</th>
      <th>did</th>
      <th>'dɪd</th>
      <td>2</td>
      <td>1</td>
      <td>1</td>
      <td></td>
      <td></td>
      <td></td>
    </tr>
    <tr>
      <th>9</th>
      <th>frame</th>
      <th>en</th>
      <th>1</th>
      <th>1</th>
      <th>frame</th>
      <th>'freɪm</th>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td></td>
      <td></td>
      <td></td>
    </tr>
  </tbody>
</table>
<p>15 rows × 6 columns</p>
</div>




```python
# build lines directly
line_from_richardIII = prosodic.Line('A horse, a horse, my kingdom for a horse!')
line_from_richardIII
```

    [34m[1mtokenizing[0m[36m @ 2023-12-15 14:14:17,991[0m
    [34m[1m⎿ 0 seconds[0m[36m @ 2023-12-15 14:14:17,992[0m






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
      <th>word_num_forms</th>
      <th>syll_is_stressed</th>
      <th>syll_is_heavy</th>
      <th>word_is_punc</th>
      <th>syll_is_strong</th>
      <th>syll_is_weak</th>
    </tr>
    <tr>
      <th>line_txt</th>
      <th>sent_num</th>
      <th>sentpart_num</th>
      <th>wordtoken_num</th>
      <th>wordtoken_txt</th>
      <th>word_lang</th>
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
    </tr>
  </thead>
  <tbody>
    <tr>
      <th rowspan="11" valign="top">A horse, a horse, my kingdom for a horse!</th>
      <th rowspan="11" valign="top">1</th>
      <th rowspan="11" valign="top">1</th>
      <th>1</th>
      <th>A</th>
      <th>en</th>
      <th>1</th>
      <th>1</th>
      <th>A</th>
      <th>eɪ</th>
      <td>1</td>
      <td>0</td>
      <td>1</td>
      <td></td>
      <td></td>
      <td></td>
    </tr>
    <tr>
      <th>2</th>
      <th>horse</th>
      <th>en</th>
      <th>1</th>
      <th>1</th>
      <th>horse</th>
      <th>'hɔːrs</th>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td></td>
      <td></td>
      <td></td>
    </tr>
    <tr>
      <th>3</th>
      <th>,</th>
      <th>en</th>
      <th>0</th>
      <th>0</th>
      <th></th>
      <th></th>
      <td>0</td>
      <td></td>
      <td></td>
      <td>1</td>
      <td></td>
      <td></td>
    </tr>
    <tr>
      <th>4</th>
      <th>a</th>
      <th>en</th>
      <th>1</th>
      <th>1</th>
      <th>a</th>
      <th>eɪ</th>
      <td>1</td>
      <td>0</td>
      <td>1</td>
      <td></td>
      <td></td>
      <td></td>
    </tr>
    <tr>
      <th>5</th>
      <th>horse</th>
      <th>en</th>
      <th>1</th>
      <th>1</th>
      <th>horse</th>
      <th>'hɔːrs</th>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td></td>
      <td></td>
      <td></td>
    </tr>
    <tr>
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
    </tr>
    <tr>
      <th>8</th>
      <th>kingdom</th>
      <th>en</th>
      <th>1</th>
      <th>2</th>
      <th>dom</th>
      <th>dəm</th>
      <td>1</td>
      <td>0</td>
      <td>1</td>
      <td></td>
      <td>0</td>
      <td>1</td>
    </tr>
    <tr>
      <th>9</th>
      <th>for</th>
      <th>en</th>
      <th>1</th>
      <th>1</th>
      <th>for</th>
      <th>fɔːr</th>
      <td>1</td>
      <td>0</td>
      <td>1</td>
      <td></td>
      <td></td>
      <td></td>
    </tr>
    <tr>
      <th>10</th>
      <th>a</th>
      <th>en</th>
      <th>1</th>
      <th>1</th>
      <th>a</th>
      <th>eɪ</th>
      <td>1</td>
      <td>0</td>
      <td>1</td>
      <td></td>
      <td></td>
      <td></td>
    </tr>
    <tr>
      <th>11</th>
      <th>horse</th>
      <th>en</th>
      <th>1</th>
      <th>1</th>
      <th>horse</th>
      <th>'hɔːrs</th>
      <td>1</td>
      <td>1</td>
      <td>1</td>
      <td></td>
      <td></td>
      <td></td>
    </tr>
    <tr>
      <th>12</th>
      <th>!</th>
      <th>en</th>
      <th>0</th>
      <th>0</th>
      <th></th>
      <th></th>
      <td>0</td>
      <td></td>
      <td></td>
      <td>1</td>
      <td></td>
      <td></td>
    </tr>
  </tbody>
</table>
<p>13 rows × 6 columns</p>
</div>



#### Metrical parsing

##### Parsing lines


```python
# parse with default options by just reaching for best parse
plausible_parses = line_from_richardIII.parse()
plausible_parses
```



<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th>parse_score</th>
      <th>parse_is_bounded</th>
      <th>meterpos_num_slots</th>
      <th>*w_peak</th>
      <th>*w_stress</th>
      <th>*s_unstress</th>
      <th>*unres_across</th>
      <th>*unres_within</th>
    </tr>
    <tr>
      <th>line_txt</th>
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
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>A horse, a horse, my kingdom for a horse!</th>
      <th>1</th>
      <th>a HORSE a HORSE my KING dom FOR a HORSE</th>
      <th>-+-+-+-+-+</th>
      <th>-+-+-+---+</th>
      <td>1.0</td>
      <td>0.0</td>
      <td>10</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
    </tr>
  </tbody>
</table>
</div>




```python
# see best parse
line_from_richardIII.best_parse
```




<div class="parse"><span class="meter_weak stress_weak">A</span> <span class="meter_strong stress_strong">horse</span> <span class="meter_weak stress_weak">a</span> <span class="meter_strong stress_strong">horse</span> <span class="meter_weak stress_weak">my</span> <span class="meter_strong stress_strong">king</span><span class="meter_weak stress_weak">dom</span> <span class="meter_strong stress_weak violation">for</span> <span class="meter_weak stress_weak">a</span> <span class="meter_strong stress_strong">horse</span></div><div class="miniquote">⎿ Parse(rank=1, meter='-+-+-+-+-+', stress='-+-+-+---+', score=1, is_bounded=0)</div>




```python
# parse with different options
diff_parses = line_from_richardIII.parse(constraints=('w_peak','s_unstress'))
diff_parses
```




<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th>parse_score</th>
      <th>parse_is_bounded</th>
      <th>meterpos_num_slots</th>
      <th>*w_peak</th>
      <th>*s_unstress</th>
    </tr>
    <tr>
      <th>line_txt</th>
      <th>parse_rank</th>
      <th>parse_txt</th>
      <th>parse_meter</th>
      <th>parse_stress</th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th rowspan="6" valign="top">A horse, a horse, my kingdom for a horse!</th>
      <th>1</th>
      <th>a HORSE a HORSE my KING dom FOR a HORSE</th>
      <th>-+-+-+-+-+</th>
      <th>-+-+-+---+</th>
      <td>1.0</td>
      <td>0.0</td>
      <td>10</td>
      <td>0</td>
      <td>1</td>
    </tr>
    <tr>
      <th>2</th>
      <th>a HORSE a HORSE my KING dom FOR a.horse</th>
      <th>-+-+-+-+--</th>
      <th>-+-+-+---+</th>
      <td>1.0</td>
      <td>0.0</td>
      <td>12</td>
      <td>0</td>
      <td>1</td>
    </tr>
    <tr>
      <th>3</th>
      <th>a HORSE a HORSE my KING dom.for A horse</th>
      <th>-+-+-+--+-</th>
      <th>-+-+-+---+</th>
      <td>1.0</td>
      <td>0.0</td>
      <td>12</td>
      <td>0</td>
      <td>1</td>
    </tr>
    <tr>
      <th>4</th>
      <th>a HORSE a HORSE my KING dom.for A.HORSE</th>
      <th>-+-+-+--++</th>
      <th>-+-+-+---+</th>
      <td>1.0</td>
      <td>0.0</td>
      <td>14</td>
      <td>0</td>
      <td>1</td>
    </tr>
    <tr>
      <th>5</th>
      <th>a HORSE a HORSE my KING.DOM for.a HORSE</th>
      <th>-+-+-++--+</th>
      <th>-+-+-+---+</th>
      <td>1.0</td>
      <td>0.0</td>
      <td>14</td>
      <td>0</td>
      <td>1</td>
    </tr>
    <tr>
      <th>6</th>
      <th>a HORSE a HORSE my KING dom FOR.A horse</th>
      <th>-+-+-+-++-</th>
      <th>-+-+-+---+</th>
      <td>2.0</td>
      <td>0.0</td>
      <td>12</td>
      <td>0</td>
      <td>2</td>
    </tr>
  </tbody>
</table>
</div>



##### Parsing texts


```python
# small texts
sonnet.parse()
```

    [34m[1mparsing 14 lines [5x][0m[36m @ 2023-12-15 14:17:43,563[0m
    [1;34m￨ stanza 01, line 14: LEESE but.their SHOW their SUBS tance STILL lives SWEET: 100%|[0;36m██████████[0;36m| 14/14 [00:00<00:00, 45.78it/s]
    [34m[1m⎿ 0.3 seconds[0m[36m @ 2023-12-15 14:17:43,873[0m






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
      <th>parse_score</th>
      <th>parse_is_bounded</th>
      <th>meterpos_num_slots</th>
      <th>*w_peak</th>
      <th>*w_stress</th>
      <th>*s_unstress</th>
      <th>*unres_across</th>
      <th>*unres_within</th>
    </tr>
    <tr>
      <th>stanza_num</th>
      <th>line_num</th>
      <th>line_txt</th>
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
    </tr>
  </thead>
  <tbody>
    <tr>
      <th rowspan="11" valign="top">1</th>
      <th rowspan="3" valign="top">1</th>
      <th rowspan="3" valign="top">Those hours, that with gentle work did frame</th>
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
    </tr>
    <tr>
      <th rowspan="2" valign="top">2</th>
      <th rowspan="2" valign="top">The lovely gaze where every eye doth dwell,</th>
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
    </tr>
    <tr>
      <th>2</th>
      <th>the LO vely GAZE where E ve.ry EYE doth DWELL</th>
      <th>-+-+-+--+-+</th>
      <th>-+-+-+--+-+</th>
      <td>1.0</td>
      <td>0.0</td>
      <td>13</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
    </tr>
    <tr>
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
    </tr>
    <tr>
      <th rowspan="4" valign="top">13</th>
      <th rowspan="4" valign="top">But flowers distill'd, though they with winter meet,</th>
      <th>1</th>
      <th>but FLO wers DIS.TILL'D though THEY with WIN ter MEET</th>
      <th>-+-++-+-+-+</th>
      <th>-+--+-+-+-+</th>
      <td>2.0</td>
      <td>0.0</td>
      <td>13</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>1</td>
    </tr>
    <tr>
      <th>2</th>
      <th>but FLO wers.dis TILL'D though THEY with WIN ter MEET</th>
      <th>-+--+-+-+-+</th>
      <th>-+--+-+-+-+</th>
      <td>2.0</td>
      <td>0.0</td>
      <td>13</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>2</td>
      <td>0</td>
    </tr>
    <tr>
      <th>3</th>
      <th>but FLO.WERS dis TILL'D though THEY with WIN ter MEET</th>
      <th>-++-+-+-+-+</th>
      <th>-+--+-+-+-+</th>
      <td>2.0</td>
      <td>0.0</td>
      <td>13</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>1</td>
    </tr>
    <tr>
      <th>4</th>
      <th>but FLO wers DIS till'd THOUGH they.with WIN ter MEET</th>
      <th>-+-+-+--+-+</th>
      <th>-+--+---+-+</th>
      <td>4.0</td>
      <td>0.0</td>
      <td>13</td>
      <td>1</td>
      <td>1</td>
      <td>2</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>14</th>
      <th>Leese but their show; their substance still lives sweet.</th>
      <th>1</th>
      <th>LEESE but.their SHOW their SUBS tance STILL lives SWEET</th>
      <th>+--+-+-+-+</th>
      <th>+--+-+-+++</th>
      <td>1.0</td>
      <td>0.0</td>
      <td>12</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
  </tbody>
</table>
<p>37 rows × 8 columns</p>
</div>




```python
# and big texts
shaksonnets.parse()
```

    [34m[1mparsing 2155 lines [5x][0m[36m @ 2023-12-15 14:17:52,124[0m
    [1;34m￨ stanza 154, line 14: love's FI re HEATS.WA ter WA ter COOLS not LOVE       : 100%|[0;36m██████████[0;36m| 2155/2155 [00:56<00:00, 38.03it/s]
    [34m[1m⎿ 57.4 seconds[0m[36m @ 2023-12-15 14:18:49,496[0m





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
      <th>parse_score</th>
      <th>parse_is_bounded</th>
      <th>meterpos_num_slots</th>
      <th>*w_peak</th>
      <th>*w_stress</th>
      <th>*s_unstress</th>
      <th>*unres_across</th>
      <th>*unres_within</th>
    </tr>
    <tr>
      <th>stanza_num</th>
      <th>line_num</th>
      <th>line_txt</th>
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
    </tr>
  </thead>
  <tbody>
    <tr>
      <th rowspan="5" valign="top">1</th>
      <th rowspan="4" valign="top">1</th>
      <th rowspan="4" valign="top">FROM fairest creatures we desire increase,</th>
      <th>1</th>
      <th>from FAI rest CREA tures WE de SIRE in CREASE</th>
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
    </tr>
    <tr>
      <th>2</th>
      <th>from FAI rest CREA tures WE de SI re IN crease</th>
      <th>-+-+-+-+-+-</th>
      <th>-+-+-+-+-++</th>
      <td>1.0</td>
      <td>0.0</td>
      <td>11</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
    </tr>
    <tr>
      <th>3</th>
      <th>from FAI rest CREA tures WE de SI re IN.CREASE</th>
      <th>-+-+-+-+-++</th>
      <th>-+-+-+-+-++</th>
      <td>1.0</td>
      <td>0.0</td>
      <td>13</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
    </tr>
    <tr>
      <th>4</th>
      <th>from FAI rest CREA tures WE de SI re.in CREASE</th>
      <th>-+-+-+-+--+</th>
      <th>-+-+-+-+--+</th>
      <td>2.0</td>
      <td>0.0</td>
      <td>13</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>2</td>
      <td>0</td>
    </tr>
    <tr>
      <th>2</th>
      <th>That thereby beauty's rose might never die,</th>
      <th>1</th>
      <th>that THE reby BEA uty's ROSE might NE ver DIE</th>
      <th>-+-+-+-+-+</th>
      <th>-+++-+-+-+</th>
      <td>1.0</td>
      <td>0.0</td>
      <td>10</td>
      <td>0</td>
      <td>1</td>
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
      <th rowspan="5" valign="top">154</th>
      <th rowspan="5" valign="top">14</th>
      <th rowspan="5" valign="top">Love's fire heats water, water cools not love.</th>
      <th>2</th>
      <th>love's FI re HEATS wa.ter WA ter COOLS not LOVE</th>
      <th>-+-+--+-+-+</th>
      <th>++-++-+-+-+</th>
      <td>4.0</td>
      <td>0.0</td>
      <td>13</td>
      <td>1</td>
      <td>2</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
    </tr>
    <tr>
      <th>3</th>
      <th>love's FI.RE heats WA ter WA ter COOLS not LOVE</th>
      <th>-++-+-+-+-+</th>
      <th>++-++-+-+-+</th>
      <td>4.0</td>
      <td>0.0</td>
      <td>13</td>
      <td>0</td>
      <td>2</td>
      <td>1</td>
      <td>0</td>
      <td>1</td>
    </tr>
    <tr>
      <th>4</th>
      <th>LOVE'S fire HEATS wa.ter WA ter COOLS not LOVE</th>
      <th>+-+--+-+-+</th>
      <th>++++-+-+-+</th>
      <td>4.0</td>
      <td>0.0</td>
      <td>12</td>
      <td>1</td>
      <td>2</td>
      <td>0</td>
      <td>0</td>
      <td>1</td>
    </tr>
    <tr>
      <th>5</th>
      <th>LOVE'S.FI re HEATS.WA ter WA ter COOLS not LOVE</th>
      <th>++-++-+-+-+</th>
      <th>++-++-+-+-+</th>
      <td>4.0</td>
      <td>0.0</td>
      <td>15</td>
      <td>0</td>
      <td>0</td>
      <td>0</td>
      <td>4</td>
      <td>0</td>
    </tr>
    <tr>
      <th>6</th>
      <th>love's FI re HEATS wa TER wa TER cools NOT love</th>
      <th>-+-+-+-+-+-</th>
      <th>++-++-+-+++</th>
      <td>9.0</td>
      <td>0.0</td>
      <td>11</td>
      <td>2</td>
      <td>5</td>
      <td>2</td>
      <td>0</td>
      <td>0</td>
    </tr>
  </tbody>
</table>
<p>7277 rows × 8 columns</p>
</div>


