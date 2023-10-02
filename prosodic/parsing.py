from .imports import *
from .constraints import *

class ParseTextUnit(entity):
    def parse(self, meter=None, **meter_kwargs):
        if meter is None: meter=Meter(**meter_kwargs)
        return MeterLine(self, meter=meter)


## METER
class Meter(entity):
    def __init__(self,
            constraints=DEFAULT_CONSTRAINTS, 
            categorical_constraints=DEFAULT_CATEGORICAL_CONSTRAINTS,
            max_s=METER_MAX_S, 
            max_w=METER_MAX_W, 
            resolve_optionality=METER_RESOLVE_OPTIONALITY,
            ):
        self.constraints = constraints
        self.categorical_constraints = categorical_constraints
        self.max_s=max_s
        self.max_w=max_w
        self.resolve_optionality=resolve_optionality

    def parse(self, text_or_line:entity):
        if isinstance(text_or_line, MeterLine):
            return text_or_line
        if isinstance(text_or_line, ParseTextUnit):
            return self.parse_line(text_or_line)
        elif text_or_line.is_text:
            return self.parse_text(text_or_line)
        logger.error(f'What type of entity is this? -> {text_or_line}')
    
    def parse_line(self, line):
        assert isinstance(line, ParseTextUnit)
        return MeterLine(line, meter=self)


class MeterLine(entity):
    def __init__(self, line_or_parseable_entity:ParseTextUnit, meter:Meter=None):
        if meter is None: meter = Meter()
        assert isinstance(meter, Meter)

        line = line_or_parseable_entity
        assert isinstance(line, ParseTextUnit)
        
        super().__init__(children=[line], parent=meter)
        self.line = line
        self.meter = meter
        self._bound_init = False
        self._parses = []
    
    @cached_property
    def wordform_matrix(self):
        from .words import WordFormList
        ll = [l for l in self.line.wordforms if l]
        ll = [WordFormList(l) for l in itertools.product(*ll)]
        ll.sort()
        return ll

    @cached_property
    def slot_matrix(self): 
        lim = 1 if not self.meter.resolve_optionality else None
        wfm = self.wordform_matrix[:lim]
        return [wfl.slots for wfl in wfm]

    # @cache
    @profile
    def parse(self, progress=None, bound=True, **kwargs):
        parses = self.possible_parses()
        if progress is None: progress = len(parses)>10000
        parses = tqdm(
            parses,
            desc='Applying constraints',
            disable=not progress,
        )
        parses = [px.init() for px in parses]
        if bound: parses = self.bound_parses(parses, progress=progress)
        parses.sort()
        for i,px in enumerate(parses): px.parse_rank=i+1
        self._parses = ParseList(parses)
        return self.scansions

    @profile
    def possible_parses(self,slot_matrix=None):
        if slot_matrix is None: 
            slot_matrix=self.slot_matrix
        all_parses = []
        for slots in slot_matrix:
            all_parses.extend(
                get_possible_parse_objs(
                    slots, 
                    constraints=self.meter.constraints, 
                    max_s=self.meter.max_s, 
                    max_w=self.meter.max_w
                )
            )
        return all_parses
    
    
    
    @profile
    def bound_parses(self, parses = None, progress=True):
        if self._bound_init: return
        if parses is None: parses = self.all_parses
        iterr = tqdm(parses, desc='Bounding parses', disable=not progress)
        for parse_i,parse in enumerate(iterr):
            for cname in self.meter.categorical_constraints:
                if cname in parse.violset:
                    parse.is_bounded = True
                    break
            if parse.is_bounded: continue
            for comp_parse in parses[parse_i+1:]:
                if comp_parse.is_bounded:
                    continue
                relation = parse.bounding_relation(comp_parse)
                if relation == Bounding.bounded:
                    parse.is_bounded = True
                    parse.bounded_by = comp_parse
                elif relation == Bounding.bounds:
                    comp_parse.is_bounded = True
                    comp_parse.bounded_by = parse
        self._bound_init = True
        return parses



    @cached_property
    def all_parses(self, **kwargs):
        if not self._parses: self.parse(**kwargs)
        return self._parses
    @cached_property
    def best_parses(self, **kwargs): 
        return self.unbounded_parses
    @cached_property
    def num_parses(self, **kwargs): 
        return len(self.unbounded_parses)
    @cached_property
    def best_parse(self): 
        return self.best_parses[0] if self.best_parses else None
    @cached_property
    def unbounded_parses(self): 
        if not self._bound_init: self.bound_parses()
        return ParseList([px for px in self.all_parses if not px.is_bounded])
    @cached_property
    def bounded_parses(self, **kwargs): 
        if not self._bound_init: self.bound_parses()
        return ParseList([px for px in self.all_parses if px.is_bounded])
    @cached_property
    def parses(self): 
        return self.scansions
    @cached_property
    def scansions(self, **kwargs):
        index_matches = pd.Series(
            [
                px.meter_str 
                for px in self.all_parses
            ]).drop_duplicates().index
        return ParseList([self.all_parses[i] for i in index_matches])
    
    @cached_property
    def parse_stats(self):
        if not hasattr(self,'_constraints'): self.parse()
        odx={**self.attrs}
        odx['parse'] = self.best_parse.txt
        nsyll = self.best_parse.num_sylls
        cnames = [f.__name__ for f in self._constraints]
        odx['nsylls']=nsyll
        odx['ncombo']=len(self.wordform_matrix) / nsyll * 10
        odx['nparse']=len(self.best_parses) / nsyll * 10
        odx['nviols']=np.mean([
            int(bool(x))
            for bp in self.best_parses
            for cnamex in bp.constraint_viols
            for x in bp.constraint_viols[cnamex]
        ]) * 10
        for cname in cnames:
            odx[f'{cname}']=np.mean([
                int(bool(x))
                for bp in self.best_parses
                for x in bp.constraint_viols.get(cname,[])
            ]) * 10
        
        return odx


@total_ordering
class Parse(entity):
    str2int = {'w':'1','s':'2'}
    def __init__(self, num_total_slots:int, constraints:list=[]):
        super().__init__()
        self.positions = []
        self.constraints = constraints
        self.num_slots = 0
        self.num_total_slots = num_total_slots
        self.is_bounded = False
        self.bounded_by = None
        self.unmetrical = False
        self.comparison_nums = set()
        self.comparison_parses = []
        self.parse_num = 0
        self.total_score = None
        self.pause_comparisons = False
        self.parse_rank = None
        self.violset = Multiset()

        if self.positions: self.init()

    @cached_property
    @profile
    def sort_key(self): 
        return (
            int(bool(self.is_bounded)),
            self.score, 
            self.positions[0].is_prom,
            self.average_position_size,
            self.num_stressed_sylls,
        )
    @cached_property
    def constraint_names(self):
        return [c.__name__ for c in self.constraints]
    @cached_property
    def constraint_d(self):
        return dict(zip(self.constraint_names, self.constraints))

    @profile
    def __lt__(self,other):
        return self.sort_key < other.sort_key

    @profile
    def __eq__(self, other):
        logger.error(f'{self} and {other} could not be compared in sort, ended up equal')
        return not (self<other) and not (other<self)
    
    @cached_property
    def txt(self): return " ".join(m.token for m in self.positions)

    # def __repr__(self):
        # attrstr=get_attr_str(self.attrs)
        # parse=self.txt
        # preattr=f'({self.__class__.__name__}: {parse})'
        # return f'{preattr}{attrstr}'
    
    @profile
    def init(self):
        if self._init: return
        self._init=True
        self.violset=Multiset()
        for mpos in self.positions: 
            mpos.init()
            self.violset.update(mpos.violset)
        return self
    
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
    @profile
    def average_position_size(self):
        l = [len(mpos.children) for mpos in self.positions if mpos.children]
        return np.mean(l) if len(l) else np.nan

    @property
    @profile
    def attrs(self):
        return {
            **self._attrs,
            'parse':self.txt,
            'rank':self.parse_rank,
            'meter':self.meter_str,
            'stress':self.stress_str,
            'score':self.score,
            **({'is_bounded':True} if self.is_bounded else {}),
            **{c:v for c,v in self.constraint_scores.items() if v!=np.nan and v}
        }

    @cached_property
    @profile
    def constraint_viols(self):
        self.init()
        # logger.debug(self)
        scores = [mpos.constraint_viols for mpos in self.positions]
        d={}
        nans=[np.nan for _ in range(len(self.slots))]
        for constraint in self.constraints:
            cname=constraint.__name__
            d[cname] = [x for score_d in scores for x in score_d.get(cname,nans)]
        return d
    
    @cached_property
    @profile
    def constraint_scores(self):
        self.init()
        return {cname:safesum(cvals) for cname,cvals in self.constraint_viols.items()}

    @cached_property
    @profile
    def score(self):
        self.init()
        try:
            return sum(self.constraint_scores.values())
        except ValueError:
            return '*'  # could be string if categorical

    # return a list of all slots in the parse
    @cached_property
    def slots(self):
        return [slot for mpos in self.positions for slot in mpos.slots]

    @cached_property
    @profile
    def meter_str(self,word_sep=""):
        return ''.join(
            '+' if mpos.is_prom else '-'
            for mpos in self.positions
            for slot in mpos.slots
        )
    
    @cached_property
    @profile
    def stress_str(self,word_sep=""):
        return ''.join(
            '+' if slot.is_stressed else '-'
            for mpos in self.positions
            for slot in mpos.slots
        ).lower()
    
    # return a representation of the bounding relation between self and parse
    @profile
    def bounding_relation(self, parse):
        self.init()
        parse.init()
        if self.violset < parse.violset:
            return Bounding.bounds
        elif self.violset > parse.violset:
            return Bounding.bounded
        elif self.violset == parse.violset:
            return Bounding.equal
        else:
            return Bounding.unequal
    

class ParsePosition(entity):
    @profile
    def __init__(self, meter_val:str, parse:Parse, slots=[]): # meter_val represents whether the position is 's' or 'w'
        self.parse=parse
        self.viold={}  # dict of lists of viols; length of these lists == length of `slots`
        self.violset=set()   # set of all viols on this position
        slots = [ParseSlot(slot,self) for slot in slots]
        self.slots=slots
        super().__init__(
            meter_val=meter_val,
            children=slots,
        )
        # init?
        for cname,constraint in self.constraint_d.items():
            slot_viols = [int(bool(vx)) for vx in constraint(self)]
            assert len(slot_viols) == len(self.slots)
            self.viold[cname] = slot_viols
            if any(slot_viols): self.violset.add(cname)


    def __copy__(self):
        other = ParsePosition(self.meter_val, parse=self, slots=self.slots[:])
        for k,v in list(self.constraint_scores.items()):
            other.constraint_scores[k]=copy(v)
        return other
    
    @profile
    def __repr__(self):
        return f'ParsePosition({self.token})'
    
    @cached_property
    @profile
    def constraint_viols(self): return self.viold
    @cached_property
    @profile
    def constraint_set(self): return self.violset
    @cached_property
    @profile
    def constraint_scores(self):
        return {cname:safesum(cvals) for cname,cvals in self.constraint_viols.items()}


    @cached_property
    def constraints(self): return self.parse.constraints
    @cached_property
    def constraint_d(self): return self.parse.constraint_d

    @cached_property
    def is_prom(self): return self.meter_val=='s'

    @cached_property
    def token(self):
        if not hasattr(self,'_token') or not self._token:
            token = '.'.join([slot.token for slot in self.slots])
            token=token.upper() if self.meter_val=='s' else token.lower()
            self._token=token
        return self._token




class ParseSlot(entity):
    @profile
    def __init__(self, unit:'Syllable', mpos:'ParsePosition'):
        self.unit = unit
        self.position = mpos
        token = unit._txt
        super().__init__(children=[unit], token=token)
    @cached_property
    def meter_val(self): return self.position.meter_val
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
    def attrs(self):
        return {
            **self._attrs, 
            **{
                'is_stressed':self.is_stressed, 
                'is_heavy':self.is_heavy, 
                'is_strong':self.is_strong, 
                'is_weak':self.is_weak
            }
        }






def getlenparse(l): return sum(len(x) for x in l)

def iter_mpos(nsyll, starter=[], pos_types=None, max_s=METER_MAX_S, max_w=METER_MAX_W):
    if pos_types is None:
        wtypes = ['w'*n for n in range(1,max_w+1)]
        stypes = ['s'*n for n in range(1,max_s+1)]
        pos_types=[[x] for x in wtypes + stypes]
        
    news=[]
    for pos_type in pos_types:
        if starter and starter[-1][-1]==pos_type[0][0]: continue
        new = starter + pos_type
        # if starter: print(starter[-1][-1], pos_type[0][0], new)
        #if not is_ok_parse(new): continue
        if getlenparse(new)<=nsyll:
            news.append(new)
    
    # news = battle_parses(news)
    if news: yield from news
    # print('\n'.join('|'.join(x) for x in news))
    for new in news: yield from iter_mpos(nsyll, starter=new, pos_types=pos_types)

@profile
def get_possible_parses(nsyll, max_s=METER_MAX_S, max_w=METER_MAX_W):
    if max_s is None: max_s = nsyll
    if max_w is None: max_w = nsyll
    return [l for l in iter_mpos(nsyll,max_s=max_s,max_w=max_w) if getlenparse(l)==nsyll]

@profile
def get_possible_parse_objs(slots, constraints=DEFAULT_CONSTRAINTS, max_s=METER_MAX_S, max_w=METER_MAX_W):
    parse_objs = []
    for parse_poss in get_possible_parses(len(slots), max_s=max_s, max_w=max_w):
        slot_i=0
        parse_obj = Parse(len(slots), constraints=constraints)
        mpos_objs=[]
        for mpos in parse_poss:
            mpos_slots=[]
            for slot_mval in mpos:
                mpos_slots.append(slots[slot_i])
                slot_i+=1
            mpos_obj = ParsePosition(mpos[0], parse=parse_obj, slots=mpos_slots)
            mpos_objs.append(mpos_obj)
        parse_obj.children = parse_obj.positions = mpos_objs
        parse_objs.append(parse_obj)
    return parse_objs







class ParseList(UserList):
    def __repr__(self):
        return repr(self.df)
    @property
    def df(self):
        l=[
            {
                'parse':px.txt,
                **px.attrs
            } 
            for px in self.data
            if px is not None
        ]
        if not l: return pd.DataFrame().rename_axis('parse')
        return pd.DataFrame(l).set_index('parse').fillna(0).applymap(lambda x: x if type(x)==str else int(x))





# class representing the potential bounding relations between to parses
class Bounding:
    bounds = 0 # first parse harmonically bounds the second
    bounded = 1 # first parse is harmonically bounded by the second
    equal = 2 # the same constraint violation scores
    unequal = 3 # unequal scores; neither set of violations is a subset of the other

