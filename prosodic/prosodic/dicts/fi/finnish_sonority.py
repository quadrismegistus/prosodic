# coding=utf-8
from finnish_functions import *

# return the sonority of a syllable
def get_sonority(vowel):

    if len(vowel) == 0:
        return '?' # no vowel in this "syllable"

    return vowel[0].upper()

def make_sonorities(split_sylls):

    return [get_sonority(syll[Syllable.nucleus]) for syll in split_sylls]
