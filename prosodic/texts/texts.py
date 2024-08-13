from ..imports import *

NUMBUILT = 0


class Text(Entity):
    """
    A class that represents a text structure, usually comprised of stanzas.

    This class inherits from the Entity class and is responsible for parsing and managing
    a body of text. It supports caching for efficient retrieval of parsed data and allows
    for text analysis at various granularities.

    Attributes:
        sep (str): Separator string used in text processing. Default is an empty string.
        child_type (str): The type of child entity expected within the text. Default is "Stanza".
        prefix (str): Prefix identifier for the text entity. Default is "text".
        parse_unit_attr (str): Attribute name representing the unit to be parsed. Default is "lines".
        list_type (StanzaList): The class type for containing child entities. Default is StanzaList.
        use_cache (bool): Flag to determine if caching should be used. Default value is taken from USE_CACHE.
        cached_properties_to_clear (list of str): List of property names whose cache should be cleared when appropriate.
    """

    sep: str = ""
    child_type: str = "Stanza"
    prefix = "text"
    parse_unit_attr = "lines"
    list_type = 'StanzaList'
    use_cache = None

    cached_properties_to_clear = [
        "best_parses",
        "all_parses",
        "unbounded_parses",
        "parse_stats",
        "meter",
    ]

    @profile
    def __init__(
        self,
        txt: str = "",
        fn: str = "",
        lang: Optional[str] = DEFAULT_LANG,
        parent: Optional[Entity] = None,
        children: Optional[list] = [],
        tokens_df: Optional[pd.DataFrame] = None,
        use_cache: Optional[bool] = None,
        force: bool = False,
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
        global NUMBUILT
        NUMBUILT += 1
        # print(NUMBUILT,len(txt),txt[:100])
        from .stanzas import Stanza

        if not txt and not fn and not children and tokens_df is None:
            raise Exception(
                "must provide either txt string or filename or token dataframe"
            )
        
        txt = clean_text(get_txt(txt, fn))
        self._txt = txt
        self._fn = fn
        self.lang = lang if lang else detect_lang(txt)
        self.use_cache = use_cache
        was_quiet = logmap.quiet
        if not children:
            numwords = len(txt.split())
            if was_quiet and numwords > 1000:
                logmap.quiet = False
            with logmap(f"building text with {numwords:,} words") as lm:
                if not force and self.use_cache!=False and caching_is_enabled():
                    children = self.children_from_cache()

                if children:
                    lm.log(f"found {len(children)} cached stanzas")
                else:
                    if tokens_df is None:
                        tokens_df = tokenize_sentwords_df(txt)
                    with logmap("building stanzas") as lm2:
                        children = [
                            Stanza(parent=self, tokens_df=stanza_df)
                            for i, stanza_df in lm2.iter_progress(
                                tokens_df.groupby("stanza_i"), desc="iterating stanzas"
                            )
                        ]
        super().__init__(txt, children=children, parent=parent, **kwargs)
        self._parses = []
        self._mtr = None
        if self.use_cache!=False:
            self.cache(force=force)
        if was_quiet:
            logmap.quiet = True

    def __repr__(self):
        if self.is_text:
            l1=self.line1
            o = ' / '.join(x.txt.strip() for x in self.lines[:2])
            o+=f'{" ... " if o else ""}[{self.num_lines} lines]'
            return f'Text({o})'
        else:
            return super().__repr__()
        
    @cached_property
    def sentences(self):
        from ..sents.sents import SentenceList
        return SentenceList(self.wordtokens)
        

    def parses_from_cache(self) -> List[Any]:
        """
        Retrieve parses from cache.

        Returns:
            List[Any]: A list of cached parses.
        """
        if not len(self._parses):
            self.meter.parses_from_cache(self)
        return self._parses

    def to_hash(self) -> str:
        """
        Generate a hash string for the text.

        Returns:
            str: A hash string representation of the text.
        """
        return hashstr(self._txt)

    def to_json(self) -> Dict[str, Any]:
        """
        Convert the text object to JSON format.

        Returns:
            Dict[str, Any]: A JSON representation of the text object.
        """
        return super().to_json(no_txt=True)

    def get_meter(self, meter: Optional[Any] = None, **meter_kwargs) -> Any:
        """
        Get or set the meter for the text.

        Args:
            meter (Optional[Any]): A meter object to set. Default is None.
            **meter_kwargs: Additional keyword arguments for meter configuration.

        Returns:
            Any: The current meter object.
        """
        from ..parsing import Meter

        if meter is not None:
            self._mtr = meter
        elif self._mtr is None:
            if self.text and self.text._mtr is not None:
                self._mtr = self.text._mtr
                logger.trace(f"meter inherited from text: {self._mtr}")
            else:
                self._mtr = Meter(**meter_kwargs)
                logger.trace(f"setting meter to: {self._mtr}")
        elif not meter_kwargs:
            logger.trace(f"no change in meter")
        else:
            # newmeter = Meter(**{**self._mtr.attrs, **meter_kwargs})
            newmeter = Meter(**meter_kwargs)
            if self._mtr.attrs != newmeter.attrs:
                self._mtr = newmeter
                logger.trace(f"resetting meter to: {self._mtr}")
            else:
                logger.trace(f"no change in meter")
        return self._mtr

    def set_meter(self, **meter_kwargs) -> None:
        """
        Set the meter for the text.

        Args:
            **meter_kwargs: Keyword arguments for meter configuration.
        """
        self.get_meter(**meter_kwargs)

    @cached_property
    def meter(self) -> Any:
        """
        Get the meter for the text.

        Returns:
            Any: The current meter object.
        """
        return self.get_meter()

    @property
    def best_parse(self) -> Any:
        """
        Get the best parse for the text.

        Returns:
            Any: The best parse object.
        """
        return self.parses.best_parse
    
    @property
    def best_parses(self) -> Any:
        """
        Get the best parse for the text.

        Returns:
            Any: The best parses.
        """
        return self.parses.best_parses

    @cached_property
    def parseable_units(self) -> Any:
        """
        Get the parseable units for the text.

        Returns:
            Any: The parseable units.
        """
        return getattr(self, self.parse_unit_attr)

    def needs_parsing(self, force: bool = False, meter: Optional[Any] = None, **meter_kwargs) -> bool:
        """
        Check if the text needs parsing.

        Args:
            force (bool): Force parsing regardless of current state. Default is False.
            meter (Optional[Any]): A meter object to compare against. Default is None.
            **meter_kwargs: Additional keyword arguments for meter configuration.

        Returns:
            bool: True if parsing is needed, False otherwise.
        """
        from ..parsing import Meter

        if force:
            return True
        if not self._parses:
            return True
        if not self._mtr:
            return True
        if meter is not None and meter.attrs != self._mtr.attrs:
            return True
        if (
            meter_kwargs
            and Meter(**{**self._mtr.attrs, **meter_kwargs}).attrs != self._mtr.attrs
        ):
            return True
        if not self.is_parseable and self._parses.num_lines != len(
            self.parseable_units
        ):
            return True
        return False

    def parse(self, **kwargs) -> Any:
        """
        Parse the text.

        Args:
            **kwargs: Keyword arguments for parsing configuration.

        Returns:
            Any: The parsed result.
        """
        deque(self.parse_iter(**kwargs), maxlen=0)
        return self._parses

    def render(self, as_str: bool = False, blockquote: bool = False, **meter_kwargs) -> Any:
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

    def reset_meter(self, **meter_kwargs) -> None:
        """
        Reset the meter with new configuration.

        Args:
            **meter_kwargs: Keyword arguments for meter configuration.
        """
        from ..parsing import DEFAULT_METER_KWARGS

        meter_kwargs = {**DEFAULT_METER_KWARGS, **meter_kwargs}
        self.set_meter(**meter_kwargs)

    def parse_iter(
        self,
        num_proc: int = DEFAULT_NUM_PROC,
        progress: bool = True,
        force: bool = False,
        meter: Optional[Any] = None,
        defaults: bool = False,
        **meter_kwargs,
    ) -> Any:
        """
        Parse the text iteratively.

        Args:
            num_proc (int): Number of processes to use for parallel processing. Default is DEFAULT_NUM_PROC.
            progress (bool): If True, show progress. Default is True.
            force (bool): Force parsing regardless of current state. Default is False.
            meter (Optional[Any]): A meter object to use. Default is None.
            defaults (bool): If True, use default meter configuration. Default is False.
            **meter_kwargs: Additional keyword arguments for meter configuration.

        Returns:
            Any: The parsed result.
        """
        from ..parsing import DEFAULT_METER_KWARGS

        if defaults:
            meter_kwargs = {**DEFAULT_METER_KWARGS, **meter_kwargs}
        if self.needs_parsing(force=force, meter=meter, **meter_kwargs):
            with logmap(f"parsing text {self}") as lm:
                meter = self.get_meter(meter=meter, **meter_kwargs)
                self.clear_cached_properties()
                # with logmap.verbosity(
                #     int((len(self.parseable_units) >= 25) or meter.exhaustive)
                # ):
                yield from meter.parse_iter(
                    self,
                    force=force,
                    num_proc=num_proc,
                    progress=progress,
                    **meter_kwargs,
                )
        else:
            yield from self.parseable_units

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

    @cache
    def parse_stats(self, norm: bool = False) -> pd.DataFrame:
        """
        Get the parse statistics for the text.

        Args:
            norm (bool): If True, normalize the statistics. Default is False.

        Returns:
            pd.DataFrame: A DataFrame containing the parse statistics.
        """
        if self.is_parseable:
            return self.parses.stats(norm=norm)
        else:
            return pd.DataFrame(
                line.parse_stats(norm=norm) for line in self.parseable_units
            )

    def to_html(self, as_str: bool = False, blockquote: bool = False) -> Any:
        """
        Convert the parsed text to HTML format.

        Args:
            as_str (bool): If True, return the result as a string. Default is False.
            blockquote (bool): If True, render as a blockquote. Default is False.

        Returns:
            Any: The HTML representation of the parsed text.
        """
        return self.parses.to_html(as_str=as_str, blockquote=blockquote)

    def get_rhyming_lines(self, max_dist: int = RHYME_MAX_DIST) -> Dict[Any, Any]:
        """
        Get rhyming lines from the text.

        Args:
            max_dist (int): Maximum distance for rhyme detection. Default is RHYME_MAX_DIST.

        Returns:
            Dict[Any, Any]: A dictionary of rhyming lines.
        """
        return dict(
            x
            for st in self.children
            for x in st.get_rhyming_lines(max_dist=max_dist).items()
        )

    @cached_property
    def rhyming_lines(self) -> Dict[Any, Any]:
        """
        Get the rhyming lines for the text.

        Returns:
            Dict[Any, Any]: A dictionary of rhyming lines.
        """
        return self.get_rhyming_lines()

    @cached_property
    def num_lines(self) -> int:
        """
        Get the number of lines in the text.

        Returns:
            int: The number of lines.
        """
        return len(self.lines)

    @cached_property
    def num_rhyming_lines(self) -> int:
        """
        Get the number of rhyming lines in the text.

        Returns:
            int: The number of rhyming lines.
        """
        return len(self.get_rhyming_lines(max_dist=RHYME_MAX_DIST))

    @cached_property
    def is_rhyming(self) -> bool:
        """
        Check if the text is rhyming.

        Returns:
            bool: True if the text is rhyming, False otherwise.
        """
        return any([st.is_rhyming for st in self.stanzas])