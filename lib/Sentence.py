from entity import entity,being


class Sentence(entity):
    def __init__(self,wordtokens,tree):
        self.children=wordtokens
        self.tree=tree

        # link wordtokens to this sentence
        for wtok in self.children:
            wtok.sentence = self

        preterminals = list(tree.preterminals())
        assert len(preterminals) == len(wordtokens)
        for wtok,preterm in zip(wordtokens,preterminals):
            wtok.preterminal=preterm
            preterm.wordtoken = wtok
            wTok.feats['phrasal_stress']=wTok.feats['norm_mean']

        for i2,w2 in enumerate(self.children):
            w1=self.children[i2-1] if i2 else None
            w3=self.children[i2+1] if (i2+1)<len(self.children) else None
            if w2.phrasal_stress is None: continue

            if w1 and w1.phrasal_stress!=None and w1.phrasal_stress < w2.phrasal_stress:
                w1.feats['phrasal_stress_valley']=True
                w2.feats['phrasal_stress_peak']=True
            if w3 and w3.phrasal_stress!=None and w3.phrasal_stress < w2.phrasal_stress:
                w3.feats['phrasal_stress_valley']=True
                w2.feats['phrasal_stress_peak']=True

        find_phrasal_heads(self.tree)

    def __getitem__(self,key):
        return self.children[key]

    def __repr__(self):
		return "<"+self.classname()+":"+' '.join([self.u2s(wtok.token) for wtok in self.children])+">"




def find_phrasal_heads(tree):
    for subtree in tree:
        if not type(subtree) in [str,unicode]:
            #if is_branching(subtree):
            #    subtree[-1].is_head_of_branch = True
            if not subtree._preterm and len(subtree)>1 and subtree[-1]._preterm and not subtree[-1].wordtoken.is_punct:
                subtree[-1].wordtoken.feats['phrasal_head']=True
                for sti in range(len(subtree)-1):
                    """
                    print sti
                    print subtree[sti]
                    print subtree[-1]
                    print
                    """
                    subtree[sti].wordtoken.feats['phrasal_head']=False
            find_phrasal_heads(subtree)
