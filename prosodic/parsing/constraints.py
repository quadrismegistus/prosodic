from ..imports import *

def constraint(desc, scope):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        wrapper.desc = desc
        wrapper.scope = scope
        return wrapper
    return decorator

@constraint(desc="No stressed syllables on weak position", scope="position")
def w_stress(mpos):
    """
    Check for stressed syllables in weak positions.

    Args:
        mpos (MeterPosition): The meter position to evaluate.

    Returns:
        list: A list of booleans indicating stressed syllables in weak positions,
              or None for each slot if the position is strong.
    """
    if mpos.is_prom:
        return [None] * len(mpos.slots)
    return [slot.is_stressed for slot in mpos.slots]

@constraint(desc="No unstressed syllable on strong position", scope="position")
def s_unstress(mpos):
    """
    Check for unstressed syllables in strong positions.

    Args:
        mpos (MeterPosition): The meter position to evaluate.

    Returns:
        list: A list of booleans indicating unstressed syllables in strong positions,
              or None for each slot if the position is weak.
    """
    if not mpos.is_prom:
        return [None] * len(mpos.slots)
    return [not slot.is_stressed for slot in mpos.slots]

@constraint(desc="Disyllabic positions within words must start with a light and stressed syllable", scope="position")
def unres_within(mpos):
    """
    Check for unresolved disyllabic positions within words.

    Args:
        mpos (MeterPosition): The meter position to evaluate.

    Returns:
        list: A list of booleans indicating unresolved disyllabic positions within words,
              or None for each slot if not applicable.
    """
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
            # first position must be light and stressed
            if unit1.is_heavy or not unit1.is_stressed:
                ol.append(True)
            else:
                ol.append(False)
    return ol

@constraint(desc="Do not allow positions to exceed two syllables", scope="position")
def foot_size(mpos):
    """
    Check if the meter position exceeds two syllables or is empty.

    Args:
        mpos (MeterPosition): The meter position to evaluate.

    Returns:
        list: A list of booleans indicating if the position violates foot size constraints.
    """
    res = bool(len(mpos.slots) > 2) or bool(len(mpos.slots) < 1)
    return [res] * len(mpos.slots)

@constraint(desc="Disyllabic positions crossing words can only contain function words", scope="position")
def unres_across(mpos):
    """
    Check for unresolved disyllabic positions across words.

    Args:
        mpos (MeterPosition): The meter position to evaluate.

    Returns:
        list: A list of booleans indicating unresolved disyllabic positions across words,
              or None for each slot if not applicable.
    """
    slots = mpos.slots
    if len(slots) < 2:
        return [None] * len(mpos.slots)
    ol = [None] # only raise viol on second (or more) position
    for si in range(1, len(slots)):
        slot1, slot2 = slots[si - 1], slots[si]
        unit1, unit2 = slot1.unit, slot2.unit
        wf1, wf2 = unit1.wordform, unit2.wordform
        if wf1 is wf2:
            ol.append(None)
        else:
            # disyllabic strong position immediately violates
            if mpos.is_prom or not wf1.is_functionword or not wf2.is_functionword:
                ol.append(True)
            else:
                ol.append(False)
    return ol

@constraint(desc="No polysyllabic stress on weak position", scope="position")
def w_peak(mpos):
    """
    Check for polysyllabic stress on weak positions.

    Args:
        mpos (MeterPosition): The meter position to evaluate.

    Returns:
        list: A list of booleans indicating polysyllabic stress on weak positions,
              or None for each slot if the position is strong.
    """
    if mpos.is_prom:
        return [None] * len(mpos.slots)
    return [slot.is_strong for slot in mpos.slots]

@constraint(desc="No polysyllabic unstress on strong position", scope="position")
def s_trough(mpos):
    """
    Check for polysyllabic unstress on strong positions.

    Args:
        mpos (MeterPosition): The meter position to evaluate.

    Returns:
        list: A list of booleans indicating polysyllabic unstress on strong positions,
              or None for each slot if the position is weak.
    """
    if not mpos.is_prom:
        return [None] * len(mpos.slots)
    return [slot.is_weak for slot in mpos.slots]

@constraint(desc="Ensure the parse has exactly 5 peaks", scope="line")
def pentameter(parse):
    return parse.num_peaks != 5

@constraint(desc="Ensure the parse is iambic", scope="line")
def iambic(parse):
    return not parse.meter_str.startswith('-+')