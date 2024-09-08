from ..imports import *

class ParsePosition(Entity):
    """
    Represents a position in a metrical parse.

    Attributes:
        viold: Dict of lists of violations; length of these lists == length of `slots`.
        violset: Set of all violations on this position.
        slots: List of child slots.
        parse: Parent parse object.
    """

    prefix: str = "meterpos"

    def __init__(self, meter_val: str, children: List = [], parent: Optional['Parse'] = None, **kwargs):
        """
        Initialize a ParsePosition.

        Args:
            meter_val: String representing whether the position is 's' or 'w'.
            children: List of child slots.
            parent: Parent parse object.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(
            meter_val=meter_val,
            children=children,
            parent=parent,
            **kwargs,
        )
        self.viold: Dict[str, List[int]] = {}
        self.violset: Set[str] = set()
        self.slots = self.children
        self.parse = self.parent
        # self.parse: Optional['Parse'] = self.parent
        # if self.parse:
        #     self.init()

    @property
    def num_slots(self):
        return len(self.children)

    def init(self) -> None:
        """Initialize violations for this position."""
        assert self.parse
        if any(not slot.unit for slot in self.slots):
            print(self.slots)
            print([slot.__dict__ for slot in self.slots])
            raise Exception
        for cname, constraint in self.parse.constraint_d.items():
            slot_viols = [int(bool(vx)) for vx in constraint(self)]
            assert len(slot_viols) == len(self.slots)
            self.viold[cname] = slot_viols
            if any(slot_viols):
                self.violset.add(cname)
            for viol, slot in zip(slot_viols, self.slots):
                slot.viold[cname] = viol

    def __copy__(self) -> 'ParsePosition':
        """
        Create a copy of this ParsePosition.

        Returns:
            A new ParsePosition object with copied attributes.
        """
        new = ParsePosition(
            meter_val=self.meter_val,
            children=[copy(slot) for slot in self.slots],
            parent=self.parent,
        )
        new.viold = copy(self.viold)
        new.violset = copy(self.violset)
        new._attrs = copy(self._attrs)
        return new

    def to_dict(self) -> Dict:
        """
        Convert the ParsePosition to a JSON-serializable dictionary.

        Returns:
            A dictionary representation of the ParsePosition.
        """
        return super().to_dict(meter_val=self.meter_val)

    @cached_property
    def attrs(self) -> Dict:
        """
        Get the attributes of this ParsePosition.

        Returns:
            A dictionary of attributes.
        """
        return {
            **self._attrs,
            "num": self.num,
            # **{k:sum(v) for k,v in self.viold.items()}
        }

    @cached_property
    def constraint_viols(self) -> Dict[str, List[int]]:
        """
        Get the constraint violations for this position.

        Returns:
            A dictionary of constraint violations.
        """
        return self.viold

    @cached_property
    def constraint_scores(self) -> Dict[str, int]:
        """
        Get the constraint scores for this position.

        Returns:
            A dictionary of constraint scores.
        """
        return {k: sum(v) for k, v in self.constraint_viols.items()}

    @cached_property
    def constraint_set(self) -> Set[str]:
        """
        Get the set of constraints violated by this position.

        Returns:
            A set of constraint names.
        """
        return self.violset

    @cached_property
    def is_prom(self) -> bool:
        """
        Check if this position is prominent.

        Returns:
            True if the position is prominent, False otherwise.
        """
        return self.meter_val == "s"

    # @cached_property
    # def txt(self) -> str:
    #     """
    #     Get the text representation of this position.

    #     Returns:
    #         A string representation of the position.
    #     """
    #     token = ".".join([slot.txt for slot in self.children])
    #     token = token.upper() if self.is_prom else token.lower()
    #     return token

    @cached_property
    def meter_str(self) -> str:
        """
        Get the meter string for this position.

        Returns:
            A string representing the meter of this position.
        """
        return self.meter_val * self.num_slots

    @cached_property
    def num_slots(self) -> int:
        """
        Get the number of slots in this position.

        Returns:
            The number of slots.
        """
        return len(self.slots)