from .imports import *


def w_stress(mpos):
    if mpos.is_prom:
        return [None] * len(mpos.slots)
    return [slot.is_stressed for slot in mpos.slots]


def s_unstress(mpos):
    if not mpos.is_prom:
        return [None] * len(mpos.slots)
    return [not slot.is_stressed for slot in mpos.slots]


def unres_within(mpos):
    slots = mpos.slots
    if len(slots) < 2:
        return [None] * len(mpos.slots)
    ol = [None]
    for si in range(1, len(slots)):
        slot1, slot2 = slots[si - 1], slots[si]
        unit1, unit2 = slot1.unit, slot2.unit
        wf1, wf2 = unit1.parent, unit2.parent
        if wf1 is not wf2:
            ol.append(None)
        else:
            # disyllabic position within word
            # first position mist be light and stressed
            if unit1.is_heavy or not unit1.is_stressed:
                ol.append(True)
            else:
                ol.append(False)
    return ol


def foot_size(mpos):
    res = bool(len(mpos.slots) > 2) or bool(len(mpos.slots) < 1)
    return [res] * len(mpos.slots)


def unres_across(mpos):
    slots = mpos.slots
    if len(slots) < 2:
        return [None] * len(mpos.slots)
    ol = [None]
    for si in range(1, len(slots)):
        slot1, slot2 = slots[si - 1], slots[si]
        unit1, unit2 = slot1.unit, slot2.unit
        wf1, wf2 = unit1.wordform, unit2.wordform
        if wf1 is wf2:
            ol.append(None)
        else:
            # disyllabic strong position immediately violates
            if mpos.is_prom or not wf1.is_functionword or not wf2.is_functionword:
                ol[si - 1] = True
                ol.append(True)
            else:
                ol.append(False)
    return ol


# @profile


def w_peak(mpos):
    if mpos.is_prom:
        return [None] * len(mpos.slots)
    return [slot.is_strong for slot in mpos.slots]


# @profile


def s_trough(mpos):
    if not mpos.is_prom:
        return [None] * len(mpos.slots)
    return [slot.is_weak for slot in mpos.slots]


DEFAULT_CONSTRAINTS_NAMES = [
    "w_peak",
    "w_stress",
    "s_unstress",
    "unres_across",
    "unres_within",
]
CONSTRAINTS = {
    "w_peak": w_peak,
    "w_stress": w_stress,
    "s_unstress": s_unstress,
    "unres_across": unres_across,
    "unres_within": unres_within,
    "s_trough": s_trough,
    "foot_size": foot_size,
}
DEFAULT_CONSTRAINTS = [
    CONSTRAINTS[cname] for cname in DEFAULT_CONSTRAINTS_NAMES
]


def get_constraints(names_or_funcs):
    if type(names_or_funcs) == str:
        names_or_funcs = names_or_funcs.strip().split()
    l = [
        CONSTRAINTS.get(cname) if type(cname) == str else cname
        for cname in names_or_funcs
    ]
    return [x for x in l if x is not None]


CONSTRAINT_DESCS = {
    'w_peak':
    'No polysyllabic stress on weak position',
    's_trough':
    'No polysyllabic unstress on strong position',
    'w_stress':
    'No stressed syllables on weak position',
    's_unstress':
    'No unstressed syllable on strong position',
    'unres_across':
    'Disyllabic positions crossing words can only contain function words',
    'unres_within':
    'Disyllabic positions within words must start with a light and stressed syllable',
    'foot_size':
    'Do not allow positions to exceed two syllables',
    'max_s':
    'Maximum number of syllables in strong position',
    'max_w':
    'Maximum number of syllables in weak position',
    'resolve_optionality':
    'Allow parser to choose best words\' stress patterns option',
    'exhaustive':
    'Compute even harmonically bounded parses (those worse in the same ways + another way compared to another parse)'
}
