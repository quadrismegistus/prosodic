############################################
# [config.py]
# CONFIGURATION SETTINGS FOR A PARTICULAR METER
#
#
# Set the long-form name of this meter
name = "*PEAK only"
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
#Cs['number_feet!=5'] = 1        # require pentameter
#Cs['number_feet!=6'] = 1       # require hexameter
#Cs['number_feet!=7'] = 1       # require heptameter
#
#
####
# [Headedness of the line]
#
#Cs['headedness!=falling'] = 1  # require a falling rhythm (e.g. trochaic, dactylic)
#Cs['headedness!=rising'] = 1    # require a rising rhythm (e.g., iambic, anapestic)
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
Cs['strength.w=>-p']=1
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
# [Constraints regulating what's permissible as a DISYLLABIC metrical position]
# [(with thanks to Sam Bowman, who programmed many of these constraints)]
#
###
# [Based on weight:]
#
# A disyllabic metrical position should not contain more than a minimal foot:
# i.e. W-resolution requires first syllable to be light and unstressed.
Cs['footmin-w-resolution']=1
#
#
# A disyllabic metrical position should not contain more than a minimal foot:
# (i.e. allowed positions are syllables weighted light-light or light-heavy)
#Cs['footmin-noHX']=1000
#
#
# A disyllabic STRONG metrical position should not contain more than a minimal foot:
# (i.e. allowed positions are syllables weighted light-light or light-heavy)
#Cs['footmin-s-noHX']=1
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
# ...allow only F-resolutions:
# (both words must be function words and be in a weak metrical position)
Cs['footmin-f-resolution']=1
#
# ...it should never cross a word boundary to begin with:
#Cs['footmin-wordbound']=1000
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
