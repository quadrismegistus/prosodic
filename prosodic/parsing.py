from .imports import *
from .constraints import *


# @total_ordering
# class Parse(Entity):
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
class Parse(Entity):
    prefix='parse'
    def __init__(self, wordforms_or_str, scansion:str='', meter:'Meter'=None, parent=None, positions=None):
        if not positions: positions = []
        
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
        # self.slots = [ParseSlot(slot) for slot in self.wordforms.slots]
        # self.slots = self.wordforms.slots

        # scansion
        if not scansion: scansion=get_iambic_parse(len(self.wordforms.slots))
        if type(scansion)==str: scansion=split_scansion(scansion)
        self.positions_ls = copy(scansion)
        
        # divide positions
        super().__init__(children=[], parent=parent)
        self.positions = positions
        self.children = self.positions
        self.line=parent
        self.is_bounded = False
        self.bounded_by = None
        self.unmetrical = False
        self.comparison_nums = set()
        self.comparison_parses = []
        self.parse_num = 0
        self.total_score = None
        self.pause_comparisons = False
        self.parse_rank = None
        # self.violset=Multiset()
        self.num_slots_positioned=0
        if not positions:
            for mpos_str in self.positions_ls: self.extend(mpos_str)
    
    @property
    def slots(self):
        return [slot for mpos in self.positions for slot in mpos.slots]

    def extend(self, mpos_str:str): # ww for 2 slots, w for 1, etc
        slots=[]
        mval=mpos_str[0]
        if self.positions and self.positions[-1].meter_val==mval:
            # logger.warning(f'cannnot extend because last position is also {mval}')
            return None
        
        for i,x in enumerate(mpos_str):
            slot_i = self.num_slots_positioned
            try:
                slot=self.wordforms.slots[slot_i]
            except IndexError:
                # logger.warning('cannot extend further, already taking up all syllable slots')
                return None
            
            slots.append(ParseSlot(slot, num=slot_i+1))
            self.num_slots_positioned+=1

        mpos = ParsePosition(
            meter_val=mval, 
            children=slots, 
            parent=self,
            num = len(self.positions) + 1
        )
        self.positions.append(mpos)
        self.constraint_viols  # init and bound
        return self
    
    @property
    def violset(self):
        s=Multiset()
        for mpos in self.positions:
            s.update(mpos.violset)
        return s
    
    def __copy__(self):
        new = Parse(
            wordforms_or_str=self.wordforms, 
            scansion=self.positions_ls, 
            meter=self.meter, 
            parent=self.parent, 
            positions=[copy(mpos) for mpos in self.positions]
        )
        new._attrs = copy(self._attrs)
        new.is_bounded = self.is_bounded
        new.num_slots_positioned = self.num_slots_positioned
        # new.violset = copy(self.violset)
        return new


    def branch(self):
        if self.is_bounded: return []
        if not self.positions: 
            logger.error('needs to start with some positions')
            return
        mval=self.positions[-1].meter_val
        otypes = self.meter.get_pos_types(self.wordforms.num_sylls)
        otypes = [x for x in otypes if x[0]!=mval]
        o = [copy(self).extend(posstr) for posstr in otypes]
        o = [x for x in o if x is not None]
        o = o if o else [self]
        o = [p for p in o if not p.is_bounded]
        return o
    
    @property
    def is_complete(self): return self.num_slots_positioned == len(self.wordforms.slots)

    
    @property
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
    def constraints(self): 
        return self.meter.constraints + self.meter.categorical_constraints
    @cached_property
    def constraint_d(self):
        return dict((c.__name__,c) for c in self.constraints)
    @cached_property
    def categorical_constraint_d(self):
        return dict((c.__name__,c) for c in self.meter.categorical_constraints)
    # @profile
    def __lt__(self,other):
        return self.sort_key < other.sort_key

    # @profile
    def __eq__(self, other):
        # logger.error(f'{self} and {other} could not be compared in sort, ended up equal')
        # return not (self<other) and not (other<self)
        return self is other
    
    def can_compare(self, other, min_slots=4):
        if self.num_slots_positioned!=other.num_slots_positioned: return False
        if min_slots and self.num_slots_positioned<min_slots: return False
        return True
    
    @cached_property
    def txt(self): return " ".join(m.txt for m in self.positions)

    # def __repr__(self):
        # attrstr=get_attr_str(self.attrs)
        # parse=self.txt
        # preattr=f'({self.__class__.__name__}: {parse})'
        # return f'{preattr}{attrstr}'
    
    @property
    def num_stressed_sylls(self):
        return len([
            slot
            for mpos in self.positions
            for slot in mpos.slots
            if slot.is_stressed
        ])
    
    @property
    def num_sylls(self):
        return len([
            slot
            for mpos in self.positions
            for slot in mpos.slots
        ])
    
    @property
    def num_peaks(self):
        return len([
            mpos
            for mpos in self.positions
            if mpos.is_prom
        ])
    

    @property
    def is_rising(self):
        if not self.positions: return
        # return not self.positions[0].is_prom
        try:
            if self.nary_feet==3:
                if self.slots[3].is_prom:
                    return False  #swws
                else:
                    return True   #wssw
            elif self.nary_feet==2:
                if self.slots[3].is_prom:
                    return True  #wsws
                else:
                    return False   #swsw
        except (IndexError,AttributeError):
            pass
        return not self.positions[0].is_prom
    
    @property
    def nary_feet(self):
        return int(np.median(self.foot_sizes))

    @property
    def feet(self):
        if self.num_positions == 1:
            feet = [self.positions[0].meter_str]
        else:
            feet=[]
            for i in range(1, self.num_positions, 2):
                pos1,pos2=self.positions[i-1],self.positions[i]
                feet.append(pos1.meter_str+pos2.meter_str)
        return feet
    
    @property
    def foot_counts(self): return Counter(self.feet)
    @property
    def foot_sizes(self): return [len(ft) for ft in self.feet]
    
    @property
    def num_positions(self): return len(self.positions)
        
    @property
    def foot_type(self):
        if self.nary_feet==2:
            return 'iambic' if self.is_rising else 'trochaic'
        elif self.nary_feet==3:
            return 'anapestic' if self.is_rising else 'dactylic'
        logger.error('foot type?')
        return ''
                
        
        
    
    @property
    # @profile
    def average_position_size(self):
        l = [len(mpos.children) for mpos in self.positions if mpos.children]
        return np.mean(l) if len(l) else np.nan

    @property
    # @profile
    def attrs(self):
        return {
            **self._attrs,
            'stanza_num':self.line.parent.num if self.line and self.line.parent else None,
            'line_num':self.line.num if self.line else None,
            'txt':self.txt,
            'rank':self.parse_rank,
            'meter':self.meter_str,
            'stress':self.stress_str,
            'score':self.score,
            'is_bounded':int(bool(self.is_bounded)),
            # **{c:v for c,v in self.constraint_scores.items() if v!=np.nan and v}
        }

    @property
    # @profile
    def constraint_viols(self):
        # logger.debug(self)
        scores = [mpos.constraint_viols for mpos in self.positions]
        d={}
        nans=[np.nan for _ in range(len(self.slots))]
        catcts=set(self.categorical_constraint_d.keys())
        for cname,constraint in self.constraint_d.items():
            d[cname] = cscores = [x for score_d in scores for x in score_d.get(cname,nans)]
            if cname in catcts and any(cscores):
                logger.debug(f'Bounding {self.meter_str} because violates categorical constraint {cname}')
                self.is_bounded = True 
        return d
    
    @property
    # @profile
    def constraint_scores(self):
        return {cname:safesum(cvals) for cname,cvals in self.constraint_viols.items()}

    @property
    # @profile
    def score(self):
        return safesum(self.constraint_scores.values())

    # return a list of all slots in the parse

    @property
    # @profile
    def meter_str(self,word_sep=""):
        return ''.join(
            '+' if mpos.is_prom else '-'
            for mpos in self.positions
            for slot in mpos.slots
        )
    
    @property
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
        selfviolset = self.violset
        parseviolset = parse.violset
        if selfviolset < parseviolset:
            return Bounding.bounds
        elif selfviolset > parseviolset:
            return Bounding.bounded
        elif selfviolset == parseviolset:
            return Bounding.equal
        else:
            return Bounding.unequal
        

    def _repr_html_(self): return repr(self)
    # def html(self, viols=True, between_words=' ',between_sylls='',line_id='ID'):
    #     last_word = None
    #     output=[]
    #     line_num=0 if self.line is None else self.line.num
    #     for pos in self.positions:
    #         violated=bool(pos.violset)
    #         if viols and violated:
    #             viol_str=' '.join(pos.violset)
    #             viol_title = 'Violated %s constraints: %s' % (len(pos.violset), viol_str)
    #             output.append(f'<span class="violation" title="{viol_title}" id="viol__line_{line_num}">')

    #         for slot in pos.slots:
    #             spclass='meter_' + ('strong' if pos.is_prom else 'weak')
    #             stclass='stress_' + ('strong' if slot.unit.is_stressed else 'weak')
    #             slotstr=f'<span class="{spclass} {stclass}">{slot.unit.txt}</span>'
    #             if last_word and last_word is not slot.unit.wordtoken:
    #                 output.append(between_words)
    #             output.append(slotstr)
    #             last_word  = slot.unit.wordtoken

    #         if viols and violated:
    #             output.append(f'</span><script type="text/javascript">tippy("#viol__line_{line_num}")</script>')
    #         if pos.is_prom and self.is_rising: output.append('|')
    #         elif not pos.is_prom and not self.is_rising: output.append('|')
    #     if output and output[-1]=='|': output.pop()
    #     return ''.join(output)
    

class ParsePosition(Entity):
    prefix='meterpos'
    # @profile
    def __init__(self, meter_val:str, children=[], parent=None, **kwargs): # meter_val represents whether the position is 's' or 'w'
        self.viold={}  # dict of lists of viols; length of these lists == length of `slots`
        self.violset=set()   # set of all viols on this position
        self.slots=children
        self.parse=parent
        super().__init__(
            meter_val=meter_val,
            children=children,
            parent=parent,
            num_slots=len(self.slots),
            **kwargs
        )
        # init?
        for cname,constraint in self.parse.constraint_d.items():
            slot_viols = [int(bool(vx)) for vx in constraint(self)]
            assert len(slot_viols) == len(self.slots)
            self.viold[cname] = slot_viols
            if any(slot_viols): self.violset.add(cname)
            for viol,slot in zip(slot_viols, self.slots):
                slot.viold[cname]=viol
    
    def __copy__(self):
        new = ParsePosition(
            self.meter_val, 
            children=[copy(slot) for slot in self.children],
            parent=self.parent
        )
        new.viold = copy(self.viold)
        new.violset = copy(self.violset)
        new._attrs = copy(self._attrs)
        return new
    
    @cached_property
    def attrs(self):
        return {
            **self._attrs, 
            # 'num':self.num,
            # **{k:sum(v) for k,v in self.viold.items()}
        }
        

    @cached_property
    # @profile
    def constraint_viols(self): return self.viold
    @cached_property
    # @profile
    def constraint_set(self): return self.violset

    @cached_property
    def is_prom(self): return self.meter_val=='s'

    @cached_property
    def txt(self):
        token = '.'.join([slot.txt for slot in self.slots])
        token=token.upper() if self.is_prom else token.lower()
        return token
    
    @cached_property
    def meter_str(self): return self.meter_val * self.num_slots
    @cached_property
    def num_slots(self): return len(self.slots)
    
    



class ParseSlot(Entity):
    prefix='meterslot'
    # @profile
    def __init__(self, unit:'Syllable', position=None, **kwargs):
        self.unit = unit
        self.viold = {}
        super().__init__(children=[], parent=position, **kwargs)

    def __copy__(self):
        new = ParseSlot(unit=self.unit)
        new.viold = copy(self.viold)
        new._attrs = copy(self._attrs)
        return new
    
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
            # 'num':self.num,
            **self.viold,
            # 'is_stressed':self.is_stressed, 
            # 'is_heavy':self.is_heavy, 
            # 'is_strong':self.is_strong, 
            # 'is_weak':self.is_weak,
        }








class ParseList(EntityList):
    index_name='parse'
    prefix='parselist'

    @cached_property
    def num_parses(self): return len(self.unbounded)
    @cached_property
    def num_all_parses(self): return len(self.data)

    @cached_property
    def attrs(self):
        return {
            **self._attrs, 
            'num_parses':self.num_parses, 
            'num_all_parses':self.num_all_parses
        }
    
    @property
    def unbounded(self): 
        return ParseList(children=[px for px in self.data if px is not None and not px.is_bounded])
    @cached_property
    def bounded(self): 
        return ParseList(children=[px for px in self.data if px is not None and px.is_bounded])

    @cached_property
    def best_parse(self): return self.data[0] if self.data else None

    def bound(self, progress=True, meter=None, **meter_kwargs):
        parses = [p for p in self.data if not p.is_bounded]
        if meter is None: meter = Meter(**meter_kwargs)
        # logger.debug(f'Bounding {len(parses)} with meter {meter}')
        iterr = tqdm(parses, desc='Bounding parses', disable=not progress)
        for parse_i,parse in enumerate(iterr):
            parse.constraint_viols  # init
            if parse.is_bounded: continue
            for comp_parse in parses[parse_i+1:]:
                if comp_parse.is_bounded: continue
                if not parse.can_compare(comp_parse): continue
                relation = parse.bounding_relation(comp_parse)
                if relation == Bounding.bounded:
                    parse.is_bounded = True
                    parse.bounded_by = comp_parse
                elif relation == Bounding.bounds:
                    comp_parse.is_bounded = True
                    comp_parse.bounded_by = parse
        self._bound_init = True
        return self.unbounded


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