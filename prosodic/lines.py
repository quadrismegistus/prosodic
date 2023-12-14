from .imports import *
from .texts import Text

class WordTokenList(EntityList): pass

class Line(Text):
    line_sep = '\n'
    sep: str = '\n'
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
        txt=txt.strip()
    
        if not children:
            if tokens_df is None: 
                tokens_df = tokenize_sentwords_df(txt)
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
                if 'word_str' in word_d# and 'word_ispunc'
            ]
        Entity.__init__(self, txt=txt, children=children, parent=parent, **kwargs)
        self._parses = []
        self.is_parseable = True

    @cached_property
    def wordform_matrix(self): return self.get_wordform_matrix()
    
    def get_wordform_matrix(self, resolve_optionality=True):
        from .words import WordFormList
        lim = 1 if not resolve_optionality else None
        ll = [l for l in self.wordforms_all if l]
        ll = [WordFormList(l) for l in itertools.product(*ll)]
        ll.sort()
        return ll[:lim]

    def match_wordforms(self, wordforms):
        from .words import WordFormList
        wordforms_ll = [l for l in self.wordforms_all if l]
        assert len(wordforms) == len(wordforms_ll)

        def iterr():
            for correct_wf, target_wfl in zip(wordforms, wordforms_ll):
                targets = [wf for wf in target_wfl if wf.to_hash() == correct_wf.to_hash()]
                if len(targets)!=1:
                    pprint([correct_wf,target_wfl,targets])
                    raise Exception('too many candidates')
                yield targets[0]
        return WordFormList(iterr())


    def to_json(self):
        return Entity.to_json(self,txt=self.txt)
    