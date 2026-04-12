from ..imports import *
from ..words import WordTokenList, WordToken
from .syll_df import build_syll_df

NUMBUILT = 0


class TextModel(Entity):
    """
    A class that represents a text structure, comprised of WordTokens.
    """

    is_text = True
    prefix = "text"

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
        if isinstance(children, str):
            txt = children
            children = []

        if not txt and not fn and not children and tokens_df is None:
            raise ValueError(
                "must provide either txt string or filename or token dataframe"
            )
        txt = clean_text(get_txt(txt, fn)).strip()
        lang = lang if lang else detect_lang(txt)

        # store for lazy construction
        self._token_dicts = None
        self._syll_df = None
        self._children_built = bool(children)

        # init entity (sets self.children via property setter below)
        super().__init__(
            children=children,
            txt=txt,
            lang=lang,
            **kwargs,
        )
        self._parse_results = {}
        self._line_parse_results = {}

        if not self._children_built:
            if tokens_df is None:
                token_dicts = list(tokenize_sentwords_iter(txt))
            else:
                token_dicts = [row.to_dict() for _, row in tokens_df.iterrows()]

            self._token_dicts = token_dicts

            # build syllable DataFrame from raw get_word() output (fast)
            self._syll_df = build_syll_df(token_dicts, lang=lang)

            # DON'T build Entity children yet — defer to first access

    def _build_children(self):
        """Lazily construct WordToken Entity objects from stored token dicts."""
        if self._children_built or self._token_dicts is None:
            return
        self._children_built = True
        for d in progress_bar(
            self._token_dicts,
            progress=len(self._token_dicts) >= 1000,
            desc="Building long text",
        ):
            self._children_data.append(WordToken(lang=self.lang, **d))
        if DEFAULT_USE_REGISTRY:
            self.register_objects()

    # property to intercept children access for lazy building
    @property
    def children(self):
        if not self._children_built and self._token_dicts is not None:
            self._build_children()
        return self._children_data

    @children.setter
    def children(self, value):
        self._children_data = value
        if value and len(value) > 0:
            self._children_built = True

    @cached_property
    def stanzas(self):
        from ..texts.stanzas import StanzaList

        return StanzaList.from_wordtokens(self.children, text=self)

    @cached_property
    def lines(self):
        from ..texts.lines import LineList

        lines = LineList.from_wordtokens(self.children, text=self)

        # attach any DF-based parse results to the line entities
        if self._line_parse_results:
            for meter_key, line_results in self._line_parse_results.items():
                for line in lines:
                    line_num = line.num
                    if line_num in line_results:
                        pl = line_results[line_num]
                        # set parent to the line's WordTokenList
                        wt_list = line.children
                        if hasattr(wt_list, '_parses'):
                            pl.parent = wt_list
                            wt_list._parses = pl
                        line._parses = pl

        return lines

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

    def cleanup(self):
        self._parse_results.clear()
        self._parses = None
        for obj in self.iter_all():
            obj.clear_cached_properties()

    def __getitem__(self, item):
        if isinstance(item, slice):
            return self.children[item]
        return super().__getitem__(item)


    @cache
    def parse(
        self,
        combine_by: Literal["line", "sent"] = DEFAULT_COMBINE_BY,
        lim=None,
        force=False,
        meter=None,
        num_proc=None,  # deprecated, ignored
        **meter_kwargs,
    ):
        from ..parsing.parselists import ParseListList

        if combine_by != self.prefix:
            self._parses = ParseListList(parent=self)
        for i,pl in enumerate(self.parse_iter(
            combine_by=combine_by,
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
        if DEFAULT_USE_REGISTRY:
            self._parses.register_objects()
        return self._parses

    def parse_iter(
        self,
        combine_by: Literal["line", "sent"] = DEFAULT_COMBINE_BY,
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
                self, force=force, lim=lim
            ):
                # DF-only path: parse_list.parent may be None
                if parse_list.parent is not None:
                    parsed_ent = self.match(parse_list.parent)
                    parse_list.parent = parsed_ent
                    parsed_ent._parses = parse_list
                else:
                    # DF path: results stored in _line_parse_results,
                    # will be attached to entities when lines are accessed
                    parsed_ent = None

                if not combine_by:
                    self._parse_results[parse_key].append(parse_list)
                    yield parse_list
                elif parsed_ent is not None:
                    this_unit = getattr(parsed_ent, combine_by)
                    if units and not last_unit.equals(this_unit):
                        new_parselist = ParseList.from_combinations(units, parent=last_unit)
                        last_unit._parses = new_parselist
                        self._parse_results[parse_key].append(new_parselist)
                        yield new_parselist
                        units = []
                    units.append(parse_list)
                    last_unit = this_unit
                else:
                    # DF path without combine: just collect
                    self._parse_results[parse_key].append(parse_list)
                    yield parse_list

            if units:
                new_parselist = ParseList.from_combinations(units, parent=last_unit)
                last_unit._parses = new_parselist
                self._parse_results[parse_key].append(new_parselist)
                yield new_parselist

    @property
    def parses(self) -> Any:
        if not self._parses:
            self.parse()
        return self._parses

    @property
    def df(self):
        """The syllable DataFrame — no entity construction needed."""
        return self._syll_df

    def parse_df(self, **meter_kwargs):
        """Parse and return results as a DataFrame. No entity construction.

        Returns a DataFrame with one row per syllable of the best parse per line,
        including meter_val (s/w), violations, and score.
        """
        self.parse(**meter_kwargs)
        if not self._line_parse_results:
            return pd.DataFrame()

        rows = []
        for meter_key, line_results in self._line_parse_results.items():
            for line_num in sorted(line_results.keys()):
                pl = line_results[line_num]
                bp = pl.best_parse
                if bp is None:
                    continue
                for pos in bp.positions:
                    mval = pos.meter_val
                    for slot in pos.children:
                        rows.append({
                            'line_num': line_num,
                            'syll_txt': slot.unit.txt if hasattr(slot.unit, 'txt') else '',
                            'syll_ipa': slot.unit.ipa if hasattr(slot.unit, 'ipa') else '',
                            'meter_val': mval,
                            'is_stressed': slot.unit.is_stressed,
                            'is_prom': slot.is_prom,
                            'score': slot.score,
                            **{f'*{k}': v for k, v in slot.viold.items()},
                        })
        return pd.DataFrame(rows)

    def iter_wordtoken_matrix(self):
        yield from self.wordtokens.iter_wordtoken_matrix()

    @cached_property
    def wordtoken_matrix(self):
        return list(self.iter_wordtoken_matrix())

    def get_parseable_units(self, combine_by: Optional[Literal["line", "sent"]] = DEFAULT_COMBINE_BY):
        return self.get_list(combine_by) if combine_by is not None else self.meter.get_parse_units()

    def get_rhyming_lines(self, max_dist: int = RHYME_MAX_DIST) -> Dict[Any, Any]:
        d={}
        for stanza in self.stanzas:
            d.update(stanza.get_rhyming_lines(max_dist=max_dist))
        return d

    @property
    def num_rhyming_lines(self) -> int:
        return len(self.get_rhyming_lines(max_dist=RHYME_MAX_DIST))

    @property
    def is_rhyming(self) -> bool:
        return self.num_rhyming_lines > 0

    def render(
        self, as_str: bool = False, blockquote: bool = False, **meter_kwargs
    ) -> Any:
        return self.parse(**meter_kwargs).render(as_str=as_str, blockquote=blockquote)


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
