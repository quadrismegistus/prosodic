from typing import List, Tuple, Dict, Any, Iterator, Optional, Union
from ..imports import *
from .constraints import *
from .constraint_utils import *
from ..texts import TextModel, Line, Stanza
from .parselists import ParseList
from .utils import *

DEFAULT_METER_KWARGS = dict(
    constraints=DEFAULT_CONSTRAINTS,
    max_s=METER_MAX_S,
    max_w=METER_MAX_W,
    resolve_optionality=METER_RESOLVE_OPTIONALITY,
    pool_forms=METER_POOL_FORMS,
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
        pool_forms: bool = MTRDEFAULT["pool_forms"],
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
            pool_forms=pool_forms,
            parse_unit=parse_unit,
        )

    @property
    def key(self):
        if self._key is None:
            # Fold learned zones/zone_weights (set by fit/fit_annotations) into
            # the key so a fitted meter hashes differently from an unfitted one.
            # These live as instance attrs (not in _attrs), so without this a
            # fit() would leave meter.key unchanged and callers keyed on it
            # (TextModel._parse_results / _line_parse_results) would return
            # stale, pre-fit parses. (C10)
            attrs = dict(self._attrs)
            zones = getattr(self, 'zones', None)
            zone_weights = getattr(self, 'zone_weights', None)
            if zones is not None:
                attrs['zones'] = zones if isinstance(zones, (str, int)) else str(zones)
            if zone_weights is not None:
                attrs['zone_weights'] = {
                    str(k): float(v) for k, v in dict(zone_weights).items()
                }
            self._key = f"{self.nice_type_name}({encode_hash(serialize(attrs))})"
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
            target_scansion: e.g. "wswswswsws" for iambic pentameter, or a
                list of targets for meters whose line length varies (e.g.
                ["wwswwswwswws", "wswwswwswws"] for anapestic tetrameter
                with an optional iamb-initial foot) — each line uses the
                target(s) matching its syllable count.
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

            # Prose fallback: for lines the parser skipped (too long), parse
            # their lineparts and stash under text._linepart_parse_results so
            # line.linepart_parses can retrieve them.
            if self.parse_unit == 'line':
                long_lnums = {ln for ln, pl in line_results.items() if len(pl) == 0}
                if long_lnums:
                    long_df = syll_df[syll_df['line_num'].isin(long_lnums)]
                    if len(long_df) > 0:
                        lp_results = parse_batch_from_df(long_df, self, line_col='linepart_num')
                        if getattr(text, '_linepart_parse_results', None) is None:
                            text._linepart_parse_results = {}
                        text._linepart_parse_results[self.key] = lp_results

            for line_num in sorted(line_results.keys()):
                pl = line_results[line_num]
                pl._text = text
                yield pl
            return

        # A single Line/LinePart entity has no _syll_df of its own: reuse its parent
        # text's, scoped to this unit, so single-unit parsing (line.parse /
        # line.best_parse) goes through the SAME DF path as text.parse() rather than
        # the entity parser. Unifies the two — line.best_parse now matches text.parse()
        # (was a real discrepancy: line-level dropped dominated cross-length readings).
        # (retire-entity-parser: replaces the Entity fallback for the common case.)
        if df_col and getattr(text, 'num', None) is not None:
            parent = getattr(text, 'text', None)
            parent_df = getattr(parent, '_syll_df', None)
            if parent_df is not None and len(parent_df) > 0:
                sub = parent_df[parent_df[df_col] == text.num]
                if len(sub) > 0:
                    from .vectorized import parse_batch_from_df
                    res = parse_batch_from_df(sub, self, line_col=df_col)
                    for ln in sorted(res.keys()):
                        pl = res[ln]
                        # hand the list its unit's wordtokens (context for scope/key/
                        # render); slots stay SyllData — not per-syllable entities.
                        pl.wordtokens = getattr(text, 'wordtokens', None)
                        pl._text = parent
                        pl.parent = text
                        text._parses = pl
                        yield pl
                    return

        # DF path for a bare WordTokenList (or any multi-unit entity, e.g. a token
        # list spanning several lines): scope the parent text's syll_df to each parse
        # unit. Its lines/lineparts live in that frame; if there is no parent frame at
        # all (a hand-built token list), parse a fresh TextModel of its text.
        # (retire-entity-parser: the entity parse_batch is gone.)
        parse_units = self.get_parse_units(text)
        if parse_units is None:
            log.warning(f"cannot parse {text}")
            return
        units = list(parse_units)[:lim] if lim else list(parse_units)
        parent_df = getattr(getattr(text, 'text', None), '_syll_df', None)
        if parent_df is None and units:
            parent_df = getattr(getattr(units[0], 'text', None), '_syll_df', None)
        if parent_df is None:
            from ..texts import TextModel
            yield from self.parse_text_iter(
                TextModel(getattr(text, 'txt', str(text))), force=force, lim=lim)
            return
        from .vectorized import parse_units_from_df
        for unit, pl in parse_units_from_df(units, parent_df, self):
            if pl is not None:
                pl._text = getattr(unit, 'text', None) or text
                pl.parent = unit
                try:
                    unit._parses = pl
                except Exception:
                    pass
                yield pl
