"""Poem-level analysis: meter type, line scheme, rhyme scheme, form detection.

Most users won't import from here directly — these are wired onto ``TextModel``
as properties (``text.meter_type``, ``text.rhyme_scheme``, ``text.summary()``).
"""
from .form import is_shakespearean_sonnet, is_sonnet
from .line_scheme import (
    BEAT_NAMES,
    detect_line_scheme,
    scheme_repr,
    scheme_type,
)
from .meter_type import classify_meter_type, text_foot_type
from .rhyme_scheme import (
    compute_rhyme_ids,
    load_named_schemes,
    match_rhyme_scheme,
    nums_to_scheme,
    scheme_to_nums,
)
from .summary import per_line_rows, summary

__all__ = [
    "BEAT_NAMES",
    "classify_meter_type",
    "compute_rhyme_ids",
    "detect_line_scheme",
    "is_shakespearean_sonnet",
    "is_sonnet",
    "load_named_schemes",
    "match_rhyme_scheme",
    "nums_to_scheme",
    "per_line_rows",
    "scheme_repr",
    "scheme_to_nums",
    "scheme_type",
    "summary",
    "text_foot_type",
]
