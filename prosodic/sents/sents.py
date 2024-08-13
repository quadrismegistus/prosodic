from ..imports import *
from ..ents import EntityList, Entity
from .trees import *
from .syntax import *

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
        super().__init__(txt=txt, children=wordtokens, parent=None, **kwargs)
        
    @cached_property
    def nlp(self):
        ll=[[wtok._txt.strip() for wtok in self.children]]
        doc = get_nlp_doc(ll)
        sents = doc.sentences
        assert len(sents) == 1, 'Should be 1 sentence only'
        return sents[0]
    
    @cached_property
    def deptree_str(self):
        return get_treeparse_str(self.nlp)        
    @cached_property
    def deptree(self):
        deptree=DependencyTree.fromstring(self.deptree_str)
        preterms=list(deptree.preterminals())
        assert len(preterms)==len(self.children), 'Should equal number of wordtokens'
        for preterm,token in zip(preterms, self.children):
            preterm._wordtoken = token
        return deptree
    @cached_property
    def tree(self):
        return ProsodicMetricalTree.from_deptree(self.deptree)