############################################
# [config.py]
# CONFIGURATION SETTINGS FOR A PARTICULAR METER
#
#
# Set the long-form name of this meter
name = "Prose Rhythm Class, Iambic Meter"
#
# [Do not remove or uncomment the following line]
Cs={}
############################################

############################################
# STRUCTURE PARAMETERS
#
# Parameters subject to conscious control by the poet. Kiparsky & Hanson (1996)
# call these "formally independent of phonological structure." By contrast,
# "realization parameters"--e.g., the size of a metrical position, which positions
# are regulated, and other constraints--"determine the way the structure is
# linguistically manifested, and are dependent on the prosodic givens of languge."
#
#
####
# [Number of feet in a line]
#
#Cs['number_feet!=2'] = 1       # require dimeter
#Cs['number_feet!=3'] = 1       # require trimeter
#Cs['number_feet!=4'] = 1       # require tetrameter
Cs['number_feet!=5'] = 10        # require pentameter
#Cs['number_feet!=6'] = 1       # require hexameter
#Cs['number_feet!=7'] = 1       # require heptameter
#
#
####
# [Headedness of the line]
#
#Cs['headedness!=falling'] = 1  # require a falling rhythm (e.g. trochaic, dactylic)
Cs['headedness!=rising'] = 10    # require a rising rhythm (e.g., iambic, anapestic)
#
############################################


############################################
# REALIZATION PARAMETERS
#
# All subsequent constraints can be seen as "realization parameters."
# See note to "structure parameters" above for more information.
#
#############################################
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
maxW=2
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
#Cs['strength.s=>-u']=1
#
# A weak metrical position may not contain any strong syllables ("peaks"):
# [Kiparsky and Hanson believe this is Shakespeare's meter]
Cs['strength.w=>-p']=100
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
#Cs['stress.s=>-u']=1
#
# A weak metrical position should not contain any stressed syllables:
#Cs['stress.w=>-p']=1
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
# [Constraints regulating HEADS of PHRASES]
#
# Phrasal heads as defined by Metrical Tree.
# The head of a phrase is the rightmost constituent of a local branch.
# In "Come to one mark, as many ways meet in one town", the phrasal heads
# are "mark" (one mark), "ways" (many ways), and "town" (one town).
#
###
# [Stricter versions:]
#
# A strong metrical position should not contain any feets of phrases (non-heads in branching phrases):
#Cs['phrasal_head.s=>-u']=10
#
# A strong metrical position should not contain any heads of phrases:
#Cs['phrasal_head.w=>-p']=1
#
###
# [Laxer versions:]
#
# A strong metrical position must contain at least one feets of phrases (non-heads in branching phrases):
#Cs['phrasal_head.s=>p']=2
#
# A weak metrical position must contain at least one phrasal head;
#Cs['phrasal_head.w=>u']=2
#
#
#
#######
# [Constraints regulating PHRASAL STRENGTH]
#
# Phrasal 'strength' as defined by Metrical Tree. Similar to "peaks" and "valleys"
# of Bruce Hayes' "A Grid-based Theory of Meter" (1983). A word is phrasally strong,
# or a phrasal "peak", if a word to its left or right is less phrasally stressed.
# Conversely, a word is phrasally "weak", or a phrasal "valley", if a word to its
# left or right is more phrasally stressed.
#
# [Caveat: A word can be both a stress valley and a stress peak, but a word cannot
# be both phrasally weak and strong. Phrasal peaks take precedence: only if a word
# is not also a phrasal peak can it be registered as a phrasal valley. We might want
# to change this, but this allows us to constrain phrasal strength in a manner
# homologous to how we constrain syllable strength.]
#
###
# [Stricter versions:]
#
# A strong metrical position should not contain any phrasally weak syllables:
#Cs['phrasal_strength.s=>-u']=10
#
# A weak metrical position should not contain any phrasally strong syllables:
#Cs['phrasal_strength.w=>-p']=1
#
###
# [Laxer versions:]
#
# A strong metrical position should contain at least one phrasally strong syllable:
#Cs['phrasal_strength.s=>p']=2
#
# A weak metrical position must contain at least one phrasally weak syllable;
#Cs['phrasal_strength.w=>u']=2
#
#
#
######
# [Constraints regulating PHRASAL STRESS]
#
# Phrasal stress as defined by Metrical Tree. A normalized numeric value is given
# to each word in the sentence, representing least (0) to most (1) stressed. Please
# see Tim Dozat's MetricalTree <https://github.com/tdozat/Metrics/> for more information.
#
# Constraint weights are multiplied against the numeric value; so if phrasally stressed syllables
# are prohibited, and that constraint's weight is "10", and the violating word has a phrasal
# stress value of 0.75, then the resulting violation score would be 10 * 0.75 = 7.5.
#
###
# [Configuration of phrasal stress]
#
# Because most words have *some* phrasal stress, a word is considered phrasally stressed
# if its numeric value is less than what is defined here; otherwise, it is considered
# phrasally unstressed. Default = 2, i.e., primary and secondary stresses count.
Cs['phrasal_stress_threshold']=2
#
#
# Should the above threshold be computed across the sentence, or the line? If this is 'sentence',
# then the above number (say, 2) refers to the secondary stresses in the *sentence.* If 'line',
# then it refers to the secondary stresses in the poetic *line* (i.e., the stress grid is moved up
# such that the biggest stress in the line becomes 1 (primary), etc.)
Cs['phrasal_stress_norm_context_is_sentence']=1
#Cs['phrasal_stress_norm_context_is_line']=1
#
#
#
###
# [Stricter versions:]
#
# A strong metrical position should not contain any phrasally unstressed syllables:
#Cs['phrasal_stress.s=>-u']=10
#
# A weak metrical position should not contain any phrasally stressed syllables:
Cs['phrasal_stress.w=>-p']=1
#
###
# [Laxer versions:]
#
# A strong metrical position should contain at least one phrasally stressed syllable:
#Cs['phrasal_stress.s=>p']=2
#
# A weak metrical position must contain at least phrasally unstressed syllable:
#Cs['phrasal_stress.w=>u']=2
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
# A disyllabic STRONG metrical position should not contain more than a minimal foot:
# (i.e. allowed positions are syllables weighted light-light or light-heavy)
Cs['footmin-s-noHX']=10
#
# A disyllabic metrical position should be syllables weighted light-light:
#Cs['footmin-noLH-noHX']=1
#
###
# [Categorical:]
#
# A metrical position should not contain more than one syllable:
# [use to discourage disyllabic positions]
#Cs['footmin-none']=1
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
# [this implementation is different in that it only takes into account
# double-weak beats *preceding* -- due to the way in which the parser
# throws away bounded parses as it goes, it might not be possible for now
# to write a constraint referencing future positions]
#Cs['footmin-no-s-unless-preceded-by-ww']=10
# [The version that does reference future positions; but appears to be unstable]:
#Cs['attridge-ss-not-by-ww']=10

#
###
# [For disyllabic positions crossing a word boundary...
# (i.e. having two syllables, each from a different word)...
#
# ...it should never cross a word boundary to begin with:
#Cs['footmin-wordbound']=1000
#
# ...both words should be function words:
Cs['footmin-wordbound-bothnotfw']=10
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
# ...neither word should be a LEXICAL monosyllable
# (i.e. function words and polysyllabic words ok)
#Cs['footmin-wordbound-lexmono']=1
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
#Cs['posthoc-no-final-ww']=2
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
#Cs['posthoc-standardize-weakpos']=1
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
# for any of the strength/stress/weight correspondence constraints:
# [set to 1 to be true]
#Cs['extrametrical-first-pos']=1
#
# The first two metrical positions will not be evaluated
# for any of the strength/stress/weight correspondence constraints:
# [set to 1 to be true]
Cs['skip_initial_foot']=1
#
# A word should not be an elision [use to discourage elisions]:
#Cs['word-elision']=1

#
# A weak metrical position should not contain any syllables
# that are stressed and heavy: [Meter of Finnish "Kalevala"]
#Cs['kalevala.w=>-p']=1
#
# A strong metrical position should not contain any syllables
# that are stressed and light: [Meter of Finnish "Kalevala"]
#Cs['kalevala.s=>-u']=1
############################################
