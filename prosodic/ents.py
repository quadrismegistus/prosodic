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
        for child in children: child.parent = self
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
        if not multiple_wordforms and self.child_type=='WordForm' and good_children:
            good_children=good_children[:1]
        if good_children:
            return [
                {**self.prefix_attrs, **child.prefix_attrs, **grandchild_d}
                for child in good_children
                for grandchild_d in child.ld
            ]
        else:
            return [{**self.prefix_attrs}]
        
    

    @cached_property
    def df(self):
        odf=pd.DataFrame(self.ld)
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
    
    
    # def __getattr__(self, __name: str, **kwargs) -> Any:
    #     if __name.startswith('_'): raise AttributeError
    #     logger.trace(f'{self.__class__.__name__}.{__name}')
    #     if __name in self._attrs: 
    #         return self._attrs[__name]
    #     if self.parent: 
    #         return getattr(self.parent, __name)
    #     return None

    def get_children(self, child_type=None):
        logger.trace(self.__class__.__name__)
        if child_type is None or child_type == self.child_type:
            o = self.children
        elif self.children:
            child = self.children[0]
            list_type = child.list_type
            o = list_type([x for child in self.children for x in child.get_children(child_type)])
        else:
            o = []
        return o
    
    def get_parent(self, parent_type=None):
        logger.trace(self.__class__.__name__)
        if not hasattr(self,'parent') or not self.parent: return
        if self.parent.__class__.__name__ == parent_type: return self.parent
        return self.parent.get_parent(parent_type)

    @cached_property
    def stanzas(self): 
        return self.get_children('Stanza')
    @cached_property
    def lines(self): 
        return self.get_children('Line')
    @cached_property
    def words(self): 
        return self.get_children('WordType')
    @cached_property
    def wordforms(self):
        return [
            w.get_children('WordForm') 
            for w in self.words
        ]
    @cached_property
    def syllables(self):
        return [s for w in self.words for s in (w.children[0].get_children('Syllable') if w.children else [])]
    @cached_property
    def phonemes(self):
        return [s for w in self.words for s in (w.children[0].get_children('Phoneme') if w.children else [])]

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
    def word(self): 
        return self.get_parent('Word')
    @cached_property
    def wordform(self): 
        return self.get_parent('WordForm')
    
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
    def is_text(self):
        return self.__class__.__name__ == 'Text'
    





class EntityList(Entity):
    def __init__(self, children=[], parent=None, **kwargs):
        self.parent = parent
        self.children = list(children)
        self._attrs = kwargs
        self._txt=None
        for k,v in self._attrs.items(): setattr(self,k,v)

    @cached_property
    def txt(self): return None