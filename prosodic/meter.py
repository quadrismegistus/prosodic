from .imports import *
from .constraints import *

## METER
class Meter(Entity):
    prefix='meter'
    
    def __init__(self,
            constraints=DEFAULT_CONSTRAINTS, 
            categorical_constraints=DEFAULT_CATEGORICAL_CONSTRAINTS,
            max_s=METER_MAX_S, 
            max_w=METER_MAX_W, 
            resolve_optionality=METER_RESOLVE_OPTIONALITY,
            ):
        self.constraints = get_constraints(constraints)
        self.categorical_constraints = get_constraints(categorical_constraints)
        self.max_s=max_s
        self.max_w=max_w
        self.resolve_optionality=resolve_optionality
        super().__init__()

    @cached_property
    def constraint_names(self):
        return tuple(c.__name__ for c in self.constraints)
    @cached_property
    def categorical_constraint_names(self):
        return tuple(c.__name__ for c in self.categorical_constraints)
    @cached_property
    def attrs(self):
        return {
            'constraints':self.constraint_names,
            'categorical_constraints':self.categorical_constraint_names,
            'max_s':self.max_s,
            'max_w':self.max_w,
            'resolve_optionality':self.resolve_optionality
        }





class ParseableText(Entity):
    prefix='parsedtxt'

    def __init__(self):
        self._parses=[]
        self._boundedparses=[]
        self._bestparses=[]

    @cached_property
    def attrs(self):
        odx=super().attrs
        odx['txt']=self.txt.strip()
        return odx
    
    @cached_property
    def wordform_matrix(self):
        from .words import WordFormList
        lim = 1 if not self.meter.resolve_optionality else None
        ll = [l for l in self.wordforms_all if l]
        ll = [WordFormList(l) for l in itertools.product(*ll)]
        ll.sort()
        return ll[:lim]

    # @cache
    # @profile
    def parse(self, progress=None, bound=True, **meter_kwargs):
        from .parsing import ParseList
        meter = self.set_meter(**meter_kwargs)
        logger.debug(f'Set meter to: {meter}')
        parses = list(self.iter_parses(progress=progress, meter=meter))
        logger.debug(f'Returned {len(parses)} parses')
        if bound: self.bound_parses(parses, progress=progress)
        parses.sort()
        for i,px in enumerate(parses): px.parse_rank=i+1
        self._parses = ParseList(parses)
        self._bestparses = ParseList([px for px in parses if not px.is_bounded])
        self._boundedparses = ParseList([px for px in parses if px.is_bounded])
        return self._bestparses

    # @profile
    def iter_parses(self, progress=True, meter=None):
        if meter is None: meter=self.meter
        from .parsing import Parse
        all_parses = []
        combos = [
            (wfl,scansion)
            for wfl in self.wordform_matrix
            for scansion in get_possible_scansions(wfl.num_sylls, max_s=meter.max_s, max_w=meter.max_w)
        ]
        wfl=self.wordform_matrix[0]
        logger.debug(f'Generated {len(combos)} from a wordfrom matrix of size {len(self.wordform_matrix), wfl, wfl.num_sylls, meter.max_s, meter.max_s, len(get_possible_scansions(wfl.num_sylls))}')
        iterr=tqdm(combos, disable=not progress)
        for wfl,scansion in iterr:
            parse = Parse(wfl, scansion, meter=meter, parent=self)
            all_parses.append(parse)
        logger.debug(f'Returning {len(all_parses)} parses')
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



    @property
    def all_parses(self, **kwargs):
        if not self._parses: self.parse(**kwargs)
        return self._parses
    @property
    def best_parses(self): 
        if not self._bestparses: self.parse()
        return self._bestparses
    @property
    def num_parses(self, **kwargs): 
        return len(self.unbounded_parses)
    @property
    def best_parse(self): 
        return self.best_parses[0] if self.best_parses else None
    @property
    def unbounded_parses(self): 
        return self.best_parses

    @property
    def bounded_parses(self, **kwargs): 
        if not self._boundedparses: self.parse()
        return self._boundedparses

    @property
    def parses(self): 
        return self.scansions
    @property
    def scansions(self, **kwargs):
        from .parsing import ParseList
        index_matches = pd.Series(
            [
                px.meter_str 
                for px in self.all_parses
            ]).drop_duplicates().index
        return ParseList(children=[self.all_parses[i] for i in index_matches])
    
    @property
    def parse_stats(self):
        if not self._parses: self.parse()
        odx={
            **(self.parent.prefix_attrs if self.parent else {}), 
            **self.prefix_attrs
        }
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



