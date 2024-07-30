from .imports import *


class StanzaList(EntityList):
    pass


class LineList(EntityList):
    # def get_rhyming_lines(self, max_dist=RHYME_MAX_DIST):
    #     o = []
    #     done = set()
    #     for i1, line1 in enumerate(self.data):
    #         for i2, line2 in enumerate(self.data):
    #             if (
    #                 i1 < i2
    #                 and len(line1.wordforms)
    #                 and len(line2.wordforms)
    #                 and i1 not in done
    #                 and i2 not in done
    #             ):
    #                 dist = line1.rime_distance(line2)
    #                 if max_dist is None or dist <= max_dist:
    #                     o.append((dist, line1, line2))
    #                     done.update({i1, i2})
    #     return sorted(o, key=lambda x: x[0])
    def get_rhyming_lines(self, max_dist=RHYME_MAX_DIST):
        line2rhyme = defaultdict(list)
        for line in self.data:
            prev_lines = self.data[: line.i]
            if not prev_lines:
                continue
            for line2 in prev_lines:
                dist = line.rime_distance(line2)
                if max_dist is None or dist <= max_dist:
                    line2rhyme[line].append((dist, line2))
        return {i: min(v) for i, v in line2rhyme.items()}


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
    list_type = StanzaList
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
        use_cache=None,
        force=False,
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
            **kwargs: Additional keyword arguments.

        Raises:
            Exception: If neither txt string, filename, nor token dataframe is provided.

        Returns:
            None
        """
        global NUMBUILT
        NUMBUILT += 1
        # print(NUMBUILT,len(txt),txt[:100])
        from .lines import Stanza

        if not txt and not fn and not children and tokens_df is None:
            raise Exception(
                "must provide either txt string or filename or token dataframe"
            )
        txt = get_txt(txt, fn)
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

    def parses_from_cache(self):
        return self.meter.parses_from_cache(self)

    def to_hash(self):
        return hashstr(self._txt)

    def to_json(self):
        return super().to_json(no_txt=True)

    ### parsing ###
    # def set_meter(self, **meter_kwargs):
    #     from .meter import Meter
    #     self._mtr = meter = Meter(**meter_kwargs)
    #     logger.debug(f'set meter to: {meter}')

    def get_meter(self, meter=None, **meter_kwargs):
        from .meter import Meter

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

    def set_meter(self, **meter_kwargs):
        self.get_meter(**meter_kwargs)

    @cached_property
    def meter(self):
        return self.get_meter()

    @property
    def best_parse(self):
        return self.parses.best

    @cached_property
    def parseable_units(self):
        return getattr(self, self.parse_unit_attr)

    def needs_parsing(self, force=False, meter=None, **meter_kwargs):
        from .meter import Meter

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

    # @cache
    def parse(self, **kwargs):
        deque(self.parse_iter(**kwargs), maxlen=0)
        return self._parses

    def render(self, as_str=False, blockquote=False, **meter_kwargs):
        return self.parse(**meter_kwargs).render(as_str=as_str, blockquote=blockquote)

    def reset_meter(self, **meter_kwargs):
        from .meter import DEFAULT_METER_KWARGS

        meter_kwargs = {**DEFAULT_METER_KWARGS, **meter_kwargs}
        self.set_meter(**meter_kwargs)

    def parse_iter(
        self,
        num_proc=DEFAULT_NUM_PROC,
        progress=True,
        force=False,
        meter=None,
        defaults=False,
        **meter_kwargs,
    ):
        from .meter import DEFAULT_METER_KWARGS

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
    def parses(self):
        if not self._parses:
            self.parse()
        return self._parses

    @cache
    def parse_stats(self, norm=False):
        if self.is_parseable:
            return self.parses.stats(norm=norm)
        else:
            return pd.DataFrame(
                line.parse_stats(norm=norm) for line in self.parseable_units
            )

    def to_html(self, as_str=False, blockquote=False):
        return self.parses.to_html(as_str=as_str, blockquote=blockquote)

    def get_rhyming_lines(self, max_dist=RHYME_MAX_DIST):
        return dict(
            x
            for st in self.children
            for x in st.get_rhyming_lines(max_dist=max_dist).items()
        )

    @cached_property
    def rhyming_lines(self):
        return self.get_rhyming_lines()

    @cached_property
    def num_lines(self):
        return len(self.lines)

    @cached_property
    def num_rhyming_lines(self):
        return len(self.get_rhyming_lines(max_dist=RHYME_MAX_DIST))

    @cached_property
    def is_rhyming(self):
        return any([st.is_rhyming for st in self.stanzas])


class Stanza(Text):
    sep: str = ""
    child_type: str = "Line"
    prefix = "stanza"
    list_type = LineList

    @profile
    def __init__(
        self,
        txt: str = "",
        children=[],
        parent=None,
        tokens_df=None,
        lang=DEFAULT_LANG,
        **kwargs,
    ):
        from .lines import Line

        if not txt and not children and tokens_df is None:
            raise Exception("Must provide either txt, children, or tokens_df")
        if not children:
            if tokens_df is None:
                tokens_df = tokenize_sentwords_df(txt)
            children = [
                Line(parent=self, tokens_df=line_df)
                for line_i, line_df in tokens_df.groupby("line_i")
            ]
        Entity.__init__(self, txt, children=children, parent=parent, **kwargs)

    def to_json(self):
        return Entity.to_json(self, no_txt=True)

    def _repr_html_(self, as_df=False, df=None):
        return super()._repr_html_(df=df) if as_df else self.to_html(as_str=True)

    def get_rhyming_lines(self, max_dist=RHYME_MAX_DIST):
        return self.children.get_rhyming_lines(max_dist=max_dist)

    @cached_property
    def num_rhyming_lines(self):
        return len(self.get_rhyming_lines(max_dist=RHYME_MAX_DIST))

    @cached_property
    def is_rhyming(self):
        return self.num_rhyming_lines > 0
