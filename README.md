# Prosodic

Prosodic is a metrical-phonological parser written in Python. It scans poems for their meter according to specified linguistic rules. The first line from Milton's *Paradise Lost*,

```
Of man's first disobedience, and the fruit     
```
becomes

```
of|MAN'S|first*|DIS|o|BE|dience|AND*|the|FRUIT
```

The metrical scansion is shown as capitalization. Shown in asterisks (*) are the syllables at odds with the scansion, departing from its ideal template, or violating its linguistic rules.

Prosodic converts each word into its stressed, syllabified, phonetic transcription, either from a pronunciation dictionary or from text-to-speech algorithms. To scan the text metrically, it finds the best available metrical parse for each line of text in the style of Optimality Theory: nearly all possibile parses are attempted; the best parses are those that least depart from a set of customizable linguistic rules or constraints. By default, the constraints are those proposed by Kristin Hanson and Paul Kiparsky in their paper "A Parametric Theory of Poetic Meter" (Language, 1996).

Currently, Prosodic can parse English and Finnish text, but adding additional languages is easy with a pronunciation dictionary or a custom python function.  Prosodic was built by [Ryan Heuser](https://github.com/quadrismegistus), [Josh Falk](https://github.com/jsfalk), and [Arto Anttila](http://web.stanford.edu/~anttila/), beginning in the summer of 2010. Josh also maintains [another repository](https://github.com/jsfalk/prosodic1b), in which he has rewritten the part of this project that does phonetic transcription for English and Finnish. [Sam Bowman](https://github.com/sleepinyourhat) has contributed to the codebase as well, adding several new metrical constraints.



## Installation

### Install Prosodic

Install from pip (preferred):

```
pip install prosodic
```

Or install latest sources (advanced):

```
git clone git@github.com:quadrismegistus/prosodic.git
cd prosodic
python setup.py develop
```

Both of these methods will create a folder `prosodic_data` in your home directory, where you can configure Prosodic, store texts, and save results. See below ("Configuring Prosodic") for more information.

### Install text-to-speech software

Prosodic uses TTS software in order to sound out unfamiliar words: otherwise, words not found in the CMU Pronunciation Dictionary will lack a phonology and so will deprive the line they appear in of the possibility of metrical parsing.

[eSpeak](http://espeak.sourceforge.net/) is an open-source TTS engine for Windows and Unix systems (including Mac OS X). To install eSpeak, [download it here for your operating system](http://espeak.sourceforge.net/download.html). Or, if you're running Mac OS X, install eSpeak with the [HomeBrew package manager](http://brew.sh/):

```
brew install espeak
```

<small>*Note:* Espeak produces *un*-syllabified IPA transcriptions of any given (real or unreal) word. To syllabify these, the [syllabifier](https://p2tk.svn.sourceforge.net/svnroot/p2tk/python/syllabify/syllabifier.py) from the [Penn Phonetics Toolkit (P2TK)](https://www.ling.upenn.edu/phonetics/old_website_2015/p2tk/) is used. An extra plus from this pipeline is consistency: this same syllabifier is responsible for the syllable boundaries in the CMU pronunciation dictionary, which  Prosodic draws from (if possible) before resorting to a TTS engine.</small>


## Quickstart

### Running Prosodic interactively

#### Run from command line: `prosodic`

```
################################################
## welcome to prosodic!                  v1.2 ##
################################################


	[please type a line of text, or enter one of the following commands:]
		/text	load a text
		/corpus	load folder of texts
		/paste	enter multi-line text

		/eval	evaluate this meter against a hand-tagged sample
		/weight	run maximum entropy on a hand-tagged sample

		/mute	hide output from screen
		/exit	exit
```

#### Paste in a text: `/paste`

```
>> enter or paste your content here. press Ctrl-D when finished.

Turning and turning in the widening gyre   
The falcon cannot hear the falconer;
Things fall apart; the centre cannot hold;
Mere anarchy is loosed upon the world,
The blood-dimmed tide is loosed, and everywhere   
The ceremony of innocence is drowned;
The best lack all conviction, while the worst   
Are full of passionate intensity.
```

#### Parse metrically: `/parse` (according to the meter specified in `/meter`)

#### Show results: `/scan` (per line, showing only the best parse)
```
text                                                        	parse                                                       	meter	num_parses	num_viols	score_viols	[*footmin-f-resolution]	[*footmin-w-resolution]	[*strength.w=>-p]	[*stress.s=>-u]	[*stress.w=>-p]
Turning and turning in the widening gyre                    	TURN|ing.and*|TURN|ing|IN|the|WIDEN|ing|GY|re               	swwswswswsw	3	1	5	0	0	5	0	0
The falcon cannot hear the falconer;                        	the|FAL|con|CAN|not|HEAR|the|FAL|coner                      	wswswswsw	1	0	0	0	0	0	0	0
Things fall apart; the centre cannot hold;                  	things*|FALL|ap|ART|the|CEN|tre|CAN|not|HOLD                	wswswswsws	2	1	1	0	0	0	0	1
Mere anarchy is loosed upon the world,                      	mere*|AN|ar|CHY*|is|LOOSED|up|ON|the|WORLD                  	wswswswsws	4	2	2	0	0	0	1	1
The blood- dimmed tide is loosed, and everywhere            	the|BLOOD|dimmed*|TIDE|is|LOOSED|and|EV|ery|WHERE           	wswswswsws	1	1	1	0	0	0	0	1
The ceremony of innocence is drowned;                       	the|CER|e|MO|ny.of*|IN|no|CENCE*|is|DROWNED                 	wswswwswsws	6	2	6	0	0	5	1	0
The best lack all conviction, while the worst               	the|BEST|lack*|ALL|con|VIC|tion|WHILE|the|WORST             	wswswswsws	3	1	1	0	0	0	0	1
Are full of passionate intensity.                           	are|FULL|of|PAS|sion|ATE*|in|TEN|si|TY*                     	wswswswsws	2	2	2	0	0	0	2	0
```
#### Save statistics: `/stats all`


### Running Prosodic as a python module

```python
# import
import prosodic as p

# create a Text object
text = p.Text(string_or_filename)`

# parse metrically
text.parse()

# save stats
text.save_stats()

# iterate over features
for line in text.lines():
    best_parse = line.bestParse()  # most plausible parse
    all_parses = line.allParses()  # all plausible parses

    first_word = line.words()[0]
    last_syllable = line.syllables()[-1]
    last_syllable_rime = line.rimes()[-1]
    last_syllable_rime_phonemes = last_syllable_rime.phonemes()
```


## Configuration

All configuration of Prosodic takes place in the `~/prosodic_data` folder located in your home directory, created upon installation (either through `pip install prosodic` or `python setup.py install` from sources).

### Main settings

* In order to configure Prosodic, copy or rename 'config_default.py' to 'config.py', and edit that file according to its instructions.
* [Note: 'config_default.py' will be overwritten if you update Prosodic, but 'config.py' will not be.]

This file configures the following options:

* Technical options about how Prosodic works:
	* The paths used for corpora, results, and tagged samples
	* The language used (currently, English or Finnish)
	* Which Text-to-Speech engine, if any, is used for parsing unknown English words
	* Whether to print output to screen

* Options about words and tokenization:
	* The regular expression used for word tokenization
	* For words with multiple stress profiles (e.g. "INto" and "inTO"), whether to allow the metrical parser to choose the stress profile based on whichever works best metrically in the line
	* Whether to allow elided pronunciations (e.g. "Plu-ton-ian" for "Plu-ton-i-an") as metrical possibilities also
	* How to display the phonetic output for words (IPA, orthography, CMU notation)


### Meters
* To edit or create your own meter, copy or rename 'meters/meter_default.py' to 'meters/your_meter_name.py', and edit that file according to its instructions.
* Then consider changing the default 'meter' setting in your config.py to 'your_meter_name'.
* You can also select 'your_meter_name' from within Prosodic.
* [Note: 'meters/meter_default.py' will be overwritten if you update Prosodic, but 'meters/your_meter_name.py' will not be.]

These files configure the following options:

* The minimum and maximum size of metrical positions: from a syllable (or even a half-syllable, or mora), to two or more syllables.
* The constraints used in metrical parsing, some of which are:
	* Constraints proposed by Kiparsky and Hanson in "A Parametric Theory of Poetic Meter" (*Language*, 1996):
		* *Strength*: A weak/strong syllable should not be in a strong/weak metrical position.
		* *Stress*: An unstressed/stressed syllable should not bein a strong/weak metrical position.
		* *Weight*: A light/heavy syllable should not be in a strong/weak metrical position.
		* *Minimal foot*: a disyllabic metrical position should not contain more than a minimal foot (only if the syllables are weighted light-heavy or light-light is a disyllabic position allowed).
	* Other constraints regulating disyllabic metrical positions
	* Constraints allowing the initial parts of lines to be extrametrical
	* Constraints regulating word elisions (e.g. "Plu-ton-i-an" becoming "Plu-ton-ian")
* What to pass to the metrical parser: a line in the text file, a line between punctuation markers, etc.


###  Tagged samples
* To run Prosodic against your own tagged sample, create a file like 'tagged_samples/tagged-sample-litlab-2016.txt', which has at least a column for the line (e.g. "From fairest creatures we desire increase") and a column for the parse (e.g. "wswswswsws").
* [Note: 'tagged_samples/tagged-sample-litlab-2016.txt' will be overwritten if you update Prosodic, but your own files will not be.]

### Results
* By default, results will be saved to the 'results' folder here.
* You can change this option in the 'folder_results' option in 'config.py'.

### Corpora and texts
* By default, Prosodic will look for texts within the 'corpora' folder here.
* You can change this option in the 'folder_corpora' option in config.py.

### For more information

Please see the documentation within `~/prosodic_data/README.txt`, `~/prosodic_data/config.py` and ~/`prosodic_data/meter/meter_default.py` for more information.


## Usage

There are two main ways of using  Prosodic: in interactive mode, and, for more Python-advanced users, as a Python module.

### Interactive mode

You can enter the interactive mode of prosodic by running `python prosodic.py`. This will bring you to an interface like this:

	################################################
	## welcome to prosodic!                  v1.1 ##
	################################################


		[please type a line of text, or enter one of the following commands:]
			/text	load a text
			/corpus	load folder of texts
			/paste	enter multi-line text

			/eval	evaluate this meter against a hand-tagged sample
			/mute	hide output from screen
			/save	save previous output to file
			/exit	exit

	>> [0.0s] prosodic:en$

#### Loading text

The first thing to do when using  Prosodic is to give it some text to work with. There's a few ways of doing this. The simplest way is to simply a type in a line, one at a time. You can also type `/paste`, and then enter or copy/paste multiple lines in at a time. You can also type `/text` to load a text, or `/corpus` to load a folder of text files. If you do, you'll be given instructions on how either to specify a relative path from within  Prosodic's corpus folder, or an absolute path to another file or folder on your disk. You can also define the text you want to work with as an argument for the command you use to boot  Prosodic with: `python prosodic.py /path/to/my/file.txt`.

#### Checking phonetic/phonological annotations

Even before metrically parsing the text you've loaded (see below), you can run a few commands to test out how  Prosodic has interpreted the text in terms of its phonetics and phonology. The command `/show` will show the phonetic transcription and stress- and weight-profiles for each word:

    000001  of                      P:ʌv                                S:U     W:L
    000002  mans                    P:'mænz                             S:P     W:H
    000003  first                   P:'fɛːst                            S:P     W:H
    000004  disobedience            P:`dɪ.sə.'biː.diː.əns               S:SUPUU W:LLHHH
    000005  and                     P:ænd                               S:U     W:L
    000006  the                     P:ðə                                S:U     W:L
    000007  fruit                   P:'fruːt                            S:P     W:H

The command `/tree` shows a hierarchical description of each word's phonology, as it is embedded in the hierarchical organization of the text. For instance, the beginning of the output from `/tree` for this line would be:

	-----| (S1) <Stanza>
	      |
	      |-----| (S1.L1) <Line>                                                                       [of mans first disobedience and the fruit]
	            |
	            |-----| (S1.L1.W1) <Word>	of	<ʌv>
	                  |     [+functionword]
	                  |     [numSyll=1]
	                  |
	                  |-----| (S1.L1.W1.S1) <Syllable>                                                 [ʌv]
	                        |     [prom.stress=0.0]
	                        |
	                        |-----| (S1.L1.W1.S1.SB1) <SyllableBody>                                   [ʌv]
	                              |     [shape=VC]
	                              |     [-prom.vheight]
	                              |     [-prom.weight]
	                              |
	                              |-----| (S1.L1.W1.S1.SB1.O1) <Onset>
	                              |
	                              |-----| (S1.L1.W1.S1.SB1.R2) <Rime>
	                                    |
	                                    |-----| (S1.L1.W1.S1.SB1.R2.N1) <Nucleus>
	                                          |     [-prom.vheight]
	                                          |
	                                          |-----| (S1.L1.W1.S1.SB1.R2.N1.P1) <Phoneme>             [ʌ]
	                                    |
	                                    |-----| (S1.L1.W1.S1.SB1.R2.C2) <Coda>
	                                          |
	                                          |-----| (S1.L1.W1.S1.SB1.R2.C2.P1) <Phoneme>             [v]
	            |
	            |-----| (S1.L1.W2) <Word>	mans	<'mænz>
	                  |     [numSyll=1]
	                  |
	                  |-----| (S1.L1.W2.S1) <Syllable>                                                 ['mænz]
	                        |     [prom.stress=1.0]
	                        |     [prom.kalevala=1.0]
	                        |
	                        |-----| (S1.L1.W2.S1.SB1) <SyllableBody>                                   [mænz]
	                              |     [shape=CVCC]
	                              |     [-prom.vheight]
	                              |     [+prom.weight]
	                              |
	                              |-----| (S1.L1.W2.S1.SB1.O1) <Onset>
	                                    |
	                                    |-----| (S1.L1.W2.S1.SB1.O1.P1) <Phoneme>                      [m]
	                              |
	                              |-----| (S1.L1.W2.S1.SB1.R2) <Rime>
	                                    |
	                                    |-----| (S1.L1.W2.S1.SB1.R2.N1) <Nucleus>
	                                          |     [-prom.vheight]
	                                          |
	                                          |-----| (S1.L1.W2.S1.SB1.R2.N1.P1) <Phoneme>             [æ]
	                                    |
	                                    |-----| (S1.L1.W2.S1.SB1.R2.C2) <Coda>
	                                          |
	                                          |-----| (S1.L1.W2.S1.SB1.R2.C2.P1) <Phoneme>             [n]
	                                          |
	                                          |-----| (S1.L1.W2.S1.SB1.R2.C2.P2) <Phoneme>             [z]

Lastly, the `/query` command allows you to query these phonological annotations. Once `/query` is entered, the query language parser starts up (type `/` to exit, or hit `Ctrl+D`). Which are the stressed syllables in the text? `(Syllable: [+prom.stress])`. Which are all the voiced phonemes? `(Phoneme: [+voice])`. Which are all the syllables with voiced onsets and codas? `(Syllable: (Onset: [+voice]) (Coda: [+voice]))`. Etc.


#### Metrically parsing text

The command `/parse` will metrically parse whatever text is currently loaded into  Prosodic. Once the text is parsed, further commands become possible, all of which either view or save the data gleaned from the parser.

The command `/scan` prints the best parse for each line, along with statistics on which constraints it violated. [This output, like any other output, can be saved to disk (and then opened with Excel) by using the `/save` command.] For instance, here are the first four lines of *Paradise Lost*, using the `/scan` command:

	text                                    		parse                                   		#pars	#viol	meter			[*footmin-none]	[*strength.s=>-u]	[*strength.w=>-p]	[*stress.s=>-u]	[*stress.w=>-p]
	of mans first disobedience and the fruit		of|MANS|first|DI|so|BE|di|ENCE|and.the|FRUIT	3		5		wswswswswws		0				0					2					2				1
	of that forbidden tree whose mortal tast		of|THAT|for|BID|den|TREE|whose|MOR|tal|TAST		1		0		wswswswsws		0				0					0					0				0
	brought death into the world and all our woe	brought|DEATH|in|TO|the|WORLD|and|ALL|our|WOE	1		2		wswswswsws		0				0					0					2				0
	with loss of eden till one greater man  		with|LOSS|of|ED|en|TILL|one|GRE|ater|MAN		1		2		wswswswsws		0				0					2					0				0



The command `/report` is a more verbose version of `/scan`, printing each possible (i.e. non-harmonically-bounded) parse for each line. For instance, for each line, it produces an output like:

	==============================
	[line #1 of 4]: of mans first disobedience and the fruit

		--------------------
		[parse #3 of 3]: 8.0 errors
		1	w	of        	
		2	s	MANS      	
		3	w	first     	[*stress.w=>-p]
		4	s	DI        	
		5	w	so        	
		6	s	BE        	
		7	w	di        	
		8	s	ENCE      	[*stress.s=>-u]
		9	w	and       	
		10	s	THE       	[*stress.s=>-u]
		11	w	fruit     	[*stress.w=>-p]

		[*stress.s=>-u]: 4.0  [*stress.w=>-p]: 4.0  
		--------------------

		--------------------
		[parse #2 of 3]: 5.0 errors
		1	w	of        	
		2	s	MANS      	
		3	w	first     	[*stress.w=>-p]
		4	s	DI        	
		5	w	so        	
		6	s	BE        	
		7	w	di ence   	[*footmin-none]
		8	s	AND       	[*stress.s=>-u]
		9	w	the       	
		10	s	FRUIT     	

		[*footmin-none]: 1.0  [*stress.s=>-u]: 2.0  [*stress.w=>-p]: 2.0  
		--------------------

		--------------------
		[parse #1 of 3]: 5.0 errors
		1	w	of        	
		2	s	MANS      	
		3	w	first     	[*stress.w=>-p]
		4	s	DI        	
		5	w	so        	
		6	s	BE        	
		7	w	di        	
		8	s	ENCE      	[*stress.s=>-u]
		9	w	and the   	[*footmin-none]
		10	s	FRUIT     	

		[*footmin-none]: 1.0  [*stress.s=>-u]: 2.0  [*stress.w=>-p]: 2.0  
		--------------------

	==============================

Finally, you can also save a variety of statistics from the metrical parser in tab-separated form by running the `/stats` command.

#### Evaluating the meter against a hand-parsed sample

How well does Prosodic do when its metrical parses are compared with those that a human reader has annotated? The statistics above, in "Accuracy of metrical parser," were generated from the evaluation command: `/eval`. From there, you can select a spreadsheet (either a tab-separated text file or an excel document) saved in the `tagged_samples/` folder to use as the "ground truth", human-annotated parse. The `/eval` command will ask which columns in the file correspond to the line ("Of man's first disobedience and the fruit"), the parse ("wswswswwsws"), and (optionally) the meter of the line ("iambic").  Prosodic will then parse the lines under the "line" column (using, as always, the current configuration of metrical constraints in `config.py`), and save statistics to the same folder in tab-separated form.

## Extending Prosodic

### Adding languages

There are two possible methods by which Prosodic can understand a language:

* using a dictionary in the format:
	* {word-token}[tab]{stressed, syllabified, IPA format}
	* eg:
		* befuddle [tab] bɪ.'fə.dəl
		* befuddled	[tab] bɪ.'fə.dəld
		* befuddles	[tab] bɪ.'fə.dəlz

* using a python function which takes in a word-token as an input, and a stressed, syllabified, IPA format as its output.

Currently, Finnish is implemented by the latter method; English, by a combination of two, using the dictionary for recognized words, and a python function for unrecognized words.

To add entries to a language's dictionary, simply add an entry in the above format to the dictionary `[language_name].tsv` under the folder `[prosodic_dir]/dicts/[language_twoletter_code]`.

To add a new language entirely, you can create a new dictionary in the above format and place it under `[prosodic_dir]/dicts/[language_twoletter_code]/[language_name].tsv`. Or, you can create a python file under `[prosodic_dir]/dicts/[language_twoletter_code]/[language_name].py`, which has a function `get(token,config={})`. This function must accept a word-token as its only argument, and  Prosodic's configuration settings as an optional keyword argument, and it must return a list of tuples in the form:

	[
		(
			<ipa unicode string>,
			<token string split into a list of syllable strings>,
			{a dictionary of optional keyword arguments to be stored on the word object},
		),
		...
	]

For example, `get("into", config={'add_elided_pronunciations':1})` might return:

	[
		(u"ɪn.'tuː", ['in','to'], {'is_elision': False}),
		u"'ɪn.tuː", ['in','to'], {'is_elision': False}),
		u"ɪn.tʌ", ['in','to'], {'is_elision': False})
	]

See the `get()` function in `dicts/en/english.py` or `dicts/fi/finnish.py` for examples.

### Contributing to the code base

Please feel free to pull and push back to the codebase here! And feel free to use this code in your projects: it is licensed by [GPLv3](https://www.gnu.org/licenses/gpl-3.0.en.html).
