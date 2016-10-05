# PROSODIC
PROSODIC is a a metrical-phonological parser written in pure Python. Currently, it can parse English and Finnish text, but adding additional languages is easy with a pronunciation dictionary or a custom python function. PROSODIC was built by [Ryan Heuser](https://github.com/quadrismegistus), [Josh Falk](https://github.com/jsfalk), and [Arto Anttila](http://web.stanford.edu/~anttila/), beginning in the summer of 2010. Josh also maintains [another repository](https://github.com/jsfalk/prosodic1b), in which he has rewritten the part of this project that does phonetic transcription for English and Finnish.

## About PROSODIC
PROSODIC does two main things. First, it tokenizes text into words, and the converts each word into its stressed, syllabified, IPA transcription. Second, if desired, it finds the best available metrical parse for each line of text. In the style of Optimality Theory, (almost) all logically possibile parses are attempted, but the best parses are those that least violate a set of user-defined constraints. The default metrical constraints are those proposed by Kiparsky and Hanson in their paper "A Parametric Theory of Poetic Meter" (Language, 1996). See below for how these and other constraints are implemented.

### Example of metrical parsing

Here's an example of the metrical parser in action, on Shakespeare's first sonnet.

	text                                    				parse                                   
	from fairest creatures we desire increase				from|FAI|rest|CREA|tures|WE|des|IRE|inc|REASE
	that thereby beauty's rose might never die				that|THE|reby|BEAU|ty's|ROSE|might|NE|ver|DIE
	but as the riper should by time decease 				but|AS|the|RI|per|SHOULD|by|TIME|dec|EASE
	his tender heir might bear his memory   				his|TEN|der|HEIR|might|BEAR|his|ME|mo|RY
	but thou contracted to thine own bright eyes			but|THOU|con|TRA|cted|TO|thine|OWN|bright|EYES
	feed'st thy light's flame with self substantial fuel	FEED'ST|thy|LIGHT'S|flame.with|SELF|sub|STA|ntial|FUE|l
	making a famine where abundance lies    				MAK|ing.a|FA|mine|WHERE|ab|UN|dance|LIES
	thy self thy foe to thy sweet self too cruel			thy|SELF|thy|FOE|to.thy|SWEET.SELF|too|CRU|el
	thou that art now the world's fresh ornament			thou|THAT|art|NOW|the|WORLD'S|fresh|ORN|ame|NT
	and only herald to the gaudy spring     				and|ONL|y|HER|ald|TO|the|GAU|dy|SPRING  
	within thine own bud buriest thy content				wi|THIN|thine|OWN|bud|BU|ri|EST|thy|CON|tent
	and tender churl mak'st waste in niggarding				and|TEN|der|CHURL|mak'st|WASTE|in|NIG|gard|ING
	pity the world or else this glutton be  				PI|ty.the|WORLD|or|ELSE|this|GLUT|ton|BE
	to eat the world's due by the grave and thee			to|EAT|the|WORLD'S|due|BY|the|GRAVE|and|THEE

Not bad, right? PROSODIC not only captures the sonnet's overall iambic meter, but also some of its variations. It accurately captures the trochaic inversions in the lines "*Mak*ing a *fam*ine *where* a*bun*dance *lies*" and "*Pi*ty the *world* or *else* this *glut*ton *be*." Also, depending on the constraints, it also captures the double-strong beat that can often follow a double-weak beat in the line "Thy *self* thy *foe* to thy *sweet self* too *cruel*" (see, for this metrical pattern, [Bruce Hayes' review of Derek Attridge's *The Rhythms of English Poetry* in *Language* 60.1, 1984](http://www.linguistics.ucla.edu/people/hayes/Papers/Hayes1984ReviewOfAttridge.pdf)).

### Accuracy of metrical parser

In preliminary tests, against a sample of 1800 hand-parsed lines of iambic, trochaic, anapestic, and dactylic verse, PROSODIC's accuracy is the following.

<center>
<table>
	<thead align=center>
		<tr>
			<th colspan="4">% Syllables Correctly Parsed</th>
			<th colspan="2">Comparison of % Syllables Correct</th>
		</tr>
		<tr>
			<th></th>
			<th width=130>PROSODIC</th>
			<th width=130>Baseline (known meter)</th>
			<th width=130>Baseline (iambic meter)</th>
			<th width=130><i>PROSODIC - Baseline (known meter)</i></th>
			<th width=130><i>PROSODIC - Baseline (iambic meter)</i></th>
		</tr>
	</thead>
	<tbody>
		<tr>
			<td>Iambic poems</td>
			<td><b>93.9%</b></td>
			<td>92.4%</td>
			<td>02.4%</td>
			<td style="color:green"><font color="green">+1.5%</font></td>
			<td style="color:green">+1.5%</td>
		</tr>
		<tr>
			<td>Trochaic poems</td>
			<td>93.7%</td>
			<td><b>94.0%</b></td>
			<td>5.8%</td>
			<td style="color:red">-0.4%</td>
			<td style="color:green">+87.8%</td>
		</tr>
		<tr>
			<td>Anapestic poems</td>
			<td><b>84.5%</b></td>
			<td>64.9%</td>
			<td>53.4%</td>
			<td style="color:green">+19.6%</td>
			<td style="color:green">+31.1%</td>
		</tr>
		<tr>
			<td>Dactylic poems</td>
			<td><b>81.2%</b></td>
			<td>80.0%</td>
			<td>49.8%</td>
			<td style="color:green">+1.2%</td>
			<td style="color:green">+31.4%</td>
		</tr>
	</tbody>
</table>
</center>

The data here show, we believe, that PROSODIC's parses match a human's about as often, and sometimes more often, than a bare template of the poem's meter does–that is, when we already know the meter of the poem. Not surprisingly, PROSODIC vastly outperforms a bare metrical template when that template doesn't match the poem: an iambic template works well for iambic poems, but not at all for poems of other meters. This means that, *for parsing poems whose meter is unknown*, or for parsing free verse poems or even prose, PROSODIC is especially useful. Its metrical descriptions, reliable enough when we know the meter of the poem, are then likely to be reliable enough (at least to be interesting) when we don't.

The data above were produced when the meter was defined as the following constraints and weights: `[*strength.s=>-u/3.0] [*strength.w=>-p/3.0] [*stress.s=>-u/2.0] [*stress.w=>-p/2.0] [*footmin-none/1.0] [*footmin-no-s-unless-preceded-by-ww/10.0] [*posthoc-no-final-ww/2.0] [*posthoc-standardize-weakpos/1.0] [*word-elision/1.0]`. These and other constraints will be discussd below.


## Installation

### Quick start

To install PROSODIC, it's best to pull the github repository here. To do that, type this into the terminal:

	git clone git@github.com:quadrismegistus/prosodic.git
	
If yo don't have git, you can [get it here](https://git-scm.com/downloads). Or, you can also [download the repository as a zip file](https://github.com/quadrismegistus/prosodic/archive/master.zip), and unzip it. Either method will create a directory called "prosodic." Enter that folder in the terminal, and boot up prosodic by typing:

	python prosodic.py
	
PROSODIC can also be used as a python module within your own applications:

	import prosodic as p
	text = p.Text("Shall I compare thee to a summer's day?")
	text.parse()

Instructions on how to use PROSODIC in interactive mode, and as a python module, are below. 

### Dependencies

#### Text to speech engine for parsing unknown English words

By default, PROSODIC uses the CMU pronunciation dictionary to discover the syllable boundaries, stress pattern, and other information about English words necessary for metrical parsing. Lines with words not in this dictionary are, again by default, skipped when parsing. However, with a Text-to-Speech engine, it's possible to "sound out" unknown English words into a stressed, syllabified form that can then be parsed. PROSODIC supports two TTS engines: *espeak* (recommended), and *OpenMary*. I find that espeak produces better syllabifications than OpenMary (at least for English), and is simpler to use, but either will work just fine.

##### Setting up espeak

[Espeak](http://espeak.sourceforge.net/) is an open-source TTS engine for Windows and Unix systems (including Mac OS X). You can [download it for your operating system here](http://espeak.sourceforge.net/download.html). But if you're running Mac OS X, an even simpler way to install espeak is via the [HomeBrew package manager](http://brew.sh/). To do so, install homebrew if you haven't, and then run in a terminal: `brew install espeak`. After you've installed espeak, set the "en_TTS_ENGINE" flag in the *config.txt* file to "espeak." That's it!

<small>*Note:* Espeak produces *un*-syllabified IPA transcriptions of any given (real or unreal) word. To syllabify these, the [syllabifier](https://p2tk.svn.sourceforge.net/svnroot/p2tk/python/syllabify/syllabifier.py) from the [Penn Phonetics Toolkit (P2TK)](https://www.ling.upenn.edu/phonetics/old_website_2015/p2tk/) is used. An extra plus from this pipeline is consistency: this same syllabifier is responsible for the syllable boundaries in the CMU pronunciation dictionary, which PROSODIC draws from (if possible) before resorting to a TTS engine.</small>

##### Setting up OpenMary

OpenMary is another open-source TTS engine, written in Java and developed by two German research institutes: the [DFKI](http://www.dfki.de/web)'s [Language Technology Lab](http://www.dfki.de/lt/) and [Saarland University](http://www.uni-saarland.de/startseite.html)'s [Institute of Phonetics](http://www.coli.uni-saarland.de/groups/WB/Phonetics/). To install OpenMary, first [download it here](http://mary.dfki.de/download/index.html) [select the "Run time package" link]. Then, unzip the zip file, go into the unzipped folder, and start OpenMary as a server. To do that, type into the terminal after unzipping: `./marytts-5.2/bin/marytts-server.sh`. To use OpenMary in PROSODIC, you'll have to make sure OpenMary is running as a server process beforehand; if not, you'll have to repeat the last command. For espeak, this step isn't necessary.

#### Python module dependencies

By default, PROSODIC has no module dependencies. The modules it does use—[lexconvert](http://people.ds.cam.ac.uk/ssb22/gradint/lexconvert.html), [P2TK](https://www.ling.upenn.edu/phonetics/old_website_2015/p2tk/)'s [syllabify.py](https://p2tk.svn.sourceforge.net/svnroot/p2tk/python/syllabify/syllabifier.py), and a [python imlpementation of the hyphenation algorithm in TeX](http://nedbatchelder.com/code/modules/hyphenate.html)—are small, and already included in the repository. However, there are a few exceptions, depending on what you want to do. To install these modules, first [install pip](https://pip.pypa.io/en/stable/installing/) if you haven't yet.

- If you'd like to use the built-in query language (available under "/query" in the interactive mode), you'll need to install pyparsing: `pip install pyparsing`.
- If you're running OpenMary, you'll need to install the xml parser Beautiful Soup 4, and the unicode module unidecode: `pip install bs4` and `pip install unidecode`.
- If you'd like to be able to read evaluation data in spreadsheet form (*.xls, *.xlsx) (available under "/eval" in interactive mode), you'll need to install xlrd: `pip install xlrd`.



## Usage

There are two main ways of using PROSODIC: in interactive mode, and, for more Python-advanced users, as a Python module.

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

The first thing to do when using PROSODIC is to give it some text to work with. There's a few ways of doing this. The simplest way is to simply a type in a line, one at a time. You can also type `/paste`, and then enter or copy/paste multiple lines in at a time. You can also type `/text` to load a text, or `/corpus` to load a folder of text files. If you do, you'll be given instructions on how either to specify a relative path from within PROSODIC's corpus folder, or an absolute path to another file or folder on your disk. You can also define the text you want to work with as an argument for the command you use to boot PROSODIC with: `python prosodic.py /path/to/my/file.txt`.

#### Checking phonetic/phonological annotations

Even before metrically parsing the text you've loaded (see below), you can run a few commands to test out how PROSODIC has interpreted the text in terms of its phonetics and phonology. The command `/show` will show the phonetic transcription and stress- and weight-profiles for each word:

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

Lastly, the `/query` command allows you to query these phonological annotations. Once `/query` is entered, the query language parser starts up (type `/` to exit, or hit `Ctrl+D`). Which are the stressed syllables in the text? `(Syllable: [+prom.stress])`. Which are all the voiced phonemes? `(Phoneme: [+voice])`. Which are all the syllables with voiced onsets and codas? `(Syllable: (Onset: [+voice]) (Coda: [+voice]))`.


#### Metrically parsing text

The command `/parse` will metrically parse whatever text is currently loaded into PROSODIC. Once the text is parsed, further commands become possible, all of which either view or save the data gleaned from the parser.

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

How well does PROSODIC do when its metrical parses are compared with those that a human reader has annotated? The statistics above, in "Accuracy of metrical parser," were generated from the evaluation command: `/eval`. From there, you can select a spreadsheet (either a tab-separated text file or an excel document) saved in the `tagged_samples/` folder to use as the "ground truth", human-annotated parse. The `/eval` command will ask which columns in the file correspond to the line ("Of man's first disobedience and the fruit"), the parse ("wswswswwsws"), and (optionally) the meter of the line ("iambic"). PROSODIC will then parse the lines under the "line" column (using, as always, the current configuration of metrical constraints in `config.txt`), and save statistics to the same folder in tab-separated form. The spreadsheet used in the above accuracy table is provided, made by the Stanford Literary Lab's [poetry project](http://github.com/quadrismegistus/litlab-poetry) in 2014.

### Configuration options

ee

### Running PROSODIC as a python module

ee


## How it works


### Overview of the IPA transcription process

PROSODIC first encounters a piece of English or Finnish text. It tokenizes that text according to a user-defined tokenizer, set under the option "tokenizer" in *config.txt*, defaulting to splitting lines into words by whitespace and hyphens. In Finnish text, a pure-Python implementation of Finnish IPA-transcription and syllabification is provided, built by Josh Falk. In English, the process is more complicated.

Prosodic annotates a given word in a language it recognizes by interpreting that word as a hierarchical organization of its phonological properties: a word contains syllables; which contain onsets, nuclei, and coda; which themselves contain phonemes. For instance, the English word "love" is interpreted:

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


Due to this hierarchical organization, sophisticated queries become possible on the linguistic structures in their interrelationships. In other words, since the hierarchy defines basic "child-of" or "contained-in" relationships between linguistic structures, it is possible to query for, say, "all onsets *with* at least one voiced consonant *in* stressed syllables." (For more details on the included query language, see below).

### Overview of metrical parser

Metrical parsing is performed in the spirit of Optimality Theory: given user-specified constraints, along with a parameter specifying the maximum number of syllables allowed in strong/weak metrical positions, all non-harmonically-bounded scansions of the line are generated, and ranked in terms of their weighted violation scores.
	- note: These and all other user-specified configurations occur in the file "config.txt" in the main prosodic directory. See that file or instructions, or #5 below for more details.

Included constraints:
	- Prosodic includes built-in support for 13 constraints, all of which we have taken from {"A Parametric Theory of Poetic Meter", Kiparsky & Hanson, Language, 1996}:
		foot-min			# a metrical position may not contain *more than* a minimal foot (ie, weight-wise, allowed positions are H, L, LL, or LH)

	strength.s=>-u		# a *strong* metrical position may not contain *any* "weak" syllables, or "troughs" (ie, the monosyllable rule, strong version 1)
	strength.w=>-p		# a *weak* metrical position may not contain *any* "strong" syllables, or "peaks" (ie, the monosyllable rule, strong version 2)
	strength.s=>p		# a *strong* metrical position must contain *at least one* syllable which is *prominent* in terms of *strength* (ie, the monosyllable rule, weak version 1)
	strength.w=>u		# a *weak* metrical position must contain *at least one* syllable which is *unprominent* in terms of *strength* (ie, the monosyllable rule, weak version 2)

	stress.s=>-u		# a *strong* metrical position may not contain *any* unstressed syllables
	stress.w=>-p		# a *weak* metrical position may not contain *any* stressed syllables
	stress.s=>p			# a *strong* position must contain *at least one* stressed syllable
	stress.w=>u			# a *weak* position must contain *at least one* unstressed syllable

	#weight.s=>-u		# a *strong* metrical position may not contain *any* light syllables
	#weight.w=>-p		# a *weak* metrical position may not contain *any* heavy syllables
	weight.s=>p			# a *strong* metrical position must contain *at least one* heavy syllable
	weight.w=>u			# a *weak* metrical position must contain *at least one* light syllable		







[6. HOWTO: EXPAND PROSODIC'S LANGUAGE COVERAGE]
 A. There are two possible methods by which Prosodic can understand a language:
	i. using a dictionary (eg, English) in the format:
		{word token}[tab]{stressed, syllabified, IPA format}
		- eg:
			befuddle	bɪ.'fə.dəl
			befuddled	bɪ.'fə.dəld
			befuddles	bɪ.'fə.dəlz

	ii. using an on-the-fly syllabifier (eg, Finnish) which has takes in a {word-token} as an input, and a {stressed, syllabified, IPA format} as its output
	
 B. To add a new word to a dictionary-language, simply add an entry in the above format to the dictionary [language_name].tsv under the folder ([prosodic_dir]/dicts/[language_twoletter_code]).

 C. To add a new language, either:
	i. create a new dictionary in the above format and place it under ([prosodic_dir]/dicts/[language_twoletter_code]/[language_name].tsv)
	ii. or create a python file under ([prosodic_dir]/dicts/[language_twoletter_code]/[language_name].py),
		which has a function "get" which accepts a word-token as its only argument, and which outputs a tuple of (stressed-syllabified-ipa,[optionally]syllabified-orthography) as its only output
