from typing import Any
from .imports import *

class Entity(UserList):
    child_type = 'Text'
    is_parseable = False
    index_name=None
    prefix='ent'
    list_type = None

    """
    Root Entity class
    """
    def __init__(self, txt:str='', children = [], parent = None, **kwargs):
        self.parent = parent
        newchildren=[]
        for child in children: 
            if not isinstance(child,Entity): 
                logger.warning(f'{child} is not an Entity')
                continue
            newchildren.append(child)
            if not child.is_wordtype:   # don't do this for wordtypes since each wordtype is a single/shared python object
                child.parent = self
        children = newchildren
        if self.list_type is None: self.list_type=EntityList
        self.children = self.list_type(children)
        self._attrs = kwargs
        self._txt=txt
        self._mtr=None
        for k,v in self._attrs.items(): setattr(self,k,v)

    def __hash__(self):
        return hash((self.txt, tuple(sorted(self.attrs.items()))))

    def __eq__(self, other):
        return self is other

    @cached_property
    def attrs(self):
        odx={'num':self.num}
        if self.__class__.__name__ not in {'Text','Stanza','MeterLine','MeterText','Meter'} and self.txt:
            odx['txt']=self.txt
        return {**odx, **self._attrs}
        
    @cached_property
    def prefix_attrs(self):
        def getkey(k):
            o=f'{self.prefix}_{k}'
            o=DF_COLS_RENAME.get(o,o)
            return o
        return {getkey(k):v for k,v in self.attrs.items() if v is not None}
    
    @cached_property
    def txt(self):
        if self._txt: 
            txt = self._txt
        elif self.children: 
            txt=''.join(child.txt for child in self.children)
        else: 
            txt=''
        return clean_text(txt)

    @cached_property
    def data(self): return self.children
    @cached_property
    def l(self): return self.children

    def show(self, indent=0):
        attrstr=get_attr_str(self.attrs)
        myself=f'{self.__class__.__name__}({attrstr})'
        if indent: myself=textwrap.indent(myself, '|' + (' ' * (indent-1)))
        lines = [myself]
        for child in self.children:
            if isinstance(child,Entity) and not child.__class__.__name__.startswith('Phoneme'):
                lines.append(child.show(indent=indent+4))
        dblbreakfor=self.__class__.__name__ in {'Text','Stanza','Line'}
        breakstr='\n|\n' if dblbreakfor else '\n'
        o=breakstr.join(lines)
        if not indent: 
            print(o)
        else:
            return o
    
    def _repr_html_(self): 
        def blank(x):
            if x in {0,None,np.nan}: return ''
            return x
        return self.df.applymap(blank)._repr_html_()
    def __repr__(self): return f'{self.__class__.__name__}({get_attr_str(self.attrs)})'
    
    @cached_property
    def ld(self): return self.get_ld()

    def get_ld(self, incl_phons=False, incl_sylls=True, multiple_wordforms=True):
        if not incl_sylls and self.child_type=='Syllable': return [{**self.prefix_attrs}]
        if not incl_phons and self.child_type=='Phoneme': return [{**self.prefix_attrs}]
        good_children = [c for c in self.children if isinstance(c,Entity)]
        # logger.debug(f'good children of {type(self)} -> {good_children}')
        if not multiple_wordforms and self.child_type=='WordForm' and good_children:
            good_children=good_children[:1]
            # logger.debug(f'good children now {good_children}')
        if good_children:
            return [
                {**self.prefix_attrs, **child.prefix_attrs, **grandchild_d}
                for child in good_children
                for grandchild_d in child.get_ld(incl_phons=incl_phons, incl_sylls=incl_sylls, multiple_wordforms=multiple_wordforms)
            ]
        else:
            return [{**self.prefix_attrs}]
        
    
    def get_df(self, **kwargs):
        odf=pd.DataFrame(self.get_ld(**kwargs))
        for c in DF_BADCOLS:
            if c in set(odf.columns):
                odf=odf.drop(c,axis=1)
        for c in odf:
            if c.endswith('_num'):
                odf[c]=odf[c].fillna(0).apply(int)
            else:
                odf[c]=odf[c].fillna('')
        odf=setindex(
            odf,
            DF_INDEX
        )
        def unbool(x):
            if x is True: return 1
            if x is False: return 0
            if x is None: return 0
            return x
        odf=odf.applymap(unbool)
        return odf
    
    @cached_property
    def df(self): return self.get_df()
    
    # def __getattr__(self, __name: str, **kwargs) -> Any:
    #     if __name.startswith('_'): raise AttributeError
    #     logger.trace(f'{self.__class__.__name__}.{__name}')
    #     if __name in self._attrs: 
    #         return self._attrs[__name]
    #     if self.parent: 
    #         return getattr(self.parent, __name)
    #     return None

    def get_parent(self, parent_type=None):
        logger.trace(self.__class__.__name__)
        if not hasattr(self,'parent') or not self.parent: return
        if self.parent.__class__.__name__ == parent_type: return self.parent
        return self.parent.get_parent(parent_type)

    @cached_property
    def stanzas(self): 
        from .texts import StanzaList
        if self.is_text: o=self.children
        elif self.is_stanza: o=[self]
        else: o=[]
        return StanzaList(o)
    
    @cached_property
    def lines(self): 
        from .texts import LineList
        if self.is_stanza: o=self.children
        elif self.is_line: o=[self]
        else: o=[line for stanza in self.stanzas for line in stanza.children]
        return LineList(o)
    
    @cached_property
    def wordtokens(self): 
        from .lines import WordTokenList
        if self.is_line: o=self.children
        elif self.is_wordtoken: o=[self]
        else:o=[wt for line in self.lines for wt in line.children]
        return WordTokenList(o)
    
    @cached_property
    def wordtypes(self): 
        from .words import WordTypeList
        if self.is_wordtoken: o=self.children
        elif self.is_wordtype: o=[self]
        else: o=[wtype for token in self.wordtokens for wtype in token.children]
        return WordTypeList(o)
    
    @cached_property
    def wordforms(self):
        from .words import WordFormList
        if self.is_wordtype: o = self.children[:1]
        elif self.is_wordtype: o=[self]
        else: o = [wtype.children[0] for wtype in self.wordtypes if wtype.children]
        return WordFormList(o)

    @cached_property
    def wordforms_all(self):
        if self.is_wordtype: o=self.children
        if self.is_wordform: o=[self]
        else: o = [wtype.children for wtype in self.wordtypes]
        return o
    
    @cached_property
    def syllables(self):
        from .words import SyllableList
        if self.is_wordform: o=self.children
        if self.is_syll: o=[self]
        else: o = [syll for wf in self.wordforms for syll in wf.children]
        return SyllableList(o)
    
    @cached_property
    def phonemes(self):
        from .syllables import PhonemeList
        if self.is_syll: o=self.children
        if self.is_phon: o=[self]
        else: o = [phon for syll in self.syllables for phon in syll.children]
        return PhonemeList(o)

    @cached_property
    def text(self): 
        return self.get_parent('Text')
    @cached_property
    def stanza(self): 
        return self.get_parent('Stanza')
    @cached_property
    def line(self): 
        return self.get_parent('Line')
    @cached_property
    def wordtoken(self): 
        return self.get_parent('WordToken')
    @cached_property
    def wordtype(self): 
        return self.get_parent('WordType')
    @cached_property
    def wordform(self): 
        return self.get_parent('WordForm')
    @cached_property
    def syllable(self): 
        return self.get_parent('Syllable')
    
    @cached_property
    def i(self):
        if self.parent is None: return None
        if not self.parent.children: return None
        try:
            return self.parent.children.index(self)
        except IndexError:
            return None
    @cached_property
    def num(self):
        return self.i+1 if self.i is not None else None

    @cached_property
    def next(self):
        if self.i is None: return None
        try:
            return self.parent.children[self.i+1]
        except IndexError:
            return None
    
    @cached_property
    def prev(self):
        if self.i is None: return None
        i=self.i
        if i-1<0: return None
        try:
            return self.parent.children[i-1]
        except IndexError:
            return None
        
    @cached_property
    def is_text(self): return self.__class__.__name__ == 'Text'
    @cached_property
    def is_stanza(self): return self.__class__.__name__ == 'Stanza'
    @cached_property
    def is_line(self): return self.__class__.__name__ == 'Line'
    @cached_property
    def is_wordtoken(self): return self.__class__.__name__ == 'WordToken'
    @cached_property
    def is_wordtype(self): return self.__class__.__name__ == 'WordType'
    @cached_property
    def is_wordform(self): return self.__class__.__name__ == 'WordForm'
    @cached_property
    def is_syll(self): return self.__class__.__name__ == 'Syllable'
    @cached_property
    def is_phon(self): return self.__class__.__name__ == 'PhonemeClass'





class EntityList(Entity):
    def __init__(self, children=[], parent=None, **kwargs):
        self.parent = parent
        self.children = list(children)
        self._attrs = kwargs
        self._txt=None
        for k,v in self._attrs.items(): setattr(self,k,v)

    @cached_property
    def txt(self): return None