from . import *


class WordTokenList(EntityList):
    """A list of WordToken objects."""

    def __init__(
        self,
        children: List["WordToken"] = [],
        parent=None,
        text=None,
        num=None,
        lang=DEFAULT_LANG,
        **kwargs,
    ):
        # print([type(self), type(children), parent, kwargs,'!!!'])
        if not all([isinstance(wt, WordToken) for wt in children]):
            raise ValueError("All children must be WordToken objects")
        self._parses = None
        self._parse_results = {}
        self._mtr = None
        super().__init__(children=children, text=text, parent=parent, num=num, **kwargs)

    @classmethod
    def _from_wordtokens(cls, wordtokens, list_type, list_num, text=None):
        from ..imports import get_list_class, get_ent_class

        list_class = get_list_class(list_type)
        ent_class = get_ent_class(list_type)
        new_list = list_class(parent=text)
        for _, group in itertools.groupby(wordtokens, key=lambda x: getattr(x, list_num)):
            ent_list = ent_class(parent=new_list)
            for ent in group:
                ent_list.append(ent)
            new_list.append(ent_list)
        return new_list

    @property
    def words(self):
        return self

    @property
    def txt(self):
        return "".join(wt.txt for wt in self)

    def __getstate__(self):
        print(f"Pickling WordTokenList: _key = {getattr(self, '_key', 'Not set')}")
        state = self.__dict__.copy()
        return state

    def __setstate__(self, state):
        print(f"Unpickling WordTokenList: _key in state = {state.get('_key', 'Not set')}")
        self.__dict__.update(state)

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
        # for every combination of wordforms...
        for _i,wfl in enumerate(itertools.product(*tokens_with_wfl)):
            # copy the wordtokenlist
            wtl = self.copy()
            # for each wordform in the combination, assign it to the corresponding wordtoken
            for i, wf in enumerate(wfl):
                # get the wordtoken that corresponds to the wordform
                wtok = tokens_with_wf[i]
                # get the wordtoken in the copy of the wordtokenlist that corresponds to the wordform
                wtok_match = next(w for w in wtl if w.num == wtok.num)
                # assign the wordform to the wordtoken
                wtype = wtok_match.wordtype
                wtype.children = WordFormList([wf], parent=wtype)
            yield wtl

    @cached_property
    def wordtoken_matrix(self):
        return list(self.iter_wordtoken_matrix())

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

    def parse(self, *args, **kwargs):
        """
        Parse the text.

        Args:
            **kwargs: Keyword arguments for parsing configuration.

        Returns:
            Any: The parsed result.
        """
        from ..texts import TextModel
        return TextModel.parse(self, *args, **kwargs)
        # from ..parsing.parselists import ParseList
        # self._parses = ParseList.from_combinations(
        #     self.parse_iter(
        #         num_proc=num_proc,
        #         force=force,
        #         meter=meter,
        #         **meter_kwargs,
        #     ),
        #     parent=self
        # )
        # return self._parses

    def parse_iter(self, *args, **kwargs):
        from ..texts import TextModel
        yield from TextModel.parse_iter(self, *args, **kwargs)
        # meter = self.get_meter(meter=meter, **meter_kwargs)
        # for parse_list in meter.parse_text_iter(self, num_proc=num_proc, force=force):
        #     parsed_ent = self.match(parse_list.parent, parse_list.parse_unit)
        #     parse_list.parent = parsed_ent
        #     parsed_ent._parses = parse_list
        #     yield parse_list

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

    # def get_rhyming_lines(self, max_dist: int = RHYME_MAX_DIST) -> Dict[Any, Any]:
    #     """
    #     Get rhyming lines from the text.

    #     Args:
    #         max_dist (int): Maximum distance for rhyme detection. Default is RHYME_MAX_DIST.

    #     Returns:
    #         Dict[Any, Any]: A dictionary of rhyming lines.
    #     """
    #     return dict(
    #         x
    #         for st in self.children
    #         for x in st.get_rhyming_lines(max_dist=max_dist).items()
    #     )

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

