from .imports import *

class StanzaList(EntityList): pass
class LineList(EntityList): pass

class Text(Entity):
    sep: str = ''
    child_type: str = 'Stanza'
    prefix='text'
    parse_unit_attr='lines'
    list_type = StanzaList

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
    def set_meter(self, **meter_kwargs):
        from .meter import Meter        
        self._mtr = meter = Meter(**meter_kwargs)
        logger.debug(f'Set meter to: {meter}')
        return meter

    @property
    def meter(self):
        if self._mtr is None: self.set_meter()
        return self._mtr
    
    @cached_property
    def parseable_units(self): 
        return getattr(self,self.parse_unit_attr)

    # @cache
    def parse(self, **meter_kwargs):
        self._parses=[]
        list(self.parse_iter(**meter_kwargs))
        return self.best_parses

    def parse_iter(self, progress=True, **meter_kwargs):
        meter = self.set_meter(**meter_kwargs)
        self._parses = []
        iterr = tqdm(
            self.parseable_units, 
            desc=f'Parsing {self.parse_unit_attr}',
            disable=not progress
        )
        for pline in iterr:
            pline.parse(progress=False, meter=meter)
            yield pline
            self._parses.append(pline._parses)

    @property
    def best_parses(self):
        from .parsing import ParseList
        return ParseList([l.best_parse for l in self.parseable_units])
    
    @property
    def parse_stats(self):
        if not self._parses: self.parse()
        odf=pd.DataFrame([
            l.parse_stats
            for l in self.parseable_units
        ])
        return setindex(odf, DF_INDEX)




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
    
