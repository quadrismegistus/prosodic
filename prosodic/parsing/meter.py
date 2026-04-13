from typing import List, Tuple, Dict, Any, Iterator, Optional, Union
from ..imports import *
from .constraints import *
from .constraint_utils import *
from ..texts import TextModel, Line, Stanza
from .parselists import ParseList
from .utils import *

NUM_GOING = 0
DEFAULT_METER_KWARGS = dict(
    constraints=DEFAULT_CONSTRAINTS,
    max_s=METER_MAX_S,
    max_w=METER_MAX_W,
    resolve_optionality=METER_RESOLVE_OPTIONALITY,
    parse_unit="line",
)
MTRDEFAULT = DEFAULT_METER_KWARGS


class Meter(Entity):
    """
    A metrical parsing system using vectorized numpy constraint evaluation.

    Evaluates all possible scansions exhaustively and uses harmonic bounding
    to identify optimal parses.
    """

    prefix: str = "meter"
    children = None

    def __init__(
        self,
        constraints: List[str] = MTRDEFAULT["constraints"],
        max_s: int = MTRDEFAULT["max_s"],
        max_w: int = MTRDEFAULT["max_w"],
        resolve_optionality: bool = MTRDEFAULT["resolve_optionality"],
        parse_unit: Literal["line", "sentpart", "linepart"] = MTRDEFAULT["parse_unit"],
        exhaustive: bool = True,  # ignored, always exhaustive
        vectorized: bool = True,  # ignored, always vectorized
        **kwargs: Any,
    ) -> None:
        super().__init__(
            constraints=(
                parse_constraint_weights(constraints)
                if not isinstance(constraints, dict)
                else constraints
            ),
            max_s=max_s,
            max_w=max_w,
            resolve_optionality=resolve_optionality,
            parse_unit=parse_unit,
        )

    @property
    def key(self):
        if self._key is None:
            self._key = f"{self.nice_type_name}({encode_hash(serialize(self._attrs))})"
        return self._key

    def to_dict(self, incl_attrs=True, **kwargs) -> Dict[str, Any]:
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

    def fit(self, text, target_scansion, zones=3, regularization=100.0,
            lang=DEFAULT_LANG, **train_kwargs):
        """Learn constraint weights from a text with a target scansion.

        Trains a MaxEnt model on the text and stores the learned zone
        weights on this meter. Subsequent parsing will use the learned
        positional weights for scoring.

        Args:
            text: a string, list of line strings, or TextModel.
            target_scansion: e.g. "wswswswsws" for iambic pentameter.
            zones: positional zone splitting (None, "initial", int N).
            regularization: L2 regularization strength.
            lang: language code for parsing.
            **train_kwargs: extra args for MaxEntTrainer.train().

        Returns:
            self (for chaining).
        """
        from .maxent import MaxEntTrainer
        trainer = MaxEntTrainer(self, regularization=regularization, zones=zones)
        trainer.load_text(text, target_scansion, lang=lang)
        trainer.train(**train_kwargs)
        self.zones = zones
        self.zone_weights = trainer.learned_weights()
        self._trainer = trainer
        # reset key since meter config changed
        self._key = None
        return self

    def fit_annotations(self, data, zones=3, regularization=100.0,
                        lang=DEFAULT_LANG, text=None, **train_kwargs):
        """Learn constraint weights from annotated scansion data.

        Args:
            data: list of (text, scansion, frequency) tuples or DataFrame.
            zones: positional zone splitting (None, "initial", int N).
            regularization: L2 regularization strength.
            lang: language code for parsing.
            text: optional pre-built TextModel (e.g. with syntax=True).
            **train_kwargs: extra args for MaxEntTrainer.train().

        Returns:
            self (for chaining).
        """
        from .maxent import MaxEntTrainer
        trainer = MaxEntTrainer(self, regularization=regularization, zones=zones)
        trainer.load_annotations(data, lang=lang, text=text)
        trainer.train(**train_kwargs)
        self.zones = zones
        self.zone_weights = trainer.learned_weights()
        self._trainer = trainer
        self._key = None
        return self

    def parse(
        self, entity: "Entity", force: bool = False, lim=None, **kwargs: Any
    ) -> "ParseList":
        return self.parse_text(entity, lim=lim)

    def parse_exhaustive(self, entity: "Entity", **kwargs):
        """Compatibility alias — the vectorized parser is always exhaustive."""
        result = self.parse(entity, **kwargs)
        # unwrap single-line ParseListList for backward compat
        if hasattr(result, 'data') and len(result) == 1:
            return result[0]
        return result

    def parse_text(self, text, force: bool = False, lim=None):
        from .parselists import ParseListList

        pll = ParseListList(parent=text)
        for i, pl in enumerate(self.parse_text_iter(text, force=force, lim=lim)):
            pl._num = i + 1
            pll.append(pl)
        return pll

    def parse_text_iter(self, text, force: bool = False, lim=None):
        syll_df = getattr(text, '_syll_df', None)

        # DF-only path: parse from DataFrame without building Entity objects
        parse_unit_col_map = {'line': 'line_num', 'linepart': 'linepart_num'}
        df_col = parse_unit_col_map.get(self.parse_unit)
        if syll_df is not None and len(syll_df) > 0 and df_col:
            from .vectorized import parse_batch_from_df
            line_results = parse_batch_from_df(syll_df, self, line_col=df_col)
            if getattr(text, '_line_parse_results', None) is None:
                text._line_parse_results = {}
            text._line_parse_results[self.key] = line_results
            for line_num in sorted(line_results.keys()):
                pl = line_results[line_num]
                pl._text = text
                yield pl
            return

        # fallback: Entity-based path (when _syll_df not available)
        parse_units = self.get_parse_units(text)
        if parse_units is None:
            log.warning(f"cannot parse {text}")
            return
        from .vectorized import parse_batch
        results = parse_batch(parse_units[:lim], self, syll_df=syll_df)
        for wt, pl in results:
            pl.parent = wt
            wt._parses = pl
            yield pl
