from .imports import *

def w_stress(mpos):
    if mpos.is_prom: return [None]*len(mpos.slots)
    return [slot.is_stressed for slot in mpos.slots]

def s_unstress(mpos):
    if not mpos.is_prom: return [None]*len(mpos.slots)
    return [not slot.is_stressed for slot in mpos.slots]

def unres_within(mpos, score=1):
    slots = mpos.slots
    if len(slots)<2: return [None]*len(mpos.slots)
    ol=[None]
    for si in range(1,len(slots)):
        slot1,slot2=slots[si-1],slots[si]
        unit1,unit2=slot1.unit,slot2.unit
        wf1,wf2=unit1.parent,unit2.parent
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
    
def unres_across(mpos):
    slots = mpos.slots
    if len(slots)<2: return [None]*len(mpos.slots)
    ol=[None]
    for si in range(1,len(slots)):
        slot1,slot2=slots[si-1],slots[si]
        unit1,unit2=slot1.unit,slot2.unit
        wf1,wf2=unit1.parent,unit2.parent
        if wf1 is wf2: 
            ol.append(None)
        else:
            # disyllabic strong position immediately violates
            if mpos.is_prom or not wf1.is_functionword or not wf2.is_functionword:
                ol[si-1] = True
                ol.append(True)
            else:
                ol.append(False)
    return ol
        
#@profile
def w_peak(mpos, score=1):
    if mpos.is_prom: return [None]*len(mpos.slots)
    return [slot.is_strong for slot in mpos.slots]

#@profile
def s_trough(mpos, score=1):
    if not mpos.is_prom: return [None]*len(mpos.slots)
    return [slot.is_weak for slot in mpos.slots]

DEFAULT_CONSTRAINTS = [w_peak, w_stress, s_unstress, unres_across, unres_within]