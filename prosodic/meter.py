from .imports import *
from .constraints import *

## METER
class Meter(entity):
    prefix='meter'
    
    def __init__(self,
            constraints=DEFAULT_CONSTRAINTS, 
            categorical_constraints=DEFAULT_CATEGORICAL_CONSTRAINTS,
            max_s=METER_MAX_S, 
            max_w=METER_MAX_W, 
            resolve_optionality=METER_RESOLVE_OPTIONALITY,
            ):
        self.constraints = [
            x for x in [
                CONSTRAINTS.get(cname) if type(cname)==str else cname 
                for cname in constraints
            ] if x is not None
        ]
        self.categorical_constraints = categorical_constraints
        self.max_s=max_s
        self.max_w=max_w
        self.resolve_optionality=resolve_optionality
        super().__init__()

    def __getitem__(self, text_or_line):
        return self.get(text_or_line)

    def get(self, text_or_line:entity):
        x=text_or_line
        if isinstance(x, MeterLine): return x
        if isinstance(x, MeterText): return x
        if isinstance(x,ParseableText):
            if x.is_parseable: 
                return MeterLine(x)
            else:
                return MeterText(x)
        logger.error(f'What type of entity is this? -> {x}')





class ParseableText(entity):
    prefix='parsedtxt'

    @cached_property
    def attrs(self):
        odx=super().attrs
        odx['txt']=self.txt.strip()
        return odx
    
    @cached_property
    def wordform_matrix(self):
        from .words import WordFormList
        lim = 1 if not self.meter.resolve_optionality else None
        ll = [l for l in self.wordforms if l]
        ll = [WordFormList(l) for l in itertools.product(*ll)][:lim]
        ll.sort()
        return ll

    @cached_property
    def slot_matrix(self): 
        return [wfl.slots for wfl in wfm]

    @cache
    # @profile
    def parse(self, progress=None, bound=True, **meter_kwargs):
        from .parsing import ParseList
        self.set_meter(**meter_kwargs)
        parses = list(self.iter_parses(progress=progress))
        if bound: self.bound_parses(parses, progress=progress)
        parses.sort()
        for i,px in enumerate(parses): px.parse_rank=i+1
        self._parses = ParseList(
            children=parses, 
        )
        return self._parses

    # @profile
    def iter_parses(self, progress=True):
        from .parsing import Parse
        all_parses = []
        combos = [
            (wfl,scansion)
            for wfl in self.wordform_matrix
            for scansion in get_possible_scansions(wfl.num_sylls)    
        ]
        iterr=tqdm(combos, disable=not progress)
        for wfl,scansion in iterr:
            parse = Parse(wfl, scansion, meter=self.meter, parent=self)
            all_parses.append(parse)
        return all_parses
    
    
    
    # @profile
    def bound_parses(self, parses = None, progress=True):
        if hasattr(self,'_bound_init') and not self._bound_init: return
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
        from .parsing import ParseList
        if hasattr(self,'_bound_init') and not self._bound_init: self.bound_parses()
        return ParseList(children=[px for px in self.all_parses if not px.is_bounded])
    @cached_property
    def bounded_parses(self, **kwargs): 
        from .parsing import ParseList
        if not self._bound_init: self.bound_parses()
        return ParseList(children=[px for px in self.all_parses if px.is_bounded])
    @cached_property
    def parses(self): 
        return self.scansions
    @cached_property
    def scansions(self, **kwargs):
        from .parsing import ParseList
        index_matches = pd.Series(
            [
                px.meter_str 
                for px in self.all_parses
            ]).drop_duplicates().index
        return ParseList(children=[self.all_parses[i] for i in index_matches])
    
    @cached_property
    def parse_stats(self):
        if not self._parses: self.parse()
        odx={**self.parent.prefix_attrs, **self.prefix_attrs}
        odx['bestparse_txt'] = self.best_parse.txt
        nsyll = self.best_parse.num_sylls
        cnames = [f.__name__ for f in self.meter.constraints]
        odx['bestparse_nsylls']=nsyll
        odx['parses_ncombo']=len(self.wordform_matrix) / nsyll * 10
        odx['parses_nparse']=len(self.best_parses) / nsyll * 10
        odx['parses_nviols']=np.mean([
            int(bool(x))
            for bp in self.best_parses
            for cnamex in bp.constraint_viols
            for x in bp.constraint_viols[cnamex]
        ]) * 10
        for cname in cnames:
            odx[f'parses_{cname}']=np.mean([
                int(bool(x))
                for bp in self.best_parses
                for x in bp.constraint_viols.get(cname,[])
            ]) * 10
        
        return odx



