from entity import entity,being
from tools import makeminlength,wordtoks2str


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
            #wtok.feats['phrasal_stress']=wtok.phrasal_stress

        for i2,w2 in enumerate(self.children):
            w1=self.children[i2-1] if i2 else None
            w3=self.children[i2+1] if (i2+1)<len(self.children) else None
            #print w1.phrasal_stress if w1 else None, w2.phrasal_stress if w2 else None, w3.phrasal_stress if w3 else None
            if w2.phrasal_stress is None: continue

            if w1 and w1.phrasal_stress!=None and w1.phrasal_stress > w2.phrasal_stress:
                w1.feats['phrasal_stress_valley']=True
                w2.feats['phrasal_stress_peak']=True
            if w3 and w3.phrasal_stress!=None and w3.phrasal_stress > w2.phrasal_stress:
                w3.feats['phrasal_stress_valley']=True
                w2.feats['phrasal_stress_peak']=True

        find_phrasal_heads(self.tree)

    def __getitem__(self,key):
        return self.children[key]

    def __repr__(self):
		return "<"+self.classname()+":"+' '.join([self.u2s(wtok.token) for wtok in self.children])+">"

    @property
    def token(self):
        return wordtoks2str(self.children)

    def lines(self):
        ## Resolve sentence back into lines in original text
        lines=[]
        lastLine=None
        line=[]
        for wtok in self.children:
            if wtok.line!=lastLine:
                lastLine=wtok.line
                #lines+=[wtok.line]  # ends up repeating lines
                if line:
                    lines+=[line]
                    line=[]
            line+=[wtok]
        if line: lines+=[line]
        return lines

    def grid(self,nspace=10):



        GRID_LINES=[]

        for LINE in self.lines():
            # word line
            line_words=[]
            for i,wtok in enumerate(LINE):
                if wtok.is_punct: continue
                line_words+=[makeminlength(wtok.token,nspace)]
            line_words = ' '.join(line_words)

            # grid lines
            import math,numpy as np
            grid_lines=[]
            max_grid = max([wtok.phrasal_stress for wtok in self.children if wtok.phrasal_stress!=None])
            min_grid = min([wtok.phrasal_stress for wtok in self.children if wtok.phrasal_stress!=None])
            #for line_num in range(int(math.ceil(min_grid))+1,int(math.ceil(max_grid))+1):
            for line_num in range(1,int(math.ceil(max_grid))+1):
                grid_line=[]
                for i,wtok in enumerate(LINE):
                    if wtok.is_punct: continue
                    mark = 'X' if wtok.phrasal_stress!=None and wtok.phrasal_stress<=line_num else ''
                    grid_line+=[makeminlength(mark,nspace)]
                grid_lines+=[' '.join(grid_line)]

            # lines data
            data_lines=[]
            for datak in ['mean','mean_line','phrasal_stress_peak','phrasal_head']:
                data_line=[]
                for i,wtok in enumerate(LINE):
                    if wtok.is_punct: continue

                    v=wtok.feats.get(datak,'')

                    if v==None:
                        v=''
                    elif type(v) in [float,np.float64]:
                        if np.isnan(v):
                            v=''
                        else:
                            v=round(v,1)
                    elif v in [True,False]:
                        v='+' if v else '-'

                    if datak == 'phrasal_stress_peak':
                        v2=wtok.feats.get('phrasal_stress_valley')
                        if v2 and v:
                            v=v+'/-'
                        elif v2 and not v:
                            v='-'

                    mark = str(v)

                    data_line+=[makeminlength(mark,nspace)]
                datak_name = datak
                if datak=='mean': datak_name='stress [sent]'
                if datak=='mean_line': datak_name='stress [line]'
                if datak=='norm_mean': datak_name='stress [sent norm]'
                if datak=='norm_mean_line': datak_name='stress [line norm]'
                if datak=='phrasal_stress_peak': datak_name='peak/valley'
                if datak=='phrasal_head': datak_name='head/foot'
                data_line+=[makeminlength('('+datak_name+')',nspace)]
                data_lines+=[' '.join(data_line)]

            #grid_lines.insert(0,line_words)

            grid_lines.append(line_words)
            grid_lines.append('')
            grid_lines.extend(data_lines)

            maxlength = max([len(l) for l in grid_lines])

            hdrftr='#' * maxlength
            hdr='STRESS GRID: '+wordtoks2str(LINE)
            #grid_lines.insert(0,self.token)
            #grid_lines.insert(0,hdr)
            #grid_lines.insert(0,hdrftr)
            #grid_lines.append(hdrftr)

            GRID_LINES+=['\n'.join(grid_lines)]

        return '\n\n\n'.join(GRID_LINES)




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
                    if hasattr(subtree[sti],'wordtoken'):
                        subtree[sti].wordtoken.feats['phrasal_head']=False
            find_phrasal_heads(subtree)
