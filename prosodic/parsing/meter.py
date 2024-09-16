from typing import List, Tuple, Dict, Any, Iterator, Optional, Union
from ..imports import *
from .constraints import *
from .constraint_utils import *
from ..texts import TextModel, Line, Stanza
from .parses import Parse
from .parselists import ParseList
from .utils import *

NUM_GOING = 0
# METER
DEFAULT_METER_KWARGS = dict(
    constraints=DEFAULT_CONSTRAINTS,
    max_s=METER_MAX_S,
    max_w=METER_MAX_W,
    resolve_optionality=METER_RESOLVE_OPTIONALITY,
    exhaustive=False,
    parse_unit="linepart",
)
MTRDEFAULT = DEFAULT_METER_KWARGS


class Meter(Entity):
    """
    A class representing a metrical parsing system.

    This class implements methods for parsing lines and texts according to
    specified metrical constraints.

    Attributes:
        constraints (list): List of constraint functions to apply.
        max_s (int): Maximum number of consecutive strong positions.
        max_w (int): Maximum number of consecutive weak positions.
        resolve_optionality (bool): Whether to resolve optional syllables.
        exhaustive (bool): Whether to perform exhaustive parsing.
    """

    prefix: str = "meter"
    children = None

    def __init__(
        self,
        constraints: List[str] = MTRDEFAULT["constraints"],
        max_s: int = MTRDEFAULT["max_s"],
        max_w: int = MTRDEFAULT["max_w"],
        resolve_optionality: bool = MTRDEFAULT["resolve_optionality"],
        exhaustive: bool = MTRDEFAULT["exhaustive"],
        parse_unit: Literal["line", "sentpart", "linepart"] = MTRDEFAULT["parse_unit"],
        **kwargs: Any,
    ) -> None:
        """
        Initialize a Meter object.

        Args:
            constraints (list): List of constraint functions to apply.
            max_s (int): Maximum number of consecutive strong positions.
            max_w (int): Maximum number of consecutive weak positions.
            resolve_optionality (bool): Whether to resolve optional syllables.
            exhaustive (bool): Whether to perform exhaustive parsing.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(
            constraints=(
                parse_constraint_weights(constraints)
                if not isinstance(constraints, dict)
                else constraints
            ),
            max_s=max_s,
            max_w=max_w,
            resolve_optionality=resolve_optionality,
            exhaustive=exhaustive,
            parse_unit=parse_unit,
        )

    @property
    def key(self):
        if self._key is None:
            self._key = f"{self.nice_type_name}({encode_hash(serialize(self._attrs))})"
        return self._key

    def to_dict(self, incl_attrs=True, **kwargs) -> Dict[str, Any]:
        """
        Convert the Meter object to JSON format.

        Returns:
            dict: JSON representation of the Meter object.
        """
        return super().to_dict(incl_attrs=incl_attrs, **kwargs)

    @cached_property
    def constraint_funcs(self):
        return get_constraints(self.constraints)

    @cached_property
    def parse_constraint_funcs(self):
        return {
            cname: cfunc
            for cname, cfunc in self.constraint_funcs.items()
            if cfunc.scope != "position"
        }

    @cached_property
    def position_constraint_funcs(self):
        return {
            cname: cfunc
            for cname, cfunc in self.constraint_funcs.items()
            if cfunc.scope == "position"
        }

    def get_pos_types(self, nsylls: Optional[int] = None) -> List[str]:
        """
        Get possible position types for a given number of syllables.

        Args:
            nsylls (int, optional): Number of syllables. Defaults to None.

        Returns:
            list: List of possible position types.
        """
        max_w = nsylls if self.max_w is None else self.max_w
        max_s = nsylls if self.max_s is None else self.max_s
        wtypes = ["w" * n for n in range(1, max_w + 1)]
        stypes = ["s" * n for n in range(1, max_s + 1)]
        return wtypes + stypes

    def get_possible_scansions(self, nsylls: int):
        return get_possible_scansions(nsylls, max_s=self.max_s, max_w=self.max_w)

    def get_parse_units(self, entity: "Entity"):
        return entity.get_list(self.parse_unit)

    def is_parse_unit(self, entity):
        return entity.__class__.__name__.lower() == self.parse_unit

    def parse(
        self, entity: "Entity", force: bool = False, num_proc=1, lim=None, **kwargs: Any
    ) -> "ParseList":
        if self.is_parse_unit(entity):
            return self.parse_wordspan(entity, lim=lim)
        else:
            return self.parse_text(entity, lim=lim)

    def parse_text(
        self, text: "WordTokenList", num_proc=1, force: bool = False, lim=None
    ):
        from .parselists import ParseListList

        pll = ParseListList(parent=text)
        for i, pl in enumerate(
            self.parse_text_iter(text, num_proc=num_proc, force=force, lim=lim)
        ):
            pl._num = i + 1
            pll.append(pl)
        pll.register_objects()
        return pll

    def parse_text_iter(
        self, text: "WordTokenList", num_proc=1, force: bool = False, lim=None
    ):
        parse_units = self.get_parse_units(text)
        if parse_units is None:
            log.warning(f"cannot parse {text}")
            return
        if self.exhaustive: num_proc = 1 # @todo fix this
        if num_proc != 0:
            yield from stash.map(
                self.parse_wordspan,
                parse_units.data,
                num_proc=num_proc,
                total=lim,
                _force=force,
                desc=f"Parsing {self.parse_unit}s",
                stash_map=False,
            ).results_iter()
        else:
            for wordtokens in progress_bar(
                parse_units[:lim], desc=f"Parsing {self.parse_unit}s"
            ):
                yield self.parse_wordspan(wordtokens)

    # @stash.stashed_result
    def parse_wordspan(self, wordtokens: "WordTokenList", **kwargs: Any) -> "ParseList":
        """
        Parse a wordtoken list.

        Args:
            wordtokens (WordTokenList): The words to parse.
            force (bool, optional): Force parsing even if cached. Defaults to False.
            **kwargs: Additional keyword arguments.

        Returns:
            ParseList: List of parses for the line.
        """
        # print('Parsing',wordtokens)
        if wordtokens.num_sylls < 2:
            return ParseList(
                wordtokens=wordtokens, type=self.parse_unit, parent=wordtokens
            )

        if self.exhaustive:
            parses = self.parse_exhaustive(wordtokens)
        else:
            parses = self.parse_fast(wordtokens)

        wordtokens._parses = parses
        parses.register_objects()
        return parses

    def get_one_parse(self, wordtokens: "WordTokenList"):
        for wtl in wordtokens.iter_wordtoken_matrix():
            # log.debug(f"Processing wordtoken list: {wtl}")
            for scansion in self.get_pos_types(nsylls=wtl[0].num_sylls):
                # log.debug(f"Creating parse with scansion: {scansion}")
                parse = Parse(
                    wordtokens=wtl,
                    scansion=scansion,
                    meter=self,
                )
                return parse

    # @stash.stashed_result
    def parse_fast(self, wordtokens: "WordTokenList") -> ParseList:
        """
        Parse a line using the fast parsing method.

        Args:
            line (Line): The line to parse.
            force (bool, optional): Force parsing even if cached. Defaults to False.

        Returns:
            ParseList: List of parses for the line.
        """
        from .parses import Parse
        from .parselists import ParseList

        # log.debug(f"Starting parse_fast for wordtokens: {wordtokens}")
        parses = []
        for wtl in wordtokens.iter_wordtoken_matrix():
            # log.info(f"Processing wordtoken list: {wtl.sylls}")
            for scansion in self.get_pos_types(nsylls=wtl[0].num_sylls):
                # log.debug(f"Creating parse with scansion: {scansion}")
                parse = Parse(
                    wordtokens=wtl,
                    scansion=scansion,
                    meter=self,
                )
                parses.append(parse)
            if not self.resolve_optionality:
                # log.info("Breaking loop as resolve_optionality is False")
                break

        # log.debug(f"Created initial ParseList with {len(parses)} parses")
        parses = ParseList(parses, parse_unit=self.parse_unit, parent=wordtokens)
        for n in range(1000):
            # log.debug(f"Starting iteration {n} of parse branching")
            parses = ParseList(
                [
                    newparse
                    for parse in parses
                    for newparse in parse.branch()
                    if not parse.is_bounded
                    and newparse is not None
                    and parse is not None
                ],
                parse_unit=self.parse_unit,
                parent=wordtokens,
            )
            # log.debug(f"After branching, ParseList has {len(parses)} parses")
            parses.bound(progress=False)
            if all(p.is_complete for p in parses):
                # log.debug("All parses are complete, breaking loop")
                break
        else:
            log.error(f"did not complete parsing: {wordtokens}")

        # log.debug("Performing final bound and rank operations")
        parses.bound(progress=False)
        parses.rank()
        wordtokens._parses = parses
        # log.debug(f"Returning ParseList with {len(parses)} parses")
        return wordtokens._parses

    # slower, exhaustive parser

    # def parse_exhaustive(self, line: Line, progress: Optional[bool] = None) -> ParseList:
    #     """
    #     Parse a line using the exhaustive parsing method.

    #     Args:
    #         line (Line): The line to parse.
    #         progress (bool, optional): Whether to show progress. Defaults to None.

    #     Returns:
    #         ParseList: List of parses for the line.
    #     """
    #     from .parses import Parse
    #     from .parselists import ParseList

    #     assert line.is_parseable

    #     def iter_parses():
    #         wfm = self.get_wordform_matrix(line)
    #         all_parses = []
    #         combos = [
    #             (wfl, scansion)
    #             for wfl in wfm
    #             for scansion in get_possible_scansions(
    #                 wfl.num_sylls, max_s=self.max_s, max_w=self.max_w
    #             )
    #         ]
    #         wfl = wfm[0]
    #         log.trace(
    #             f"Generated {len(combos)} from a wordfrom matrix of size {len(wfm), wfl, wfl.num_sylls, self.max_s, self.max_s, len(get_possible_scansions(wfl.num_sylls))}"
    #         )
    #         iterr = tqdm(combos, disable=not progress, position=0)
    #         for wfl, scansion in iterr:
    #             parse = Parse(wfl, scansion, meter=self, parent=line)
    #             all_parses.append(parse)
    #         log.trace(f"Returning {len(all_parses)} parses")
    #         return all_parses

    #     parses = ParseList(iter_parses(), type="line", parent=line)
    #     parses.bound(progress=False)
    #     parses.rank()
    #     line._parses = parses
    #     return line._parses

    def parse_exhaustive(
        self, wordtokens: "WordTokenList", progress: Optional[bool] = None
    ) -> ParseList:
        """
        Parse a line using the fast parsing method.

        Args:
            line (Line): The line to parse.
            force (bool, optional): Force parsing even if cached. Defaults to False.

        Returns:
            ParseList: List of parses for the line.
        """
        from .parses import Parse
        from .parselists import ParseList

        # log.debug(f"Starting parse_fast for wordtokens: {wordtokens}")
        parses = []
        for wtl in wordtokens.iter_wordtoken_matrix():
            for scansion in progress_bar(
                self.get_possible_scansions(nsylls=wtl.num_sylls),
                desc=f"Parsing {self.parse_unit}s",
                disable=not progress,
            ):
                parse = Parse(
                    wordtokens=wtl,
                    scansion=scansion,
                    meter=self,
                )
                parses.append(parse)
            if not self.resolve_optionality:
                break

        parses = ParseList(parses, parse_unit=self.parse_unit, parent=wordtokens)

        parses.bound(progress=False)
        parses.rank()
        wordtokens._parses = parses
        return wordtokens._parses
