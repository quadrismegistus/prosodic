# PROSODIC
PROSODIC is a a metrical-phonological parser written in pure Python. Currently, it can parse English and Finnish text, but adding additional languages is easy with a pronunciation dictionary or a custom python function. PROSODIC was built by [Ryan Heuser](https://github.com/quadrismegistus), [Josh Falk](https://github.com/jsfalk), and [Arto Anttila](http://web.stanford.edu/~anttila/), beginning in the summer of 2010. Josh also maintains [another repository](https://github.com/jsfalk/prosodic1b), in which he has rewritten the part of this project that does phonetic transcription for English and Finnish.

## About PROSODIC
PROSODIC does two main things. First, it tokenizes text into words, and the converts each word into its stressed, syllabified, IPA transcription. Second, if desired, it finds the best available metrical parse for each line of text. In the style of Optimality Theory, (almost) all logically possibile parses are attempted, but the best parses are those that least violate a set of user-defined constraints. The default metrical constraints are those proposed by Kiparsky and Hanson in their paper "A Parametric Theory of Poetic Meter" (Language, 1996). See below for how these and other constraints are implemented.

## Example of metrical parsing

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

## Accuracy of metrical parser

In preliminary tests, against a sample of 1800 hand-parsed lines of iambic, trochaic, anapestic, and dactylic verse, PROSODIC's accuracy is the following.

<table>
	<thead align=center>
		<tr style="font-style:italic">
			<th></th>
			<th colspan="3">% Syllables Correctly Parsed</th>
			<th colspan="3">% Lines Correctly Parsed</th>
		</tr>
		<tr>
			<th></th>
			<th>PROSODIC</th>
			<th>Baseline (knowing meter)</th>
			<th>Baseline (iambic)</th>
			<th>PROSODIC</th>
			<th>Baseline (knowing meter)</th>
			<th>Baseline (iambic)</th>
		</tr>
	</thead>
	<tbody>
		<tr>
			<td>Iambic</td>
			<td>89.9%</td>
			<td>93.6%</td>
			<td>93.6%</td>
			<td>68.5%</td>
			<td>83.3%</td>
			<td>83.3%</td>
		</tr>
		<tr>
			<td>Trochaic</td>
			<td>91.6%</td>
			<td>94.4%</td>
			<td>5.6%</td>
			<td>77.7%</td>
			<td>93.2%</td>
			<td>4.9%</td>
		</tr>
		<tr>
			<td>Anapestic</td>
			<td>85.0%</td>
			<td>64.2%</td>
			<td>53.3%</td>
			<td>47.3%</td>
			<td>41.3%</td>
			<td>0.0%</td>
		</tr>
		<tr>
			<td>Dactylic</td>
			<td>83.0%</td>
			<td>80.7%</td>
			<td>50.1%</td>
			<td>40.9%</td>
			<td>57.5%</td>
			<td>0.0%</td>
		</tr>
	</tbody>
</table>

The data here show, we believe, that PROSODIC is about as good or better than a bare template of the poem's meter at accurately capturing the metrical position of syllables—sometimes better capturing, in other words, the metrical variations in the poems. Moreover, PROSODIC vastly outperforms a bare metrical template when that template does not match the poem: an iambic template works well for iambic poems, but not at all for poems of other meters. This means that, for parsing poems whose meter is unknown, or for parsing free verse poems or even prose, PROSODIC is especially useful. Its metrical descriptions, reliable enough when we know the meter of the poem, are then arguably reliable enough (at least to be interesting) when we don't.

The data above were produced when the meter was defined as the following constraints and weights: *strength.s=>-u/3 strength.w=>-p/3 stress.s=>-u/2 stress.w=>-p/2 footmin-none/1 footmin-no-s-unless-preceded-by-ww/10 posthoc-no-final-ww/1 posthoc-standardize-weakpos/1*. These constraints will be discussd below. 







## Overview of the IPA transcription process

PROSODIC first encounters a piece of English or Finnish text. It tokenizes that text according to a user-defined tokenizer, set under the option "tokenizer" in *config.txt*, defaulting to splitting lines into words by whitespace and hyphens. In Finnish text, a pure-Python implementation of Finnish IPA-transcription and syllabification is provided, built by Josh Falk. In English, the process is more complicated.


 A. Prosodic annotates a given word in a language it recognizes by interpreting that word as a hierarchical organization of its phonological properties.
	
	i. These properties include:
		- Word				# the word
		- Syllable			# the syllable with respect to the word in which it exists (ie, with stress information)
		- SyllableBody		# the syllable, without respect to the word in which it exists (ie, Onset+Rime)
		- Onset				# the syllable onset
		- Rime				# the syllable rime
		- Nucleus			# the syllable nucleus
		- Coda				# the syllable coda
		- Phoneme(s)		# the phonemes referenced by Onsets, Nuclei, and Codae
	
	ii. For instance, the English word "love" is interpreted:
		
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

 B. We find two main virtues to this object-oriented approach:

	i. Since each object (eg. Word, Syllable, SyllableBody...) is defined by the sum of its features -- or, conversely, has only those features which define it -- sophisticated queries become possible on the linguistic structures in their interrelationships. In other words, since the hierarchy defines basic "child-of" or "contained-in" relationships between linguistic structures, it is possible to query for, say, "all onsets *with* at least one voiced consonant *in* stressed syllables." (For more details on the query language, see #?).
		
	ii. A more technical benefit is memory-conservation: since each level of the hierarchy is represented by an independent 'object' in the program's memory, Prosodic can 'recycle' all future references to the same linguistic object. For instance, the word "beloved" would not recreate the Syllable ['l ah v] and all its children, but simply attach a 'reference' to the already-created ['l ah v] in the computer's memory. Given the finitude of the phonological properties in any language, this approach accelerates the annotation of a given text, as that text is ultimately bound to reuse words, syllables, onsets, etc.




[2. OVERVIEW: METRICAL PARSING]
 A.  When annotating a text, Prosodic not only builds objects at the level of the word and below, but also groups words into lines, lines into "stanzas", stanzas into texts, and (potentially) texts into corpora. These further groupings are not necessarily relevant to Prosodic's first main function of linguistic annotation; however, they do come into play in the program's second main function of metrical parsing, as it is the Line which is passed to the metrical parser.

 B. Metrical parsing is performed in the spirit of Optimality Theory: given user-specified constraints, along with a parameter specifying the maximum number of syllables allowed in strong/weak metrical positions, all non-harmonically-bounded scansions of the line are generated, and ranked in terms of their weighted violation scores.
	- note: These and all other user-specified configurations occur in the file "config.txt" in the main prosodic directory. See that file or instructions, or #5 below for more details.

 C. Included constraints:
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

 D. <A technical aside on the engine behind parsing: Josh?>




[3. HOWTO: RUN PROSODIC]
 A. There are three possible ways to initiate prosodic:
	i. With no arguments:
		- [enter:] 	python [path_to_prosodic]/prosodic.py
		- [effect:]	This has the effect of bringing the user to the "interactive mode" of the script (for more details, see #4 below).
		- [uses:]	This runtime method is most useful for testing out prosodic: entering a line, looking at its syllabifications, parsing it, and so on.
		
	ii. With one argument: a text-file or directory of text-files
		- [enter:]	python [path_to_prosodic]/prosodic.py [path_to_textfile_or_directory]
		- [effect:]	This runtime method is unique in that it does *not* bring the user into the interactive mode of the script; instead, as Prosodic annotates the text or corpus, it outputs the following:
						## loading Text en.poison.txt...
						1	never       P:'n eh . v er     S:PU		W:LH
						2	came        P:'k ey m          S:P		W:H
						3	poison      P:'p oy . z ah n   S:PU		W:HH
						4	from        P:f er m           S:U		W:H
						5	so          P:'s ow            S:P		W:H
						6	sweet       P:'s w iy t        S:P		W:H
						7	a           P:ah               S:U		W:L
						8	place       P:'p l ey s        S:P		W:H
						. . .
		- [uses:]	The principal benefit of this method is that it allows the user to manipulate this output using other terminal-based commands.
					For instance, to "pipe" this output to a separate file:
						python prosodic.py file.txt > myoutput.txt
					Or to use "grep" to search for patterns in the pronunciation (P:), stress (S:), and/or weight outputs (W:):
						<some grep example(s) from Arto here?>

	iii. With two arguments: (1) a text-file or directory of text-files, and (2) any other character or string, eg "$"
		- [enter:]	python [path_to_prosodic]/prosodic.py [path_to_textfile_or_directory] $
		- [effect:]	Like ii, this method annotates the text or directory of texts; however, it does not output the above, but instead brings the user to the interactive mode of the script.
		- [uses:]	If you want to parse a particular text or corpus, it's often more convenient to load that text or directory as an argument; but in order to parse, one needs to be "inside" the interactive mode of the script. This third option is geared toward this and other uses which require using Prosodic's interactive commands (see just below, #4).




[4. HOWTO: USE PROSODIC'S INTERACTIVE COMMANDS]
 A. Once "inside" the interactive mode of the script -- which can be arrived at either by initiating prosodic with no arguments (see #3.i), or with two arguments (see #3.iii) -- Prosodic features several commands you can run by typing "/" followed by the command's name, and then hitting [return].

 B. Loading commands:
	i. /text
		- Without any "argument" -- ie, anything following the command "/text" -- this command will show all the text-files contained under the "corpusfolder": by default, "corpora/" under the main prosodic directory.
		- With an argument -- ie, a path to a particular text-file, which can either begin from the "corpusfolder" ([prosodic_dir]/corpora/) or from the root directory of your machine -- this command will load and annotate the text whose path you have given.
	
	ii. /corpus
		- As with /text above, without an "argument" (ie, here, a path to a directory), this command will show all the directories contained under the "corpusfolder" ([prosodic_dir]/corpora/).
		- With an argument -- also as with /text, a path to a directory which can either begin from the corpusfolder or from the root of your machine -- this command will load and annotate all the text-files contained within the directory whose path you have given.
		
	iii. [any text not beginning with a /]
		- To have Prosodic annotate text not contained in a text-file or directory, simply type that text directly and hit [return].
		- note: You may use the "/" character to separate multiple lines. (Be careful that your line does not begin with a /, as this will be interpreted as a "command").
	
 C. Parsing commands:
	i. /parse
		- This command will metrically parse either the lines of the text you have loaded, or the line(s) of the text you have typed into Prosodic directly.
		- This command makes the following further commands possible, which all either view or save the data gleaned from the parser:
	
	ii. /scan
		- This is the brief version of the parsing output-viewer, which prints only the 1 or more parses which have the lowest weighted violation score.
		- eg:
				(3 best parse(s): weighted score of 20)	[24 others]
	       		NE|ver|CAME|poi.son|FROM|so|SWEET|a|PLACE
	       		NE|ver|CAME.POI|son|FROM|so|SWEET|a|PLACE
	       		NE|ver.came|POI|son|FROM|so|SWEET|a|PLACE
		
	iii. /report
		- This command is the verbose version of the parsing output-viewer, which prints, for every non-harmonically-bounded parse of every line, its viola
	 	- eg:
				[parse #1 of 27]: 20 errors
				1	s	NE        	[*weight.s=>p]
				2	w	ver       	[*weight.w=>u]
				3	s	CAME      	
				4	w	poi son   	[*weight.w=>u][*foot-min]
				5	s	FROM      	[*stress.s=>p]
				6	w	so        	[*stress.w=>u][*weight.w=>u]
				7	s	SWEET     	
				8	w	a         	
				9	s	PLACE     	
				[*foot-min]:10  [*strength.s=>p]:0  [*stress.w=>u]:3  [*stress.s=>p]:3  [*strength.w=>u]:0  [*weight.s=>p]:1  [*weight.w=>u]:3
		
	iv. /stats
		- This command saves four tab-separated statistics-files to the folder ([prosodic_dir]/results/data):
			-- parsing statistics by position
			-- parsing statistics by line
			-- parsing statistics by text
			-- the standard Optimality Theory output, of line[tab]parse[tab]violation_scores
			
	v. /draw
		- This command computes a directed graph, akin to a finite state machine, of all the non-harmonically bounded parses, and saves it to the folder ([prosodic_dir]/results/metnets/).
		- Unfortunately, this command requires several other packages to be installed on your machine:
			-- networkx <http://networkx.lanl.gov/>
			-- pydot <http://dkbza.org/pydot.html>
			-- graphviz <http://www.graphviz.org/>
		
 D. Query command:
	i. /query
		- This command allows the user to perform queries on the linguistic annotations performed on the inputted text.
		- <need help on documenting possible query combinatorics?>
	
 E. Structure-viewing command:
	i. /tree
		- This command shows a tabbed-hierarchical display of the inputted text.
		- eg: see (#1.ii) above.
		
 F. Exiting commands:
	i. /exit
		- softly, stage left!
	
	ii. [Ctrl]+C
		- hard, stage right!


[5. HOWTO: CONFIGURE PROSODIC]
 A. All configuration options are stored in the file "config.txt". Please see that file for more detailed instructions.

 B. There are three main areas of configuration:
	i. Options for the metrical parser (maximum position size, and metrical constraints);
	ii. options determining how texts group words into lines (by linebreak, punctuation, or both);
	iii. how linguistic annotations are displayed.




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
