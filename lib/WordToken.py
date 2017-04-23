from entity import entity,being


class WordToken(entity):
    def __init__(self,words,token,is_punct=False,sentence=None,line=None):
        self.children=words
        self.token=token
        self.is_punct=is_punct
        self.sentence=None
        self.feats={}
        self.line=line

    def __getitem__(self,key):
        return self.children[key]

    def __repr__(self):
		return "<"+self.classname()+":"+self.u2s(self.token)+">"

    @property
    def phrasal_stress(self):
        import numpy as np
        #ps=self.feats.get('norm_mean',None)
        ps=self.feats.get('mean',None)
        #if ps: return None
        if ps==None: return None
        if np.isnan(ps): return None
        return ps

    @property
    def phrasal_stress_line(self):
        import numpy as np
        #ps=self.feats.get('norm_mean_line',None)
        ps=self.feats.get('mean_line',None)
        #if ps: return None
        if ps==None: return None
        if np.isnan(ps): return None
        return ps

    @property
    def phrasal_stress_norm(self):
        import numpy as np
        ps=self.feats.get('norm_mean',None)
        #if not ps: return None
        if ps==None: return None
        if np.isnan(ps): return None
        return ps

    @property
    def phrasal_stress_norm_line(self):
        import numpy as np
        ps=self.feats.get('norm_mean_line',None)
        #if not ps: return None
        if ps==None: return None
        if np.isnan(ps): return None
        return ps
