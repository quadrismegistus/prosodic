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
#         self.violset=Multiseft()
#         for mpos in self.positions: 
#             self.violset.update(mpos.violset)

@total_ordering
class Parse(Entity):
    prefix='parse'
    def __init__(
            self, 
            wordforms_or_str, 
            scansion:str='', 
            meter:'Meter'=None, 
            parent=None, 
            positions=None, 
            is_bounded=False,
            bounded_by=None):
        from .meter import Meter
        if not positions: positions = []
        self.positions = positions

        # meter
        if meter is None:
            meter = Meter()
        self.meter_obj=self.meter=meter
        
        # wordforms
        assert wordforms_or_str
        if hasattr(wordforms_or_str,'is_parseable') and wordforms_or_str.is_parseable:
            parent = wordforms_or_str
            self.wordforms = meter.get_wordform_matrix(parent)[0]
        elif type(wordforms_or_str)==str:
            parent = Line(wordforms_or_str)
            self.wordforms = meter.get_wordform_matrix(parent)[0]
        elif type(wordforms_or_str)==list:
            self.wordforms = WordFormList(wordforms_or_str)
        else:
            self.wordforms = wordforms_or_str

        
        
        # slots
        # self.slots = [ParseSlot(slot) for slot in self.wordforms.slots]
        # self.slots = self.wordforms.slots

        # scansion
        if not scansion: scansion=get_iambic_parse(len(self.wordforms.slots))
        if type(scansion)==str: scansion=split_scansion(scansion)
        self.positions_ls = copy(scansion)
        
        # divide positions
        self.line=parent
        self.is_bounded = is_bounded
        self.bounded_by = [] if not bounded_by else [x for x in bounded_by]
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
            super().__init__(children=[], parent=parent)
            for mpos_str in self.positions_ls: self.extend(mpos_str)
        else:
            super().__init__(children=positions, parent=parent)
        self.children = self.positions
        self.init()

    def init(self):
        for pos in self.positions:
            pos.parse = self
            pos.init()
    
    def to_json(self):
        return {
            '_class':self.__class__.__name__,
            'children':[pos.to_json() for pos in self.positions],
            'wordforms':self.wordforms.to_json(),
            'meter':self.meter_obj.to_json(),
            'is_bounded':self.is_bounded,
            'rank':self.parse_rank,
            'meter_str':self.meter_str,
            'stress_str':self.stress_str,
            'score':self.score,
            'bounded_by':list(self.bounded_by),
        }
    
    @staticmethod
    def from_json(json_d, line=None):
        wordforms = from_json(json_d['wordforms'])
        meter = from_json(json_d['meter'])
        positions = [from_json(d) for d in json_d['children']]
        slots = [slot for pos in positions for slot in pos.slots]
        sylls = [syll for word in wordforms for syll in word.children]
        assert len(slots) == len(sylls)
        for syll,slot in zip(sylls,slots):
            slot.unit = syll
        return Parse(
            wordforms,
            positions=positions,
            parent=line,
            meter=meter,
            is_bounded=json_d['is_bounded'],
            bounded_by=json_d['bounded_by']
        )

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
            **(self.stanza.prefix_attrs if self.line and self.line.stanza else {}),
            **(self.line.prefix_attrs if self.line else {}),
            **self._attrs,
            # 'stanza_num':self.line.parent.num if self.line and self.line.parent else None,
            # 'line_num':self.line.num if self.line else None,
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
        
    def bounds(self, parse):
        return self.bounding_relation(parse) == Bounding.bounds

    def _repr_html_(self): 
        return self.to_html(as_str=True, blockquote=True)

    @cached_property
    def html(self): return self.to_html()

    @cached_property
    def wordtokens(self): 
        if self.line: return self.line.wordtokens
        return WordTokenList(WordToken(wf.txt) for wf in self.wordforms)


    def to_html(self, as_str=False, css=HTML_CSS, blockquote=False):
        wordtokend = {wt:[] for wt in self.wordtokens}
        for slot in self.slots:
            wordtokend[slot.unit.wordtoken].append(slot)
        output=[]
        for wordtoken in wordtokend:
            prefstr=get_initial_whitespace(wordtoken.txt)
            output.append(prefstr)
            wordtoken_slots = wordtokend[wordtoken]
            if wordtoken_slots:
                for slot in wordtoken_slots:
                    pos=slot.parent
                    spclass='meter_' + ('strong' if slot.is_prom else 'weak')
                    stclass='stress_' + ('strong' if slot.unit.is_stressed else 'weak')
                    vclass=' violation' if pos.violset else ''
                    slotstr=f'<span class="{spclass} {stclass}{vclass}">{slot.unit.txt}</span>'
                    output.append(slotstr)
                    # viol_str=' '.join(pos.violset)
                    # viol_title = 'Violated %s constraints: %s' % (len(pos.violset), viol_str)
                    # slotstr=f'<span class="violation" title="{viol_title}" id="viol__line_{self.line.num}">{slotstr}</span>'
            else:
                output.append(wordtoken.txt)
        out = ''.join(output)
        out = f'<style>{css}</style><div class="parse">{out}</div>'
        if blockquote: out+=f'<div class="miniquote">⎿ {self.__repr__(bad_keys={"txt","line_txt"})}</div>'
        return out if as_str else HTML(out)


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
        if self.parse: self.init()
    
    def init(self):
        assert self.parse
        if any (not slot.unit for slot in self.slots):
            print(self.slots)
            print([slot.__dict__ for slot in self.slots])
            raise Exception
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
    
    def to_json(self):
        return super().to_json(meter_val=self.meter_val)
    
    # def from_json(json_d):
    #     return ParsePosition(
    #         json_d['meter_val'],
    #         children=[
    #             ParseSlot.from_json(d)
    #             for d in json_d['children']
    #         ]
    #     )

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
    def __init__(self, unit:'Syllable'=None, parent=None, children=[], viold={}, **kwargs):
        # print(unit,parent,children,viold,kwargs)
        if unit is None and children:
            assert len(children)==1
            unit = children[0]
            
        self.unit = unit
        self.viold = {**viold}
        super().__init__(
            children=[], 
            parent=parent, 
            **kwargs
        )

    def __copy__(self):
        new = ParseSlot(unit=self.unit)
        new.viold = copy(self.viold)
        new._attrs = copy(self._attrs)
        return new
    
    def to_json(self):
        d=super().to_json(
            unit=self.unit.to_hash(),
            viold=self.viold
        )
        d.pop('children')
        return d
    
    
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

    @staticmethod
    def from_json(json_d, line=None):
        parses = [
            Parse.from_json(d, line=line)
            for d in json_d['children']
        ]
        return ParseList(parses, parent=line)


    @cached_property
    def num_parses(self): return self.num_unbounded
    @cached_property
    def num_all_parses(self): return len(self.data)

    @cached_property
    def attrs(self):
        return {
            **self.line.prefix_attrs,
            **self._attrs,
            'num_parses':self.num_parses,
            # 'num_all_parses':self.num_all_parses
        }
    
    @cached_property
    def unbounded(self): 
        return ParseList(children=[px for px in self.data if px is not None and not px.is_bounded])
    @cached_property
    def bounded(self): 
        return ParseList(children=[px for px in self.data if px is not None and px.is_bounded])

    @cached_property
    def best_parse(self): return self.data[0] if self.data else None
    
    @cached_property
    def num_unbounded(self): return len(self.unbounded)
    @cached_property
    def num_bounded(self): return len(self.bounded)
    @cached_property
    def num_all(self): return len(self.data)

    @cached_property
    def parses(self): return self

    def bound(self, progress=False):
        parses = [p for p in self.data if not p.is_bounded]
        iterr = tqdm(parses, desc='Bounding parses', disable=not progress,position=0)
        for parse_i,parse in enumerate(iterr):
            parse.constraint_viols  # init
            if parse.is_bounded: continue
            for comp_parse in parses[parse_i+1:]:
                if comp_parse.is_bounded: continue
                if not parse.can_compare(comp_parse): continue
                relation = parse.bounding_relation(comp_parse)
                if relation == Bounding.bounded:
                    parse.is_bounded = True
                    parse.bounded_by.append((comp_parse.meter_str,comp_parse.stress_str))
                elif relation == Bounding.bounds:
                    comp_parse.is_bounded = True
                    comp_parse.bounded_by.append((parse.meter_str,parse.stress_str))
        self._bound_init = True
        return self.unbounded
    
    def rank(self):
        self.data.sort()
        for i,parse in enumerate(self.data):
            parse.parse_rank = i+1
    
    @cached_property
    def line(self):
        for parse in self.data:
            if parse.line:
                return parse.line

    @cached_property
    def lines(self):
        return LineList(
            unique(
                parse.line
                for parse in self.data
            )
        )

    def stats(self, norm=False):
        return setindex(
            pd.DataFrame([
                line.parse_stats if not norm else line.parse_stats_norm
                for line in self.lines
            ]),
            DF_INDEX
        )
    

    def _repr_html_(self): 
        df=self.unbounded.df if self.num_unbounded else self.df
        return super()._repr_html_(df=df)
    
    @cached_property
    def df(self):
        df = self.df_syll[[
            c for c in self.df_syll 
            if not c.endswith('_txt') 
            and not c.startswith('parselist_')
        ]]
        index = [
            i
            for i in df.index.names
            if not i.startswith('meter')# meterpos_ and metersyll_ are by syll
        ]
        aggby = {
            col:np.median if 'parse' in col else np.sum
            for col in df
        }
        odf = self.df_syll.groupby(index).agg(aggby)
        return odf

    @cached_property
    def df_syll(self):
        return self.get_df().assign(**self._attrs)
    
    @cached_property
    def scansions(self, **kwargs):
        """
        Unique scansions
        """
        from .parsing import ParseList
        index_matches = pd.Series(
            [
                px.meter_str 
                for px in self
            ]).drop_duplicates().index
        return ParseList(children=[self.parses[i] for i in index_matches])
    

    
    def stats(self, norm=False):
        odx={
            **(self.parent.prefix_attrs if self.parent else {}), 
            **self.prefix_attrs
        }
        odx['bestparse_txt'] = self.best_parse.txt
        nsyll = self.best_parse.num_sylls
        cnames = [f.__name__ for f in self.best_parse.meter.constraints]
        odx['bestparse_nsylls']=nsyll
        odx['n_combo']=len(self.best_parse.meter.get_wordform_matrix(self))
        odx['n_parse']=self.num_unbounded
        if not norm:
            odx['n_viols']=np.median([
                parse.score
                for parse in self.unbounded
            ])
            for cname in cnames:
                odx['*'+cname] = np.median([
                    parse.constraint_scores.get(cname,0)
                    for parse in self.unbounded
                ])
        else:
            odx[f'n_viols']=np.mean([
                int(bool(x))
                for bp in self.unbounded
                for cnamex in bp.constraint_viols
                for x in bp.constraint_viols[cnamex]
            ])
            for cname in cnames:
                odx[f'n_{cname}']=np.mean([
                    int(bool(x))
                    for bp in self.unbounded
                    for x in bp.constraint_viols.get(cname,[])
                ])
        return odx


class ParseListList(EntityList):
    index_name='parse'
    prefix='parselists'

    def __getattr__(self, attr):
        results = [getattr(plist,attr) for plist in self.data if hasattr(plist,attr)]
        if not results: return
        res = results[0]
        if callable(res):
            def f(*x,**y):
                return self.combine([res(*x,**y) for res in results])
            return f
        else:
            return self.combine(results)


    def combine(self, results):
        if not results: return
        res = results[0]
        if res is None:
            return
        elif is_numeric(res):
            return np.median(results)
        elif isinstance(res, ParseList):
            return ParseList(parse for parselist in results for parse in parselist)
        elif isinstance(res,pd.DataFrame):
            return pd.concat(results)
        elif isinstance(res,dict) or isinstance(res,pd.Series):
            return pd.DataFrame(results)

        raise Exception(f'what is this? {results}')
    
    @cached_property
    def best_parse(self):
        return min(self.parses.data)
    
    @cached_property
    def lines(self):
        return LineList(pl.line for pl in self.data)

    @cached_property
    def attrs(self):
        return {
            **self._attrs, 
            'num_parsed':len(self.data),
        }



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





