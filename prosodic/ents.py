from typing import Any
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

    child_type = "Text"
    is_parseable = False
    index_name = None
    prefix = "ent"
    list_type = None
    cached_properties_to_clear = []
    use_cache = False
    sep = ""

    def __init__(self, txt: str = "", children=[], parent=None, **kwargs):
        """
        Initialize an Entity object.

        Args:
            txt (str): The text content of the entity.
            children (list): List of child entities.
            parent (Entity): The parent entity.
            **kwargs: Additional attributes to set on the entity.
        """
        self.parent = parent
        newchildren = []
        for child in children:
            if not isinstance(child, Entity):
                logger.warning(f"{child} is not an Entity")
                continue
            newchildren.append(child)
            # if not child.is_wordtype:   # don't do this for wordtypes since each wordtype is a single/shared python object
            child.parent = self
        children = newchildren
        if self.list_type is None:
            self.list_type = 'EntityList'
        from .imports import GLOBALS
        self.children = GLOBALS[self.list_type](children)
        self._attrs = kwargs
        self._txt = txt
        self._mtr = None
        for k, v in self._attrs.items():
            setattr(self, k, v)

    def __iter__(self):
        """
        Iterate over the children of this entity.

        Yields:
            Entity: The next child entity.
        """
        yield from self.children

    def to_hash(self):
        """
        Generate a hash representation of the entity.

        Returns:
            str: A hash string representing the entity's content and attributes.
        """
        return hashstr(
            self.txt, tuple(sorted(self._attrs.items())), self.__class__.__name__
        )

    @cached_property
    def html(self):
        """
        Get the HTML representation of the entity.

        Returns:
            str: HTML representation of the entity, if available.
        """
        if hasattr(self, "to_html"):
            return self.to_html()

    @cached_property
    def key(self):
        """
        Generate a unique key for the entity.

        Returns:
            str: A string key representing the entity's class and attributes.
        """
        attrs = {
            **{k: v for k, v in self.attrs.items() if v is not None},
            "txt": self._txt,
        }
        return f"{self.__class__.__name__}({get_attr_str(attrs)})"

    @cached_property
    def hash(self):
        """
        Get a hash value for the entity.

        Returns:
            str: A hash string for the entity.
        """
        return hashstr(self.key)

    def __hash__(self):
        """
        Get the hash value for use in hash-based collections.

        Returns:
            int: The hash value of the entity.
        """
        return hash(self.hash)

    def __eq__(self, other):
        """
        Check if this entity is equal to another.

        Args:
            other: The other object to compare with.

        Returns:
            bool: True if the objects are the same instance, False otherwise.
        """
        return self is other

    def __bool__(self):
        """
        Check if the entity is considered True in a boolean context.

        Returns:
            bool: Always returns True for Entity objects.
        """
        return True

    def to_json(self, fn=None, no_txt=False, yes_txt=False, no_children=None, **kwargs):
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
        txt = (self._txt if not yes_txt else self.txt) if not no_txt else None
        return to_json(
            {
                "_class": self.__class__.__name__,
                **({"txt": txt} if txt is not None and (yes_txt or txt) else {}),
                **({"children": [kid.to_json() for kid in self.children]} if not no_children else {}),
                **kwargs,
            },
            fn=fn,
        )
    
    to_dict = to_json

    def save(self, fn, **kwargs):
        """
        Save the entity to a file in JSON format.

        Args:
            fn (str): The filename to save to.
            **kwargs: Additional arguments to pass to to_json.

        Returns:
            The result of to_json with the given filename.
        """
        return self.to_json(fn=fn, **kwargs)

    def render(self, as_str=False):
        """
        Render the entity as HTML.

        Args:
            as_str (bool): If True, return the result as a string.

        Returns:
            str or HTML: The rendered HTML representation of the entity.
        """
        return self.to_html(as_str=as_str)

    @staticmethod
    def from_json(json_d):
        """
        Create an Entity object from a JSON dictionary.

        Args:
            json_d (dict): A dictionary containing the entity data.

        Returns:
            Entity: An instance of the appropriate Entity subclass.
        """
        from .imports import GLOBALS, CHILDCLASSES

        classname = json_d["_class"]
        classx = GLOBALS[classname]
        childx = CHILDCLASSES.get(classname)
        children = json_d.get("children", [])
        inpd = {k: v for k, v in json_d.items() if k not in {"children", "_class"}}
        if children and childx:
            children = [childx.from_json(d) for d in json_d["children"]]
        return classx(children=tuple(children), **inpd)
    
    from_dict = from_json


    def __reduce__(self):
        # Return a tuple of (callable, args) that allows recreation of this object
        return (self.__class__.from_json, (self.to_json(),))
    

    @property
    def attrs(self):
        """
        Get the attributes of the entity.

        Returns:
            dict: A dictionary of the entity's attributes.
        """
        odx = {"num": self.num}
        if (
            self.__class__.__name__
            not in {"Text", "Stanza", "MeterLine", "MeterText", "Meter"}
            and self.txt
        ):
            odx["txt"] = self.txt
        return {**odx, **self._attrs}

    @cached_property
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
        if self._txt:
            txt = self._txt
        elif self.children:
            txt = self.child_class.sep.join(child.txt for child in self.children)
        else:
            txt = ""
        return txt

    @cached_property
    def data(self):
        """
        Get the data associated with the entity.

        Returns:
            list: The list of child entities.
        """
        return self.children

    @cached_property
    def l(self):
        """
        Get the list of child entities.

        Returns:
            list: The list of child entities.
        """
        return self.children

    def clear_cached_properties(self):
        """
        Clear cached properties to free up memory.
        """
        for attr_name in list(self.__dict__.keys()):
            if isinstance(getattr(type(self), attr_name, None), cached_property):
                del self.__dict__[attr_name]

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

        return (self.df if df is None else df).applymap(blank)._repr_html_()

    def __repr__(self, attrs=None, bad_keys=None):
        """
        Get a string representation of the entity.

        Args:
            attrs (dict): An optional dictionary of attributes to use.
            bad_keys (list): An optional list of keys to exclude.

        Returns:
            str: A string representation of the entity.
        """
        d = {
            k: v
            for k, v in (
                attrs
                if attrs is not None
                else (self.attrs if self.attrs is not None else self._attrs)
            ).items()
        }
        return f"{self.__class__.__name__}({get_attr_str(d, bad_keys=bad_keys)})"

    @cached_property
    def ld(self):
        """
        Get a list of dictionaries representing the entity and its children.

        Returns:
            list: A list of dictionaries representing the entity and its children.
        """
        return self.get_ld()

    @cached_property
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
        # logger.debug(f'good children of {type(self)} -> {good_children}')
        if not multiple_wordforms and self.child_type == "WordForm" and good_children:
            good_children = good_children[:1]
            # logger.debug(f'good children now {good_children}')
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

    @cached_property
    def df(self):
        """
        Get a DataFrame representation of the entity and its children.

        Returns:
            DataFrame: A DataFrame representation of the entity and its children.
        """
        return self.get_df()

    def __getattr__(self, attr):
        """
        Get an attribute of the entity by name.

        Args:
            attr (str): The name of the attribute.

        Returns:
            Any: The value of the attribute.
        """
        objs = {
            "stanza": "stanzas",
            "line": "lines",
            "word": "wordtokens",
            "wordtoken": "wordtokens",
            "wordtype": "wordtypes",
            "wordform": "wordforms",
            "syllable": "syllables",
            "phoneme": "phonemes",
        }
        if attr[-1].isdigit():
            for pref, lname in objs.items():
                if attr.startswith(pref) and attr[len(pref) :].isdigit():
                    num = int(attr[len(pref) :])
                    try:
                        return getattr(self, lname)[num - 1]
                    except IndexError:
                        logger.warning(f"no {pref} at that number")
                        return

    def get_parent(self, parent_type=None):
        """
        Get the parent entity of a specific type.

        Args:
            parent_type (str): The type of parent entity to find.

        Returns:
            Entity: The parent entity of the specified type, or None if not found.
        """
        logger.trace(self.__class__.__name__)
        if not hasattr(self, "parent") or not self.parent:
            return
        if self.parent.__class__.__name__ == parent_type:
            return self.parent
        return self.parent.get_parent(parent_type)

    @cached_property
    def stanzas(self):
        """
        Get the list of stanza entities.

        Returns:
            StanzaList: A list of stanza entities.
        """
        from .texts import StanzaList

        if self.is_text:
            o = self.children
        elif self.is_stanza:
            o = [self]
        else:
            o = []
        return StanzaList(o)

    @property
    def line_r(self):
        """
        Get a random line entity.

        Returns:
            Line: A random line entity, or None if no lines exist.
        """
        return random.choice(self.lines) if self.lines else None

    @property
    def word_r(self):
        """
        Get a random word entity.

        Returns:
            WordToken: A random word entity, or None if no words exist.
        """
        return random.choice(self.words) if self.words else None

    @cached_property
    def lines(self):
        """
        Get the list of line entities.

        Returns:
            LineList: A list of line entities.
        """
        from .texts import LineList

        if self.is_stanza:
            o = self.children
        elif self.is_line:
            o = [self]
        else:
            o = [line for stanza in self.stanzas for line in stanza.children]
        return LineList(o)

    @cached_property
    def wordtokens(self):
        """
        Get the list of word token entities.

        Returns:
            WordTokenList: A list of word token entities.
        """
        from .words import WordTokenList

        if self.is_line:
            o = self.children
        elif self.is_wordtoken:
            o = [self]
        else:
            o = [wt for line in self.lines for wt in line.children]
        return WordTokenList(o)

    @property
    def words(self):
        """
        Get the list of word token entities.

        Returns:
            WordTokenList: A list of word token entities.
        """
        return self.wordtokens

    @cached_property
    def wordtypes(self):
        """
        Get the list of word type entities.

        Returns:
            WordTypeList: A list of word type entities.
        """
        from .words import WordTypeList

        if self.is_wordtoken:
            o = self.children
        elif self.is_wordtype:
            o = [self]
        else:
            o = [wtype for token in self.wordtokens for wtype in token.children]
        return WordTypeList(o)

    @cached_property
    def wordforms(self):
        """
        Get the list of word form entities.

        Returns:
            WordFormList: A list of word form entities.
        """
        from .words import WordFormList

        if self.is_wordtype:
            o = self.children[:1]
        elif self.is_wordtype:
            o = [self]
        else:
            o = [wtype.children[0] for wtype in self.wordtypes if wtype.children]
        return WordFormList(o)

    @cached_property
    def wordforms_nopunc(self):
        """
        Get the list of word form entities, excluding punctuation.

        Returns:
            list: A list of word form entities, excluding punctuation.
        """
        return [wf for wf in self.wordforms if not wf.parent.is_punc]

    @cached_property
    def wordforms_all(self):
        """
        Get the list of all word form entities.

        Returns:
            list: A list of all word form entities.
        """
        if self.is_wordtype:
            o = self.children
        if self.is_wordform:
            o = [self]
        else:
            o = [wtype.children for wtype in self.wordtypes]
        return o

    @cached_property
    def syllables(self):
        """
        Get the list of syllable entities.

        Returns:
            SyllableList: A list of syllable entities.
        """
        from .words import SyllableList

        if self.is_wordform:
            o = self.children
        if self.is_syll:
            o = [self]
        else:
            o = [syll for wf in self.wordforms for syll in wf.children]
        return SyllableList(o)

    @cached_property
    def phonemes(self):
        """
        Get the list of phoneme entities.

        Returns:
            PhonemeList: A list of phoneme entities.
        """
        from .words import PhonemeList

        if self.is_syll:
            o = self.children
        if self.is_phon:
            o = [self]
        else:
            o = [phon for syll in self.syllables for phon in syll.children]
        return PhonemeList(o)

    @cached_property
    def text(self):
        """
        Get the parent text entity.

        Returns:
            Text: The parent text entity, or None if not found.
        """
        return self.get_parent("Text")

    @cached_property
    def stanza(self):
        """
        Get the parent stanza entity.

        Returns:
            Stanza: The parent stanza entity, or None if not found.
        """
        return self.get_parent("Stanza")

    @cached_property
    def line(self):
        """
        Get the parent line entity.

        Returns:
            Line: The parent line entity, or None if not found.
        """
        return self.get_parent("Line")

    @cached_property
    def wordtoken(self):
        """
        Get the parent word token entity.

        Returns:
            WordToken: The parent word token entity, or None if not found.
        """
        return self.get_parent("WordToken")

    @cached_property
    def wordtype(self):
        """
        Get the parent word type entity.

        Returns:
            WordType: The parent word type entity, or None if not found.
        """
        return self.get_parent("WordType")

    @cached_property
    def wordform(self):
        """
        Get the parent word form entity.

        Returns:
            WordForm: The parent word form entity, or None if not found.
        """
        return self.get_parent("WordForm")

    @cached_property
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
        except IndexError:
            return None

    @cached_property
    def num(self):
        """
        Get the 1-based index of the entity in its parent's children list.

        Returns:
            int: The 1-based index of the entity, or None if not found.
        """
        return self.i + 1 if self.i is not None else None

    @cached_property
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

    @cached_property
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

    @cached_property
    def is_text(self):
        """
        Check if the entity is a text entity.

        Returns:
            bool: True if the entity is a text entity, False otherwise.
        """
        return self.__class__.__name__ == "Text"

    @cached_property
    def is_stanza(self):
        """
        Check if the entity is a stanza entity.

        Returns:
            bool: True if the entity is a stanza entity, False otherwise.
        """
        return self.__class__.__name__ == "Stanza"

    @cached_property
    def is_line(self):
        """
        Check if the entity is a line entity.

        Returns:
            bool: True if the entity is a line entity, False otherwise.
        """
        return self.__class__.__name__ == "Line"

    @cached_property
    def is_wordtoken(self):
        """
        Check if the entity is a word token entity.

        Returns:
            bool: True if the entity is a word token entity, False otherwise.
        """
        return self.__class__.__name__ == "WordToken"

    @cached_property
    def is_wordtype(self):
        """
        Check if the entity is a word type entity.

        Returns:
            bool: True if the entity is a word type entity, False otherwise.
        """
        return self.__class__.__name__ == "WordType"

    @cached_property
    def is_wordform(self):
        """
        Check if the entity is a word form entity.

        Returns:
            bool: True if the entity is a word form entity, False otherwise.
        """
        return self.__class__.__name__ == "WordForm"

    @cached_property
    def is_syll(self):
        """
        Check if the entity is a syllable entity.

        Returns:
            bool: True if the entity is a syllable entity, False otherwise.
        """
        return self.__class__.__name__ == "Syllable"

    @cached_property
    def is_phon(self):
        """
        Check if the entity is a phoneme entity.

        Returns:
            bool: True if the entity is a phoneme entity, False otherwise.
        """
        return self.__class__.__name__ == "PhonemeClass"

    def children_from_cache(self):
        """
        Get the children of the entity from the cache.

        Returns:
            list: The list of child entities, or None if not found in the cache.
        """
        if caching_is_enabled():
            res = self.from_cache()
            return None if res is None else res.children

    def get_key(self, key):
        """
        Get a key for caching purposes.

        Args:
            key: The key object.

        Returns:
            str: The hashed key.
        """
        if hasattr(key, "to_hash"):
            key = key.to_hash()
        elif key:
            key = hashstr(key)
        return key

    def from_cache(self, obj=None, key=None, as_dict=False):
        """
        Get an object from the cache.

        Args:
            obj: The object to cache.
            key: The key for the cache.
            as_dict (bool): If True, return the cached data as a dictionary.

        Returns:
            Any: The cached object, or None if not found.
        """
        if obj is None:
            obj = self
        key = self.get_key(obj) if not key else key
        if key and self.use_cache != False:
            cache = self.get_cache()
            if key in cache:
                dat = cache[key]
                if dat:
                    return from_json(dat) if not as_dict else dat

    def get_cache(self):
        """
        Get the cache object.

        Returns:
            SimpleCache: The cache object.
        """
        return SimpleCache()

    def cache(
        self, key_obj=None, val_obj=None, key=None, force=False
    ):
        """
        Cache an object.

        Args:
            key_obj: The object to use as the cache key.
            val_obj: The object to cache.
            key: An optional key for the cache.
            force (bool): If True, force the cache to be updated.
        """
        if key_obj is None:
            key_obj = self
        if val_obj is None:
            val_obj = key_obj
        logger.trace(f"key_obj = {key_obj}")
        logger.trace(f"val_obj = {val_obj}")
        key = self.get_key(key_obj) if not key else key
        cache = self.get_cache()
        if key and (force or not key in cache):
            cache[key] = val_obj.to_json()
            # with logmap(f"saving object under key {key[:8]}", level='trace'):
                # with logmap("exporting to json", level="trace"):
                    # data = val_obj.to_json()
                # with logmap("uploading json to cache", level="trace"):
                    # cache[key] = data


class EntityList(Entity):
    """
    A list of Entity objects.
    """

    def __init__(self, children=[], parent=None, txt=None, **kwargs):
        """
        Initialize an EntityList object.

        Args:
            children (list): List of child entities.
            parent (Entity): The parent entity.
            **kwargs: Additional attributes to set on the entity.
        """
        self.parent = parent
        self.children = children
        self._attrs = kwargs
        self._txt = txt
        for k, v in self._attrs.items():
            setattr(self, k, v)

    def __repr__(self, indent=0):
        class_name = self.__class__.__name__
        items = []
        for item in self.data:
            if isinstance(item, EntityList):
                item_repr = item.__repr__(indent + 4)
            else:
                item_repr = repr(item)
            items.append(" " * (indent + 4) + item_repr)
        
        items_str = ",\n".join(items)
        return f"{class_name}([\n{items_str}\n{' ' * indent}])"

    @cached_property
    def txt(self):
        """
        Get the text content of the entity list.

        Returns:
            None: Always returns None for EntityList objects.
        """
        return None




EntityCache = SimpleCache