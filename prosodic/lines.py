from .imports import *
from .texts import Text

class WordTokenList(EntityList): pass

class Line(Text):
    line_sep = '\n'
    sep: str = ''
    child_type: str = 'WordToken'
    is_parseable = True
    prefix='line'
    list_type=WordTokenList
    is_parseable = False
    use_cache = False

    @profile
    def __init__(self, txt:str='', children=[], parent=None, tokens_df=None, lang=DEFAULT_LANG, **kwargs):
        from .words import WordToken
        if not txt and not children and tokens_df is None:
            raise Exception('Must provide either txt, children, or tokens_df')
        with logmap(f'init line: {txt}',level='trace') as lm:
            needs_caching=False
            txt=txt.strip()
        
            if not children:
                if self.use_cache: 
                    children = self.from_cache(txt)
                    lm.log(f'got from cache: {children}')
                if not children:
                    needs_caching = True
                    if tokens_df is None: 
                        tokens_df = pd.DataFrame(tokenize_sentwords_iter(txt))
                    children=[
                        WordToken(
                            txt=word_d.get('word_str',''),
                            lang=lang,
                            parent=self,
                            # is_punc=word_d.get('word_ispunc'),
                            sent_num=word_d.get('sent_i'),
                            sentpart_num=word_d.get('sent_i'),
                        )
                        for word_d in tokens_df.to_dict('records')
                        if 'word_str' in word_d and 'word_ispunc'
                    ]
            Entity.__init__(self, txt=txt, children=children, parent=parent, **kwargs)
            self._parses = []
            self.is_parseable = True
            if needs_caching and self.use_cache:
                self.to_cache(txt)
        
        

    def only_wordforms(self, wordforms):
        from .words import WordFormList
        line = Line(txt=self._txt, children=copy(self.children), parent=self.parent)
        wordformset = {wf.to_hash() for wf in wordforms}
        for wtype in self.wordtypes:
            wtype.children = WordFormList(wf for wf in wtype.children if wf.to_hash() in wordformset)
        return line    

    def to_json(self):
        return Entity.to_json(self,yes_txt=True)
    
    # # @staticmethod
    # # def from_json(json_d):
    # #     from .words import WordType,WordTypeList
    # #     return Line(
    # #         txt=json_d['txt'],
    # #         children=WordTypeList(
    # #             WordType.from_json(d)
    # #             for d in json_d['children']
    # #         )
    # #     )
