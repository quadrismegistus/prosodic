from .imports import *

def w_stress(mpos, score=1):
    if mpos.is_prom: return [np.nan for s in mpos.slots]
    return [(score if slot.is_stressed else 0) for slot in mpos.slots]

def s_unstress(mpos, score=1):
    if not mpos.is_prom: return [np.nan for s in mpos.slots]
    return [(score if not slot.is_stressed else 0) for slot in mpos.slots]

def unres_within(mpos, score=1):
    slots = mpos.slots
    if len(slots)<2: return [np.nan for s in mpos.slots]
    ol=[np.nan]
    for si in range(1,len(slots)):
        slot1,slot2=slots[si-1],slots[si]
        unit1,unit2=slot1.unit,slot2.unit
        wf1,wf2=unit1.parent,unit2.parent
        if wf1 is not wf2: 
            ol.append(np.nan)
        else:
            # disyllabic position within word
            # first position mist be light and stressed
            if unit1.is_heavy or not unit1.is_stressed: 
                ol.append(score)
            else:
                ol.append(0)
    return ol
    

def unres_across(mpos, score=1):
    slots = mpos.slots
    if len(slots)<2: return [np.nan for s in mpos.slots]
    ol=[np.nan]
    for si in range(1,len(slots)):
        slot1,slot2=slots[si-1],slots[si]
        unit1,unit2=slot1.unit,slot2.unit
        wf1,wf2=unit1.parent,unit2.parent
        if wf1 is wf2: 
            ol.append(np.nan)
        else:
            # disyllabic strong position immediately violates
            if mpos.is_prom or not wf1.is_functionword or not wf2.is_functionword:
                ol[si-1] = score
                ol.append(score)
            else:
                ol.append(0)
    return ol
        

def w_peak(mpos, score=1):
    if mpos.is_prom: return [np.nan for s in mpos.slots]
    return [(score if slot.is_strong else 0) for slot in mpos.slots]

def s_trough(mpos, score=1):
    if not mpos.is_prom: return [np.nan for s in mpos.slots]
    return [(score if slot.is_weak else 0) for slot in mpos.slots]

DEFAULT_CONSTRAINTS = [w_peak, w_stress, s_unstress, unres_across, unres_within]