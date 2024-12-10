from ..imports import *
from ..words import WordTokenList, WordToken

NUMBUILT = 0


class TextModel(Entity):
    """
    A class that represents a text structure, comprised of WordTokens.
    """

    is_text = True
    prefix = "text"

    # @#log.debug
    def __init__(
        self,
        children: Optional[list] = [],
        txt: str = None,
        fn: str = None,
        lang: Optional[str] = DEFAULT_LANG,
        parent: Optional[Entity] = None,
        tokens_df: Optional[pd.DataFrame] = None,
        **kwargs,
    ):
        """
        Initializes an instance of the class.

        Args:
            txt (str): The text string. Default is an empty string.
            fn (str): A path or URL to a text file to read
            lang (Optional[str]): The language of the text. Default is DEFAULT_LANG.
            parent (Optional[Entity]): The parent entity. Default is None.
            children (Optional[list]): The list of child entities. Default is an empty list.
            tokens_df (Optional[pd.DataFrame]): The token dataframe. Default is None.
            use_cache (bool): Whether to use cache. Default is USE_CACHE.
            force (bool): Force parsing regardless of current state. Default is False.
            **kwargs: Additional keyword arguments.

        Raises:
            Exception: If neither txt string, filename, nor token dataframe is provided.

        Returns:
            None
        """

        if isinstance(children, str):
            txt = children
            children = []

        if not txt and not fn and not children and tokens_df is None:
            raise ValueError(
                "must provide either txt string or filename or token dataframe"
            )
        txt = clean_text(get_txt(txt, fn)).strip()
        lang = lang if lang else detect_lang(txt)

        # init entity
        super().__init__(
            children=children,
            txt=txt,
            lang=lang,
            **kwargs,
        )
        self._parse_results = {}

        if not self.children:
            if tokens_df is None:
                tokens_df = tokenize_sentwords_df(txt)

            for _, row in progress_bar(
                list(tokens_df.iterrows()),
                progress=len(tokens_df) >= 1000,
                desc="Building long text",
            ):
                self.children.append(WordToken(lang=self.lang, **row.to_dict()))
        
        # assign objects to global OBJECTS dict
        self.register_objects()
        

    @cached_property
    def stanzas(self):
        from ..texts.stanzas import StanzaList

        return StanzaList.from_wordtokens(self.children, text=self)

    @cached_property
    def lines(self):
        from ..texts.lines import LineList

        return LineList.from_wordtokens(self.children, text=self)

    @cached_property
    def lineparts(self):
        from ..texts.lines import LinePartList

        return LinePartList.from_wordtokens(self.children, text=self)

    @cached_property
    def sents(self):
        from ..sents.sents import SentenceList

        return SentenceList.from_wordtokens(self.children, text=self)

    @cached_property
    def sentparts(self):
        from ..sents.sents import SentPartList

        return SentPartList.from_wordtokens(self.children, text=self)
    
    @property
    def wordtokens(self):
        return self.children

    def to_hash(self) -> str:
        """
        Generate a hash string for the text.

        Returns:
            str: A hash string representation of the text.
        """
        return hashstr(self._txt)

    @property
    def hash(self):
        pkg={"txt": self._txt, "lang": self.lang}
        return encode_hash(serialize(pkg))

    @property
    def key(self):
        if self._key is None:
            self._key = f"{self.nice_type_name}({self.hash})"
        return self._key
    
    def __getitem__(self, item):
        if isinstance(item, slice):
            return self.children[item]
        return super().__getitem__(item)
        

    @cache
    def parse(
        self,
        combine_by: Literal["line", "sent"] = DEFAULT_COMBINE_BY,
        num_proc=None,
        lim=None,
        force=False,
        meter=None,
        **meter_kwargs,
    ):
        """
        Parse the text.

        Args:
            **kwargs: Keyword arguments for parsing configuration.

        Returns:
            Any: The parsed result.
        """
        from ..parsing.parselists import ParseListList

        if combine_by != self.prefix:
            self._parses = ParseListList(parent=self)
        for i,pl in enumerate(self.parse_iter(
            combine_by=combine_by,
            num_proc=num_proc,
            force=force,
            meter=meter,
            lim=lim,
            **meter_kwargs,
        )):
            if combine_by == self.prefix:
                return pl
            else:
                pl._num = i+1
                self._parses.append(pl)
        self._parses.register_objects()
        return self._parses

    def parse_iter(
        self,
        combine_by: Literal["line", "sent"] = DEFAULT_COMBINE_BY,
        num_proc=None,
        lim=None,
        force=False,
        meter=None,
        **meter_kwargs,
    ):
        from ..parsing.parselists import ParseList

        meter = self.get_meter(meter=meter, **meter_kwargs)
        if combine_by and meter.parse_unit == combine_by:
            combine_by = None

        parse_key = (meter.key, combine_by)
        if parse_key in self._parse_results:
            yield from self._parse_results[parse_key]
        else:
            self._parse_results[parse_key] = []
            last_unit = None
            units = []
            for parse_list in meter.parse_text_iter(
                self, num_proc=num_proc, force=force, lim=lim
            ):
                # log.info(f'parse_list: {parse_list}')
                # log.info(f'parsed_ent v1: {parse_list.parent}')
                parsed_ent = self.match(parse_list.parent)
                parse_list.parent = parsed_ent
                parsed_ent._parses = parse_list
                if not combine_by:
                    self._parse_results[parse_key].append(parse_list)
                    yield parse_list
                else:
                    this_unit = getattr(parsed_ent, combine_by)
                    if units and not last_unit.equals(this_unit):
                        new_parselist = ParseList.from_combinations(units, parent=last_unit)
                        last_unit._parses = new_parselist
                        self._parse_results[parse_key].append(new_parselist)
                        yield new_parselist
                        units = []
                    units.append(parse_list)
                    last_unit = this_unit

            if units:
                new_parselist = ParseList.from_combinations(units, parent=last_unit)
                last_unit._parses = new_parselist
                self._parse_results[parse_key].append(new_parselist)
                yield new_parselist

    @property
    def parses(self) -> Any:
        """
        Get the parses for the text.

        Returns:
            Any: The parses object.
        """
        if not self._parses:
            self.parse()
        return self._parses

    def iter_wordtoken_matrix(self):
        yield from self.wordtokens.iter_wordtoken_matrix()

    @cached_property
    def wordtoken_matrix(self):
        return list(self.iter_wordtoken_matrix())

    def get_parseable_units(self, combine_by: Optional[Literal["line", "sent"]] = DEFAULT_COMBINE_BY):
        return self.get_list(combine_by) if combine_by is not None else self.meter.get_parse_units()

    def get_rhyming_lines(self, max_dist: int = RHYME_MAX_DIST) -> Dict[Any, Any]:
        """
        Get the rhyming lines within the stanza.

        Args:
            max_dist (int): Maximum distance between rhyming lines. Default is RHYME_MAX_DIST.

        Returns:
            Dict[Any, Any]: A dictionary of rhyming lines.
        """
        d={}
        for stanza in self.stanzas:
            d.update(stanza.get_rhyming_lines(max_dist=max_dist))
        return d
    
    @property
    def num_rhyming_lines(self) -> int:
        """
        Get the number of rhyming lines in the text.

        Returns:
            int: The number of rhyming lines.
        """
        return len(self.get_rhyming_lines(max_dist=RHYME_MAX_DIST))
    
    @property
    def is_rhyming(self) -> bool:
        """
        Check if the text is rhyming.

        Returns:
            bool: True if the text is rhyming, False otherwise.
        """
        return self.num_rhyming_lines > 0
    
    def render(
        self, as_str: bool = False, blockquote: bool = False, **meter_kwargs
    ) -> Any:
        """
        Render the parsed text.

        Args:
            as_str (bool): If True, return the result as a string. Default is False.
            blockquote (bool): If True, render as a blockquote. Default is False.
            **meter_kwargs: Additional keyword arguments for meter configuration.

        Returns:
            Any: The rendered text.
        """
        return self.parse(**meter_kwargs).render(as_str=as_str, blockquote=blockquote)


# @stash.stashed_result
def Text(
    txt: str = "",
    fn: str = "",
    lang: Optional[str] = DEFAULT_LANG,
    parent: Optional[Entity] = None,
    children: Optional[list] = [],
    tokens_df: Optional[pd.DataFrame] = None,
):
    return TextModel(
        txt=txt, fn=fn, lang=lang, parent=parent, children=children, tokens_df=tokens_df
    )


class TextList(EntityList):
    pass
