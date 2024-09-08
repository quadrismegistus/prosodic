from ..imports import *
from ..words import WordTokenList, WordToken

NUMBUILT = 0


class TextModel(WordTokenList):
    """
    A class that represents a text structure, comprised of WordTokens.
    """
    is_text = True
    prefix = "text"

    @log.debug
    def __init__(
        self,
        txt: str = None,
        fn: str = None,
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
        if not txt and not fn and not children and tokens_df is None:
            raise ValueError(
                "must provide either txt string or filename or token dataframe"
            )
        self._text = None

        log.debug("Cleaning and getting text")
        txt = clean_text(get_txt(txt, fn))

        log.debug(f"Cleaned text: {txt[:100]}...")

        self._txt = txt
        self._fn = fn

        log.debug(f"Setting language: {lang}")

        self.lang = lang if lang else detect_lang(txt)
        log.debug(f"Language set to: {self.lang}")

        self.use_cache = use_cache
        log.debug(f"Use cache set to: {self.use_cache}")

        was_quiet = logmap.quiet
        log.debug(f"Was quiet: {was_quiet}")

        if not children:
            log.debug("No children provided, processing text")

            numwords = len(txt.split())
            log.debug(f"Number of words: {numwords}")

            if was_quiet and numwords > 1000:
                log.debug("Setting logmap to not quiet due to large text")
                logmap.quiet = False

            log.debug(f"building text with {numwords:,} words")
            if tokens_df is None:
                log.debug("Tokenizing text into DataFrame")
                tokens_df = tokenize_sentwords_df(txt)
            children = [
                WordToken(lang=self.lang, parent=self, text=self, **row.to_dict())
                for _, row in tokens_df.iterrows()
            ]
        log.debug("Initializing parent class")
        super().__init__(children=children, parent=parent, text=self, **kwargs)

    

    @cached_property
    def stanzas(self):
        from ..texts.stanzas import StanzaList
        return StanzaList.from_wordtokens(self, text=self)
    
    @cached_property
    def lines(self):
        from ..texts.lines import LineList
        return LineList.from_wordtokens(self, text=self)
    
    @cached_property
    def lineparts(self):
        from ..texts.lines import LinePartList
        return LinePartList.from_wordtokens(self, text=self)
    
    @cached_property
    def sents(self):
        from ..sents.sents import SentenceList
        return SentenceList.from_wordtokens(self, text=self)
    
    @cached_property
    def sentparts(self):
        from ..sents.sents import SentPartList
        return SentPartList.from_wordtokens(self, text=self)




    # def __repr__(self):
    #     o = " / ".join(x.txt.strip() for x in self.lines[:2])
    #     o += f'{" ... " if o else ""}[{self.num_lines} lines]'
    #     return f"Text({o})"

    # @cached_property
    # def sents(self):
    #     from ..sents import SentenceList

    #     return SentenceList.from_wordtokens(self.wordtokens)

    def to_hash(self) -> str:
        """
        Generate a hash string for the text.

        Returns:
            str: A hash string representation of the text.
        """
        return hashstr(self._txt)

    # def to_dict(self) -> Dict[str, Any]:
    #     """
    #     Convert the text object to JSON format.

    #     Returns:
    #         Dict[str, Any]: A JSON representation of the text object.
    #     """
    #     return super().to_dict(no_txt=True)

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
                log.trace(f"meter inherited from text: {self._mtr}")
            else:
                self._mtr = Meter(**meter_kwargs)
                log.trace(f"setting meter to: {self._mtr}")
        elif not meter_kwargs:
            log.trace(f"no change in meter")
        else:
            # newmeter = Meter(**{**self._mtr.attrs, **meter_kwargs})
            newmeter = Meter(**meter_kwargs)
            if self._mtr.attrs != newmeter.attrs:
                self._mtr = newmeter
                log.trace(f"resetting meter to: {self._mtr}")
            else:
                log.trace(f"no change in meter")
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

    def needs_parsing(
        self, force: bool = False, meter: Optional[Any] = None, **meter_kwargs
    ) -> bool:
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

    @stash.stashed_result
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

    def reset_meter(self, **meter_kwargs) -> None:
        """
        Reset the meter with new configuration.

        Args:
            **meter_kwargs: Keyword arguments for meter configuration.
        """
        from ..parsing import DEFAULT_METER_KWARGS

        meter_kwargs = {**DEFAULT_METER_KWARGS, **meter_kwargs}
        self.set_meter(**meter_kwargs)

    def parse_iter_mtr(
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


@stash.stashed_result
def Text(
    txt: str = "",
    fn: str = "",
    lang: Optional[str] = DEFAULT_LANG,
    parent: Optional[Entity] = None,
    children: Optional[list] = [],
    tokens_df: Optional[pd.DataFrame] = None,
):
    return TextModel(txt, fn, lang, parent, children, tokens_df)


class TextList(EntityList):
    pass
