from ..imports import *
from ..ents import EntityList, Entity

class SentenceList(EntityList):
    def __init__(self, wordtokens, **kwargs):
        l = []
        last = None
        sent=[]
        for wtok in wordtokens:
            if sent and wtok.sent_num!=last:
                l.append(Sentence(sent))
                sent = []
            sent.append(wtok)
            last = wtok.sent_num
        self.data = l



class Sentence(Entity):
    def __init__(self, wordtokens, **kwargs):
        txt=''.join(wtok._txt for wtok in wordtokens)
        Entity.__init__(self, txt=txt, children=wordtokens, parent=None, **kwargs)