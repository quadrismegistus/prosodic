# coding=utf-8
# symbol to demarcate syllable boundaries; should be one character
#SYLLABLE_SEPARATOR = '.'

# consonant clusters that should be kept together, following Karlsson 1985: (4)
#CLUSTERS = set(['bl', 'br', 'dr', 'fl', 'fr', 'gl', 'gr', 'kl', 'kr', 'kv', 'pl', 'pr', 'cl', 'qv', 'schm'])
#CLUSTER_LENGTHS = set(len(cluster) for cluster in CLUSTERS)

# sets of Finnish vowels, diphthongs, and consonants
#VOWELS = set(['i', 'e', 'ä', 'y', 'ö', 'a', 'u', 'o'])
#DIPHTHONGS = set(['ai', 'ei', 'oi', 'äi', 'öi', 'au', 'eu', 'ou', 'ey', 'äy', 'öy', 'ui', 'yi', 'iu', 'iy', 'ie', 'uo', 'yö'])
#CONSONANTS = set(['b', 'c', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'n', 'p', 'q', 'r', 's', 't', 'v', 'x', 'z', "'"]) # ' included for purposes of words like vaa'an

# following Anttila 2008 on Finnish stress (p. 5)
#SON_HIGH = set(['i', 'e', 'u', 'y'])
#SON_LOW = set(['a', 'ä', 'o', 'ö'])


SYLLABLE_SEPARATOR = '.'

# consonant clusters that should be kept together, following Karlsson 1985: (4)
CLUSTERS = set(['bl', 'br', 'dr', 'fl', 'fr', 'gl', 'gr', 'kl', 'kr', 'kv', 'pl', 'pr', 'cl', 'qv', 'schm'])
CLUSTER_LENGTHS = set(len(cluster) for cluster in CLUSTERS)

# sets of Finnish vowels, diphthongs, and consonants
VOWELS = set(['i', 'e', 'ä', 'y', 'ö', 'a', 'u', 'o'])
DIPHTHONGS = set(['ai', 'ei', 'oi', 'äi', 'öi', 'au', 'eu', 'ou', 'ey', 'äy', 'öy', 'ui', 'yi', 'iu', 'iy', 'ie', 'uo', 'yö'])
CONSONANTS = set(['b', 'c', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'n', 'p', 'q', 'r', 's', 't', 'v', 'x', 'z', "'"]) # ' included for purposes of words like vaa'an

# following Anttila 2008 on Finnish stress (p. 5)
SON_HIGH = set(['i', 'e', 'u', 'y'])
SON_LOW = set(['a', 'ä', 'o', 'ö'])



def is_vowel(ch):
    return ch in VOWELS

def is_consonant(ch):
    return ch in CONSONANTS

def is_cluster(ch):
    return ch in CLUSTERS

def is_diphthong(chars):
    return chars in DIPHTHONGS

def is_long(chars):
    return chars[0] == chars[1] # no error checking

# in a split syllable, the onset is the 0th element, the nucleus is the 1st, and the coda is the 2nd
class Syllable:
    onset = 0
    nucleus = 1
    coda = 2

# syllable weights in increasing order of weight, for purposes of deciding which syllable to stress in a sequence of two syllables
class Weight:
    CV = 0 # (C)V
    CVC = 1 # (C)VC+
    CVV = 2 # (C)VV+C*
    
    dict = {CV:'L', CVC:'H', CVV:'H'}

# return true if weight is greater than the weight of a light syllable
def is_heavy(weight):
    return weight > Weight.CV

# return true if weight1 is greater than weight2
def is_heavier(weight1, weight2):
    return weight1 > weight2

# modelled after CMU Pronouncing Dictionary
class Stress:
    none = 0
    primary = 1
    secondary = 2

    dict = {none:'U', primary:'P', secondary:'S'}

# given a single syllable, split it into a list of its onset, nucleus, and coda
def split_syllable(syllable):
    
    result = []
    
    i = 0
    while i < len(syllable) and is_consonant(syllable[i].lower()):
        i += 1

    nucleus_start = i
    result += [syllable[0:nucleus_start]] # store onset (composed of consonants)
    
    while i < len(syllable) and is_vowel(syllable[i].lower()):
        i += 1

    coda_start = i  
    result += [syllable[nucleus_start:coda_start]] # store nucleus (composed of vowels)

    result += [syllable[coda_start:]] # store coda (composed of consonants)

    return result
