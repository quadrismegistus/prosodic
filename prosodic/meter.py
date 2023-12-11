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
    
    @cache
    def get_pos_types(self, nsylls=None):
        max_w=nsylls if self.max_w is None else self.max_w
        max_s=nsylls if self.max_s is None else self.max_s
        wtypes = ['w'*n for n in range(1,max_w+1)]
        stypes = ['s'*n for n in range(1,max_s+1)]
        return wtypes + stypes
    




class ParseableText(Entity):
    prefix='parsedtxt'
    cached_properties_to_clear = [
        'all_parses',
        'best_parses',
        'num_parses',
        'best_parse',
        'unbounded_parses',
        'parses',
        'scansions',
        'parse_stats',
        'parse_stats_norm',
        'html'
    ]

    def __init__(self):
        self._parses=[]
        self._boundedparses=[]
        self._unboundedparses=[]

    @cached_property
    def attrs(self):
        odx=super().attrs
        odx['txt']=self.txt.strip()
        return odx
    
    @property
    def wordform_matrix(self):
        return self.get_wordform_matrix()
    
    @cache
    def get_wordform_matrix(self, resolve_optionality=METER_RESOLVE_OPTIONALITY):
        from .words import WordFormList
        lim = 1 if not resolve_optionality else None
        ll = [l for l in self.wordforms_all if l]
        ll = [WordFormList(l) for l in itertools.product(*ll)]
        ll.sort()
        return ll[:lim]
    


    @cache
    # @profile
    def parse_all(self, progress=None, bound=True, meter=None, **meter_kwargs):
        from .parsing import ParseList
        logger.debug([progress,bound,meter,meter_kwargs])
        meter = self.get_meter(meter=meter,**meter_kwargs)
        parses = list(self.iter_parses(progress=progress, meter=meter))
        logger.debug(f'Returned {len(parses)} parses')
        if bound: self.bound_parses(parses, progress=progress, meter=meter)
        parses.rank()
        for i,px in enumerate(parses): px.parse_rank=i+1
        self._parses = ParseList(parses)
        self._unboundedparses = ParseList([px for px in parses if not px.is_bounded])
        self._boundedparses = ParseList([px for px in parses if px.is_bounded])
        return self._unboundedparses
    
    @cache
    def parse(self, meter=None, **meter_kwargs):
        from .parsing import ParseList, Parse
        if self._unboundedparses and self._mtr and not meter and (not meter_kwargs or Meter(**meter_kwargs).attrs == self._mtr.attrs):
            return self._unboundedparses
        meter = self.get_meter(meter=meter,**meter_kwargs)
        parses = ParseList([
            Parse(wfl, pos, meter=meter, parent=self)
            for wfl in self.wordform_matrix
            for pos in meter.get_pos_types(nsylls=wfl.num_sylls)
        ])
        i=0
        while True and len(parses):
            i+=1
            # logger.debug(f'Now at {i}A, there are {len(parses)} parses')
            parses = ParseList([
                newparse
                for parse in parses
                for newparse in parse.branch()
                if not parse.is_bounded and newparse is not None and parse is not None
            ])
            parses.bound(meter=meter, progress=False)
            if all(p.is_complete for p in parses): break
            if i>1000: 
                logger.error('!')
                break
        parses.bound(meter=meter, progress=False)
        parses.rank()
        self._parses = parses
        self._unboundedparses = parses.unbounded
        self._boundedparses = parses.bounded
        return self._unboundedparses



    # @profile
    def iter_parses(self, progress=True, meter=None, **meter_kwargs):
        logger.debug([progress,meter,meter_kwargs])
        meter = self.get_meter(meter=meter,**meter_kwargs)
        self.clear_cached_properties()

        from .parsing import Parse
        wfm = self.get_wordform_matrix(resolve_optionality=meter.resolve_optionality)
        all_parses = []
        combos = [
            (wfl,scansion)
            for wfl in wfm
            for scansion in get_possible_scansions(wfl.num_sylls, max_s=meter.max_s, max_w=meter.max_w)
        ]
        wfl=wfm[0]
        logger.debug(f'Generated {len(combos)} from a wordfrom matrix of size {len(self.wordform_matrix), wfl, wfl.num_sylls, meter.max_s, meter.max_s, len(get_possible_scansions(wfl.num_sylls))}')
        iterr=tqdm(combos, disable=not progress,position=0)
        for wfl,scansion in iterr:
            parse = Parse(wfl, scansion, meter=meter, parent=self)
            all_parses.append(parse)
        logger.debug(f'Returning {len(all_parses)} parses')
        return all_parses
    
    
    
    # @profile
    def bound_parses(self, parses = None, progress=True, meter=None, **meter_kwargs):
        from .parsing import ParseList
        if hasattr(self,'_bound_init') and not self._bound_init: return
        meter = self.get_meter(meter=meter,**meter_kwargs)
        if parses is None: parses = self.all_parses
        if type(parses) is list: parses=ParseList(parses)
        return parses.bound(meter=meter, progress=progress)
        
        # logger.debug(f'Bounding {len(parses)} with meter {meter}')
        # iterr = tqdm(parses, desc='Bounding parses', disable=not progress)
        # for parse_i,parse in enumerate(iterr):
        #     if parse.is_bounded: continue
        #     for comp_parse in parses[parse_i+1:]:
        #         if comp_parse.is_bounded:
        #             continue
        #         relation = parse.bounding_relation(comp_parse)
        #         if relation == Bounding.bounded:
        #             parse.is_bounded = True
        #             parse.bounded_by = comp_parse
        #         elif relation == Bounding.bounds:
        #             comp_parse.is_bounded = True
        #             comp_parse.bounded_by = parse
        # self._bound_init = True
        # return parses



    @cached_property
    def all_parses(self, **kwargs):
        if not self._parses: self.parse(**kwargs)
        return self._parses
    @cached_property
    def best_parses(self):
        from .parsing import ParseList
        l = [self.best_parse] if self.best_parse else [] 
        return ParseList(l)
    @cached_property
    def num_parses(self, **kwargs): 
        return len(self.unbounded_parses)
    @cached_property
    def best_parse(self): 
        return self.unbounded_parses[0] if self.unbounded_parses else None
    @cached_property
    def unbounded_parses(self): 
        if not self._unboundedparses: self.parse()
        return self._unboundedparses

    @cached_property
    def bounded_parses(self, **kwargs): 
        if not self._boundedparses: self.parse()
        return self._boundedparses

    @cached_property
    def parses(self): 
        return self.unbounded_parses
    
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
        odx={
            **(self.parent.prefix_attrs if self.parent else {}), 
            **self.prefix_attrs
        }
        odx['bestparse_txt'] = self.best_parse.txt
        nsyll = self.best_parse.num_sylls
        cnames = [f.__name__ for f in self.meter.constraints]
        odx['bestparse_nsylls']=nsyll
        odx['n_combo']=len(self.wordform_matrix)
        odx['n_parse']=len(self.best_parses)
        odx['n_viols']=np.median([
            parse.score
            for parse in self.unbounded_parses
        ])
        for cname in cnames:
            odx['*'+cname] = np.median([
                parse.constraint_scores.get(cname,0)
                for parse in self.unbounded_parses
            ])
        return odx
    
    @cached_property
    def parse_stats_norm(self):
        odx = {**self.parse_stats}
        cnames = [f.__name__ for f in self.meter.constraints]
        odx[f'n_viols']=np.mean([
            int(bool(x))
            for bp in self.unbounded_parses
            for cnamex in bp.constraint_viols
            for x in bp.constraint_viols[cnamex]
        ]) * 10
        for cname in cnames:
            odx[f'n_{cname}']=np.mean([
                int(bool(x))
                for bp in self.unbounded_parses
                for x in bp.constraint_viols.get(cname,[])
            ]) * 10
        return odx

    
    @cached_property
    def html(self):
        wordtokend = {wt:[] for wt in self.wordtokens}
        for slot in self.best_parse.slots:
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
                    slotstr=f'<span class="{spclass} {stclass}">{slot.unit.txt}</span>'
                    if pos.violset:
                        viol_str=' '.join(pos.violset)
                        viol_title = 'Violated %s constraints: %s' % (len(pos.violset), viol_str)
                        slotstr=f'<span class="violation" title="{viol_title}" id="viol__line_{self.num}">{slotstr}</span>'
                    output.append(slotstr)
            else:
                output.append(wordtoken.txt)
        return ''.join(output)    