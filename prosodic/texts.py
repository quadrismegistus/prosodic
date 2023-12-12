from .imports import *

class StanzaList(EntityList): pass
class LineList(EntityList): pass

class Text(Entity):
    sep: str = ''
    child_type: str = 'Stanza'
    prefix='text'
    parse_unit_attr='lines'
    list_type = StanzaList

    cached_properties_to_clear = [
        'best_parses',
        'all_parses',
        'unbounded_parses',
        'parse_stats',
        'meter',
    ]

    @profile
    def __init__(self,
            txt: str = '',
            filename: str = '',
            lang: Optional[str] = DEFAULT_LANG,
            parent: Optional[Entity] = None,
            children: Optional[list] = [],
            tokens_df: Optional[pd.DataFrame] = None,
            init: bool = True,
            **kwargs
            ):
        from .lines import Stanza
        if not txt and not filename and not children and tokens_df is None:
            raise Exception('must provide either txt string or filename or token dataframe')
        txt = get_txt(txt,filename)
        self._fn = filename
        self.lang=lang if lang else detect_lang(txt)
        
        if not children:
            if tokens_df is None: tokens_df = pd.DataFrame(tokenize_sentwords_iter(txt))
            children = [
                Stanza(parent=self, tokens_df=stanza_df)                
                for i,stanza_df in tokens_df.groupby('stanza_i')
            ]
        
        super().__init__(
            txt, 
            children=children, 
            parent=parent, 
            **kwargs
        )
        self._parses=[]
        self._mtr=None


    ### parsing ###
    # def set_meter(self, **meter_kwargs):
    #     from .meter import Meter        
    #     self._mtr = meter = Meter(**meter_kwargs)
    #     logger.debug(f'set meter to: {meter}')


    def get_meter(self, meter=None,**meter_kwargs):
        from .meter import Meter
        if meter is not None:
            self._mtr = meter     
        elif self._mtr is None:
            if self.text and self.text._mtr is not None:
                self._mtr = self.text._mtr
                logger.trace(f'meter inherited from text: {self._mtr}')
            else:
                self._mtr = Meter(**meter_kwargs)
                logger.trace(f'setting meter to: {self._mtr}')
        elif not meter_kwargs:
            logger.trace(f'no change in meter')
        else:
            newmeter = Meter(**meter_kwargs)
            if self._mtr.attrs != newmeter.attrs:
                self._mtr = newmeter
                logger.trace(f'resetting meter to: {self._mtr}')
            else:
                logger.trace(f'no change in meter')
        return self._mtr

    def set_meter(self, **meter_kwargs):
        self.get_meter(**meter_kwargs)

    @cached_property
    def meter(self):
        return self.get_meter()
    
    @cached_property
    def parseable_units(self): 
        return getattr(self,self.parse_unit_attr)

    # @cache
    def parse(self, **meter_kwargs):
        if not self._parses or not self._mtr or (meter_kwargs and Meter(**meter_kwargs).attrs != self._mtr.attrs):
            self._parses=[]
            deque(self.parse_iter(**meter_kwargs), maxlen=0)
        return self._parses

    def parse_iter(self, progress=True, **meter_kwargs):
        meter = self.get_meter(**meter_kwargs)
        self._parses = []
        self.clear_cached_properties()
        iterr = tqdm(
            self.parseable_units, 
            desc=f'Parsing {self.parse_unit_attr}',
            disable=not progress,
            position=0
        )
        for pline in iterr:
            pline.parse(progress=False, meter=meter)
            yield pline
            self._parses.append(pline._parses)

    

    def _concat_line_parses(self, attr):
        from .parsing import ParseList
        return ParseList([
            parse
            for line in self.parseable_units
            for parse in getattr(line,attr)
        ])


    def _concat_line_dfs(self, attr):
        if not self._parses: self.parse()
        odf=pd.concat([
            getattr(line,attr).df
            for line in self.parseable_units
        ])
        return setindex(odf, DF_INDEX)
    
    @property
    def parses(self): return self.best_parses
    
    @cached_property
    def best_parses(self):
        from .parsing import ParseList
        return ParseList(line.best_parse for line in self.parseable_units)

    @cached_property
    def unbounded_parses(self):
        return self._concat_line_parses('unbounded_parses')
    
    @cache
    def parse_stats(self, norm=False):
        return pd.DataFrame(
            line.parse_stats(norm=norm)
            for line in self.parseable_units
        )




class Stanza(Text):
    sep: str = ''
    child_type: str = 'Line'
    prefix='stanza'
    list_type = LineList

    @profile
    def __init__(self, txt:str='', children=[], parent=None, tokens_df=None, lang=DEFAULT_LANG, **kwargs):
        from .lines import Line
        if not txt and not children and tokens_df is None:
            raise Exception('Must provide either txt, children, or tokens_df')
        if not children:
            if tokens_df is None: tokens_df = pd.DataFrame(tokenize_sentwords_iter(txt))
            children = [
                Line(parent=self, tokens_df=line_df)                
                for line_i,line_df in tokens_df.groupby('line_i')
            ]
        Entity.__init__(self, txt, children=children, parent=parent, **kwargs)
    
