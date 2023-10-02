from typing import Any
from .imports import *

class entity:
    child_type = 'Text'

    """
    Root entity class
    """
    def __init__(self, children = [], parent = None, **kwargs):
        logger.trace(self.__class__.__name__)
        self.parent = parent
        self.children = children
        self._attrs = kwargs
        for k,v in self._attrs.items(): setattr(self,k,v)
        self._init = False

    @property
    def attrs(self):
        return self._attrs

    def __repr__(self):
        attrstr=get_attr_str(self.attrs)
        return f'{self.__class__.__name__}({attrstr})'


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
    def next(self):
        i=self.parent.children.index(self)
        try:
            return self.parent.children[i+1]
        except IndexError:
            return None
    
    @cached_property
    def prev(self):
        i=self.parent.children.index(self)
        if i-1<0: return None
        try:
            return self.parent.children[i-1]
        except IndexError:
            return None