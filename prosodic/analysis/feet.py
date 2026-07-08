"""Principled foot delineation + headedness — a DERIVED VIEW over a Parse's
metrical positions (an addition to the hierarchy, not a replacement).

Two ideas, both computed post-hoc from the scansion (no re-parsing):

1. HEADEDNESS is a *phase* parameter — do beats fall on the rise (iamb/anapest,
   "rising") or the fall (trochee/dactyl, "falling")? The per-position scansion
   is head-agnostic (the exhaustive parser doesn't prefer either), so headedness
   is *inferred* by the phase of the strong-beat pattern. Aggregating over more
   positions gives a more robust estimate — hence the same estimator works at
   poem / line / foot scale, differing only in support:
     - line:  head_of(one line's positions)  -> (direction, confidence)
     - poem:  mean of the line estimates
   This is robust to a lone inversion, unlike reading position[0] alone.

2. FEET are the positions chunked by (foot_size, head). For an in-phase line the
   *boundaries* are just every-k-from-0 regardless of head — headedness tells you
   which slot in each foot is the beat, and thus whether a foot is *substituted*
   (its intrinsic head disagrees with the line's). Syllables inherit their foot
   from their position, so resolution/elision never shift a boundary.
"""

from collections import namedtuple

# position-level pattern (one char per POSITION, s=strong/head w=weak) -> label
FOOT_LABELS = {
    "ws": "iamb", "sw": "trochee", "ww": "pyrrhic", "ss": "spondee",
    "wws": "anapest", "sww": "dactyl", "wsw": "amphibrach", "sws": "cretic",
    "www": "tribrach", "sss": "molossus",
}

Head = namedtuple("Head", ["direction", "confidence"])
Foot = namedtuple("Foot", ["pattern", "label", "head", "is_substituted", "slots", "sylls"])


def slot_proms(slots):
    """Per-SYLLABLE prominence: True where the syllable sits in a strong position.

    Feet are read over SYLLABLES, not positions: traditional scansion pairs
    syllables, so "Pi-ty | the-world" = (S w)(w S) shows the trochaic first-foot
    inversion. Prosodic can't store that (two weak *positions* can't be adjacent),
    so it resolves the ty·the juncture into one weak position — but the per-slot
    prominence still carries the syllable-level pattern the feet need."""
    return [bool(s.is_prom) for s in slots]


def head_of(proms, foot_size=2):
    """Headedness by the phase of the strong-beat pattern.

    A foot of size k has its head on the last slot when rising (…w s) and the
    first slot when falling (s w…). So count strong positions whose index mod k
    lands on each candidate head slot:

        rising  beats: index % k == k-1     falling beats: index % k == 0

    Returns Head(direction, confidence) with confidence =
    |rising - falling| / (rising + falling) in [0, 1]. A clean iambic line ->
    ('rising', 1.0); one initial trochee in pentameter -> ('rising', ~0.6);
    a 50/50 line -> confidence 0.0.
    """
    k = foot_size
    rising = sum(1 for i, s in enumerate(proms) if s and i % k == k - 1)
    falling = sum(1 for i, s in enumerate(proms) if s and i % k == 0)
    total = rising + falling
    if total == 0:
        return Head("rising", 0.0)
    direction = "rising" if rising >= falling else "falling"
    return Head(direction, abs(rising - falling) / total)


def foot_head(pattern):
    """Intrinsic head of a foot from where its strong position sits: strong-last
    -> 'rising', strong-first -> 'falling', all-weak/all-strong -> 'none',
    otherwise 'ambiguous'."""
    ns = pattern.count("s")
    if ns == 0 or ns == len(pattern):
        return "none"  # pyrrhic / spondee — no directional head
    if pattern[-1] == "s" and pattern[0] != "s":
        return "rising"
    if pattern[0] == "s" and pattern[-1] != "s":
        return "falling"
    return "ambiguous"


def parse_feet(slots, foot_size=2, head=None):
    """Chunk SYLLABLE SLOTS into feet of `foot_size` from slot 0, keeping any short
    final foot (fixes the old bug that dropped an odd line's last position). Footing
    over slots (not positions) is what recovers traditional scansion: a resolution
    that prosodic stores as one weak position gets split across a foot boundary when
    that's where the pairing falls (ty·the -> …ty)(the…). A foot is `is_substituted`
    when its intrinsic head is directional and disagrees with the line `head`.
    """
    proms = slot_proms(slots)
    if head is None:
        head = head_of(proms, foot_size).direction
    feet = []
    for i in range(0, len(slots), foot_size):
        chunk = slots[i : i + foot_size]
        pattern = "".join("s" if s.is_prom else "w" for s in chunk)
        fh = foot_head(pattern)
        sylls = [s.unit for s in chunk]
        substituted = fh not in (head, "none", "ambiguous")
        feet.append(Foot(pattern, FOOT_LABELS.get(pattern, pattern), fh, substituted, chunk, sylls))
    return feet


def foot_str(feet):
    """Compact rendering: '(w s)(w s)(s w*)...' — '*' marks a substituted foot."""
    return "".join(f"({' '.join(ft.pattern)}{'*' if ft.is_substituted else ''})" for ft in feet)
