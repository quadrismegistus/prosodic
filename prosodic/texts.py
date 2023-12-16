from .imports import *


class StanzaList(EntityList):
    pass


class LineList(EntityList):
    pass


class Text(Entity):
    """
    Primarily the class one begins from, to create
    a multi-line text in prosodic. You can.

    Arguments:
        Entity -- _description_

    Raises:
        Exception: _description_

    Returns:
        _description_

    Yields:
        _description_
    """

    sep: str = ""
    child_type: str = "Stanza"
    prefix = "text"
    parse_unit_attr = "lines"
    list_type = StanzaList
    use_cache = USE_CACHE

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
        filename: str = "",
        lang: Optional[str] = DEFAULT_LANG,
        parent: Optional[Entity] = None,
        children: Optional[list] = [],
        tokens_df: Optional[pd.DataFrame] = None,
        use_cache=USE_CACHE,
        **kwargs,
    ):
        """
        Initializes an instance of the class.

        Args:
            txt (str): The text string. Default is an empty string.
            filename (str): The name of the file. Default is an empty string.
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
        from .lines import Stanza

        if not txt and not filename and not children and tokens_df is None:
            raise Exception(
                "must provide either txt string or filename or token dataframe"
            )
        txt = get_txt(txt, filename)
        self._txt = txt
        self._fn = filename
        self.lang = lang if lang else detect_lang(txt)
        self.use_cache = use_cache
        if not children:
            with logmap(f"building text with {len(txt.split()):,} words") as lm:
                if self.use_cache:
                    children = self.children_from_json_cache()

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
        if self.use_cache:
            self.to_json_cache()

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
            newmeter = Meter(**{**self._mtr.attrs, **meter_kwargs})
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

    def reset_meter(self, **meter_kwargs):
        from .meter import DEFAULT_METER_KWARGS

        meter_kwargs = {**DEFAULT_METER_KWARGS, **meter_kwargs}
        self.set_meter(**meter_kwargs)

    def parse_iter(
        self,
        num_proc=None,
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
            meter = self.get_meter(meter=meter, **meter_kwargs)
            self.clear_cached_properties()
            yield from meter.parse_iter(
                self, force=force, num_proc=num_proc, progress=progress, **meter_kwargs
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
        html_strs = (
            line.to_html(blockquote=blockquote, as_str=True) for line in self.lines
        )
        html = "</li>\n<li>".join(html_strs)
        html = f'<ol class="parselist"><li>{html}</li></ol>'
        return to_html(html, as_str=as_str)


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
