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
        **kwargs,
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
        if unit is None and children:
            assert len(children) == 1
            unit = children[0]
        self.unit = unit
        super().__init__(parent=parent, viold={**viold}, **kwargs)

    @property
    def position(self):
        return self.parent

    # @log.info
    def copy(self):
        """
        Create a shallow copy of the parse slot.

        Returns:
            ParseSlot: A shallow copy of the parse slot.
        """
        new = ParseSlot.__new__(ParseSlot)
        new.__dict__.update(
            {
                k: v
                for k, v in self.__dict__.items()
                if not isinstance(getattr(self.__class__, k, None), cached_property)
            }
        )
        new.viold = self.viold.copy()
        return new

    def to_dict(self, incl_key=True, **kwargs):
        return super().to_dict(viold=self.viold, incl_key=incl_key, **kwargs)

    @property
    def violset(self) -> Set[str]:
        """
        Set of constraint violations.

        Returns:
            A set of constraint violation keys.
        """
        return {k for k, v in self.viold.items() if v}

    @property
    def num_viols(self) -> int:
        """
        Number of constraint violations.

        Returns:
            The number of constraint violations.
        """
        return len(self.violset)

    @property
    def scores(self):
        return {
            cname: cnum * self.constraint_weights.get(cname)
            for cname, cnum in self.viold.items()
        }

    @property
    def meter_val(self) -> Any:
        """
        Meter value of the parent.

        Returns:
            The meter value of the parent.
        """
        return self.parent.meter_val

    @property
    def position(self):
        return self.parent.parent

    @property
    def is_prom(self) -> bool:
        """
        Whether the slot is prominent.

        Returns:
            True if the slot is prominent, False otherwise.
        """
        return self.position.is_prom

    @property
    def wordform(self) -> Any:
        """
        The wordform associated with this slot.

        Returns:
            The wordform associated with this slot.
        """
        return self.unit.parent.parent

    @property
    def syll(self) -> "Syllable":
        """
        The syllable associated with this slot.

        Returns:
            The syllable associated with this slot.
        """
        return self.unit

    @property
    def is_stressed(self) -> bool:
        """
        Whether the syllable is stressed.

        Returns:
            True if the syllable is stressed, False otherwise.
        """
        return self.unit.is_stressed

    @property
    def is_heavy(self) -> bool:
        """
        Whether the syllable is heavy.

        Returns:
            True if the syllable is heavy, False otherwise.
        """
        return self.unit.is_heavy

    @property
    def is_strong(self) -> bool:
        """
        Whether the syllable is strong.

        Returns:
            True if the syllable is strong, False otherwise.
        """
        return self.unit.is_strong

    @property
    def is_weak(self) -> bool:
        """
        Whether the syllable is weak.

        Returns:
            True if the syllable is weak, False otherwise.
        """
        return self.unit.is_weak

    @property
    def score(self) -> float:
        """
        Total violation score.

        Returns:
            The total violation score.
        """
        return sum(self.viold.values())

    @property
    def has_viol(self) -> bool:
        """
        Whether the slot has any violations.

        Returns:
            True if the slot has any violations, False otherwise.
        """
        return bool(self.score)

    @property
    def attrs(self):
        return {
            "num": self.num,
            "txt": self.txt,
            **{f"*{c}": self.viold.get(c, 0) for c in self.viold},
        }

    @property
    def txt(self) -> str:
        """
        Text representation of the slot.

        Returns:
            The text representation of the slot.
        """
        assert isinstance(self.unit, Syllable)
        o = self.unit.txt
        result = o.upper() if self.is_prom else o.lower()
        return result


class ParseSlotList(EntityList):
    pass
