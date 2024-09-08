from typing import List, Tuple, Dict, Any, Iterator, Optional, Union
from ..imports import *
from .constraints import *
from ..texts import TextModel, Line, Stanza
from .parses import Parse
from .parselists import ParseList
from .utils import *

NUM_GOING = 0
# METER
DEFAULT_METER_KWARGS = dict(
    constraints=DEFAULT_CONSTRAINTS,
    categorical_constraints=DEFAULT_CATEGORICAL_CONSTRAINTS,
    max_s=METER_MAX_S,
    max_w=METER_MAX_W,
    resolve_optionality=METER_RESOLVE_OPTIONALITY,
    exhaustive=False,
    parse_unit='lineparts'
)
MTRDEFAULT = DEFAULT_METER_KWARGS


class Meter(Entity):
    """
    A class representing a metrical parsing system.

    This class implements methods for parsing lines and texts according to
    specified metrical constraints.

    Attributes:
        constraints (list): List of constraint functions to apply.
        categorical_constraints (list): List of categorical constraint functions.
        max_s (int): Maximum number of consecutive strong positions.
        max_w (int): Maximum number of consecutive weak positions.
        resolve_optionality (bool): Whether to resolve optional syllables.
        exhaustive (bool): Whether to perform exhaustive parsing.
    """

    prefix: str = "meter"

    def __init__(
        self,
        constraints: List[Callable] = MTRDEFAULT["constraints"],
        categorical_constraints: List[Callable] = MTRDEFAULT["categorical_constraints"],
        max_s: int = MTRDEFAULT["max_s"],
        max_w: int = MTRDEFAULT["max_w"],
        resolve_optionality: bool = MTRDEFAULT["resolve_optionality"],
        exhaustive: bool = MTRDEFAULT["exhaustive"],
        parse_unit: Literal['lines', 'sentparts', 'lineparts']=MTRDEFAULT['parse_unit'],
        **kwargs: Any
    ) -> None:
        """
        Initialize a Meter object.

        Args:
            constraints (list): List of constraint functions to apply.
            categorical_constraints (list): List of categorical constraint functions.
            max_s (int): Maximum number of consecutive strong positions.
            max_w (int): Maximum number of consecutive weak positions.
            resolve_optionality (bool): Whether to resolve optional syllables.
            exhaustive (bool): Whether to perform exhaustive parsing.
            **kwargs: Additional keyword arguments.
        """
        self.constraints = get_constraints(constraints)
        self.categorical_constraints = get_constraints(categorical_constraints)
        self.max_s = max_s
        self.max_w = max_w
        self.resolve_optionality = resolve_optionality
        self.exhaustive = exhaustive
        self.parse_unit = parse_unit
        super().__init__()

    @property
    def use_cache(self) -> bool:
        """
        Check if caching is enabled.

        Returns:
            bool: True if caching is enabled, False otherwise.
        """
        return caching_is_enabled()

    @property
    def use_cache_lines(self) -> bool:
        """
        Check if line caching is enabled.

        Returns:
            bool: True if line caching is enabled, False otherwise.
        """
        return False

    @property
    def use_cache_texts(self) -> bool:
        """
        Check if text caching is enabled.

        Returns:
            bool: True if text caching is enabled, False otherwise.
        """
        return caching_is_enabled()

    # def to_dict(self) -> Dict[str, Any]:
    #     """
    #     Convert the Meter object to JSON format.

    #     Returns:
    #         dict: JSON representation of the Meter object.
    #     """
    #     return super().to_dict(**self.attrs)

    @cached_property
    def constraint_names(self) -> Tuple[str, ...]:
        """
        Get the names of the constraint functions.

        Returns:
            tuple: Names of the constraint functions.
        """
        return tuple(c.__name__ for c in self.constraints)

    @cached_property
    def categorical_constraint_names(self) -> Tuple[str, ...]:
        """
        Get the names of the categorical constraint functions.

        Returns:
            tuple: Names of the categorical constraint functions.
        """
        return tuple(c.__name__ for c in self.categorical_constraints)

    @cached_property
    def attrs(self) -> Dict[str, Any]:
        """
        Get the attributes of the Meter object.

        Returns:
            dict: Attributes of the Meter object.
        """
        return {
            "constraints": self.constraint_names,
            "categorical_constraints": self.categorical_constraint_names,
            "max_s": self.max_s,
            "max_w": self.max_w,
            "resolve_optionality": self.resolve_optionality,
            "exhaustive": self.exhaustive,
            "parse_unit": self.parse_unit,
        }

    @cache
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

    def get_wordform_matrix(self, wordtokens: WordTokenList) -> List[List['WordForm']]:
        """
        Get the wordform matrix for a given line.

        Args:
            line (Line): The line to process.

        Returns:
            List[List[WordForm]]: The wordform matrix for the line.
        """
        return wordtokens.get_wordform_matrix(
            resolve_optionality=self.resolve_optionality
        )

    def get_parse_units(self, entity: "Entity"):
        try:
            return getattr(entity, self.parse_unit)
        except AttributeError:
            return None


    def parse(self, entity: "Entity", force:bool = False, **kwargs: Any) -> 'ParseList':
        parse_units = self.get_parse_units(entity)
        if parse_units is None:
            log.warning(f'cannot parse {entity}')
            return
        
        return stash.map(
            self.parse_wordtokens,
            parse_units,
            num_proc=1
        )
        


    # @stash.stashed_result
    def parse_wordtokens(self, wordtokens: 'WordTokenList', force: bool = False, **kwargs: Any) -> 'ParseList':
        """
        Parse a wordtoken list.

        Args:
            wordtokens (WordTokenList): The words to parse.
            force (bool, optional): Force parsing even if cached. Defaults to False.
            **kwargs: Additional keyword arguments.

        Returns:
            ParseList: List of parses for the line.
        """
        print('Parsing',wordtokens)
        if wordtokens.num_sylls < 2:
            return ParseList(type="wordtokens", wordtokens=wordtokens)

        if self.exhaustive:
            parses = self.parse_exhaustive(wordtokens)
        else:
            parses = self.parse_fast(wordtokens)

        wordtokens._parses = parses
        return parses


    def parse_fast(self, wordtokens: 'WordTokenList', force: bool = False) -> ParseList:
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

        parses = ParseList(
            [
                Parse(
                    wfl,
                    pos,
                    meter=self,
                    parent=wordtokens,
                )
                for wfl in self.get_wordform_matrix(wordtokens)
                for pos in self.get_pos_types(nsylls=wfl.num_sylls)
            ],
            line=wordtokens,
        )
        for n in range(1000):
            # log.debug(f'Now at {i}A, there are {len(parses)} parses')
            parses = ParseList(
                [
                    newparse
                    for parse in parses
                    for newparse in parse.branch()
                    if not parse.is_bounded
                    and newparse is not None
                    and parse is not None
                ],
                type="wordtokens",
                line=wordtokens,
            )
            parses.bound(progress=False)
            if all(p.is_complete for p in parses):
                break
        else:
            log.error(f"did not complete parsing: {wordtokens}")
        parses.bound(progress=False)
        parses.rank()
        wordtokens._parses = parses
        return wordtokens._parses

    # slower, exhaustive parser

    def parse_exhaustive(self, line: Line, progress: Optional[bool] = None) -> ParseList:
        """
        Parse a line using the exhaustive parsing method.

        Args:
            line (Line): The line to parse.
            progress (bool, optional): Whether to show progress. Defaults to None.

        Returns:
            ParseList: List of parses for the line.
        """
        from .parses import Parse
        from .parselists import ParseList

        assert line.is_parseable

        def iter_parses():
            wfm = self.get_wordform_matrix(line)
            all_parses = []
            combos = [
                (wfl, scansion)
                for wfl in wfm
                for scansion in get_possible_scansions(
                    wfl.num_sylls, max_s=self.max_s, max_w=self.max_w
                )
            ]
            wfl = wfm[0]
            log.trace(
                f"Generated {len(combos)} from a wordfrom matrix of size {len(wfm), wfl, wfl.num_sylls, self.max_s, self.max_s, len(get_possible_scansions(wfl.num_sylls))}"
            )
            iterr = tqdm(combos, disable=not progress, position=0)
            for wfl, scansion in iterr:
                parse = Parse(wfl, scansion, meter=self, parent=line)
                all_parses.append(parse)
            log.trace(f"Returning {len(all_parses)} parses")
            return all_parses

        parses = ParseList(iter_parses(), type="line", line=line)
        parses.bound(progress=False)
        parses.rank()
        line._parses = parses
        return line._parses

    def parse_text(self, text: TextModel, num_proc: int = DEFAULT_NUM_PROC, progress: bool = True) -> None:
        """
        Parse a text.

        Args:
            text (Text): The text to parse.
            num_proc (int, optional): Number of processes to use. Defaults to DEFAULT_NUM_PROC.
            progress (bool, optional): Whether to show progress. Defaults to True.
        """
        iterr = self.parse_text_iter(text, num_proc=num_proc, progress=progress)
        deque(iterr, maxlen=0)

    def parse_text_iter(
        self,
        text: Union[TextModel, Stanza],
        progress: bool = True,
        force: bool = False,
        num_proc: int = DEFAULT_NUM_PROC,
        use_mp: bool = True,
        **kwargs: Any
    ) -> Iterator[Line]:
        """
        Iterator for parsing a text.

        Args:
            text (Text): The text to parse.
            progress (bool, optional): Whether to show progress. Defaults to True.
            force (bool, optional): Force parsing even if cached. Defaults to False.
            num_proc (int, optional): Number of processes to use. Defaults to DEFAULT_NUM_PROC.
            use_mp (bool, optional): Whether to use multiprocessing. Defaults to True.
            **kwargs: Additional keyword arguments.

        Yields:
            Line: Individual lines of the text.
        """
        global NUM_GOING
        NUM_GOING += 1
        # print(NUM_GOING,type(type),text)
        from .parselists import ParseList

        assert type(text) in {TextModel, Stanza}

        done = False
        if not force and self.use_cache_texts and caching_is_enabled():
            parses = self.parses_from_cache(text)
            if parses:
                text._parses = parses
                for st in text:
                    st._parses = ParseList(type="stanza")
                    for l in st:
                        l._parses = ParseList(type="list")
                for parse in parses:
                    if parse.stanza_num:
                        stanza = text.stanzas[parse.stanza_num - 1]
                        stanza._parses.append(parse)
                        line = stanza.lines[parse.line_num - 1]
                        line._parses.append(parse)

                yield from text.parseable_units
                done = True

        if not done:
            text._parses = ParseList(type="text")
            lines = text.parseable_units
            numlines = len(lines)

            # reset parses for stanzas
            for stanza in unique(line.stanza for line in lines):
                stanza._parses = ParseList(type="text")

            # if num_proc is None: num_proc = 1 if numlines<=14 else mp.cpu_count()-1
            if not use_mp:
                num_proc = 1
            if num_proc is None:
                num_proc = mp.cpu_count() // 2 if mp.cpu_count() > 1 else 1
            desc = f"parsing {numlines} {text.parse_unit_attr}"

            if num_proc > 1:
                desc += f" [{num_proc}x]"
            with logmap(desc) as lm:
                if num_proc > 1:
                    iterr = self._parse_text_iter_mp(
                        text,
                        progress=progress,
                        force=force,
                        num_proc=num_proc,
                        lm=lm,
                        desc="parsing",
                    )

                # @TODO: not working?
                else:
                    iterr = (
                        self.parse_line(
                            line,
                            force=force,
                            **kwargs,
                        )
                        for line in lm.iter_progress(
                            text.parseable_units,
                            desc="parsing",
                        )
                    )

                # newstanzas = set()
                for i, parselist in enumerate(iterr):
                    line = text.parseable_units[i]
                    parselist.line = line
                    line._parses = parselist
                    text._parses.extend(parselist)
                    line.stanza._parses.extend(parselist)
                    yield line
                    if line.num and line.stanza and line.stanza.num:
                        # if not line.stanza.num in newstanzas:
                        # newstanzas.add(line.stanza.num)
                        log.debug(
                            f"stanza {line.stanza.num:02}, line {line.num:02}: {line.best_parse.txt if line.best_parse else line.txt}",
                            linelim=70,
                        )

            if self.use_cache_texts and caching_is_enabled():
                self.cache(val_obj=text._parses, key=self.get_key(text))

    def _parse_text_iter_mp(
        self,
        text: TextModel,
        force: bool = False,
        progress: bool = True,
        num_proc: int = DEFAULT_NUM_PROC,
        lm: Optional[Any] = None,
        **progress_kwargs: Any
    ) -> Iterator[ParseList]:
        """
        Helper function for parsing a text in parallel processing.

        Args:
            text (Text): The text to parse.
            force (bool, optional): Force parsing even if cached. Defaults to False.
            progress (bool, optional): Whether to show progress. Defaults to True.
            num_proc (int, optional): Number of processes to use. Defaults to DEFAULT_NUM_PROC.
            lm (logmap, optional): Logmap object. Defaults to None.
            **progress_kwargs: Additional keyword arguments for progress logging.

        Yields:
            ParseList: List of parses for each line.
        """
        from .parselists import ParseList

        assert lm
        objs = [
            (
                line.to_dict(),
                self.to_dict(),
                force or not self.use_cache_lines or not caching_is_enabled(),
            )
            for line in text.parseable_units
        ]
        iterr = lm.imap(
            _parse_iter, objs, progress=progress, num_proc=num_proc, **progress_kwargs
        )
        for i, parselist_json in enumerate(iterr):
            line = text.parseable_units[i]
            yield ParseList.from_dict(parselist_json, line=line)


def _parse_iter(obj: Tuple[Dict[str, Any], Dict[str, Any], bool]) -> Dict[str, Any]:
    line_json, meter_json, force = obj
    line, meter = from_dict(line_json), from_dict(meter_json)
    if not force:
        parse_data = meter.parses_from_cache(line, as_dict=True)
        if parse_data:
            return parse_data

    parses = meter.parse_line(line, force=True)
    return parses.to_dict()
