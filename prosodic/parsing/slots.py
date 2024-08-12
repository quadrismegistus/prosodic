from ..imports import *

class ParseSlot(Entity):
    """
    Represents a slot in a metrical parse.

    Attributes:
        prefix (str): The prefix for this entity type.
        unit (Syllable): The syllable associated with this slot.
        viold (Dict[str, Any]): Dictionary of violation data.
    """

    prefix: str = "meterslot"

    def __init__(
        self,
        unit: Optional["Syllable"] = None,
        parent: Optional[Any] = None,
        children: List[Any] = [],
        viold: Dict[str, Any] = {},
        **kwargs
    ) -> None:
        """
        Initialize a ParseSlot.

        Args:
            unit: The syllable associated with this slot.
            parent: The parent entity.
            children: List of child entities.
            viold: Dictionary of violation data.
            **kwargs: Additional keyword arguments.
        """
        # print(unit,parent,children,viold,kwargs)
        if unit is None and children:
            assert len(children) == 1
            unit = children[0]

        self.unit = unit
        self.viold = {**viold}
        super().__init__(children=[], parent=parent, **kwargs)

    @cached_property
    def position(self):
        return self.parent

    def __copy__(self) -> "ParseSlot":
        """
        Create a shallow copy of the ParseSlot.

        Returns:
            A new ParseSlot instance with copied attributes.
        """
        new = ParseSlot(unit=self.unit)
        new.viold = copy(self.viold)
        new._attrs = copy(self._attrs)
        return new

    def to_json(self) -> Dict[str, Any]:
        """
        Convert the ParseSlot to a JSON-serializable dictionary.

        Returns:
            A dictionary representation of the ParseSlot.
        """
        d = super().to_json(unit=self.unit.to_hash(), viold=self.viold)
        d.pop("children")
        return d

    @cached_property
    def violset(self) -> Set[str]:
        """
        Set of constraint violations.

        Returns:
            A set of constraint violation keys.
        """
        return {k for k, v in self.viold.items() if v}

    @cached_property
    def num_viols(self) -> int:
        """
        Number of constraint violations.

        Returns:
            The number of constraint violations.
        """
        return len(self.violset)

    @cached_property
    def constraint_scores(self) -> Dict[str, Any]:
        """
        Dictionary of constraint scores.

        Returns:
            A dictionary of constraint scores.
        """
        return self.viold

    @cached_property
    def meter_val(self) -> Any:
        """
        Meter value of the parent.

        Returns:
            The meter value of the parent.
        """
        return self.parent.meter_val

    @cached_property
    def is_prom(self) -> bool:
        """
        Whether the slot is prominent.

        Returns:
            True if the slot is prominent, False otherwise.
        """
        return self.parent.is_prom

    @cached_property
    def wordform(self) -> Any:
        """
        The wordform associated with this slot.

        Returns:
            The wordform associated with this slot.
        """
        return self.unit.parent

    @cached_property
    def syll(self) -> "Syllable":
        """
        The syllable associated with this slot.

        Returns:
            The syllable associated with this slot.
        """
        return self.unit

    @cached_property
    def is_stressed(self) -> bool:
        """
        Whether the syllable is stressed.

        Returns:
            True if the syllable is stressed, False otherwise.
        """
        return self.unit.is_stressed

    @cached_property
    def is_heavy(self) -> bool:
        """
        Whether the syllable is heavy.

        Returns:
            True if the syllable is heavy, False otherwise.
        """
        return self.unit.is_heavy

    @cached_property
    def is_strong(self) -> bool:
        """
        Whether the syllable is strong.

        Returns:
            True if the syllable is strong, False otherwise.
        """
        return self.unit.is_strong

    @cached_property
    def is_weak(self) -> bool:
        """
        Whether the syllable is weak.

        Returns:
            True if the syllable is weak, False otherwise.
        """
        return self.unit.is_weak

    @cached_property
    def score(self) -> float:
        """
        Total violation score.

        Returns:
            The total violation score.
        """
        return sum(self.viold.values())

    @cached_property
    def has_viol(self) -> bool:
        """
        Whether the slot has any violations.

        Returns:
            True if the slot has any violations, False otherwise.
        """
        return bool(self.score)

    @cached_property
    def txt(self) -> str:
        """
        Text representation of the slot.

        Returns:
            The text representation of the slot.
        """
        o = self.unit.txt
        return o.upper() if self.is_prom else o.lower()

    @cached_property
    def i(self) -> int:
        """
        Index of the slot in the parent's slots list.

        Returns:
            The index of the slot in the parent's slots list.
        """
        return self.parent.parent.slots.index(self)

    @cached_property
    def attrs(self) -> Dict[str, Any]:
        """
        Dictionary of attributes for the slot.

        Returns:
            A dictionary of attributes for the slot.
        """
        return {
            **{
                k: v
                for k, v in self.unit.prefix_attrs.items()
                if k.split("_")[0] in {"wordtoken", "syll"}
            },
            **self._attrs,
            "num": self.num,
            "is_prom": self.is_prom,
            **self.viold,
        }
    