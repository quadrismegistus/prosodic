# Prosodic

Prosodic is a a metrical-phonological parser written in Python. Currently, it can parse English and Finnish text, but adding additional languages is easy with a pronunciation dictionary or a custom python function. Prosodic was built by [Ryan Heuser](https://github.com/quadrismegistus), [Josh Falk](https://github.com/jsfalk), and [Arto Anttila](http://web.stanford.edu/~anttila/), beginning in the summer of 2010. Josh also maintains [another repository](https://github.com/jsfalk/prosodic1b), in which he has rewritten the part of this project that does phonetic transcription for English and Finnish. [Sam Bowman](https://github.com/sleepinyourhat) has contributed to the codebase as well, adding several new metrical constraints.

## About Prosodic

Prosodic does two main things. First, it tokenizes text into words, and then converts each word into its stressed, syllabified, phonetic transcription. Second, if desired, it finds the best available metrical parse for each line of text. In the style of Optimality Theory, (almost) all logically possibile parses are attempted, but the best parses are those that least violate a set of user-defined constraints. The default metrical constraints are those proposed by Kiparsky and Hanson in their paper "A Parametric Theory of Poetic Meter" (Language, 1996). See below for how these and other constraints are implemented.

### Example of metrical parsing

Here's an example of the metrical parser in action, on Shakespeare's first sonnet.

	[text]                                    				[parse]                                   
	from fairest creatures we desire increase				from|FAI|rest|CREA|tures|WE|de|SIRE|in|CREASE
	that thereby beauty's rose might never die				that|THERE|by|BEAU|ty's|ROSE|might|NEV|er|DIE
	but as the riper should by time decease 				but|AS|the|RI|per|SHOULD|by|TIME|de|CEASE
	his tender heir might bear his memory   				his|TEN|der|HEIR|might|BEAR|his|MEM|o|RY
	but thou contracted to thine own bright eyes			but|THOU|con|TRACT|ed|TO|thine|OWN|bright|EYES
	feed'st thy light's flame with self substantial fuel	FEED'ST|thy|LIGHT'S|flame.with|SELF|sub|STAN|tial|FU|el
	making a famine where abundance lies    				MAK|ing.a|FA|mine|WHERE|ab|UN|dance|LIES
	thy self thy foe to thy sweet self too cruel			thy|SELF|thy|FOE|to.thy|SWEET.SELF|too|CRU|el
	thou that art now the world's fresh ornament			thou|THAT|art|NOW|the|WORLD'S|fresh|OR|na|MENT
	and only herald to the gaudy spring     				and|ON|ly|HER|ald|TO|the|GAU|dy|SPRING  
	within thine own bud buriest thy content				with|IN|thine|OWN|bud|BU|ri|EST|thy|CON|tent
	and tender churl mak'st waste in niggarding				and|TEN|der|CHURL|mak'st|WASTE|in|NIG|gard|ING
	pity the world or else this glutton be  				PI|ty.the|WORLD|or|ELSE|this|GLUT|ton|BE
	to eat the world's due by the grave and thee			to|EAT|the|WORLD'S|due|BY|the|GRAVE|and|THEE

Not bad, right? Prosodic not only captures the sonnet's overall iambic meter, but also some of its variations. It accurately captures the trochaic inversions in the lines "*Mak*ing a *fam*ine *where* a*bun*dance *lies*" and "*Pi*ty the *world* or *else* this *glut*ton *be*." Also, depending on the constraints, it also captures the double-strong beat that can often follow a double-weak beat in the line "Thy *self* thy *foe* to thy *sweet self* too *cruel*" (see, for this metrical pattern, [Bruce Hayes' review of Derek Attridge's *The Rhythms of English Poetry* in *Language* 60.1, 1984](http://www.linguistics.ucla.edu/people/hayes/Papers/Hayes1984ReviewOfAttridge.pdf)). It also gets some lines wrong: its interpretation of "feed'st thy light's flame," for example. But how accurate is it on average?

#### Metrical annotation output

See [here](https://www.dropbox.com/sh/q13jsvsxem5lvdw/AACE0VSc0hL4UfEJDhWpFs5oa?dl=0) for a quick look of the three output statistics files are produced in the metrical annotation process.

### Accuracy of metrical parser

In preliminary tests, we ran Prosodic against a sample of 1800 hand-parsed lines of iambic, trochaic, anapestic, and dactylic verse ([included](https://github.com/quadrismegistus/prosodic/blob/master/tagged_samples/tagged-sample-litlab-2016.txt)). For example, here is a line, and how it was parsed by a human, Prosodic, and the "bare template" of its poem's meter (iambic).

	Line:       Anxious  in  vain  to  find  the  distant  floor

	Human:      ANxious  in  VAIN  to  FIND  the  DIStant  FLOOR
                s   w    w   s     w   s     w    s  w     s

	Prosodic:   ANxious  in  VAIN  to  FIND  the  DIStant  FLOOR
                s   w    w   s     w   s     w    s  w     s

	Template:   anXIOUS  in  VAIN  to  FIND  the  DIStant  FLOOR
                w   s    w   s     w   s     w    s  w     s
	            *   *

We can see that Prosodic gets this line right; the template gets most of it right, missing only the trochaic inversion. By running all of the lines through in this way (using the `/eval` command of Prosodic [see below]) we can see what percentage of syllables both Prosodic and a template "correctly" capture—where "correct" is to agree with the human parse.

<table>
	<thead align=center>
		<tr>
			<th colspan="5">% Syllables Correctly Parsed</th>
		</tr>
		<tr>
			<th></th>
			<th width=140>Another Human</th>
			<th width=140>Prosodic</th>
			<th width=140>Base Template (for this meter)</th>
			<th width=140>Base Template (iambic meter)</th>
		</tr>
	</thead>
	<tbody>
		<tr>
			<td>Iambic lines</td>
			<td>93.7%</td>
			<td>92.6%</td>
			<td>89.0%</td>
			<td>89.0%</td>
		</tr>
		<tr>
			<td>Trochaic lines</td>
			<td>98.8%</td>
			<td>94.5%</td>
			<td>95.3%</td>
			<td>4.5%</td>
		</tr>
		<tr>
			<td>Anapestic lines</td>
			<td>97.2%</td>
			<td>84.7%</td>
			<td>66.1%</td>
			<td>52.9%</td>
		</tr>
		<tr>
			<td>Dactylic lines</td>
			<td>95.8%</td>
			<td>83.8%</td>
			<td>75.6%</td>
			<td>49.7%</td>
		</tr>
	</tbody>
</table>

The extent to which two human taggers (both English literature Ph.D. students) agree is in the first column: given that metrical scansion inevitably varies from person to person, this might be taken as the upper threshold of what we could expect Prosodic to do. But Prosodic is not too far off, especially for the binary meters (iambic and trochaic). The ternary meters are more complicated: they depart more often from their metrical templates, as can be seen in the third column. But the third column of metrical templates assumes that we already know the meter of the poem (which, in this evaluation sample, we do). Not surprisingly, if we don't already know the meter, and simply apply an iambic temlpate to every poem, then it works well for iambic poems, but not at all for poems of other meters—as can be seen in the fourth column. This means that, *for parsing poems whose meter is unknown*, or for parsing free verse poems or even prose, Prosodic is especially useful. Parsing lines individually, and agnostic as to the meter of "the poem," Prosodic is nonetheless able to discover the basic contours of the metrical patterns in the lines. In [another research project](https://github.com/quadrismegistus/litlab-poetry), run out of the [Stanford Literary Lab](http://litlab.stanford.edu/), Prosodic's parses were able to predict the overall meter in 200 poems with about 98% accuracy.

The data above were produced when the meter was defined as the following constraints and weights: `[*strength.s=>-u/3.0] [*strength.w=>-p/3.0] [*stress.s=>-u/2.0] [*stress.w=>-p/2.0] [*footmin-none/1.0] [*footmin-no-s-unless-preceded-by-ww/10.0] [*posthoc-no-final-ww/2.0] [*posthoc-standardize-weakpos/1.0] [*word-elision/1.0]`. These and other constraints are mentioned below, but are best documented in their confuration file, `config.py`.

[One final note: these human annotations—made by literature Ph.D. students—embody certain assumptions about meter that are common in literary, but not linguistic circles. For instance, representing a trochaic inversion as a literal inversion of feet, "swws," is not how Kiparsky would represent it; for him, a trochaic inversion is simply a conventional, permissible violation of the iambic meter. However, Prosodic doesn't necessarily commit itself to either of these theories or approaches: parses that conform to either theory can be generated using different sets of constraints.]


## Installation

### Quick start

To install Prosodic, it's best to install using pip. In a terminal, type:

	pip install git+git://github.com/quadrismegistus/prosodic.git

After installation, you should have access to the "prosodic" executable. Simply run:

	prosodic

to open up the interactive terminal interface.

#### Quick start (within Python)

Prosodic can also be used as a python module within your own applications:

	import prosodic as p
	text = p.Text("Shall I compare thee to a summer's day?")
	text.parse()

Instructions on how to use Prosodic in interactive mode, and as a python module, are below.

## Usage

There are two main ways of using Prosodic: in interactive mode, and, for more Python-advanced users, as a Python module.

### Interactive mode

You can enter the interactive mode of prosodic by running `prosodic`. This will bring you to an interface like this:

	################################################
	## welcome to prosodic!                  v1.3 ##
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

The first thing to do when using Prosodic is to give it some text to work with. There's a few ways of doing this. The simplest way is to simply a type in a line, one at a time. You can also type `/paste`, and then enter or copy/paste multiple lines in at a time. You can also type `/text` to load a text, or `/corpus` to load a folder of text files. If you do, you'll be given instructions on how either to specify a relative path from within Prosodic's corpus folder, or an absolute path to another file or folder on your disk. You can also define the text you want to work with as an argument for the command you use to boot Prosodic with: `prosodic /path/to/my/file.txt`.

#### Checking phonetic/phonological annotations

Even before metrically parsing the text you've loaded (see below), you can run a few commands to test out how Prosodic has interpreted the text in terms of its phonetics and phonology. The command `/show` will show the phonetic transcription and stress- and weight-profiles for each word:

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

The command `/parse` will metrically parse whatever text is currently loaded into Prosodic. Once the text is parsed, further commands become possible, all of which either view or save the data gleaned from the parser.

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

How well does Prosodic do when its metrical parses are compared with those that a human reader has annotated? The statistics above, in "Accuracy of metrical parser," were generated from the evaluation command: `/eval`. From there, you can select a spreadsheet (either a tab-separated text file or an excel document) saved in the `tagged_samples/` folder to use as the "ground truth", human-annotated parse. The `/eval` command will ask which columns in the file correspond to the line ("Of man's first disobedience and the fruit"), the parse ("wswswswwsws"), and (optionally) the meter of the line ("iambic"). Prosodic will then parse the lines under the "line" column (using, as always, the current configuration of metrical constraints in `config.py`), and save statistics to the same folder in tab-separated form. The spreadsheet used in the above accuracy table is provided, made by the Stanford Literary Lab's [poetry project](http://github.com/quadrismegistus/litlab-poetry) in 2014 and 2016.

### Configuration options

All configuration of Prosodic takes place in `config.py` in your prosodic data folder, which is by default the folder `prosodic_data` in your home folder. (If only `config_default.py` is there, copy that to `config.py`.) This file is fairly well documented and is the best source of documentation on how to use it. (It's best to edit this file inside a text editor that highlights the Python syntax, so you can visually see which settings are deactivated by being "commented-out," i.e. by having a "#" character at the start of their lines.) Here is a list of what you will find there.

* Technical options about how Prosodic works:
	* The paths used for corpora, results, and tagged samples
	* The language used (currently, English or Finnish)
	* Which Text-to-Speech engine, if any, is used for parsing unknown English words
	* Whether to print output to screen
* Options about metrical parsing:
	* The minimum and maximum size of metrical positions (from a mora to two or more syllables)
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
* Options about words and tokenization:
	* The regular expression used for word tokenization
	* For words with multiple stress profiles (e.g. "INto" and "inTO"), whether to allow the metrical parser to choose the stress profile based on whichever works best metrically in the line
	* Whether to allow elided pronunciations (e.g. "Plu-ton-ian" for "Plu-ton-i-an") as metrical possibilities also
	* How to display the phonetic output for words (IPA, orthography, CMU notation)

Again, please see the documentation within `config.py` for more information.


### Running Prosodic as a python module

Prosodic can also be run within other python applications.

	In [1]: import prosodic as p

	In [2]: t = p.Text("corpora/shakespeare/sonnet-001.txt")

	In [3]: t.parse()

	In [4]: for parse in t.bestParses():
	   ...:     print parse
	   ...:     
	from|FAI|rest|CREA|tures|WE|de|SIRE|in|CREASE
	that|THERE|by|BEAU|ty's|ROSE|might|NEV|er|DIE
	[...]

For more information on this, please see [the Wiki](https://github.com/quadrismegistus/prosodic/wiki).



### Dependencies

#### Text to speech engine for parsing unknown English words

By default, Prosodic uses the CMU pronunciation dictionary to discover the syllable boundaries, stress pattern, and other information about English words necessary for metrical parsing. Lines with words not in this dictionary are, again by default, skipped when parsing. However, with a Text-to-Speech engine, it's possible to "sound out" unknown English words into a stressed, syllabified form that can then be parsed. Prosodic supports two TTS engines: *espeak* (recommended), and *OpenMary*. I find that espeak produces better syllabifications than OpenMary (at least for English), and is simpler to use, but either will work just fine.

##### Setting up espeak

[Espeak](http://espeak.sourceforge.net/) is an open-source TTS engine for Windows and Unix systems (including Mac OS X). You can [download it for your operating system here](http://espeak.sourceforge.net/download.html). But if you're running Mac OS X, an even simpler way to install espeak is via the [HomeBrew package manager](http://brew.sh/). To do so, install homebrew if you haven't, and then run in a terminal: `brew install espeak`. After you've installed espeak, set the "en_TTS_ENGINE" flag in the *config.py* file to "espeak." That's it!

<small>*Note:* Espeak produces *un*-syllabified IPA transcriptions of any given (real or unreal) word. To syllabify these, the [syllabifier](https://p2tk.svn.sourceforge.net/svnroot/p2tk/python/syllabify/syllabifier.py) from the [Penn Phonetics Toolkit (P2TK)](https://www.ling.upenn.edu/phonetics/old_website_2015/p2tk/) is used. An extra plus from this pipeline is consistency: this same syllabifier is responsible for the syllable boundaries in the CMU pronunciation dictionary, which Prosodic draws from (if possible) before resorting to a TTS engine.</small>

##### Setting up OpenMary

OpenMary is another open-source TTS engine, written in Java and developed by two German research institutes: the [DFKI](http://www.dfki.de/web)'s [Language Technology Lab](http://www.dfki.de/lt/) and [Saarland University](http://www.uni-saarland.de/startseite.html)'s [Institute of Phonetics](http://www.coli.uni-saarland.de/groups/WB/Phonetics/). To install OpenMary, first [download it here](http://mary.dfki.de/download/index.html) [select the "Run time package" link]. Then, unzip the zip file, go into the unzipped folder, and start OpenMary as a server. To do that, type into the terminal after unzipping: `./marytts-5.2/bin/marytts-server.sh`. To use OpenMary in Prosodic, you'll have to make sure OpenMary is running as a server process beforehand; if not, you'll have to repeat the last command. For espeak, this step isn't necessary.

#### Python module dependencies

By default, Prosodic has no module dependencies. The modules it does use—[lexconvert](http://ssb22.user.srcf.net/gradint/lexconvert.html), [P2TK](https://www.ling.upenn.edu/phonetics/old_website_2015/p2tk/)'s [syllabify.py](https://p2tk.svn.sourceforge.net/svnroot/p2tk/python/syllabify/syllabifier.py), and a [python hyphenator for syllabifying English orthography](https://github.com/Kozea/Pyphen)—are small, and already included in the repository. However, there are a few exceptions, depending on what you want to do. To install these modules, first [install pip](https://pip.pypa.io/en/stable/installing/) if you haven't yet.

- If you'd like to use the built-in query language (available under "/query" in the interactive mode), you'll need to install pyparsing: `pip install pyparsing`.
- If you're running OpenMary, you'll need to install the xml parser Beautiful Soup 4, and the unicode module unidecode: `pip install bs4` and `pip install unidecode`.
- If you'd like to be able to read evaluation data in spreadsheet form (*.xls, *.xlsx) (available under "/eval" in interactive mode), you'll need to install xlrd: `pip install xlrd`.





## How it works

How does Prosodic work? Here is an overview of its two major aspects: how words are tokenized, phonetically transcribed, syllabified, and stressed; and then how that information is used to find the optimal metrical parse according to a set of constraints.

### From text, to words, to phonetics and phonology

Prosodic first encounters a piece of English or Finnish text. It tokenizes that text according to a user-defined tokenizer, set under the option "tokenizer" in `config.py`, defaulting to splitting lines into words by whitespace and hyphens. In Finnish text, a pure-Python implementation of Finnish IPA-transcription and syllabification is provided, built by Josh Falk. In English, the process is more complicated. If the word is found in the [CMU pronunciation dictionary](http://www.speech.cs.cmu.edu/cgi-bin/cmudict), its syllabified, stressed, phonetic transcription is used. If not, a text-to-speech engine is used to "sound out" the unknown word, and then a syllabifier is used to break the stressed IPA transcription into syllables. For details on which text-to-speech engine and syllabifier are used, see above, "Text to speech engine for parsing unknown English words."

With these phonetic-phonological transcriptions, Prosodic builds each word as a hierarchy of its constituent parts. For instance, the English word "love" is interpreted:

	| (W1) <Word>	love	<'l ah v>
	|     [numSyll=1]
	|
	|-----| (W1.S1) <Syllable>                               
	      |     [prom.stress=1.0]
	      |
	      |-----| (W1.S1.SB1) <SyllableBody>
	            |     [shape=CVC]
	            |     [+prom.weight]
	            |
	            |-----| (W1.S1.SB1.O1) <Onset>
	                  |
	                  |-----| (W1.S1.SB1.O1.P1) <Phoneme>          [l]
	            |
	            |-----| (W1.S1.SB1.R2) <Rime>
	                  |
	                  |-----| (W1.S1.SB1.R2.N1) <Nucleus>
	                        |
	                        |-----| (W1.S1.SB1.R2.N1.P1) <Phoneme> [ʌ]
	                  |
	                  |-----| (W1.S1.SB1.R2.C2) <Coda>
	                        |
	                        |-----| (W1.S1.SB1.R2.C2.P1) <Phoneme> [v]


Due to this hierarchical organization, sophisticated queries become possible on the linguistic structures in their interrelationships. In other words, since the hierarchy defines basic "child-of" or "contained-in" relationships between linguistic structures, it is possible to query for, say, "all onsets *with* at least one voiced consonant *in* stressed syllables." (For more details on the included query language, see above).

### From phonology to metrics

Once these phonetic and phonological annotations on words are in place, metrical parsing can then use them as it tries to maximize the correspondence between metrically strong positions and, say, syllable stress. The parsing is performed in the spirit of Optimality Theory: (almost) all logically possibile parses are attempted, but the best parses are those that least violate a set of user-defined constraints. If Parse A's total violation score is, for each constraint, the same as Parse B's, but there is at least one constraint where Parse A's violation score is even worse than Parse B's—then parse A is "harmonically bounded" by parse B. Parse A is never better than Parse B; and in at least one instance, it's worse. No matter how the constraints are weighted, these "bounded" parses are categorically worse than others. The metrical parser, written primarily by [Josh Falk](https://github.com/jsfalk), works as fast as it does by disregarding harmonically bounded parses as it goes: this way, it doesn't have to travel further down a parse once it realizes that that parse has already been bounded by other parses.

The number of *unbounded* parses for a given line then represents something about the metrical complexity of the line. For instance, take (Shakespeare's) Richard III's line, "A horse! A horse! My kingdom for a horse!" Only one parse survives the harmonic bounding process:

	[parse #1 of 1]: 2.0 errors
	1	w	a         	
	2	s	HORSE     	
	3	w	a         	
	4	s	HORSE     	
	5	w	my        	
	6	s	KING      	
	7	w	dom       	
	8	s	FOR       	[*stress.s=>-u]
	9	w	a         	
	10	s	HORSE     	

	[*stress.s=>-u]: 2.0  

This parse only violates one constraint: it elevated an unstressed word, "for," to a metrically strong position. Compare this line to another of Shakespeare's, which has the same number of syllables, but is metrically more complex: "Never came poison from so sweet a place." Here, four parses survive:

	--------------------
	[parse #4 of 4]: 14.0 errors
	1	w	nev       	[*strength.w=>-p][*stress.w=>-p]
	2	s	ER        	[*strength.s=>-u][*stress.s=>-u]
	3	w	came      	[*stress.w=>-p]
	4	s	POI       	
	5	w	son       	
	6	s	FROM      	[*stress.s=>-u]
	7	w	so        	
	8	s	SWEET     	
	9	w	a         	
	10	s	PLACE     	

	[*strength.s=>-u]: 3.0  [*strength.w=>-p]: 3.0  [*stress.s=>-u]: 4.0  [*stress.w=>-p]: 4.0  
	--------------------

	--------------------
	[parse #3 of 4]: 13.0 errors
	1	s	NEV       	
	2	w	er        	
	3	s	CAME POI  	[*footmin-none][*footmin-no-s-unless-preceded-by-ww]
	4	w	son       	
	5	s	FROM      	[*stress.s=>-u]
	6	w	so        	
	7	s	SWEET     	
	8	w	a         	
	9	s	PLACE     	

	[*footmin-no-s-unless-preceded-by-ww]: 10.0  [*footmin-none]: 1.0  [*stress.s=>-u]: 2.0  
	--------------------

	--------------------
	[parse #2 of 4]: 9.0 errors
	1	s	NEV       	
	2	w	er came   	[*stress.w=>-p][*footmin-none]
	3	s	POI       	
	4	w	son from  	[*footmin-none]
	5	s	SO        	[*stress.s=>-u]
	6	w	sweet a   	[*stress.w=>-p][*footmin-none]
	7	s	PLACE     	

	[*footmin-none]: 3.0  [*stress.s=>-u]: 2.0  [*stress.w=>-p]: 4.0  
	--------------------

	--------------------
	[parse #1 of 4]: 6.0 errors
	1	s	NEV       	
	2	w	er came   	[*stress.w=>-p][*footmin-none]
	3	s	POI       	
	4	w	son       	
	5	s	FROM      	[*stress.s=>-u]
	6	w	so        	
	7	s	SWEET     	
	8	w	a         	
	9	s	PLACE     	[*posthoc-standardize-weakpos]

	[*footmin-none]: 1.0  [*posthoc-standardize-weakpos]: 1.0  [*stress.s=>-u]: 2.0  [*stress.w=>-p]: 2.0  
	--------------------

The best parse (at the bottom) is iambic with a trochaic inversion; it violates the constraint against demoting stressed syllables ("came") into a metrically weak position, as well as a constraint discouraging disyllabic positions. The next best is a dactylic interpretation of the line, but it too violates certain constraints. The third best tried to squeeze two syllables into a strong position, and the last—the traditional iambic parse—tried to alter the stress contour of "never," which violates constraints encouraging the correspondence between the meter and syllable "strength" in polysyllabic words.

The default metrical constraints are those proposed by Kiparsky and Hanson in their paper "A Parametric Theory of Poetic Meter" (Language, 1996). See `config.py` for a better description of these and other constraints.

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

To add a new language entirely, you can create a new dictionary in the above format and place it under `[prosodic_dir]/dicts/[language_twoletter_code]/[language_name].tsv`. Or, you can create a python file under `[prosodic_dir]/dicts/[language_twoletter_code]/[language_name].py`, which has a function `get(token,config={})`. This function must accept a word-token as its only argument, and Prosodic's configuration settings as an optional keyword argument, and it must return a list of tuples in the form:

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
