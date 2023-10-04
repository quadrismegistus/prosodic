from .imports import *
from .constraints import *


# @total_ordering
# class Parse(entity):
#     str2int = {'w':'1','s':'2'}
#     def __init__(self, num_total_slots:int, constraints:list=[]):
#         super().__init__()
#         self.positions = []
#         self.constraints = constraints
#         self.num_slots = 0
#         self.num_total_slots = num_total_slots
#         self.is_bounded = False
#         self.bounded_by = None
#         self.unmetrical = False
#         self.comparison_nums = set()
#         self.comparison_parses = []
#         self.parse_num = 0
#         self.total_score = None
#         self.pause_comparisons = False
#         self.parse_rank = None
#         self.violset=Multiset()
#         for mpos in self.positions: 
#             self.violset.update(mpos.violset)

@total_ordering
class Parse(entity):
    prefix='parse'
    def __init__(self, wordforms_or_str, scansion:str='', meter:'Meter'=None, parent=None):
        
        # wordforms
        assert wordforms_or_str
        if type(wordforms_or_str)==str:
            self.wordforms = Line(wordforms_or_str).wordform_matrix[0]
        elif type(wordforms_or_str)==list:
            self.wordforms = WordFormList(wordforms_or_str)
        else:
            self.wordforms = wordforms_or_str

        # meter
        if meter is None:
            from .meter import Meter
            meter = Meter()
        self.meter=meter
        
        # slots
        self.slots = [ParseSlot(slot) for slot in self.wordforms.slots]

        # scansion
        if not scansion: scansion=get_iambic_parse(len(self.slots))
        if type(scansion)==str: scansion=split_scansion(scansion)
        self.positions_ls = scansion
        
        # divide positions
        self.positions = []
        self.children = []
        slot_i=0
        for mpos_str in self.positions_ls:
            slots=[]
            mval=mpos_str[0]
            for x in mpos_str:
                slot=self.slots[slot_i]
                slot_i+=1
                slots.append(slot)
            mpos = ParsePosition(
                meter_val=mval, 
                children=slots, 
                parent=self
            )
            self.positions.append(mpos)

        self.line=parent
        super().__init__(children=self.positions, parent=parent)
        self.is_bounded = False
        self.bounded_by = None
        self.unmetrical = False
        self.comparison_nums = set()
        self.comparison_parses = []
        self.parse_num = 0
        self.total_score = None
        self.pause_comparisons = False
        self.parse_rank = None
        self.violset=Multiset()
        for mpos in self.positions: 
            self.violset.update(mpos.violset)
    
    @cached_property
    # @profile
    def sort_key(self): 
        return (
            int(bool(self.is_bounded)),
            self.score, 
            self.positions[0].is_prom,
            self.average_position_size,
            self.num_stressed_sylls,
        )
    @cached_property
    def constraints(self): return self.meter.constraints
    @cached_property
    def constraint_names(self):
        return [c.__name__ for c in self.constraints]
    @cached_property
    def constraint_d(self):
        return dict(zip(self.constraint_names, self.constraints))

    # @profile
    def __lt__(self,other):
        return self.sort_key < other.sort_key

    # @profile
    def __eq__(self, other):
        logger.error(f'{self} and {other} could not be compared in sort, ended up equal')
        return not (self<other) and not (other<self)
    
    @cached_property
    def txt(self): return " ".join(m.txt for m in self.positions)

    # def __repr__(self):
        # attrstr=get_attr_str(self.attrs)
        # parse=self.txt
        # preattr=f'({self.__class__.__name__}: {parse})'
        # return f'{preattr}{attrstr}'
    
    @cached_property
    def num_stressed_sylls(self):
        return len([
            slot
            for mpos in self.positions
            for slot in mpos.slots
            if slot.is_stressed
        ])
    
    @cached_property
    def num_sylls(self):
        return len([
            slot
            for mpos in self.positions
            for slot in mpos.slots
        ])
    
    @cached_property
    def num_peaks(self):
        return len([
            mpos
            for mpos in self.positions
            if mpos.is_prom
        ])
    

    @cached_property
    def is_rising(self):
        if not self.positions: return
        return not self.positions[0].is_prom
    
    @cached_property
    def nary_feet(self):
        fsizes=[]
        for i in range(1,len(self.positions)):
            pos1,pos2=self.positions[i-1],self.positions[i]
            if not pos2.is_prom: continue
            fsizes.append(len(pos1.slots) + len(pos2.slots))
        if not fsizes: return
        return int(round(np.median(fsizes)))
    
    @cached_property
    def foot_type(self):
        if self.nary_feet==2:
            return 'iambic' if self.is_rising else 'trochaic'
        elif self.nary_feet==3:
            return 'anapestic' if self.is_rising else 'dactylic'
        logger.error('foot type?')
        return ''
                
        
        
    
    @cached_property
    # @profile
    def average_position_size(self):
        l = [len(mpos.children) for mpos in self.positions if mpos.children]
        return np.mean(l) if len(l) else np.nan

    @property
    # @profile
    def attrs(self):
        return {
            **self._attrs,
            'line_num':self.line.num if self.line else None,
            'txt':self.txt,
            'rank':self.parse_rank,
            'meter':self.meter_str,
            'stress':self.stress_str,
            'score':self.score,
            **({'is_bounded':True} if self.is_bounded else {}),
            # **{c:v for c,v in self.constraint_scores.items() if v!=np.nan and v}
        }

    @cached_property
    # @profile
    def constraint_viols(self):
        # logger.debug(self)
        scores = [mpos.constraint_viols for mpos in self.positions]
        d={}
        nans=[np.nan for _ in range(len(self.slots))]
        for constraint in self.constraints:
            cname=constraint.__name__
            d[cname] = [x for score_d in scores for x in score_d.get(cname,nans)]
        return d
    
    @cached_property
    # @profile
    def constraint_scores(self):
        return {cname:safesum(cvals) for cname,cvals in self.constraint_viols.items()}

    @cached_property
    # @profile
    def score(self):
        try:
            return sum(self.constraint_scores.values())
        except ValueError:
            return '*'  # could be string if categorical

    # return a list of all slots in the parse
    @cached_property
    def slots(self):
        return [slot for mpos in self.positions for slot in mpos.slots]

    @cached_property
    # @profile
    def meter_str(self,word_sep=""):
        return ''.join(
            '+' if mpos.is_prom else '-'
            for mpos in self.positions
            for slot in mpos.slots
        )
    
    @cached_property
    # @profile
    def stress_str(self,word_sep=""):
        return ''.join(
            '+' if slot.is_stressed else '-'
            for mpos in self.positions
            for slot in mpos.slots
        ).lower()
    
    # return a representation of the bounding relation between self and parse
    # @profile
    def bounding_relation(self, parse):
        if self.violset < parse.violset:
            return Bounding.bounds
        elif self.violset > parse.violset:
            return Bounding.bounded
        elif self.violset == parse.violset:
            return Bounding.equal
        else:
            return Bounding.unequal
    

class ParsePosition(entity):
    prefix='meterpos'
    # @profile
    def __init__(self, meter_val:str, children=[], parent=None): # meter_val represents whether the position is 's' or 'w'
        self.viold={}  # dict of lists of viols; length of these lists == length of `slots`
        self.violset=set()   # set of all viols on this position
        self.slots=children
        self.parse=parent
        super().__init__(
            meter_val=meter_val,
            children=children,
            parent=parent,
            num_slots=len(self.slots)
        )
        # init?
        for cname,constraint in self.constraint_d.items():
            slot_viols = [int(bool(vx)) for vx in constraint(self)]
            assert len(slot_viols) == len(self.slots)
            self.viold[cname] = slot_viols
            if any(slot_viols): self.violset.add(cname)
            for viol,slot in zip(slot_viols, self.slots):
                slot.viold[cname]=viol
    
    @cached_property
    def attrs(self):
        return {
            **self._attrs, 
            'num':self.num,
            # **{k:sum(v) for k,v in self.viold.items()}
        }

    @cached_property
    # @profile
    def constraint_viols(self): return self.viold
    @cached_property
    # @profile
    def constraint_set(self): return self.violset


    @cached_property
    def constraints(self): return self.parse.constraints
    @cached_property
    def constraint_d(self): return self.parse.constraint_d

    @cached_property
    def is_prom(self): return self.meter_val=='s'

    @cached_property
    def txt(self):
        token = '.'.join([slot.txt for slot in self.slots])
        token=token.upper() if self.is_prom else token.lower()
        return token




class ParseSlot(entity):
    prefix='meterslot'
    # @profile
    def __init__(self, unit:'Syllable'):
        self.unit = unit
        self.viold = {}
        super().__init__()
        self.children=[unit]
    
    @cached_property
    def meter_val(self): return self.parent.meter_val
    @cached_property
    def is_prom(self): return self.parent.is_prom
    @cached_property
    def wordform(self): return self.unit.parent
    @cached_property
    def syll(self): return self.unit
    @cached_property
    def is_stressed(self): return self.unit.is_stressed
    @cached_property
    def is_heavy(self): return self.unit.is_heavy
    @cached_property
    def is_strong(self): return self.unit.is_strong
    @cached_property
    def is_weak(self): return self.unit.is_weak
    @cached_property
    def txt(self):
        o=self.unit.txt
        return o.upper() if self.is_prom else o.lower()

    @cached_property
    def i(self):
        return self.parent.parent.slots.index(self)
    
    @cached_property
    def attrs(self):
        return {
            **self._attrs, 
            'num':self.num,
            **self.viold,
            # 'is_stressed':self.is_stressed, 
            # 'is_heavy':self.is_heavy, 
            # 'is_strong':self.is_strong, 
            # 'is_weak':self.is_weak,
        }








class ParseList(entity):
    index_name='parse'
    prefix='parselist'

    @cached_property
    def attrs(self):
        return {**self._attrs, 'num_parses':len(self.unbounded), 'num_all_parses':len(self.data)}
    
    @cached_property
    def unbounded(self): 
        return ParseList(children=[px for px in self.data if not px.is_bounded])
    @cached_property
    def bounded(self): 
        return ParseList(children=[px for px in self.data if px.is_bounded])




# class representing the potential bounding relations between to parses
class Bounding:
    bounds = 0 # first parse harmonically bounds the second
    bounded = 1 # first parse is harmonically bounded by the second
    equal = 2 # the same constraint violation scores
    unequal = 3 # unequal scores; neither set of violations is a subset of the other

def get_iambic_parse(nsyll):
    o=[]
    while len(o)<nsyll:
        x='w' if not o or o[-1]=='s' else 's'
        o.append(x)
    return o