from ..imports import *
from .constraints import *
from .utils import *
from .positions import *
from .slots import *

@total_ordering
class Parse(Entity):
    """
    Represents a metrical parse of a line of text.

    Attributes:
        prefix (str): The prefix used for naming this entity type.
        positions (List[ParsePosition]): List of metrical positions in the parse.
        meter_obj (Meter): The meter object associated with this parse.
        meter (Meter): Alias for meter_obj.
        wordforms (WordFormList): List of word forms in the parse.
        line (Line): The line object this parse is associated with.
        is_bounded (bool): Whether this parse is bounded.
        bounded_by (List): List of constraints that bound this parse.
        unmetrical (bool): Whether this parse is unmetrical.
        comparison_nums (set): Set of comparison numbers.
        comparison_parses (List[Parse]): List of comparison parses.
        parse_num (int): The number of this parse.
        total_score (Optional[float]): The total score of this parse.
        pause_comparisons (bool): Whether to pause comparisons.
        parse_rank (Optional[int]): The rank of this parse.
        num_slots_positioned (int): Number of slots positioned in this parse.
        _line_num (Optional[int]): The line number.
        _stanza_num (Optional[int]): The stanza number.
        _line_txt (str): The text of the line.

    Args:
        wordforms_or_str (Union[str, List, WordFormList]): The word forms or string to parse.
        scansion (str): The scansion string.
        meter (Optional[Meter]): The meter to use for parsing.
        parent (Optional[Any]): The parent object of this parse.
        positions (Optional[List[ParsePosition]]): List of parse positions.
        is_bounded (bool): Whether this parse is bounded.
        bounded_by (Optional[List]): List of constraints that bound this parse.
        rank (Optional[int]): The rank of this parse.
        line_num (Optional[int]): The line number.
        stanza_num (Optional[int]): The stanza number.
        line_txt (str): The text of the line.
    """

    prefix: str = "parse"

    def __init__(
        self,
        wordforms_or_str: Union[str, List, "WordFormList"],
        scansion: str = "",
        meter: Optional["Meter"] = None,
        parent: Optional[Any] = None,
        positions: Optional[List["ParsePosition"]] = None,
        is_bounded: bool = False,
        bounded_by: Optional[List] = None,
        rank: Optional[int] = None,
        line_num: Optional[int] = None,
        stanza_num: Optional[int] = None,
        line_txt: str = "",
    ) -> None:
        from .meter import Meter

        if not positions:
            positions = []
        self.positions = positions

        # meter
        if meter is None:
            meter = Meter()
        self.meter_obj = self.meter = meter

        # wordforms
        assert wordforms_or_str
        if hasattr(wordforms_or_str, "is_parseable") and wordforms_or_str.is_parseable:
            parent = wordforms_or_str
            self.wordforms = meter.get_wordform_matrix(parent)[0]
        elif type(wordforms_or_str) == str:
            parent = Line(wordforms_or_str)
            self.wordforms = meter.get_wordform_matrix(parent)[0]
        elif type(wordforms_or_str) == list:
            from ..words import WordFormList
            self.wordforms = WordFormList(wordforms_or_str)
        else:
            self.wordforms = wordforms_or_str

        # slots
        # self.slots = [ParseSlot(slot) for slot in self.wordforms.slots]
        # self.slots = self.wordforms.slots

        # scansion
        if not scansion:
            scansion = get_iambic_parse(len(self.wordforms.slots))
        if type(scansion) == str:
            scansion = split_scansion(scansion)
        self.positions_ls = copy(scansion)

        # divide positions
        self.line = parent
        self.is_bounded = is_bounded
        self.bounded_by = [] if not bounded_by else [x for x in bounded_by]
        self.unmetrical = False
        self.comparison_nums = set()
        self.comparison_parses = []
        self.parse_num = 0
        self.total_score = None
        self.pause_comparisons = False
        self.parse_rank = rank
        # self.violset=Multiset()
        self.num_slots_positioned = 0
        self._line_num = line_num
        self._stanza_num = stanza_num
        self._line_txt = line_txt
        if not positions:
            super().__init__(children=[], parent=parent)
            for mpos_str in self.positions_ls:
                self.extend(mpos_str)
        else:
            super().__init__(children=positions, parent=parent)
        self.children = self.positions
        self.init()

    @property
    def line_num(self) -> Optional[int]:
        """
        Get the line number.

        Returns:
            Optional[int]: The line number.
        """
        return self.line.num if self.line else self._line_num

    @property
    def stanza_num(self) -> Optional[int]:
        """
        Get the stanza number.

        Returns:
            Optional[int]: The stanza number.
        """
        return self.stanza.num if self.line else self._stanza_num

    def init(self) -> None:
        """Initialize the parse positions."""
        for pos in self.positions:
            pos.parse = self
            pos.init()

    def to_json(self, fn: Optional[str] = None) -> Dict[str, Any]:
        """
        Convert the parse to a JSON-serializable dictionary.

        Args:
            fn (Optional[str]): Filename to save the JSON to.

        Returns:
            Dict[str, Any]: JSON-serializable dictionary representation of the parse.
        """
        return to_json(
            {
                "_class": self.__class__.__name__,
                **self.attrs,
                "children": [pos.to_json() for pos in self.positions],
                "_wordforms": self.wordforms.to_json(),
                "_meter": self.meter_obj.to_json(),
                "is_bounded": self.is_bounded,
                "bounded_by": list(self.bounded_by),
            },
            fn=fn,
        )

    @staticmethod
    def from_json(json_d: Dict[str, Any], line: Optional[Union["Text", "Stanza", "Line"]] = None) -> "Parse":
        """
        Create a Parse object from a JSON dictionary.

        Args:
            json_d (Dict[str, Any]): JSON dictionary representation of the parse.
            line (Optional[Union[Text, Stanza, Line]]): The line object to associate with the parse.

        Returns:
            Parse: A new Parse object created from the JSON data.
        """
        from ..texts import Line

        wordforms = from_json(json_d["_wordforms"])
        if line:
            if type(line) == Text:
                line = line.stanzas[json_d["stanza_num"] - 1].lines[
                    json_d["line_num"] - 1
                ]
            elif type(line) == Stanza:
                line = line.lines[json_d["line_num"] - 1]
            elif type(line) != Line:
                raise Exception(f"what is {line}?")
            wordforms = line.match_wordforms(wordforms)
        meter = from_json(json_d["_meter"])
        positions = [from_json(d) for d in json_d["children"]]
        slots = [slot for pos in positions for slot in pos.slots]
        sylls = [syll for word in wordforms for syll in word.children]
        assert len(slots) == len(sylls)
        for syll, slot in zip(sylls, slots):
            slot.unit = syll
        return Parse(
            wordforms,
            positions=positions,
            parent=line,
            meter=meter,
            is_bounded=json_d["is_bounded"],
            bounded_by=json_d["bounded_by"],
            rank=json_d["rank"],
            line_num=json_d["line_num"],
            stanza_num=json_d["stanza_num"],
        )

    @property
    def slots(self) -> List["ParseSlot"]:
        """
        Get all slots in the parse.

        Returns:
            List[ParseSlot]: List of all slots in the parse.
        """
        return [slot for mpos in self.positions for slot in mpos.slots]

    @property
    def is_complete(self) -> bool:
        """
        Check if the parse is complete.

        Returns:
            bool: True if the parse is complete, False otherwise.
        """
        return len(self.slots) == len(self.syllables)

    def extend(self, mpos_str: str) -> Optional["Parse"]:
        """
        Extend the parse with a new metrical position.

        Args:
            mpos_str (str): String representation of the metrical position to add.

        Returns:
            Optional[Parse]: The extended parse, or None if extension is not possible.
        """
        slots = []
        mval = mpos_str[0]
        if self.positions and self.positions[-1].meter_val == mval:
            # logger.warning(f'cannnot extend because last position is also {mval}')
            return None

        for i, x in enumerate(mpos_str):
            slot_i = self.num_slots_positioned
            try:
                slot = self.wordforms.slots[slot_i]
            except IndexError:
                # logger.warning('cannot extend further, already taking up all syllable slots')
                return None

            slots.append(ParseSlot(slot, num=slot_i + 1))
            self.num_slots_positioned += 1

        mpos = ParsePosition(
            meter_val=mval, children=slots, parent=self, num=len(self.positions) + 1
        )
        self.positions.append(mpos)
        self.constraint_viols  # init and bound
        return self

    @property
    def violset(self) -> Multiset:
        """
        Get the set of constraint violations for this parse.

        Returns:
            Multiset: A multiset of constraint violations.
        """
        s = Multiset()
        for mpos in self.positions:
            s.update(mpos.violset)
        return s

    def __copy__(self) -> "Parse":
        """
        Create a shallow copy of the parse.

        Returns:
            Parse: A shallow copy of the parse.
        """
        new = Parse(
            wordforms_or_str=self.wordforms,
            scansion=self.positions_ls,
            meter=self.meter,
            parent=self.parent,
            positions=[copy(mpos) for mpos in self.positions],
        )
        new._attrs = copy(self._attrs)
        new.is_bounded = self.is_bounded
        new.num_slots_positioned = self.num_slots_positioned
        # new.violset = copy(self.violset)
        return new

    def branch(self) -> List["Parse"]:
        """
        Create branching parses from this parse.

        Returns:
            List[Parse]: List of branching parses.
        """
        if self.is_bounded:
            return []
        if not self.positions:
            logger.error("needs to start with some positions")
            return
        mval = self.positions[-1].meter_val
        otypes = self.meter.get_pos_types(self.wordforms.num_sylls)
        otypes = [x for x in otypes if x[0] != mval]
        o = [copy(self).extend(posstr) for posstr in otypes]
        o = [x for x in o if x is not None]
        o = o if o else [self]
        o = [p for p in o if not p.is_bounded]
        return o

    @property
    def is_complete(self) -> bool:
        """
        Check if the parse is complete.

        Returns:
            bool: True if the parse is complete, False otherwise.
        """
        return self.num_slots_positioned == len(self.wordforms.slots)

    @property
    def sort_key(self) -> tuple:
        """
        Get the sort key for this parse.

        Returns:
            tuple: A tuple used for sorting parses.
        """
        return (
            self.stanza_num,
            self.line_num,
            int(bool(self.is_bounded)),
            self.score,
            self.positions[0].is_prom if self.positions else 10,
            self.average_position_size,
            self.num_stressed_sylls,
            self.meter_ints,
            self.stress_ints,
        )

    @cached_property
    def constraints(self) -> List[Callable]:
        """
        Get the list of constraints for this parse.

        Returns:
            List[Callable]: List of constraint functions.
        """
        return self.meter.constraints + self.meter.categorical_constraints

    @cached_property
    def constraint_d(self) -> Dict[str, Callable]:
        """
        Get a dictionary of constraints keyed by their names.

        Returns:
            Dict[str, Callable]: Dictionary of constraints.
        """
        return dict((c.__name__, c) for c in self.constraints)

    @cached_property
    def categorical_constraint_d(self) -> Dict[str, Callable]:
        """
        Get a dictionary of categorical constraints keyed by their names.

        Returns:
            Dict[str, Callable]: Dictionary of categorical constraints.
        """
        return dict((c.__name__, c) for c in self.meter.categorical_constraints)

    def __lt__(self, other: "Parse") -> bool:
        """
        Compare this parse to another parse.

        Args:
            other (Parse): The other parse to compare to.

        Returns:
            bool: True if this parse is less than the other parse, False otherwise.
        """
        return self.sort_key < other.sort_key

    def __eq__(self, other: object) -> bool:
        """
        Check if this parse is equal to another parse.

        Args:
            other (object): The other object to compare to.

        Returns:
            bool: True if the parses are equal, False otherwise.
        """
        # logger.error(f'{self} and {other} could not be compared in sort, ended up equal')
        # return not (self<other) and not (other<self)
        return self is other

    def can_compare(self, other: "Parse", min_slots: int = 4) -> bool:
        """
        Check if this parse can be compared to another parse.

        Args:
            other (Parse): The other parse to compare to.
            min_slots (int): Minimum number of slots required for comparison.

        Returns:
            bool: True if the parses can be compared, False otherwise.
        """
        if (self.stanza_num, self.line_num) != (other.stanza_num, other.line_num):
            return False

        if min_slots and self.num_slots_positioned < min_slots:
            return False

        if self.is_complete and other.is_complete:
            return True

        if self.num_slots_positioned != other.num_slots_positioned:
            return False

        return True

    @cached_property
    def txt(self) -> str:
        """
        Get the text representation of the parse.

        Returns:
            str: Text representation of the parse.
        """
        return " ".join(m.txt for m in self.positions)

    @property
    def num_stressed_sylls(self) -> int:
        """
        Get the number of stressed syllables in the parse.

        Returns:
            int: Number of stressed syllables.
        """
        return len(
            [slot for mpos in self.positions for slot in mpos.slots if slot.is_stressed]
        )

    @property
    def num_sylls(self) -> int:
        """
        Get the total number of syllables in the parse.

        Returns:
            int: Total number of syllables.
        """
        return len(self.slots)

    @property
    def num_words(self) -> int:
        """
        Get the number of words in the parse.

        Returns:
            int: Number of words.
        """
        return len(self.wordforms)

    @property
    def num_peaks(self) -> int:
        """
        Get the number of metrical peaks in the parse.

        Returns:
            int: Number of metrical peaks.
        """
        return len([mpos for mpos in self.positions if mpos.is_prom])

    @property
    def is_rising(self) -> Optional[bool]:
        """
        Check if the parse has a rising rhythm.

        Returns:
            Optional[bool]: True if rising, False if falling, None if undetermined.
        """
        if not self.positions:
            return
        # return not self.positions[0].is_prom
        try:
            if self.nary_feet == 3:
                if self.slots[3].is_prom:
                    return False  # swws
                else:
                    return True  # wssw
            elif self.nary_feet == 2:
                if self.slots[3].is_prom:
                    return True  # wsws
                else:
                    return False  # swsw
        except (IndexError, AttributeError):
            pass
        return not self.positions[0].is_prom

    @property
    def nary_feet(self) -> int:
        """
        Get the n-ary foot type of the parse.

        Returns:
            int: The n-ary foot type (2 for binary, 3 for ternary, etc.).
        """
        return int(np.median(self.foot_sizes))

    @property
    def feet(self) -> List[str]:
        """
        Get the list of feet in the parse.

        Returns:
            List[str]: List of feet as strings.
        """
        if self.num_positions == 1:
            feet = [self.positions[0].meter_str]
        else:
            feet = []
            for i in range(1, self.num_positions, 2):
                pos1, pos2 = self.positions[i - 1], self.positions[i]
                feet.append(pos1.meter_str + pos2.meter_str)
        return feet

    @property
    def foot_counts(self) -> Counter:
        """
        Get a counter of foot types in the parse.

        Returns:
            Counter: Counter of foot types.
        """
        return Counter(self.feet)

    @property
    def foot_sizes(self) -> List[int]:
        """
        Get the sizes of feet in the parse.

        Returns:
            List[int]: List of foot sizes.
        """
        return [len(ft) for ft in self.feet]

    @property
    def num_positions(self) -> int:
        """
        Get the number of metrical positions in the parse.

        Returns:
            int: Number of metrical positions.
        """
        return len(self.positions)

    @property
    def foot_type(self) -> str:
        """
        Get the foot type of the parse.

        Returns:
            str: The foot type (e.g., "iambic", "trochaic", etc.).
        """
        if self.nary_feet == 2:
            return "iambic" if self.is_rising else "trochaic"
        elif self.nary_feet == 3:
            return "anapestic" if self.is_rising else "dactylic"
        logger.error("foot type?")
        return ""

    @property
    def is_iambic(self) -> bool:
        """
        Check if the parse is iambic.

        Returns:
            bool: True if iambic, False otherwise.
        """
        return self.foot_type == "iambic"

    @property
    def is_trochaic(self) -> bool:
        """
        Check if the parse is trochaic.

        Returns:
            bool: True if trochaic, False otherwise.
        """
        return self.foot_type == "trochaic"

    @property
    def is_anapestic(self) -> bool:
        """
        Check if the parse is anapestic.

        Returns:
            bool: True if anapestic, False otherwise.
        """
        return self.foot_type == "anapestic"

    @property
    def is_dactylic(self) -> bool:
        """
        Check if the parse is dactylic.

        Returns:
            bool: True if dactylic, False otherwise.
        """
        return self.foot_type == "dactylic"

    @property
    def average_position_size(self) -> float:
        """
        Get the average size of metrical positions in the parse.

        Returns:
            float: Average position size.
        """
        l = [len(mpos.children) for mpos in self.positions if mpos.children]
        return np.mean(l) if len(l) else np.nan

    @property
    def attrs(self) -> Dict[str, Any]:
        """
        Get a dictionary of attributes for the parse.

        Returns:
            Dict[str, Any]: Dictionary of parse attributes.
        """
        return {
            "stanza_num": force_int(self.stanza_num),
            "line_num": force_int(self.line_num),
            "line_txt": self.line_txt,
            **self._attrs,
            "txt": self.txt,
            "rank": self.parse_rank,
            "meter": self.meter_str,
            "stress": self.stress_str,
            "score": self.score,
            "ambig": self.ambig,
            "is_bounded": int(bool(self.is_bounded)),
        }

    @property
    def line_txt(self) -> str:
        """
        Get the text of the line associated with this parse.

        Returns:
            str: The text of the line.
        """
        return self.line.txt if self.line else self._line_txt

    @property
    def ambig(self) -> Optional[int]:
        """
        Get the ambiguity score of the parse.

        Returns:
            Optional[int]: The ambiguity score, or None if not available.
        """
        return (
            self.line._parses.num_unbounded if self.line and self.line._parses else None
        )

    @property
    def constraint_viols(self) -> Dict[str, List[float]]:
        """
        Get the constraint violations for this parse.

        Returns:
            Dict[str, List[float]]: Dictionary of constraint violations.
        """
        # logger.debug(self)
        scores = [mpos.constraint_viols for mpos in self.positions]
        d = {}
        nans = [np.nan for _ in range(len(self.slots))]
        catcts = set(self.categorical_constraint_d.keys())
        for cname, constraint in self.constraint_d.items():
            d[cname] = cscores = [
                x for score_d in scores for x in score_d.get(cname, nans)
            ]
            if cname in catcts and any(cscores):
                logger.debug(
                    f"Bounding {self.meter_str} because violates categorical constraint {cname}"
                )
                self.is_bounded = True
        return d

    @property
    def constraint_scores(self) -> Dict[str, float]:
        """
        Get the constraint scores for this parse.

        Returns:
            Dict[str, float]: Dictionary of constraint scores.
        """
        return {cname: safesum(cvals) for cname, cvals in self.constraint_viols.items()}

    @property
    def score(self) -> float:
        """
        Get the total score of the parse.

        Returns:
            float: The total score.
        """
        return safesum(self.constraint_scores.values())

    @property
    def meter_str(self, word_sep: str = "") -> str:
        """
        Get the meter string representation of the parse.

        Args:
            word_sep (str): Separator between words.

        Returns:
            str: Meter string representation.
        """
        return "".join(
            "+" if mpos.is_prom else "-"
            for mpos in self.positions
            for slot in mpos.slots
        )

    @property
    def meter_ints(self, word_sep: str = "") -> tuple:
        """
        Get the meter as a tuple of integers.

        Args:
            word_sep (str): Separator between words.

        Returns:
            tuple: Tuple of integers representing the meter.
        """
        return tuple(
            int(mpos.is_prom) for mpos in self.positions for slot in mpos.slots
        )

    @property
    def stress_ints(self, word_sep: str = "") -> tuple:
        """
        Get the stress pattern as a tuple of integers.

        Args:
            word_sep (str): Separator between words.

        Returns:
            tuple: Tuple of integers representing the stress pattern.
        """
        return tuple(int(slot.is_stressed) for slot in self.slots)

    @property
    def stress_str(self, word_sep: str = "") -> str:
        """
        Get the stress string representation of the parse.

        Args:
            word_sep (str): Separator between words.

        Returns:
            str: Stress string representation.
        """
        return "".join(
            "+" if slot.is_stressed else "-"
            for mpos in self.positions
            for slot in mpos.slots
        ).lower()

    def bounding_relation(self, parse: "Parse") -> Bounding:
        """
        Get the bounding relation between this parse and another parse.

        Args:
            parse (Parse): The other parse to compare to.

        Returns:
            Bounding: The bounding relation.
        """
        selfviolset = self.violset
        parseviolset = parse.violset
        if selfviolset < parseviolset:
            return Bounding.bounds
        elif selfviolset > parseviolset:
            return Bounding.bounded
        elif selfviolset == parseviolset:
            return Bounding.equal
        else:
            return Bounding.unequal

    def bounds(self, parse: "Parse") -> bool:
        """
        Check if this parse bounds another parse.

        Args:
            parse (Parse): The other parse to compare to.

        Returns:
            bool: True if this parse bounds the other parse, False otherwise.
        """
        return self.bounding_relation(parse) == Bounding.bounds

    def _repr_html_(self) -> str:
        """
        Get an HTML representation of the parse for Jupyter notebooks.

        Returns:
            str: HTML representation of the parse.
        """
        return self.to_html(as_str=True, blockquote=True)

    @cached_property
    def html(self) -> str:
        """
        Get an HTML representation of the parse.

        Returns:
            str: HTML representation of the parse.
        """
        return self.to_html()

    def to_html(self, as_str: bool = False, css: str = HTML_CSS, blockquote: bool = True) -> Union[
        str, 'HTML']:
        """
        Convert the parse to an HTML representation.

        Args:
            as_str (bool): Whether to return the HTML as a string.
            css (str): CSS styles to apply to the HTML.
            blockquote (bool): Whether to include a blockquote with parse attributes.

        Returns:
            Union[str, HTML]: HTML representation of the parse.
        """
        if self.line:
            out = self.line.to_html(as_str=True, css=css)
            if blockquote:
                reprstr = get_attr_str(self.attrs, bad_keys={"txt", "line_txt"})
                out += f'<div class="miniquote">⎿ {reprstr}</div>'
            return to_html(out, as_str=as_str)
        else:
            return str(self)

    @cached_property
    def wordtoken2slots(self) -> Dict[str, List["ParseSlot"]]:
        """
        Get a dictionary mapping word tokens to their corresponding parse slots.

        Returns:
            Dict[str, List[ParseSlot]]: Dictionary mapping word tokens to parse slots.
        """
        wordtokend = defaultdict(list)
        for slot in self.slots:
            wordtokend[slot.unit.wordtoken].append(slot)
        return wordtokend

    def stats_d(self, norm: Optional[bool] = None) -> Dict[str, Any]:
        """
        Get a dictionary of statistics for the parse.

        Args:
            norm (Optional[bool]): Whether to normalize the statistics.

        Returns:
            Dict[str, Any]: Dictionary of parse statistics.
        """
        if norm is None:
            odx1 = self.stats_d(norm=False)
            odx2 = self.stats_d(norm=True)
            for k in list(odx2.keys()):
                if k[0] == "*":
                    odx2[k + "_norm"] = odx2.pop(k)
            return {**odx1, **odx2}

        odx = {**self.attrs}
        cnames = [f.__name__ for f in self.meter.constraints]
        odx["num_sylls"] = self.num_sylls
        odx["num_words"] = self.num_words

        for cname in cnames:
            odx[f"*{cname}"] = (
                np.mean([slot.viold[cname] for slot in self.slots])
                if norm
                else self.constraint_scores[cname]
            )
        viols = [int(slot.has_viol) for slot in self.slots]
        scores = [int(slot.score) for slot in self.slots]
        odx["*total_sylls"] = np.mean(viols) if norm else sum(viols)
        odx["*total"] = np.mean(scores) if norm else sum(scores)
        return odx

    def get_df(self, *x, **y) -> pd.DataFrame:
        """
        Get a DataFrame representation of the parse.

        Args:
            *x: Additional positional arguments.
            **y: Additional keyword arguments.

        Returns:
            pd.DataFrame: DataFrame representation of the parse.
        """
        df = super().get_df(*x, **y)
        df.columns = [
            c.replace("meterslot_syll_", "syll_").replace(
                "meterslot_wordtoken_", "wordtoken_"
            )
            for c in df
        ]
        return setindex(df.reset_index(), DF_COLS).sort_index()
