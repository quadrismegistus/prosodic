# coding=utf-8
from finnish_functions import *

# -*- coding: utf-8 -*-

# note: initial consonant cluster not listed in inseparable clusters will be split up (e.g., traffic -> .t.raf.fic.)

# for a word w, syllable boundaries are represented by a list l of length len(w)+1
# l[i] = 1 iff w[i] should be preceded by a syllable boundary, else l[i] = 0
# thus, the first and last elements of l are always 1 (since words are surrounded by syllable boundaries)

# fill dict with key-value pairs where key is an entry from entries with the hyphens removed,
# value is a list representing syllable boundaries as described above
def initialize_dict(dict, entries, separator):
    for entry in entries:
        hyphen_free = entry.replace(separator, '').lower()
        boundary_list = [1]
        i = 1
        while i < len(entry):
            if entry[i] == separator:
                boundary_list += [1]
                i += 1
            else:
                boundary_list += [0]
            i += 1
        dict[hyphen_free] = boundary_list + [1]

# initialize a dictionary from a file
# the first line of the file is the separator character
# the remaining lines are words with separations marked by the separator character
def initialize_dict_from_file(dict, filename):
    
    try:
        
        f = open(filename, 'r')
        entries = f.readlines()
        f.close()

        for i in range(len(entries)-1):
            entries[i] = entries[i][:-1] # remove final newline character
            
        separator = entries[0]
        entries = entries[1:]
        initialize_dict(dict, entries, separator)
        
    except IOError:
        
        print "Error: File not found."

pre_sep_dict = {} # map between words that have been hand-annotated and their annotations

# initialize the presyllabified words from a file of format described above
def initialize_presyllabified(filename):

    initialize_dict_from_file(pre_sep_dict, filename)

vowel_seq_dict = {} # map between sequences of three and for vowels and their syllabifications [modelled after Karlsson 1985: (2b), but using Karlsson 1982 T-5/T-7 to deal with 'ieu', 'uoi']
VOWEL_SEQUENCES = ['ai-oi', 'ai-ui', 'au-oi', 'eu-oi', 'ie-oi', 'ie-ui', 'oi-oi', 'oi-ui', 'uo-ui', 'yö-yi', 'a-ei', 'a-oi', 'e-ai', 'e-oi', 'e-äi', 'e-öi', 'i-ai', 'i-au',
                   'i-oi', 'i-äi', 'i-öi', 'o-ai', 'u-ai', 'u-ei', 'u-oi', 'y-ei', 'y-äi', 'ä-yi', 'ä-öi', 'ai-a', 'ai-e', 'ai-o', 'ai-u', 'au-a', 'au-e', 'eu-a', 'ie-a', 'ie-o', 'ie-u', 'ie-y',
                   'i-o-a', 'i-o-e', 'i-ö-e', 'i-ö-ä', 'iu-a', 'iu-e', 'iu-o', 'oi-a', 'oi-e', 'oi-o', 'oi-u', 'ou-e', 'ou-o', 'u-e-a', 'ui-e', 'uo-a', 'uo-u', 'y-e-ä', 'yö-e', 'äi-e']
initialize_dict(vowel_seq_dict, VOWEL_SEQUENCES, '-')

# return the index of the start of the first long vowel in chars; -1 if absent
def locate_long(chars):
    for i in range(len(chars)-1):
        if is_long(chars[i:i+2]):
            return i
    return -1

# diphthongs and long vowels should not be split
def is_inseparable_vowels(chars):
    return is_diphthong(chars) or is_long(chars)

# return true if chars is an inseparable cluster or a lone consonant
def consonantal_onset(chars):
    return is_cluster(chars) or is_consonant(chars)

# applied Karlsson (3c); only checks for 'ien', since others are handled by vowel splitting rules
# word-final 'ien' will be syllabified 'i-en', unless following a 't'
def apply_3c(word, boundary_list):
    
    sequence = 'ien'
    seq_len = len(sequence)
    
    if len(word) > seq_len:
        
        if word[-seq_len:] == sequence and word[-(seq_len+1)] != 't':
            
            boundary_list[-3] = 1 # last entry is for word-final syllable boundary

# Karlsson 1982: T-4 applies to diphthongs ending in 'u' and 'y'
t4_final_v = ['u', 'y']
t4_diphthongs = set(vv for vv in DIPHTHONGS if vv[-1] in t4_final_v)

# apply rule T-4 from Karlsson 1982 to two vowels, assuming the word is already syllabified
def apply_t4(word, boundary_list):
    
    for i in range(3, len(word)): # check for rule application at syllable boundary (including word end); first possible boundary at index 3 (VVC-)

        if boundary_list[i] == 1:

            # if syllable ends in a T-4 diphthong followed by a consonant, introduce split in former diphthong
            if is_consonant(word[i-1]) and word[i-3:i-1] in t4_diphthongs:

                    boundary_list[i-2] = 1

    return word

# return vowels with syllable boundaries for appropriate separations
def separate_vowels(vowels, boundary_list, start):

    v_len = len(vowels)
    
    if v_len == 2 and not is_inseparable_vowels(vowels):
            
        boundary_list[start+1] = 1 # insert boundary before the second vowel
        
    elif v_len > 2:

        if vowels in vowel_seq_dict:

            # store information from vowel sequence dictionary; ignore first entry, as the dictionary does not know if a syllable boundary precedes the vowel sequence
            boundary_list[start+1:start+v_len+1] = vowel_seq_dict[vowels][1:] # ignore initial syllable separator and first vowel

        else:

            # first look for long vowels, following Karlsson 1985: (2a)
            boundary = locate_long(vowels)

            if boundary != -1:

                # if long vowel starts the sequence, separation should precede the third vowel; otherwise it should procede the location of the long vowel
                if boundary == 0:

                    boundary = 2
                    separate_vowels(vowels[boundary:], boundary_list, start+boundary) # syllabify vowels following long vowel

                else:

                    separate_vowels(vowels[:boundary], boundary_list, start) # syllabify vowels preceding long vowel
                    
                boundary_list[start + boundary] = 1 # split vowel from long vowel
                
            else: # if no such sequence, simply separate all separable VV sequences
                
                for i in range(len(vowels)-1):

                    if not is_inseparable_vowels(vowels[i:i+2]):

                        boundary_list[start + (i + 1)] = 1 # insert boundary before the second vowel
                    
                
            
# return the syllabification of word, preserving capitalization; syllable boundaries are placed at the start and end of the word
def make_syllables(word):
    
    entry = word.lower()
    boundary_list = [1]
    
    if entry in pre_sep_dict: # introduces annotations, but will still be syllabified so that only partial annotations are required
        boundary_list = pre_sep_dict[entry]
    else:
        for i in range(1, len(entry)):
            boundary_list += [0]
        boundary_list += [1]

    make_splits(entry + SYLLABLE_SEPARATOR, boundary_list) # syllable separator added to ensure that final vowel sequence is syllabified

    syllables = introduce_splits(word, boundary_list)
    
    return syllables

# return a string with the syllable boundaries represented in syllabified_word but the capitalization represented in original_word
def introduce_splits(word, boundary_list):
    result = []
    start = 0
    end = 0
    while end < len(word):
        end += 1
        if boundary_list[end] == 1:
            
            if word[start] == "'":
                result += [word[start+1:end]] # do not start a syllable with '
                
            else:
                result += [word[start:end]]
                
            start = end
        
    return result


# account for Karlsson 1985: (4); certain consonants should be clusters
# stored in order: test clusters first, then the basic CV-rule
onset_lengths = [cluster_length for cluster_length in CLUSTER_LENGTHS]
onset_lengths += [1]

# store syllable boundaries in boundary_list
def make_splits(word, boundary_list):

    # stores the location of the start and end of the longest vowel sequence encountered so far
    v_seq_start = 0
    v_seq_end = 0

    for i in range(len(word)):
        
        if is_vowel(word[i]): # continuing or starting vowel sequence
            
            v_seq_end += 1

            # potential application of CV-rule [Karlsson 1985: (1)]
            if v_seq_end - v_seq_start == 1:

                # test possible onsets
                for onset_length in onset_lengths:

                    cluster_start = i - onset_length

                    # if encounter a good boundary, only insert separator if not already present; break regardless so that basic CV won't apply if appropriate cluster exists
                    if cluster_start >= 0 and consonantal_onset(word[cluster_start:i]):

                        no_syllable_break = True

                        for h_index in range(cluster_start, i):
                            
                            if boundary_list[h_index] == 1:
                                no_syllable_break = False
                        
                        if no_syllable_break:
                            boundary_list[cluster_start] = 1
                            
                        break
                    
        else: # vowel sequence interrupted; if there is a sequence to be split, deal with it
            
            if v_seq_end - v_seq_start > 1:
                
                separate_vowels(word[v_seq_start:v_seq_end], boundary_list, v_seq_start)

            v_seq_start = v_seq_end = i+1 # vowel sequence (if any) starts after current index

    apply_3c(word[:-1], boundary_list) # chop off final syllable separator
    apply_t4(word, boundary_list)
