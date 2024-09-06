from ..imports import *
from ..ents import EntityList, Entity

class SentenceList(EntityList):
    def __init__(self, sents, **kwargs):
        super().__init__(
            children=sents,
            txt = '\n'.join(sent._txt for sent in sents),
            **kwargs
        )

    @classmethod
    def from_wordtokens(self, wordtokens):
        last = None
        sent=[]
        sents = []
        for wtok in wordtokens:
            if sent and wtok.sent_num!=last:
                sents.append(Sentence(sent))
                sent = []
            sent.append(wtok)
            last = wtok.sent_num
        if sent: sents.append(Sentence(sent))
        sl = SentenceList(sents)
        sl.wordtokens = wordtokens
        return sl
    

    @cached_property
    def trees(self):
        with logmap('parsing syntax in sentences') as lm:
            return [sent.tree for sent in lm.iter_progress(self.children)]

    @cached_property
    def trees_df(self):
        l=[tree.df for tree in self.trees]
        return pd.concat(l) if l else pd.DataFrame()



class Sentence(EntityList):
    def __init__(self, wordtokens, **kwargs):
        from ..words import WordTokenList
        if not isinstance(wordtokens, WordTokenList):
            wordtokens = WordTokenList(wordtokens)
        
        txt=''.join(wtok._txt for wtok in wordtokens)
        
        self.wordtokens = wordtokens
        
        for wtok in self.wordtokens:
            wtok.sent = self
        
        super().__init__(
            children=wordtokens.data,
            txt = txt,
            **kwargs
        )
        
        
    @cached_property
    def nlp(self):
        from .syntax import get_nlp_doc

        ll=[[wtok._txt.strip() for wtok in self.children]]
        doc = get_nlp_doc(ll)
        sents = doc.sentences
        assert len(sents) == 1, 'Should be 1 sentence only'
        return sents[0]

    @cached_property
    def tree(self):
        from .trees import SentenceTree
        return SentenceTree.from_sent(self)

    @cached_property
    def grid(self):
        from .grids import SentenceGrid
        return SentenceGrid.from_wordtokens(self.wordtokens)
    
    # def plot_grid(self, prom_type="total_stress", **kwargs):
    #     import plotnine as p9

    #     p9.options.figure_size = (11, 5)
    #     figdf = self.tree_df.copy()
    #     figdf[prom_type]=figdf[prom_type]+abs(figdf[prom_type].min())+1
    #     figdf[prom_type]=figdf[prom_type].fillna(0)
    #     return (
    #         p9.ggplot(
    #             figdf,
    #             p9.aes(
    #                 x="preterm_num",
    #                 y=prom_type,
    #                 label="preterm_str",
    #             ),
    #         )
    #         + p9.geom_col(alpha=0.25)
    #         + p9.geom_text(size=15)
    #         + p9.theme_void()
    #     )
