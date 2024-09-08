from . import *

class WordTokenList(EntityList):
    """A list of WordToken objects."""

    def __init__(self, children: List['WordToken'], parent=None, text=None, num=None, lang=DEFAULT_LANG, **kwargs):
        print([type(x) for x in children])

        assert all([isinstance(wt,WordToken) for wt in children])
        self._parses = []
        self._mtr = None
        if text is None:
            from ..texts import TextModel
            text = TextModel(children = children, lang=lang)
        super().__init__(children=children, text=text, parent=parent, num=num, **kwargs)

    @classmethod
    def _from_wordtokens(cls, wordtokens, list_type, list_num, text=None):
        from ..imports import get_list_class, get_ent_class
        list_class = get_list_class(list_type)
        ent_class = get_ent_class(list_type)
        return list_class(
            [
                ent_class(children=list(group), text=text, num=i+1)
                for i,(_, group) in enumerate(itertools.groupby(wordtokens, key=lambda x: getattr(x,list_num)))
            ],
            parent=wordtokens,
            text=text
        )

    
    # def get_list(self, list_type: str):
    #     """
    #     Override get_list for WordTokenList to handle its own lists.
    #     """
    #     from ..imports import get_list_class_name
    #     list_name = get_list_class_name(list_type)
        
    #     # Check if we have a specific method for this list type
    #     if self.text and hasattr(self.text, list_name):
    #         full_list = getattr(self.text, list_name)
    #         if full_list is None:
    #             return None
            
    #         list_class = get_list_class(list_type)
            
    #         filtered_list = [ent for ent in full_list if self.overlaps(ent)]
    #         return list_class(filtered_list,text=self.text)
        
    #     # If not, fall back to the parent class implementation
    #     return super().get_list(list_type)

    @property
    def words(self):
        return self
    
    def to_dict(self, **kwargs):
        return {self.nice_type_name:{'children':[wtok.to_dict() for wtok in self]}}
    

    # @classmethod
    # def from_dict(cls, data):
    #     from ..imports import GLOBALS
         
    #     assert len(data) == 1, "Should only be classname in key"
    #     cls_name,cls_data = next(iter(data.items()))
    #     cls = GLOBALS.get(cls_name)
    #     assert cls is not None, "Class should exist"
    #     children = [WordToken.from_dict(wt) for wt in cls_data['children']]
    #     return cls(children=children)


    @property
    def nums(self):
        return [wtok.num for wtok in self]
    
    @property
    def numset(self):
        return set(self.nums)

    # @property
    # def sents(self):
    #     from ..sents import SentenceList
    #     return SentenceList(unique_list([wtok.sent for wtok in self if wtok.sent]))

    @property
    def is_sent_parsed(self):
        l=self.children
        if not l: return False
        return all(wt.preterm for wt in l)
    
    @property
    def trees(self):
        return self.sents.trees
    
    
    @property
    def grid(self):
        from ..sents.grids import SentenceGrid
        return SentenceGrid.from_wordtokens(self, text=self.text)
    

    @property
    def wordform_matrix(self) -> List[Any]:
        """
        Get the matrix of word forms for the line.

        Returns:
            List[Any]: A matrix of word forms.
        """
        return self.get_wordform_matrix()

    def get_wordform_matrix(self, resolve_optionality: bool = True) -> List[Any]:
        """
        Generate a matrix of word forms for the line.

        Args:
            resolve_optionality (bool): Whether to resolve optional forms. Default is True.

        Returns:
            List[Any]: A matrix of word forms.
        """

        lim = 1 if not resolve_optionality else None
        ll = [l for l in self.wordforms_all if l]
        ll = [WordFormList(list(l)) for l in itertools.product(*ll)]
        ll.sort()
        return ll[:lim]

    def match_wordforms(self, wordforms: List[Any]) -> Any:
        """
        Match given word forms to the line's word forms.

        Args:
            wordforms (List[Any]): List of word forms to match.

        Returns:
            Any: A WordFormList of matched word forms.
        """

        wordforms_ll = [l for l in self.wordforms_all if l]
        assert len(wordforms) == len(wordforms_ll)

        def iterr():
            for correct_wf, target_wfl in zip(wordforms, wordforms_ll):
                targets = [wf for wf in target_wfl if wf.key == correct_wf.key]
                if targets:
                    yield targets[0]
                else:
                    yield target_wfl[0]

        return WordFormList(iterr())


    