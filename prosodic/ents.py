from typing import Any
from .imports import *

class entity(UserList):
    child_type = 'Text'
    is_parseable = False
    index_name=None
    prefix='ent'

    """
    Root entity class
    """
    def __init__(self, txt:str='', children = [], parent = None, **kwargs):
        logger.trace(self.__class__.__name__)
        self.parent = parent
        for child in children: child.parent = self
        self.children = children
        self._attrs = kwargs
        self._txt=txt
        for k,v in self._attrs.items(): setattr(self,k,v)

    def __eq__(self, other):
        return self is other

    @cached_property
    def attrs(self):
        odx={'num':self.num}
        if self.__class__.__name__ not in {'Text','Stanza'} and self.txt:
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
            if isinstance(child,entity) and not child.__class__.__name__.startswith('Phoneme'):
                lines.append(child.show(indent=indent+4))
        dblbreakfor=self.__class__.__name__ in {'Text','Stanza','Line'}
        breakstr='\n|\n' if dblbreakfor else '\n'
        o=breakstr.join(lines)
        if not indent: 
            print(o)
        else:
            return o
    
    def _repr_html_(self): return self.df._repr_html_()
    def __repr__(self): return f'{self.__class__.__name__}({get_attr_str(self.attrs)})'
    
    @cached_property
    def ld(self): return self.get_ld()

    def get_ld(self, incl_phons=False, incl_sylls=True, multiple_wordforms=True):
        if not incl_sylls and self.child_type=='Syllable': return [{**self.prefix_attrs}]
        if not incl_phons and self.child_type=='Phoneme': return [{**self.prefix_attrs}]
        good_children = [c for c in self.children if isinstance(c,entity)]
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
        return odf
    
    
    

    def init(self):
        logger.trace(self.__class__.__name__)
        self._init=True

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
            return self.children
        else:
            return [x for child in self.children for x in child.get_children(child_type)]
    
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
        return self.get_children('Word')
    @cached_property
    def wordforms(self):
        if self.child_type=='WordForm': return self.children
        return [w.children for w in self.words]
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
    





class Parseable(entity):
    @cache
    def parse(self, meter=None, **meter_kwargs):
        from .parsing import Meter
        if meter is None: meter=Meter(**meter_kwargs)
        m = self._metertext = meter[self]
        return m.parse()
    @property
    def has_metertext(self): 
        return hasattr(self,'_metertext') and self._metertext is not None
    @property
    def metertext(self):
        if not self.has_metertext: self.parse()
        if self.has_metertext: return self._metertext
    @property
    def best_parses(self): return self.metertext.best_parses
    @property
    def best_parse(self): return self.metertext.best_parse
    @property
    def parses_df(self): return self.metertext.parses_df




# class EntityList(UserList):
#     index_name=None

#     def _repr_html_(self): return self.df._repr_html_()
#     def __repr__(self): return repr(self.df)
    
#     @property
#     def df(self):
#         l=[px.attrs for px in self.data if px is not None]
#         odf=pd.DataFrame(l)
#         if len(odf) and self.index_name and self.index_name in set(odf.columns):
#             odf=odf.set_index(self.index_name)
#         return odf
    
#     @property
#     def l(self): return self.data