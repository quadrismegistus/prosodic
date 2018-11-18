#encoding=utf-8
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
# METRICAL PARSING
#
# Set the default Meter ID: the filename to its configuration file
# in the "meters" subdirectory, e.g. "kiparskyhanson_shakespeare"
# (omit the .py from the filename).
#
meter = 'meter_default'
#
# If no Meter ID is provided, PROSODIC will ask you to set the meter
# in its interactive mode. As a python module, you will have to
# create the meter first and pass it to the Text object to parse.
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
#
# Cache results of TTS for an unknown word so it's not necessary
# to use TTS for that word again [Change to 0 to be false]
en_TTS_cache = 1
############################################

############################################
# CONFIGURE METRICALTREE
#
# Parse text using metrical tree? (Only for English).
parse_using_metrical_tree = False
############################################


############################################
# OPTIONS ABOUT PRINTING TO SCREEN
#
# Print loaded words, parses, etc. to screen:
#print_to_screen=True
#
# Do not print loaded words, parses, etc. to screen:
# Although hiden, you may still save any output to disk
# using the /save command.
print_to_screen=True
#
# The default length for the line used by printing
linelen=60
############################################


############################################
# OPTIONS ABOUT LINES
#
######
# [Line SIZE]
#
# The maximum size of the line to parse:
# [others will be skipped during parsing]
# [PROSODIC can parse lines of up to approximately 20 syllables
# before the number of possibilities become too large,
# slowing the algorithm down to a halt.]
line_maxsylls=60
#
# The minimum size of the line to parse:
# [useful if lines are determined by punctuation,
# because sometimes they can be very very short
# and so pointless for metrical parsing.]
#line_minsylls=9
#
# Alternatively, after how many seconds should Prosodic give up
# when trying to parse a (long or ambiguous) line?
parse_maxsec = 30
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
#tokenizer='[^\s+-]+'
#
# Words are tokenized against [^] white-spaces [\s+]
tokenizer='[^\s+]+'
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


############################################
# PATHS USED BY PROSODIC
#
# If these are relative paths (no leading /),
# they are defined from the point of view of
# the home directory for prosodic (~/prosodic_data).
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
# MAXIMUM ENTROPY settings
#
# Should negative weights be allowed?
negative_weights_allowed = False
#
# How many epochs should it run for at most?
max_epochs = 10000
#
# What should the step size be?
step_size = 0.1
#
# How small does the gradient have to be before
# we consider it converged?
gradient_norm_tolerance = 1e-6

############################################

####
# MEMORY DECISIONS
#
num_bounded_parses_to_store = 100
#
###
