from ..imports import *
from ..ents import EntityList
from ..words import WordTokenList

class SentenceList(EntityList):
    # def __init__(self, sents, **kwargs):
    #     super().__init__(
    #         children=sents,
    #         txt = '\n'.join(sent._txt for sent in sents),
    #         **kwargs
    #     )

    @classmethod
    def from_wordtokens(cls, wordtokens, text=None):
        return WordTokenList._from_wordtokens(wordtokens, 'sent', 'sent_num', text=text)

    # @classmethod
    # def from_wordtokens(cls, wordtokens, parent=None):
    #     last = None
    #     sent=[]
    #     sents = []
    #     for wtok in wordtokens:
    #         if sent and wtok.sent_num!=last:
    #             sents.append(Sentence(sent, parent=parent))
    #             sent = []
    #         sent.append(wtok)
    #         last = wtok.sent_num
    #     if sent: sents.append(Sentence(sent, parent=parent))
    #     sl = SentenceList(sents)
    #     sl.wordtokens = wordtokens
    #     return sl
    
    @property
    def parts(self):
        return SentPartList([part for sent in self for part in sent.parts], parent=self)
    

    @property
    def trees(self):
        with logmap('parsing syntax in sentences') as lm:
            return [sent.tree for sent in lm.iter_progress(self.children)]

    @property
    def trees_df(self):
        l=[tree.df for tree in self.trees]
        return pd.concat(l) if l else pd.DataFrame()



class SentPart(WordTokenList):
    prefix = 'sentpart'
    pass

class SentPartList(EntityList):
    @classmethod
    def from_wordtokens(cls, wordtokens, text=None):
        return cls(
            [
                SentPart(children=list(group), text=text)
                for _, group in itertools.groupby(wordtokens, key=lambda x: x.sentpart_num)
            ],
            parent=wordtokens,
            text=text
        )


class Sentence(WordTokenList):
    prefix = 'sent'

    @property
    def nlp(self):
        from .syntax import get_nlp_doc

        ll=[[wtok._txt.strip() for wtok in self.children]]
        doc = get_nlp_doc(ll)
        sents = doc.sentences
        assert len(sents) == 1, 'Should be 1 sentence only'
        return sents[0]

    @property
    def tree(self):
        from .trees import SentenceTree
        return SentenceTree.from_sent(self)

    @property
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
