from typing import Any, List, Type
from .imports import *


class Entity(UserList):
    """
    Root Entity class representing a hierarchical structure in prosodic analysis.

    This class serves as the base for various prosodic entities such as texts, stanzas,
    lines, words, syllables, and phonemes. It provides common functionality for
    managing hierarchical relationships, attributes, and data representation.

    Attributes:
        child_type (str): The type of child entities this entity can contain.
        is_parseable (bool): Whether this entity can be parsed.
        index_name (str): The name used for indexing this entity type.
        prefix (str): A prefix used for attribute naming.
        list_type (type): The type of list used for storing children.
        cached_properties_to_clear (list): Properties to clear from cache.
        use_cache (bool): Whether to use caching for this entity.
        sep (str): Separator used when joining child texts.
    """

    is_parseable = False
    index_name = None
    prefix = "ent"
    cached_properties_to_clear = []
    use_cache = False
    is_text = False
    sep = ""

    # Define parent and child relationships
    _parent_types = {
        "text": "TextModel",
        "stanza": "Stanza",
        "line": "Line",
        "wordtoken": "WordToken",
        "wordtype": "WordType",
        "wordform": "WordForm",
        "syllable": "Syllable",
    }

    _child_types = {
        "TextModel": ["stanzas", "Stanza", "StanzaList"],
        "Stanza": ["lines", "Line", "LineList"],
        "Line": ["wordtokens", "WordToken", "WordTokenList"],
        "WordToken": ["wordtypes", "WordType", "WordTypeList"],
        "WordType": ["wordforms", "WordForm", "WordFormList"],
        "WordForm": ["syllables", "Syllable", "SyllableList"],
        "Syllable": ["phonemes", "PhonemeClass", "PhonemeList"],
    }

    # @log.info
    def copy(self):
        new = self.__class__.__new__(self.__class__)
        new.__dict__.update({k: v for k, v in self.__dict__.items() if not isinstance(getattr(self.__class__, k, None), cached_property)})
        if self.children is not None:
            new.children = self.children.copy() if isinstance(self.children, EntityList) else [ent.copy() for ent in self.children]
        return new
        # return unstuff(stuff(self))
        # data = self.to_dict()
        # if 'children' in data:
        #     if isinstance(data['children'],list):
        #         data['children'] = [x.copy() for x in data['children']]
        #     elif isinstance(data['children'],EntityList):
        #         data['children'] = data['children'].copy()
        # return self.__class__(**data)
    
    def find(self, ent):
        if ent.class_depth < 2:
            attr_name = ent.key.split('.')[-1].lower()
            return getattr(self.text,attr_name)
        else:
            return self.text.descendants.get(ent.key)

    def match(self, ent, ent_type=None):
        res = self.find(ent)
        if res is not None: return res
        if ent_type is None: ent_type = type(ent).__name__.lower()
        ent_list = self.get_list(ent_type)
        for ent2 in ent_list:
            if ent2.equals(ent):
                return ent2

    @property
    def list_type(self):
        from .imports import get_list_class
        return get_list_class(self.__class__.__name__.lower())

    @property
    def type_name(self):
        name = type(self).__name__.lower()
        return name if not name.endswith("list") else name[:-4] + "s"
    
    @property
    def nice_type_name(self):
        return self.__class__.__name__.replace('Model','').replace('Class','')

    @property
    def children_type(self):
        from .imports import CHILDCLASSLISTS
        return CHILDCLASSLISTS.get(type(self))

    @property
    def type(self):
        return type(self)

    @classmethod
    def _get_class(cls, name):
        from .imports import SELFCLASSES

        return SELFCLASSES.get(name.lower())

    @property
    def child_type(self):
        """
        Discover the child_type based on the class name.

        Returns:
            str: The child_type of the EntityList.
        """
        class_name = (
            self.__class__.__name__
            if type(self.__class__) is not type
            else self.__name__
        )
        if class_name.endswith("List"):
            return class_name[:-4]
        return None

    # def __init_subclass__(cls, **kwargs):
    #     super().__init_subclass__(**kwargs)
    #     cls._generate_parent_properties()
    #     cls._generate_child_properties()

    # @classmethod
    # def _generate_parent_properties(cls):
    #     for prop_name, parent_type in cls._parent_types.items():
    #         setattr(cls, prop_name, property(lambda self, pt=parent_type: self.get_parent(pt)))

    # @classmethod
    # def _generate_child_properties(cls):
    #     for child_prop, (list_name, child_type, list_type) in cls._child_types.items():
    #         setattr(cls, list_name, property(lambda self, ct=child_type: self.get_children(ct)))

    def __init__(self, txt: str = "", children=[], parent=None, num=None, text=None, **kwargs):
        """
        Initialize an Entity object.

        Args:
            txt (str): The text content of the entity.
            children (list): List of child entities.
            parent (Entity): The parent entity.
            **kwargs: Additional attributes to set on the entity.
        """
        self._attrs = kwargs
        self._num = num
        self._mtr = None
        self.parent = parent
        self._text = text
        self._txt = txt if txt else ""
        for k, v in self._attrs.items():
            try:
                setattr(self, k, v)
            except Exception as e:
                #log.debug(e)
                pass

        if not isinstance(children, EntityList):
            self.children = (
                self.children_type(children, parent=self)
                if self.children_type is not None
                else None
            )
        else:
            self.children = children
            self.children.parent = self
        
        

    @property
    def is_wordtokenlist(self):
        from .words.wordtokenlist import WordTokenList
        return isinstance(self, WordTokenList)



    @property
    def text(self):
        if self._text is not None: return self._text
        if self.parent: return self.parent.text
        if self.is_wordtokenlist: return self
        
        

    def __iter__(self):
        """
        Iterate over the children of this entity.

        Yields:
            Entity: The next child entity.
        """
        yield from self.children

    @staticmethod
    def _rename_attr(x):
        d = {
            # "word": "wordtoken",
            # "words": "wordtokens",
            # "text": "textmodel",
            # "texts": "textmodels",
            # "syll": "syllable",
            # "sylls": "syllables",
            # "is_word": "is_wordtoken",
            # "is_words": "is_wordtokens",
            # "num_words": "num_wordtokens",
            # "is_text": "is_textmodel",
            # "is_texts": "is_textmodels",
            # "num_texts": "num_textmodels",
            # "is_syll": "is_syllable",
            # "is_sylls": "is_syllables",
            # "num_sylls": "num_syllables",
            # "is_phon": "is_phonemeclass",
            # "is_phons": "is_phonemes",
            # "num_phons": "num_phonemes",
            "sentence":"sent",
            "sentences":"sents",
            "phon":"phoneme",
            "phons":"phonemes",
            "syllable":"syll",
            "syllables":"sylls",

        }
        x = x.lower().strip()
        return d.get(x, x)
    
    def __getitem__(self, key):
        res = super().__getitem__(key)
        if isinstance(res,type(self)) and res is not self:
            res._text = self.text
            res.parent = self.parent
        return res


    def __getattr__(self, attr):
        """
        Get an attribute of the entity by name.

        Args:
            attr (str): The name of the attribute.

        Returns:
            Any: The value of the attribute.
        """
        attr = self._rename_attr(attr)

        try:
            # First, try to get the attribute normally
            return self.__dict__.get(attr, self.__getattribute__(attr))
        except AttributeError:
            # If AttributeError is raised, implement the custom logic
            from .imports import PLURAL_ATTRS, SINGULAR_ATTRS, get_class

            res = None
            if attr in PLURAL_ATTRS:
                #log.debug(f"'{attr}' is in PLURAL_ATTRS, returning list")
                res = self.get_list(attr)
            if attr in SINGULAR_ATTRS:
                #log.debug(f"'{attr}' is in SINGULAR_ATTRS, returning one")
                res = self.get_one(attr)
            if attr.endswith("_r") and attr[:-2] in SINGULAR_ATTRS:
                #log.debug(f"'{attr}' is in SINGULAR_ATTRS, returning random")
                res = self.get_random(attr[:-2])
                return res # don't cache

            elif attr.startswith("num_"):
                cls_name = attr[4:]
                children = self.get_list(cls_name)
                res = len(children) if children is not None else 0
            elif (
                (digits := "".join(x for x in attr if x.isdigit()))
                and (nondigits := "".join(x for x in attr if not x.isdigit()))
                and nondigits in SINGULAR_ATTRS
            ):
                num = int(digits)
                i = 0 if num == 0 else num - 1
                try:
                    #log.debug(f"Attempting to return child at index {i}")
                    res = self.get_list(nondigits)[i]
                except IndexError:
                    #log.debug(f"Index {i} out of range, returning None")
                    res = None


            elif attr.endswith('_span'):
                lname = attr[:-5]
                l = self.get_list(lname)
                return (l[0].num, l[-1].num) if l else None


            if res is not None:
                self.__dict__[attr] = res
                return res

    # @cache
    def get_list(self, list_type: str):
        """
        Get a list of entities of the specified type, either from this entity's children
        or by finding the intersecting list from the text.

        Args:
            list_type (str): The type of list to retrieve (e.g., 'lines', 'words', 'syllables').

        Returns:
            EntityList or None: The requested list of entities, or None if not found.
        """
        # if list_type in {'wordform','wordforms','syll','sylls'}: stopx
        from .imports import get_class_depth, get_ent_class, get_list_class
        list_type = self._rename_attr(list_type)
        cls_depth = get_class_depth(list_type)
        ent_class = get_ent_class(list_type)
        list_class = get_list_class(list_type)
        # log.info(f"Getting list of type: {list_type}")
        # log.info(f'My class: {self.__class__}')
        # log.info(f'My depth: {self.class_depth}')
        # log.info(f"Class depth: {cls_depth}")
        # log.info(f"Entity class: {ent_class}")
        # log.info(f"List class: {list_class}")
        

        if list_class is None:
            return None

        # If this entity is already the requested list type, return self
        if isinstance(self, list_class):
            return self

        # Check if this entity contains the requested list type
        if self.children and isinstance(self.children, list_class):
            return self.children
        
        if cls_depth == 1: # on text level
            # log.info(f"Getting text list for type: {list_type}")
            full_list = self.get_text_list(list_type)
            if self.is_text:
                return full_list
            if full_list is not None:
                # log.info(f"Found text list for type: {list_type}: {full_list[:1]}")
                return self.get_overlapping_list(full_list)

        # If the current entity is above the requested type
        if self.class_depth < cls_depth:
            # log.info(f"Current class depth ({self.class_depth}) is less than requested class depth ({cls_depth})")
            # log.info(f"Getting descendants of type: {list_type}")
            descendants = self.get_descendants(list_type)
            # log.info(f"Found {len(descendants)} descendants")
            if descendants:
                # log.info("Creating new list with descendants")
                return list_class(descendants, parent=self, text=self.text)
            # else:
                # log.info("No descendants found")
        # If the current entity is below the requested type
        elif self.class_depth > cls_depth:
            # log.info(f"Current class depth ({self.class_depth}) is greater than requested class depth ({cls_depth})")
            # log.info(f"Searching for ancestor of type: {list_type}")
            ancestor = self._get_ancestor(list_type)
            # log.info(f"Found ancestor: {ancestor}")
            return list_class([ancestor], parent=ancestor.parent, text=self.text) if ancestor else None

        # If the depths are the same or we couldn't find an appropriate ancestor
        # log.warning(f'Could not find list for type {list_type}')
        return None

    @cached_property
    def children_keys(self):
        return {child.key for child in self.children} if self.children and len(self.children) else set()

    def get_overlapping_list(self, full_list: 'EntityList', entity:'Entity' = None):
        list_class = type(full_list)
        list_class_depth = full_list.class_depth
        if entity is None: entity = self
        entity_depth = entity.class_depth

        assert list_class_depth < 2
        assert entity_depth < 2

        # filtered_list = [ent for ent in full_list if ent.contains(entity)]
        filtered_list = [ent for ent in full_list if ent.children_keys & entity.children_keys]
        return list_class(children=filtered_list,text=self.text, parent=self)
    
    def get_text_list(self, list_type: str):
        from .imports import get_list_class_name
        list_type = get_list_class_name(list_type)
        return getattr(self.text, list_type) if hasattr(self.text, list_type) else None

    @classmethod
    def _class_depth(cls):
        from .imports import CLASS_DEPTHS
        return CLASS_DEPTHS.get(cls)

    @property
    def class_depth(self):
        return self._class_depth()

    @cached_property
    def descendants(self):
        d={
            self.key: self
        }
        if self.children is not None:
            if isinstance(self.children,Entity):
                d[self.children.key] = self.children
            for child in self.children:
                d.update(child.descendants)
        return d

    def get_descendants(self, ent_type: str):
        return list(self._get_descendants(ent_type))

    def _get_descendants(self, ent_type: str):
        """
        Recursively get all descendants of the specified type.

        Args:
            descendant_type (str): The type of descendants to retrieve.

        Returns:
            list: A list of descendant entities of the specified type.
        """
        from .imports import get_ent_class
        descendant_cls = get_ent_class(ent_type)
        # return [v for k,v in self.descendants.items() if isinstance(v, descendant_cls)]
        if isinstance(self.children, descendant_cls):
            yield self.children
        elif self.children and len(self.children):
            for child in self.children:
                if isinstance(child, descendant_cls):
                    yield child
                else:
                    yield from child._get_descendants(ent_type)
    
    def _get_ancestor(self, ent_type: str):
        from .imports import get_ent_class
        ancestor_cls = get_ent_class(ent_type)
        if self.parent:
            if isinstance(self.parent, ancestor_cls):
                return self.parent
            else:
                return self.parent._get_ancestor(ent_type)
        return None
    
    @cached_property
    def children_set(self):
        return set(self.children) if self.children is not None else set()

    def contains(self, entity: 'Entity') -> bool:
        """
        Check if this entity contains the given entity.

        Args:
            entity (Entity): The entity to check for containment.

        Returns:
            bool: True if this entity contains the given entity, False otherwise.
        """
        if self is entity:
            return True
        
        if self.class_depth>1 and self.class_depth >= entity.class_depth: 
            return False
        
        if entity.key.startswith(self.key):
            return True
        
        if self.children:
            if isinstance(entity, EntityList):
                return bool(self.descendant_keys & entity.descendant_keys)
            else:
                print([self.key, entity.key])
                return entity.key in self.descendant_keys
        return False

    def get_random(self, ent_type: str) -> "Entity":
        ent_type = self._rename_attr(ent_type)
        children = self.get_list(ent_type)
        return (
            random.choice(children) if children else None
        )  # will return parent if available

    def get_one(self, ent_type: str) -> "Entity":
        children = self.get_list(ent_type)
        return children[0] if children and len(children) else None  # will return parent if available

    def get_parent(self, parent_type: str) -> "Entity":
        from .imports import SELFCLASSES, PLURAL_ATTRS

        parent_type = self._rename_attr(parent_type)
        if parent_type in PLURAL_ATTRS:
            parent_type = parent_type[:-1]
        parent_class = SELFCLASSES.get(parent_type)
        if parent_class is None:
            return

        while self.parent and not isinstance(self.parent, parent_class):
            self = self.parent

        return self.parent

    def get_children(self, child_type: str) -> List["Entity"]:
        from .imports import LISTCLASSES

        #log.debug(f"Getting children of type: {child_type}")
        child_type = self._rename_attr(child_type)
        #log.debug(f"Renamed child_type: {child_type}")
        list_class = LISTCLASSES.get(child_type)
        #log.debug(f"List class for {child_type}: {list_class}")
        if list_class is None:
            #log.debug("List class is None, returning None")
            return None

        # same?
        if isinstance(self, list_class):
            #log.debug("Self is instance of list_class, returning self")
            return self

        # above?
        parent = self.get_parent(child_type)
        #log.debug(f"Parent of type {child_type}: {parent}")
        if parent is not None:
            #log.debug("Returning list with parent")
            return list_class([parent], parent=parent.parent, text=self.text)

        if self.children is None or list_class is None:
            #log.debug("Children or list_class is None, returning None")
            return None

        # below?
        if self.children is not None and isinstance(self.children, list_class):
            #log.debug("Returning children as they are of the correct list_class")
            return self.children

        #log.debug("Recursively getting grandchildren")
        if self.children is not None:
            grandchildren = []
            for child in self.children:
                child_children = child.get_children(child_type)
                if child_children is not None:
                    grandchildren.extend(list(child_children))

            return list_class(grandchildren, parent=self, text=self.text)

    # @property
    # def sents(self):
    #     from .sents.sents import SentenceList

    #     if self.is_text:
    #         return SentenceList.from_wordtokens(self.wordtokens, parent=self)
    #     else:
    #         return SentenceList(
    #             [
    #                 sent
    #                 for sent in self.text.sents
    #                 if set(sent.wordtokens) & set(self.wordtokens)
    #             ]
    #         )

    # @property
    # def sentparts(self):
    #     from .sents.sents import SentPartList

    #     return SentPartList(
    #         [part for sent in self.sents for part in sent.parts], parent=self
    #     )

    # @property
    # def lineparts(self):
    #     from .texts.lines import LinePartList

    #     return LinePartList(
    #         [part for line in self.lines for part in line.lineparts], parent=self
    #     )

    @cached_property
    def wordforms_first(self):
        from .words.words import WordFormList

        o = []
        for wtyp in self.wordtypes:
            wforms = wtyp.children
            if wforms and len(wforms):
                o.append(wforms[0])
        return WordFormList(o, parent=self)

    @cached_property
    def wordforms_all(self):
        from .words.words import WordFormList

        o = []
        for wtyp in self.wordtypes:
            wforms = wtyp.children
            if wforms:
                o.append(wforms)
        return [WordFormList(ox, parent=self) for ox in o]

    @cached_property
    def wordform_matrix(self):
        return self.wordtokens.wordform_matrix

    def to_hash(self):
        """
        Generate a hash representation of the entity.

        Returns:
            str: A hash string representing the entity's content and attributes.
        """
        return hashstr(
            self.txt, tuple(sorted(self._attrs.items())), self.__class__.__name__
        )

    @property
    def html(self):
        """
        Get the HTML representation of the entity.

        Returns:
            str: HTML representation of the entity, if available.
        """
        if hasattr(self, "to_html"):
            return self.to_html()


    @cached_property
    def hash(self):
        """
        Get a hash value for the entity.

        Returns:
            str: A hash string for the entity.
        """
        return encode_hash(self.key)

    @cached_property
    def stuffed(self):
        return stuff(self)

    @property
    def unstuffed(self):
        return unstuff(self.stuffed)

    @cached_property
    def serialized(self):
        return serialize(self)

    @property
    def deserialized(self):
        return deserialize(self.serialized)

    @classmethod
    def deserialize(cls, obj):
        return deserialize(obj)

    def __hash__(self):
        """
        Get the hash value for use in hash-based collections.

        Returns:
            int: The hash value of the entity.
        """
        try:
            return hash(self.hash)
        except TypeError:
            log.error(f'hash of {self.key} failed')
            log.error(self)
            return hash(self.key)

    def __eq__(self, other):
        """
        Check if this entity is equal to another.

        Args:
            other: The other object to compare with.

        Returns:
            bool: True if the objects are the same instance, False otherwise.
        """
        return self is other

    def equals(self, other):
        return self is other or self.key == other.key or self.serialized == other.serialized

    @property
    def meter(self):
        return self.text.meter

    def __bool__(self):
        """
        Check if the entity is considered True in a boolean context.

        Returns:
            bool: Always returns True for Entity objects.
        """
        return True

    @cached_property
    def id(self):
        return encode_hash(serialize(self.key))

    @cached_property
    def ancestors(self):
        l = []
        obj = self
        while obj.parent:
            l.append(obj.parent)
            obj = obj.parent
        return l

    @cached_property
    def root(self):
        ancestors = self.ancestors
        return ancestors[0] if ancestors else self

    # def get_root_key(self):
    #     return self.root.key

    @property
    def prefix_key(self):
        from .imports import CLASSPREFIXES
        return CLASSPREFIXES[self.__class__]
    
    @property
    def grandparent(self):
        try:
            return self.parent.parent
        except AttributeError:
            return None

    @cached_property
    def key(self):
        key=f"{self.parent.key}.{self.nice_type_name}"
        if self.num is not None:
            key+=f'{self.num}'
        return key


    @cached_property
    def wordspan(self):
        try:
            return (self.wordtokens[0].num, self.wordtokens[-1].num)
        except (IndexError,AttributeError):
            return None

    def to_dict(self, incl_num=True, incl_attrs=False, incl_txt=None, incl_children=True, **kwargs):
        """
        Convert the entity to a JSON representation.

        Args:
            fn (str, optional): Filename to save the JSON output.
            no_txt (bool): If True, exclude the text content.
            yes_txt (bool): If True, include the full text content.
            **kwargs: Additional key-value pairs to include in the JSON.

        Returns:
            dict: A dictionary representation of the entity.
        """
        pkgd = {}
        if incl_num and self._num:
            pkgd['num'] = self._num
        if incl_txt:
            pkgd["txt"] = self._txt

        if incl_children and self.children:
            pkgd["children"] = (
                self.children.to_dict()
                if isinstance(self.children, EntityList)
                else [child.to_dict() for child in self.children]
            )

        if incl_attrs and hasattr(self, "_attrs"):
            for k, v in self._attrs.items():
                pkgd[k] = v

        for k, v in kwargs.items():
            pkgd[k] = v

        return {self.__class__.__name__:pkgd}

    def save(self, fn, **kwargs):
        """
        Save the entity to a file in JSON format.

        Args:
            fn (str): The filename to save to.
            **kwargs: Additional arguments to pass to to_dict.

        Returns:
            The result of to_dict with the given filename.
        """
        return self.to_dict(fn=fn, **kwargs)

    def render(self, as_str=False):
        """
        Render the entity as HTML.

        Args:
            as_str (bool): If True, return the result as a string.

        Returns:
            str or HTML: The rendered HTML representation of the entity.
        """
        return self.to_html(as_str=as_str)

    @classmethod
    def from_dict(cls, data):
        assert isinstance(data,dict)
        from .imports import GLOBALS
        if len(data)>1:
            pprint(data)
        assert len(data) == 1, "Should only be classname in key"
        cls_name,cls_data = next(iter(data.items()))
        cls2 = GLOBALS.get(cls_name)
        if cls is not cls2:
            return cls2.from_dict(data)
        
        assert cls is not None, "Class should exist"
        children = cls_data.pop('children', None)
        if children is not None:
            if isinstance(children, dict):
                children = Entity.from_dict(children)
            elif isinstance(children,list):
                children = [Entity.from_dict(child) for child in children]
        return cls(children=children, **cls_data)


    # @classmethod
    # @#log.debug
    # def from_dict(cls, data):
    #     """
    #     Create an Entity object from a JSON dictionary.

    #     Args:
    #         json_d (dict): A dictionary containing the entity data.

    #     Returns:
    #         Entity: An instance of the appropriate Entity subclass.
    #     """
    #     # log.info(f'stuffed: {data}')
    #     data = unstuff(data) if isinstance(data, dict) else data
    #     # log.info(f'unstuffed: {data}')

    #     # New code to handle children properly
    #     if isinstance(data, dict) and "children" in data:
    #         if isinstance(data["children"], type):
    #             # If children is a class, instantiate it
    #             data["children"] = data["children"]()
    #         elif isinstance(data["children"], list):
    #             # If children is a list, recursively process each child
    #             data["children"] = [cls.from_dict(child) for child in data["children"]]

    #     return call_function_politely(cls, **data) if isinstance(data, dict) else data

    def __reduce__(self):
        # Return a tuple of (callable, args) that allows recreation of this object
        return (self.__class__.from_dict, (self.to_dict(),))

    @property
    def attrs(self):
        """
        Get the attributes of the entity.

        Returns:
            dict: A dictionary of the entity's attributes.
        """
        return self._attrs
        # odx = {}
        # if (
        #     self.__class__.__name__
        #     not in {"TextModel", "Stanza", "MeterLine", "MeterText", "Meter"}
        #     and self.txt
        # ):
        #     odx["txt"] = self.txt
        # return {**odx, **self._attrs}

    @property
    def prefix_attrs(self, with_parent=True):
        """
        Get the attributes of the entity with a prefix.

        Args:
            with_parent (bool): If True, include parent attributes.

        Returns:
            dict: A dictionary of the entity's attributes with a prefix.
        """

        def getkey(k):
            o = f"{self.prefix}_{k}"
            o = DF_COLS_RENAME.get(o, o)
            return o

        odx = {getkey(k): v for k, v in self.attrs.items() if v is not None}
        if with_parent and self.parent:
            return {**self.parent.prefix_attrs, **odx}
        return odx

    @cached_property
    def txt(self):
        """
        Get the text content of the entity.

        Returns:
            str: The text content of the entity.
        """
        #log.debug(type(self), self._txt)
        if self._txt:
            txt = self._txt
        elif self.children:
            txt = "".join(child.txt for child in self.children)
        else:
            txt = ""
        return txt

    @property
    def data(self):
        """
        Get the data associated with the entity.

        Returns:
            list: The list of child entities.
        """
        return self.children

    @property
    def l(self):
        """
        Get the list of child entities.

        Returns:
            list: The list of child entities.
        """
        return self.children

    def inspect(self, indent=0, maxlines=None, incl_phons=False):
        """
        Inspect the entity and its children.

        Args:
            indent (int): The indentation level for the output.
            maxlines (int): The maximum number of lines to display.
            incl_phons (bool): If True, include phoneme information.
        """
        attrstr = get_attr_str(self.attrs)
        myself = f"{self.__class__.__name__}({attrstr})"
        if indent:
            myself = textwrap.indent(myself, "|" + (" " * (indent - 1)))
        lines = [myself]
        for child in self.children:
            if isinstance(child, Entity) and (
                incl_phons or not child.__class__.__name__.startswith("Phoneme")
            ):
                lines.append(
                    child.inspect(indent=indent + 4, incl_phons=incl_phons).replace(
                        "PhonemeClass", "Phoneme"
                    )
                )
        # self.__class__.__name__ in {'Text', 'Stanza', 'Line'}
        dblbreakfor = False
        breakstr = "\n|\n" if dblbreakfor else "\n"
        o = breakstr.join(lines)
        if not indent:
            if maxlines:
                o = "\n".join(o.split("\n")[:maxlines])
            print(o)
        else:
            return o

    def _repr_html_(self, df=None):
        """
        Get the HTML representation of the entity.

        Args:
            df (DataFrame): An optional DataFrame to use for rendering.

        Returns:
            str: The HTML representation of the entity.
        """

        def blank(x):
            if x in {None, np.nan}:
                return ""
            return x

        return f"<b>{self.__class__.__name__}</b><br>{ (self.df if df is None else df).applymap(blank)._repr_html_() }"

    def __repr__(self):
        kwargs = {}
        attrs = self._attrs if hasattr(self, "_attrs") and self._attrs else {}
        for attr in ["num", "txt"] + list(attrs.keys()):
            attrval = getattr(self, attr, None) if not attr in attrs else attrs[attr]
            if attrval:
                kwargs[attr] = repr(attrval).strip()[:100]
        params_str = f", ".join(f"{k}={v}" for k, v in kwargs.items())
        return f"{self.nice_type_name}({params_str})"

    @property
    def ld(self):
        """
        Get a list of dictionaries representing the entity and its children.

        Returns:
            list: A list of dictionaries representing the entity and its children.
        """
        return self.get_ld()

    @property
    def child_class(self):
        """
        Get the class of the child entities.

        Returns:
            type: The class of the child entities.
        """
        from .imports import GLOBALS

        return GLOBALS.get(self.child_type)

    def get_ld(self, incl_phons=False, incl_sylls=True, multiple_wordforms=True):
        """
        Get a list of dictionaries representing the entity and its children.

        Args:
            incl_phons (bool): If True, include phoneme information.
            incl_sylls (bool): If True, include syllable information.
            multiple_wordforms (bool): If True, include multiple word forms.

        Returns:
            list: A list of dictionaries representing the entity and its children.
        """
        if not incl_sylls and self.child_type == "Syllable":
            return [{**self.prefix_attrs}]
        if not incl_phons and self.child_type == "Phoneme":
            return [{**self.prefix_attrs}]
        good_children = [c for c in self.children if isinstance(c, Entity)]
        # #log.debug(f'good children of {type(self)} -> {good_children}')
        if not multiple_wordforms and self.child_type == "WordForm" and good_children:
            good_children = good_children[:1]
            # #log.debug(f'good children now {good_children}')
        if good_children:
            return [
                {**self.prefix_attrs, **child.prefix_attrs, **grandchild_d}
                for child in good_children
                for grandchild_d in child.get_ld(
                    incl_phons=incl_phons,
                    incl_sylls=incl_sylls,
                    multiple_wordforms=multiple_wordforms,
                )
            ]
        else:
            return [{**self.prefix_attrs}]

    def get_df(self, **kwargs):
        """
        Get a DataFrame representation of the entity and its children.

        Args:
            **kwargs: Additional arguments to pass to get_ld.

        Returns:
            DataFrame: A DataFrame representation of the entity and its children.
        """
        odf = pd.DataFrame(self.get_ld(**kwargs))
        for c in DF_BADCOLS:
            if c in set(odf.columns):
                odf = odf.drop(c, axis=1)
        for c in odf:
            if c.endswith("_num"):
                odf[c] = odf[c].fillna(0).apply(int)
            else:
                odf[c] = odf[c].fillna("")
        odf = niceindex(odf)

        def unbool(x):
            if x is True:
                return 1
            if x is False:
                return 0
            if x is None:
                return 0
            return x

        odf = odf.applymap(unbool)
        return odf

    @property
    def df(self):
        """
        Get a DataFrame representation of the entity and its children.

        Returns:
            DataFrame: A DataFrame representation of the entity and its children.
        """
        return self.get_df()

    
    @property
    def num_wordforms_nopunc(self):
        return len([wf for wf in self.wordforms if not wf.parent.is_punc])

    @property
    def num_wordforms_all(self):
        return sum(len(wt.children) for wt in self.wordtypes)

    def syllable(self):
        """
        Get the parent syllable entity.

        Returns:
            Syllable: The parent syllable entity, or None if not found.
        """
        return self.get_parent("Syllable")

    @cached_property
    def i(self):
        """
        Get the index of the entity in its parent's children list.

        Returns:
            int: The index of the entity, or None if not found.
        """
        if self.parent is None:
            return None
        if not self.parent.children:
            return None
        try:
            return self.parent.children.index(self)
        except (IndexError, ValueError):
            return None

    @cached_property
    def num(self):
        """
        Get the 1-based index of the entity in its parent's children list.

        Returns:
            int: The 1-based index of the entity, or None if not found.
        """
        if self._num is not None: return self._num
        return
        return self.i + 1 if self.i is not None else None

    @property
    def next(self):
        """
        Get the next sibling entity.

        Returns:
            Entity: The next sibling entity, or None if not found.
        """
        if self.i is None:
            return None
        try:
            return self.parent.children[self.i + 1]
        except IndexError:
            return None

    @property
    def prev(self):
        """
        Get the previous sibling entity.

        Returns:
            Entity: The previous sibling entity, or None if not found.
        """
        if self.i is None:
            return None
        i = self.i
        if i - 1 < 0:
            return None
        try:
            return self.parent.children[i - 1]
        except IndexError:
            return None


class EntityList(Entity):
    """
    A list of Entity objects.
    """

    @property
    def is_text_list(self):
        return self.parent and self.parent.class_depth < 2

    @cached_property
    def key(self):
        if self.is_text_list and self.children and len(self.children):
            w1,w2=self.children[0].key, self.children[-1].key
            w1='.'.join(w1.split('.')[1:])
            w2='.'.join(w2.split('.')[1:])
            textkey=self.text.key+'.' if self.text is not self else ''
            return f'{textkey}{self.nice_type_name}({w1}, {w2})'
        else:
            return f'{self.parent.key}.{self.nice_type_name}'

    

    @property
    def list_type(self):
        return type(self)
    
    @property
    def children_type(self):
        from .imports import CHILDCLASSLISTS
        return CHILDCLASSLISTS.get(type(self))

    def __init__(self, children=[], parent=None, txt=None, text=None, num=None, **kwargs):
        """
        Initialize an EntityList object.

        Args:
            children (list): List of child entities.
            parent (Entity): The parent entity.
            **kwargs: Additional attributes to set on the entity.
        """
        self._num=num
        self._text = text
        self.parent = parent
        if children is None: children=[]
        self.children = list(children)
        for child in self.children:
            if child.parent is None:
                child.parent = self

        self._attrs = kwargs
        self._txt = txt
        for k, v in self._attrs.items():
            try:
                setattr(self, k, v)
            except AttributeError:
                pass

    def __repr__(self, indent=1, indenter="    "):
        class_name = self.__class__.__name__
        items = []
        if self.data is not None:
            for item in self.data:
                if isinstance(item, EntityList):
                    item_repr = item.__repr__(indent=indent+1)
                else:
                    item_repr = repr(item).strip()
                items.append((indenter * indent) + item_repr)

        items_str = ",\n".join(items)
        return f"{self.nice_type_name}([\n{items_str}\n{' ' * indent}])"

    @property
    def txt(self):
        """
        Get the text content of the entity list.

        Returns:
            None: Always returns None for EntityList objects.
        """
        return None


def get_class(class_name):
    from .imports import get_class
    return get_class(class_name)