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

    @profile
    def __init__(self, txt:str='', children=[], parent=None, tokens_df=None, lang=DEFAULT_LANG, **kwargs):
        from .words import WordToken
        if not txt and not children and tokens_df is None:
            raise Exception('Must provide either txt, children, or tokens_df')
        if not children:
            if tokens_df is None: tokens_df = pd.DataFrame(tokenize_sentwords_iter(txt))
            children=[
                WordToken(
                    token=word_d.get('word_str',''),
                    lang=lang,
                    parent=self,
                    # is_punc=word_d.get('word_ispunc'),
                    sent_num=word_d.get('sent_i'),
                    sentpart_num=word_d.get('sent_i'),
                )
                for word_d in tokens_df.to_dict('records')
                if 'word_str' in word_d and 'word_ispunc'
            ]
        
        super().__init__(txt=txt, children=children, parent=parent, **kwargs)
        self.is_parseable = True
        if self.txt and self.txt.startswith('\n'): self.txt = self.txt[1:]