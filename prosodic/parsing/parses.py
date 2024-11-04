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
        wordtokens: "WordTokenList",
        scansion: str = "",
        meter: Optional["Meter"] = None,
        parent: Optional[Any] = None,
        children: Optional[List["ParsePositionList"]] = None,
        is_bounded: bool = False,
        bounded_by: Optional[List] = None,
        rank: Optional[int] = None,
        parse_viold={},
        key=None,
        num=None,
        scope=None,
        num_slots_positioned=0,
        **meter_kwargs,
        # line_num: Optional[int] = None,
        # stanza_num: Optional[int] = None,
        # line_txt: str = "",
    ) -> None:
        from .meter import Meter

        global OBJECTS
        # meter
        # if meter is None and parent:
        # meter = parent.meter
        if meter is None:
            meter = Meter(**meter_kwargs)
        # self._attrs = {}
        self.meter_obj = meter
        self._key = key
        self._num = num
        self._scope = scope
        self.constraint_names = list(meter.constraints.keys())
        self.parse_constraints = meter.parse_constraint_funcs
        self.position_constraints = meter.position_constraint_funcs
        self.constraint_weights = meter.constraints

        # wordforms
        if isinstance(wordtokens, str):
            wordtokens = next(TextModel(wordtokens).wordtokens.iter_wordtoken_matrix())
        assert wordtokens.num_with_forms == wordtokens.num_wordforms
        self.wordtokens = wordtokens
        self.wordforms = wordtokens.wordforms
        self.slot_units = [syll for wf in self.wordforms for syll in wf]

        # self.parent = parent if parent is not None else wordtokens
        self.parent = None # wait for parselist

        # slots
        # self.slots = [ParseSlot(syll, parent=self) for syll in self.slot_units]

        # scansion
        if not scansion:
            scansion = get_iambic_parse(len(self.slot_units))
        if type(scansion) == str:
            scansion = split_scansion(scansion)
        self.scansion = copy(scansion)

        self.is_bounded = is_bounded
        self.bounded_by = [] if not bounded_by else [x for x in bounded_by]
        self.unmetrical = False
        self.comparison_nums = set()
        self.comparison_parses = []
        self.parse_num = 0
        self.total_score = None
        self.pause_comparisons = False
        self.parse_rank = rank
        self.num_slots_positioned = num_slots_positioned
        self.parse_viold = Counter(parse_viold)
        self.children = ParsePositionList() if not children else children
        self.children.parent = self
        if not self.children:
            for mpos_str in self.scansion:
                self.extend(mpos_str)
        self.init()

    @property
    def positions(self):
        return self.children

    def init(self, force=False) -> None:
        """Initialize the parse positions."""
        for pos in self.positions:
            pos.init()
        self.apply_parse_constraints(force=force)

    def apply_parse_constraints(self, force=False):
        # parse constraints
        for cname, cfunc in self.parse_constraints.items():
            if (force or cname not in self.parse_viold) and cfunc.scope == self.scope:
                res = cfunc(self)
                # log.debug(f'applying {cname}, got {res}')
                assert isinstance(res, bool), "Parse constraints must return True/False"
                self.parse_viold[cname] = int(res)

    def to_dict(self, **kwargs) -> Dict[str, Any]:
        """
        Convert the parse to a JSON-serializable dictionary.

        Args:
            fn (Optional[str]): Filename to save the JSON to.

        Returns:
            Dict[str, Any]: JSON-serializable dictionary representation of the parse.
        """
        return super().to_dict(
            wordtokens=self.wordtokens.to_dict(incl_children=True, _use_registry=False),   # different from registered wordtokens
            meter=self.meter_obj.to_dict(),
            is_bounded=self.is_bounded,
            bounded_by=list(self.bounded_by),
            rank=self.parse_rank,
            parse_viold=dict(self.parse_viold),
            num_slots_positioned=self.num_slots_positioned,
            # _use_registry=False,
            **kwargs,
        )
        # return to_dict(
        #     {
        #         "_class": self.__class__.__name__,
        #         **self.attrs,
        #         "children": [pos.to_dict() for pos in self.positions],
        #         "_wordforms": self.wordforms.to_dict(),
        #         "_meter": self.meter_obj.to_dict(),
        #         "is_bounded": self.is_bounded,
        #         "bounded_by": list(self.bounded_by),
        #     },
        #     fn=fn,
        # )

    @classmethod
    def from_dict(
        cls,
        json_d: Dict[str, Any],
        use_registry=DEFAULT_USE_REGISTRY,
    ) -> "Parse":
        """
        Create a Parse object from a JSON dictionary.

        Args:
            json_d (Dict[str, Any]): JSON dictionary representation of the parse.
            line (Optional[Union[TextModel, Stanza, Line]]): The line object to associate with the parse.

        Returns:
            Parse: A new Parse object created from the JSON data.
        """
        from ..texts import Line

        cls_name, data = next(iter(json_d.items()))
        assert cls_name == cls.__name__
        wordtokens = Entity.from_dict(data.pop("wordtokens"), use_registry=use_registry)
        meter = Entity.from_dict(data.pop("meter"), use_registry=use_registry)
        children = Entity.from_dict(data.pop("children"), use_registry=use_registry)
        slots = [slot for pos in children for slot in pos.slots]
        sylls = [syll for wtok in wordtokens for wtyp in wtok for wf in wtyp for syll in wf]
        assert len(slots) == len(sylls)
        for syll, slot in zip(sylls, slots):
            slot.unit = syll
        return Parse(wordtokens, children=children, meter=meter, **data)

    @property
    def key(self):
        if self._key is not None:
            return self._key
        key = f"""{self.parent.key}.{self.nice_type_name}(scansion="{self.meter_str}",stress="{self.stress_str}").{self.meter_obj.key}"""
        self._key = key
        return key

    @property
    def slots(self) -> List["ParseSlot"]:
        """
        Get all slots in the parse.

        Returns:
            List[ParseSlot]: List of all slots in the parse.
        """
        return ParseSlotList(
            [slot for mpos in self.positions for slot in mpos.slots], parent=self
        )

    @property
    def parse_unit(self):
        return self.meter_obj.parse_unit

    @property
    def scope(self):
        if self._scope: 
            log.info(f'parse _scope: {self._scope}')
            return self._scope
        return self.wordtokens.prefix# if self.parent and self.parent.parent else None

    @classmethod
    def concat(cls, *parses: "Parse", wordtokens=None) -> "Parse":
        from .positions import ParsePositionList
        from ..words.wordtokenlist import WordTokenList

        assert len(parses) > 0
        # if len(parses) == 1:
        #     parse = parses[0].copy()
        #     if wordtokens is not None:
        #         parse.wordtokens = wordtokens
        #     return parse
        assert all(parses[0].meter_obj.equals(parse.meter_obj) for parse in parses[1:])
        # parses = [parse.copy() for parse in parses]
        positions = ParsePositionList(
            [mpos for parse in parses for mpos in parse.positions],
            parent=parses[0].parent,
        )
        wordtokens_limited = [wt for parse in parses for wt in parse.wordtokens]
        if wordtokens is not None:
            wordtokens = wordtokens.copy()
            wordtokens.children = wordtokens_limited
        else:
            wordtokens_cls = type(wordtokens) if wordtokens is not None else WordTokenList
            wordtokens = wordtokens_cls(
                children=wordtokens_limited,
                parent=parses[0].wordtokens.parent,
            )
        scansion = [x for parse in parses for x in parse.scansion]

        parse = Parse(
            wordtokens=wordtokens,
            scansion=scansion,
            meter=parses[0].meter_obj,
            children=positions,
        )
        parse.num_slots_positioned = sum(px.num_slots_positioned for px in parses)
        return parse

    def extend(self, mpos_str: str) -> Optional["Parse"]:
        """
        Extend the parse with a new metrical position.

        Args:
            mpos_str (str): String representation of the metrical position to add.

        Returns:
            Optional[Parse]: The extended parse, or None if extension is not possible.
        """
        mval = mpos_str[0]
        if self.positions and self.positions[-1].meter_val == mval:
            # log.warning(f'cannnot extend because last position is also {mval}')
            return None

        mpos = ParsePosition(meter_val=mval)
        for i, x in enumerate(mpos_str):
            slot_i = self.num_slots_positioned
            try:
                mpos.add_slot(self.slot_units[slot_i])
            except IndexError:
                # log.warning('cannot extend further, already taking up all syllable slots')
                return None

            self.num_slots_positioned += 1
        self.positions.append(mpos)
        # init
        mpos.init()
        return self

    @cached_property
    def positions_viold(self):
        viold = Counter()
        for position in self.positions:
            for cname, cviol in position.viold.items():
                viold[cname] += cviol
        return viold

    @cached_property
    def viold(self):
        return self.positions_viold + self.parse_viold

    @cached_property
    def scores(self):
        return {
            cname: cnum * self.constraint_weights.get(cname)
            for cname, cnum in self.viold.items()
        }

    @cached_property
    def parse_violset(self):
        return {cname for cname, cval in self.parse_viold.items() if cval > 0}

    @cached_property
    def violset(self) -> Multiset:
        """
        Get the set of constraint violations for this parse.

        Returns:
            Multiset: A multiset of constraint violations.
        """
        s = Multiset()
        for mpos in self.positions:
            s.update(mpos.violset)
        s.update(self.parse_violset)
        return s

    # # @log.info
    # def copy(self):
    #     """
    #     Create a shallow copy of the parse.

    #     Returns:
    #         Parse: A shallow copy of the parse.
    #     """
    #     from .positions import ParsePositionList
    #     new = Parse.__new__(Parse)
    #     new.__dict__.update({k: v for k, v in self.__dict__.items() if not isinstance(getattr(self.__class__, k, None), cached_property)})
    #     new.children = ParsePositionList(parent=new)
    #     for pos in self.children:
    #         new.children.append(pos.copy())
    #     return new

    def branch(self) -> List["Parse"]:
        """
        Create branching parses from this parse.

        Returns:
            List[Parse]: List of branching parses.
        """
        if self.is_bounded:
            return []
        if not self.positions or not len(self.positions):
            # log.debug("needs to start with some positions")
            return []
        mval = self.positions[-1].meter_val
        otypes = self.meter_obj.get_pos_types(self.wordforms.num_sylls)
        otypes = [x for x in otypes if x[0] != mval]
        o = [self.copy().extend(posstr) for posstr in otypes]
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
        return self.num_slots_positioned == len(self.slot_units)

    @cached_property
    def sort_key(self) -> tuple:
        """
        Get the sort key for this parse.

        Returns:
            tuple: A tuple used for sorting parses.
        """
        return (
            int(bool(self.is_bounded)),
            self.score,
            self.positions[0].is_prom if self.positions else 10,
            self.average_position_size,
            self.num_stressed_sylls,
            self.meter_ints,
            self.stress_ints,
        )

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
        # log.error(f'{self} and {other} could not be compared in sort, ended up equal')
        # return not (self<other) and not (other<self)
        return self is other

    @cached_property
    def wordtokens_key(self):
        return self.wordtokens.key

    def can_compare(self, other: "Parse", min_slots: int = 4) -> bool:
        """
        Check if this parse can be compared to another parse.

        Args:
            other (Parse): The other parse to compare to.
            min_slots (int): Minimum number of slots required for comparison.

        Returns:
            bool: True if the parses can be compared, False otherwise.
        """
        if self.wordtokens_key != other.wordtokens_key:
            return False

        if min_slots and self.num_slots_positioned < min_slots:
            return False

        if self.is_complete and other.is_complete:
            return True

        if self.num_slots_positioned != other.num_slots_positioned:
            return False

        return True

    @property
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
        log.error(f"foot type? {self.nary_feet}")
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
        d={**(self._attrs or {})}
        for unit_type in ['stanza', 'line', 'linepart', 'sentpart', 'sent']:
            unit = self.get_unit(unit_type)
            if unit is not None:
                d[f"{unit_type}_num"] = unit.num
                if unit_type == self.scope:
                    d[f'{unit_type}_txt'] = unit.txt.strip()
        return {
            **d,
            "rank": self.parse_rank,
            "txt": self.txt,
            "meter": self.meter_str,
            "stress": self.stress_str,
            "score": self.score,
            "num_viols": self.num_viols,
            "ambig": self.ambig,
            "is_bounded": int(bool(self.is_bounded)),
            **{f'*{c}':self.parse_viold.get(c,0) for c in self.parse_constraints},
        }
    
    @property
    def line_txt(self) -> str:
        """
        Get the text of the line associated with this parse.

        Returns:
            str: The text of the line.
        """
        return self.parent.txt if self.parent else self._line_txt

    @property
    def ambig(self) -> Optional[int]:
        """
        Get the ambiguity score of the parse.

        Returns:
            Optional[int]: The ambiguity score, or None if not available.
        """
        return (
            self.parent.num_unbounded if self.parent else None
        )

    @cached_property
    def score(self) -> float:
        """
        Get the total score of the parse.

        Returns:
            float: The total score.
        """
        return sum(self.scores.values())
    
    @cached_property
    def num_viols(self):
        return len(self.violset)

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

    @property
    def html(self) -> str:
        """
        Get an HTML representation of the parse.

        Returns:
            str: HTML representation of the parse.
        """
        return self.to_html()

    def to_html(
        self, as_str: bool = False, css: str = HTML_CSS, blockquote: bool = True
    ) -> Union[str, "HTML"]:
        """
        Convert the parse to an HTML representation.

        Args:
            as_str (bool): Whether to return the HTML as a string.
            css (str): CSS styles to apply to the HTML.
            blockquote (bool): Whether to include a blockquote with parse attributes.

        Returns:
            Union[str, HTML]: HTML representation of the parse.
        """
        if self.parent:
            out = self.parent.to_html(as_str=True, css=css)
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
            wordtokend[slot.unit.wordtoken.key].append(slot)
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
        cnames = [f for f in self.meter_obj.constraints]
        odx["num_sylls"] = self.num_sylls
        odx["num_words"] = self.num_words

        for cname in cnames:
            odx[f"*{cname}"] = float(
                np.mean([slot.viold.get(cname,0) for slot in self.slots])
                if norm
                else self.scores.get(cname,0)
            )
        viols = [int(slot.has_viol) for slot in self.slots]
        scores = [int(slot.score) for slot in self.slots]
        odx["*total_sylls"] = float(np.mean(viols)) if norm else sum(viols)
        odx["*total"] = float(np.mean(scores)) if norm else sum(scores)
        return odx

    def get_unit(self, unit_type:str=None):
        if unit_type is None: unit_type = self.scope
        unit = self.parent.parent if self.parent and self.parent.parent else None
        if unit is None: return None
        return getattr(unit, unit_type)
    
    def get_unit_num(self, unit_type:str=None):
        unit = self.get_unit(unit_type)
        if unit is None: return None
        return getattr(unit, 'num')

    @property
    def line(self):
        return self.get_unit('line')

    @property
    def linepart(self):
        return self.get_unit('linepart')
    
    @property
    def stanza(self):
        return self.get_unit('stanza')
    
    @property
    def sentpart(self):
        return self.get_unit('sentpart')
    
    @property
    def sent(self):
        return self.get_unit('sent')

    def get_ld(self, *args, **kwargs):
        l=[]
        attrs = {f'parse_{k}' if not k.endswith('_num') and not k.endswith('_txt') and k[0]!='*' else k:v for k,v in self.attrs.items()}
        for pos in self.positions:
            pos_attrs = {f'meterpos_{k}' if not k.endswith('_num') and k[0]!='*' else k:v for k,v in pos.attrs.items()}
            for slot in pos.slots:
                slot_attrs = {
                    'wordtoken_num':slot.unit.wordtoken.num,
                    'wordtoken_txt':slot.unit.wordtoken.txt,
                    # 'syll_num':slot.unit.num,
                    **{f'meterslot_{k}' if not k.endswith('_num') and k[0]!='*' else k:v for k,v in slot.attrs.items()}
                }
                all_attrs = {**attrs, **pos_attrs, **slot_attrs}
                viol_attrs = {k:v for k,v in all_attrs.items() if k and k[0] == '*'}
                non_viol_attrs = {k:v for k,v in all_attrs.items() if k and k[0] != '*'}
                l.append({**non_viol_attrs, **viol_attrs})
        return l


    def get_df(self, *args, **kwargs) -> pd.DataFrame:
        """
        Get a DataFrame representation of the parse.

        Args:
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            pd.DataFrame: DataFrame representation of the parse.
        """
        return setindex(pd.DataFrame(self.get_ld(*args, **kwargs)), sort=True)
