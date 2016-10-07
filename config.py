############################################
# [config.py]
# CONFIGURATION SETTINGS FOR PROSODIC
#
# Here you may change the runtime settings for prosodic.
# For more help on this file, please see the README in this folder,
# or visit it online: <https://github.com/quadrismegistus/prosodic>.
# If you have any questions, please email Ryan <heuser@stanford.edu>.
#
############################################


############################################
# PATHS USED BY PROSODIC
#
# If these are relative paths (no leading /),
# they are defined from the point of view of
# the root directory of PROSODIC.
#
# Folder used as the folder of corpora:
# [it should contain folders, each of which contains text files]
folder_corpora='corpora/'
#
# Folder to store results within (statistics, etc)
folder_results='results/'
#
# Folder in which tagged samples (hand-parsed lines) are stored:
folder_tagged_samples = 'tagged_samples/'
############################################


############################################
# SELECT THE LANGUAGE
#
# Select the language that will be used in PROSODIC,
# when typing text directly or loading text.
#
# All text is English:
lang='en'
#
# All text is Finnish:
#lang='fi'
#
# Detect language from first two characters of filename:
# e.g. "en.[filename].txt" is English, "fi.[filename].txt" is Finnish
#lang='**'
############################################


############################################
# CONFIGURE TEXT-TO-SPEECH ENGINE (for English)
#
# To parse unknown English words, you'll need a TTS engine installed.
# For instructions, please see the README.
#
# Use espeak for TTS (recommended):
# [Note: syllabification done with CMU Syllabifier]
en_TTS_ENGINE = 'espeak'
#
# Use OpenMary for TTS:
#en_TTS_ENGINE = 'openmary'
#
# Do not use TTS:
# [Lines with unknown words will be skipped during metrical parsing]
#en_TTS_ENGINE = 'none'
############################################


############################################
# OPTIONS ABOUT PRINTING TO SCREEN
# 
# Print loaded words, parses, etc. to screen:
print_to_screen=1
#
# Do not print loaded words, parses, etc. to screen:
# Although hiden, you may still save any output to disk
# using the /save command.
#print_to_screen=0
#
# The default length for the line used by printing
linelen=60
############################################


############################################
# METRICAL PARSING: POSITION SIZE
#
# Select how many syllables are at least *possible* in strong or weak positions
# cf. Kiparsky & Hanson's "position size" parameter ("Parametric Theory" 1996)
#
#
######
# [Maximum position size]
#
# The maximum number of syllables allowed in strong metrical positions (i.e. "s")
maxS=2
#
# The maximum number of syllables allowed in weak metrical positions (i.e. "w")
maxW=3
#
#
######
# [Minimum position size]
#
# (Recommended) Positions are at minimum one syllable in size
splitheavies=0
#
# (Unrecommended) Allow positions to be as small as a single mora
# i.e. (a split heavy syllable can straddle two metrical positions)
#splitheavies=1
############################################


############################################
# METRICAL PARSING: METRICAL CONSTRAINTS
#
# Here you can configure the constraints used by the metrical parser.
# Each constraint is expressed in the form:
#  Cs['(constraint name)']=(constraint weight)
# Constraint weights do not affect harmonic bounding (i.e. which parses
# survive as possibilities), but they do affect how those possibilities
# are sorted to select the "best" parse.
# 
# [Do not remove or uncomment the following line]
Cs={}
#
#
######
# [Constraints regulating the 'STRENGTH' of a syllable]
#
# A syllable is strong if it is a peak in a polysyllabic word:
# the syllables in 'liberty', stressed-unstressed-unstressed,
# are, in terms of *strength*, strong-weak-neutral, because
# the first syllable is more stressed than its neighbor;
# the second syllable less stressed; and the third equally stressed.
#
###
# [Stricter versions:]
#
# A strong metrical position should not contain any weak syllables ("troughs"):
Cs['strength.s=>-u']=3
#
# A weak metrical position may not contain any strong syllables ("peaks"):
# [Kiparsky and Hanson believe this is Shakespeare's meter]
Cs['strength.w=>-p']=3
#
###
# [Laxer versions:]
#
# A strong metrical position should contain at least one strong syllable:
#Cs['strength.s=>p']=3
#
# A weak metrical position should contain at least one weak syllable:
#Cs['strength.w=>u']=3
#
#
#
######
# [Constraints regulating the STRESS of a syllable]
#
###
# [Stricter versions:]
#
# A strong metrical position should not contain any unstressed syllables:
# [Kiparsky and Hanson believe this is Hopkins' meter]
Cs['stress.s=>-u']=2
#
# A weak metrical position should not contain any stressed syllables:
Cs['stress.w=>-p']=2
#
###
# [Laxer versions:]
#
# A strong metrical position should contain at least one stressed syllable:
#Cs['stress.s=>p']=2
# 
# A weak metrical position must contain at least one unstressed syllable;
#Cs['stress.w=>u']=2
#
#
#
######
# [Constraints regulating the WEIGHT of a syllable]
#
# The weight of a syllable is its "quantity": short or long.
# These constraints are designed for "quantitative verse",
# as for example in classical Latin and Greek poetry.
#
###
# [Stricter versions:]
#
# A strong metrical position should not contain any light syllables:
#Cs['weight.s=>-u']=2
#
# A weak metrical position should not contain any heavy syllables:
#Cs['weight.w=>-p']=2
#
###
# [Laxer versions:]
#
# A strong metrical position should contain at least one heavy syllable:
#Cs['weight.s=>p']=2
# 
# A weak metrical position must contain at least one light syllable;
#Cs['weight.w=>u']=2
#
#
#
######
# [Constraints regulating what's permissible as a DISYLLABIC metrical position]
# [(with thanks to Sam Bowman, who programmed many of these constraints)]
#
###
# [Based on weight:]
#
# A disyllabic metrical position should not contain more than a minimal foot:
# (i.e. allowed positions are syllables weighted light-light or light-heavy)
#Cs['footmin-noHX']=1
#
# A disyllabic metrical position should be syllables weighted light-light:
#Cs['footmin-noLH-noHX']=1
#
###
# [Categorical:]
#
# A metrical position should not contain more than one syllable:
# [use to discourage disyllabic positions]
Cs['footmin-none']=1
#
# A strong metrical position should not contain more than one syllable:
#Cs['footmin-no-s']=1
#
# A weak metrical position should not contain more than one syllable:
#Cs['footmin-no-w']=1
#
# A metrical position should not contain more than one syllable,
# *unless* that metrical position is the *first* or *second* in the line:
# [use to discourage disyllabic positions, but not trochaic inversions,
# or an initial "extrametrical" syllable]
#Cs['footmin-none-unless-in-first-two-positions']=1
#
# A metrical position should not contain more than one syllable,
# *unless* that metrical position is the *second* in the line:
# [use to discourage disyllabic positions, but not trochaic inversions]
#Cs['footmin-none-unless-in-second-position']=1
#
# A strong metrical position should not contain more than one syllable,
# *unless* it is preceded by a disyllabic *weak* metrical position:
# [use to implement the metrical pattern described by Derek Attridge,
# in The Rhythms of English Poetry (1982), and commented on by Bruce Hayes
# in his review of the book in Language 60.1 (1984).
# e.g. Shakespeare's "when.your|SWEET.IS|ue.your|SWEET.FORM|should|BEAR"
Cs['footmin-no-s-unless-preceded-by-ww']=10
#
###
# [For disyllabic positions crossing a word boundary...
# (i.e. having two syllables, each from a different word)...
#
# ...both words should be function words:
#Cs['footmin-wordbound-bothnotfw']=1
#
# ...at least one word should be a function word:
#Cs['footmin-wordbound-neitherfw']=1
#
# ...the left-hand syllable should be a function-word:
#Cs['footmin-wordbound-leftfw']=1
#
# ...the right-hand syllable should be a function word:
#Cs['footmin-wordbound-rightfw']=1
#
# ...neither word should be a monosyllable:
#Cs['footmin-wordbound-nomono']=1
#
###
# [Miscellaneous constraints relating to disyllabic positions]
#
# A disyllabic metrical position may contain a strong syllable
# of a lexical word only if the syllable is (i) light and 
# (ii) followed within the same position by an unstressed
# syllable normally belonging to the same word.
# [written by Sam Bowman]
#Cs['footmin-strongconstraint']=1
#
# The final metrical position of the line should not be 'ww'
# [use to encourage "...LI|ber|TY" rather than "...LI|ber.ty"]
Cs['posthoc-no-final-ww']=2
#
# The final metrical position of the line should not be 'w' or 'ww'
#Cs['posthoc-no-final-w']=2
#
# A line should have all 'ww' or all 'w':
# It works by:
# Nw = Number of weak positions in the line
# Mw = Maximum number of occurrences of 'w' metrical position
# Mww = Maximum number of occurrences of 'ww' metrical position
# M = Whichever is bigger, Mw or Mww
# V = Nw - M
# Violation Score = V * [Weight]
# [use to encourage consistency of meter across line]
# [feel free to make this a decimal number, like 0.25]
Cs['posthoc-standardize-weakpos']=1
#
#
#
######
# [MISCELLANEOUS constraints]
#
# A function word can fall only in a weak position:
#Cs['functiontow']=2
#
# An initial syllable must be in a weak position:
#Cs['initialstrong']=2
#
# The first metrical position will not be evaluated
# for any metrical constraints whatsoever:
# [set to 1 to be true]
#Cs['extrametrical-first-pos']=0
#
# The first two metrical positions will not be evaluated
# for any metrical constraints whatsoever:
# [set to 1 to be true]
#Cs['skip_initial_foot']=0
#
# A word should not be an elision [use to discourage elisions]:
Cs['word-elision']=1

#
# A weak metrical position should not contain any syllables
# that are stressed and heavy: [Meter of Finnish "Kalevala"]
#Cs['kalevala.w=>-p']=1
#
# A strong metrical position should not contain any syllables
# that are stressed and light: [Meter of Finnish "Kalevala"]
#Cs['kalevala.s=>-u']=1
############################################


############################################
# METRICAL PARSING: OPTIONS ABOUT LINES
#
######
# [Line SIZE]
#
# The maximum size of the line to parse:
# [others will be skipped during parsing]
# [PROSODIC can parse lines of up to approximately 20 syllables
# before the number of possibilities become too large,
# slowing the algorithm down to a halt.]
line_maxsylls=20
#
# The minimum size of the line to parse:
# [useful if lines are determined by punctuation,
# because sometimes they can be very very short
# and so pointless for metrical parsing.]
line_minsylls=8
#
#
######
# [Line DIVISIONS]
#
# Here you may decide how texts divide into lines.
# This is significant only because the line,
# with its words and syllables, is the unit passed
# to the metrical parser for parsing.
#
# Linebreaks occur only at actual linebreaks in the
# processed text file (good for metrical poetry):
linebreak='line'
#
# Linebreaks occur only upon encountering any of these
# punctuation marks (good for prose):
#linebreak=',;:.?!()[]{}<>'
#
# Linebreaks occur both at linebreaks in the text,
# *and* at any of these punctuation marks (good for
# prose and free-verse poetry):
#linebreak='line,;:.?!()[]{}<>'
#
#
######
# [MISCELLANEOUS line options]
#
# Headedness [optional]
# If there are multiple parses tied for the lowest score,
# break the tie by preferring lines that begin with this pattern:
line_headedness='ws'
#line_headedness='sw'
#line_headedness='wws'
#line_headedness='ssw'
############################################


############################################
# OPTIONS ABOUT WORDS
#
######
# [Tokenization]
# 
# How are lines of text split into words? Define the regular
# expression that is applied to a string of text in order
# to split it into a list of words.
#
# Words are tokenized against [^] white-spaces [\s+] and hyphens [-]
tokenizer='[^\s+-]+'
#
# Words are tokenized against [^] white-spaces [\s+]
#tokenizer='[^\s+]+'
#
######
# [Resolving stress ambiguity]
#
# Some words are multiple stress profiles: ambiguous polysyllabic
# words, and also ambiguous monosyllabic words. Words in the
# "maybestressed.txt" file of a language folder (e.g. dicts/en)
# will be given two stress profiles, one stressed and the other
# unstressed. The CMU also has multiple stress profiles for words.
#
# Allow the metrical parser to parse all stress profiles for all
# words in the line, thus choosing the stress profile for each
# word that best fit the metrical parse:
resolve_optionality=1
#resolve_optionality=0
#
#
######
# [ELISIONS of Syllables: English only]
# 
# Some syllables are elided in English verse, e.g.
# e.g. sweet as love, which overflows her bower
# --> with|MU|sic|SWEET|as|LOVE|which|OV|er|FLOWS|her|BOW'R
# or e.g. scattering unbeholden
# --> SCAT|tring|UN|be|HOLD|en
# 
# Add pronunciations for words that could have elided syllables:
add_elided_pronunciations=1
#add_elided_pronunciations=0
#
#
######
# [Output formatting]
# 
# Here you may change the format under which the syllabified,
# phonetic output will appear. The options are:
#  - ipa
#  - cmu (the formatting used in the CMU Pronunciation Dictionary)
#  - orth (the orthography itself [good for Finnish])
#
# The default phonetic output for all languages:
output='ipa'
#
# The phonetic output for English:
output_en='ipa'
#
# The phonetic output for Finnish:
output_fi='orth'		# since finnish pronunciation is essentially identical to its orthography
############################################

