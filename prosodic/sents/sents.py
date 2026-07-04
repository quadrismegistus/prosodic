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
