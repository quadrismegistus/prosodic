from .imports import *



class Stanza(TextPart):
    sep: str = ''
    child_type: str = 'Line'

    def __init__(self, txt:str='', children=[], parent=None, tokens_df=None, lang=DEFAULT_LANG, **kwargs):
        if not txt and not children and tokens_df is None:
            raise Exception('Must provide either txt, children, or tokens_df')
        self._txt=txt
        if not children:
            if tokens_df is None: tokens_df = pd.DataFrame(tokenize_sentwords_iter(txt))
            children = [
                Line(parent=self, tokens_df=line_df)                
                for line_i,line_df in tokens_df.groupby('line_i')
            ]
        super().__init__(children=children, parent=parent, **kwargs)
    

class Line(TextPart):
    line_sep = '\n'
    sep: str = ''
    child_type: str = 'Word'
    is_parseable = True

    def __init__(self, txt:str='', children=[], parent=None, tokens_df=None, lang=DEFAULT_LANG, **kwargs):
        from .words import WordToken
        if not txt and not children and tokens_df is None:
            raise Exception('Must provide either txt, children, or tokens_df')
        self._txt=txt
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
        
        super().__init__(children=children, parent=parent, **kwargs)



    def init(self):
        if self._init or self.children: return self
        if self.txt:
            line = Text(self.txt.replace('\n','  '), **self._attrs).lines[0]
            self._txt = line._txt
            self._attrs = line._attrs
            self.children = line.children

        
        self._init=True
        return self
