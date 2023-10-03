from .imports import *

class TextPart(entity):
    @cached_property
    def txt(self):
        logger.trace(self.__class__.__name__)
        if hasattr(self,'_txt') and self._txt: txt = self._txt
        elif self.children: txt=self.sep.join(child.txt for child in self.children)
        else: txt=''
        return clean_text(txt)
    
class Text(TextPart):
    sep: str = ''
    child_type: str = 'Stanza'

    def __init__(self,
            txt: str = '',
            filename: str = '',
            lang: Optional[str] = DEFAULT_LANG,
            parent: Optional[entity] = None,
            children: Optional[list] = [],
            tokens_df: Optional[pd.DataFrame] = None,
            init: bool = True,
            **kwargs
            ):
        from .lines import Stanza
        if not txt and not filename and tokens_df is None:
            raise Exception('must provide either txt string or filename or token dataframe')
        self._txt = txt = get_txt(txt,filename).strip()
        self._fn = filename
        self.lang=lang if lang else detect_lang(txt)
        
        if not children:
            if tokens_df is None: tokens_df = pd.DataFrame(tokenize_sentwords_iter(txt))
            children = [
                Stanza(parent=self, tokens_df=stanza_df)                
                for i,stanza_df in tokens_df.groupby('stanza_i')
            ]

        super().__init__(children=children, parent=parent, **kwargs)
