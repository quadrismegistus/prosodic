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
    
    @property
    def parse(self):
        from .parses import Parse
        if isinstance(self.parent, Parse):
            return self.parent
        elif self.parent and isinstance(self.parent.parent, Parse):
            return self.parent.parent
        print([self, self.parent, self.parent.parent])
        raise Exception
    
    def add_slot(self, unit):
        from .slots import ParseSlot
        slot = ParseSlot(unit=unit)
        self.children.append(slot)
    
    @property
    def slots(self):
        return self.children

    @property
    def num_slots(self):
        return len(self.children)

    def init(self, force=False) -> None:
        """Initialize violations for this position.

        Each position constraint is evaluated at most once per position (unless
        ``force``). We track the set of already-computed constraint names rather
        than inferring it from ``slot.viold``: viold stores only *nonzero*
        violations, so the old ``cname not in slot.viold`` guard was true for
        every non-violating constraint and let ``Parse.concat`` / a manual
        re-init re-run constraints — overwriting already-correct violations
        (e.g. the vectorized clash/lapse) with zeros. Positions built directly
        by the vectorized path arrive with ``_init=True`` and viold already
        populated; those count as fully computed. (AUDIT C16)
        """
        assert self.parse
        if any(not slot.unit for slot in self.slots):
            print(self.slots)
            print([slot.__dict__ for slot in self.slots])
            raise Exception
        computed = getattr(self, "_computed_cnames", None)
        if computed is None:
            # A position pre-initialized elsewhere (vectorized builder sets
            # _init=True after filling viold) counts as fully computed.
            computed = (
                set(self.parse.position_constraints)
                if getattr(self, "_init", False)
                else set()
            )
            self._computed_cnames = computed
        for cname, constraint in self.parse.position_constraints.items():
            if force or cname not in computed:
                slot_viols = [int(bool(vx)) for vx in constraint(self)]
                #log.debug(f'applying position constriant {cname}, got {slot_viols}')
                assert len(slot_viols) == len(self.slots)
                for viol, slot in zip(slot_viols, self.slots):
                    slot.viold[cname] = viol
                computed.add(cname)
        self._init = True

    @property
    def viold(self):
        viold = Counter()
        for slot in self.slots:
            for cname,cviol in slot.viold.items():
                viold[cname]+=cviol
        return viold
    
    @property
    def scores(self):
        return {cname:cnum*self.constraint_weights.get(cname) for cname,cnum in self.viold.items()}

    @property
    def violset(self):
        return {cname for cname,cval in self.viold.items() if cval>0}

    def to_dict(self, **kwargs) -> Dict:
        """
        Convert the ParsePosition to a JSON-serializable dictionary.

        Returns:
            A dictionary representation of the ParsePosition.
        """
        return super().to_dict(meter_val=self.meter_val, **kwargs)

    @property
    def is_prom(self) -> bool:
        """
        Check if this position is prominent.

        Returns:
            True if the position is prominent, False otherwise.
        """
        return self.meter_val == "s"

    @property
    def txt(self) -> str:
        """
        Get the text representation of this position.

        Returns:
            A string representation of the position.
        """
        token = ".".join([slot.txt for slot in self.children])
        token = token.upper() if self.is_prom else token.lower()
        return token

    @property
    def meter_str(self) -> str:
        """
        Get the meter string for this position.

        Returns:
            A string representing the meter of this position.
        """
        return self.meter_val * self.num_slots

    @property
    def num_slots(self) -> int:
        """
        Get the number of slots in this position.

        Returns:
            The number of slots.
        """
        return len(self.slots)
    
class ParsePositionList(EntityList):
    pass
