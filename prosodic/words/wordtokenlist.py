from . import *


class WordTokenList(EntityList):
    """A list of WordToken objects."""

    def __init__(
        self,
        children: List["WordToken"],
        parent=None,
        text=None,
        num=None,
        lang=DEFAULT_LANG,
        **kwargs,
    ):
        # print([type(self), type(children), parent, kwargs,'!!!'])
        assert all([isinstance(wt, WordToken) for wt in children])
        self._parses = None
        self._parsed = {}
        self._mtr = None
        super().__init__(children=children, text=text, parent=parent, num=num, **kwargs)

    @classmethod
    def _from_wordtokens(cls, wordtokens, list_type, list_num, text=None):
        from ..imports import get_list_class, get_ent_class

        list_class = get_list_class(list_type)
        ent_class = get_ent_class(list_type)
        return list_class(
            [
                ent_class(children=list(group), text=text, num=i + 1)
                for i, (_, group) in enumerate(
                    itertools.groupby(wordtokens, key=lambda x: getattr(x, list_num))
                )
            ],
            parent=wordtokens,
            text=text,
        )

    @property
    def words(self):
        return self

    def to_dict(self, incl_children=False, **kwargs):
        return {
            self.__class__.__name__: {
                "children": [wtok.to_dict(incl_children=incl_children) for wtok in self]
            }
        }

    @property
    def nums(self):
        return [wtok.num for wtok in self]

    @property
    def numset(self):
        return set(self.nums)

    @property
    def is_sent_parsed(self):
        l = self.children
        if not l:
            return False
        return all(wt.preterm for wt in l)

    @property
    def trees(self):
        return self.sents.trees

    @property
    def grid(self):
        from ..sents.grids import SentenceGrid

        return SentenceGrid.from_wordtokens(self, text=self.text)

    @property
    def num_with_forms(self):
        return len([tok for tok in self if tok.has_wordform])

    def iter_wordtoken_matrix(self):
        tokens_with_wf = [tok for tok in self if tok.has_wordform]
        tokens_with_wfl = [tok.wordforms for tok in tokens_with_wf]
        for wfl in itertools.product(*tokens_with_wfl):
            wtl = self.copy()
            for i, wf in enumerate(wfl):
                wtok = tokens_with_wf[i]
                wtok_match = next(w for w in wtl if w.num == wtok.num)
                wtok_match.wordtype.children = WordFormList(
                    [wf], parent=wtok_match.wordtype
                )
            yield wtl

    # @log.info
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
                self.text._mtr = self._mtr = Meter(**meter_kwargs)
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

    @property
    def key(self):
        return f'{self.text.key+"." if self.text and self.text is not self else ""}{self.nice_type_name}{self.num}'
        

    @property
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

    @property
    def parseable_units(self) -> Any:
        """
        Get the parseable units for the text.

        Returns:
            Any: The parseable units.
        """
        return getattr(self, self.parse_unit_attr)

    def parse(self, num_proc=None, force=False, meter=None, **meter_kwargs):
        """
        Parse the text.

        Args:
            **kwargs: Keyword arguments for parsing configuration.

        Returns:
            Any: The parsed result.
        """
        from ..parsing.parselists import ParseList
        self._parses = ParseList.from_combinations(
            self.parse_iter(
                num_proc=num_proc,
                force=force,
                meter=meter,
                **meter_kwargs,
            ),
            parent=self
        )
        return self._parses

    def parse_iter(self, num_proc=None, force=False, meter=None, **meter_kwargs):
        meter = self.get_meter(meter=meter, **meter_kwargs)
        for parse_list in meter.parse_text_iter(self, num_proc=num_proc, force=force):
            parsed_ent = self.match(parse_list.parent, parse_list.parse_unit)
            parse_list.parent = parsed_ent
            parsed_ent._parses = parse_list
            yield parse_list

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

    @property
    def rhyming_lines(self) -> Dict[Any, Any]:
        """
        Get the rhyming lines for the text.

        Returns:
            Dict[Any, Any]: A dictionary of rhyming lines.
        """
        return self.get_rhyming_lines()

    @property
    def num_lines(self) -> int:
        """
        Get the number of lines in the text.

        Returns:
            int: The number of lines.
        """
        return len(self.lines)

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
        return any([st.is_rhyming for st in self.stanzas])