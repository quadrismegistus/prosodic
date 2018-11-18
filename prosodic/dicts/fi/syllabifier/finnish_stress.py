# coding=utf-8
from finnish_functions import *

from copy import deepcopy

stress_dict = {} # map between words and their hand-annotated for stress

# given a list of weights, and a list of equal length of stresses, store added stress markings in stresses
def make_stresses(weights):

    stresses = []

    if len(weights) == 1 and not is_heavy(weights[0]):

        return [[Stress.none]]

    if len(weights) > 0:
        stresses += [Stress.primary]
        
    for i in range(1, len(weights)):
        stresses += [Stress.none]

    stress_parity = 0 # currently stressing odd syllables, located at even indices

    # first syllable is always stressed, and following syllable is never stressed, so start with third syllable
    i = 2
    while i < len(weights) - 1:

        # if at a syllable to potentially be stressed
        if i % 2 == stress_parity:

            # shift stress forward one if following syllable is already stressed (to avoid clash), or if the following syllable is non-final and heavier
            if stresses[i+1] != Stress.none or (is_heavier(weights[i+1], weights[i]) and i+1 < len(weights) - 1):
            
                stresses[i+1] = Stress.secondary
                i += 1
                stress_parity = (stress_parity + 1) % 2 # swap which parity to stress on, since stress assignment continues from stressed syllable
                
            else:
                
                stresses[i] = Stress.secondary

        i += 2 # can ignore syllable after the one just stressed, since it won't be stressed to avoid clash

    stresses = [stresses]

    # optionally stress a final heavy where appropriate, and if the preceding syllable is light and stressed make its stress optional
    if len(weights) > 1 and is_heavy(weights[-1]):

        if stresses[0][-2] == Stress.none:

            stresses += deepcopy(stresses)
            stresses[1][-1] = Stress.secondary

        elif stresses[0][-2] == Stress.secondary and not is_heavy(weights[-2]):

            stresses += deepcopy(stresses)
            stresses[1][-1] = Stress.secondary
            stresses[1][-2] = Stress.none
    
    return stresses
