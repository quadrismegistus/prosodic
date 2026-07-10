"""Principled foot delineation + headedness — a DERIVED VIEW over a Parse's
syllables (an addition to the hierarchy, not a replacement).

Footing is a SEGMENTATION problem: cut the per-syllable s/w string into feet,
minimizing a small cost. Foot size AND headedness both fall out of the cut — no
per-line k or head is assumed. Solved exactly by DP over syllable positions, so a
foot may have one head (iamb/trochee/anapest/dactyl), two (spondee), or zero
(pyrrhic) — the latter two as costed substitutions.

Headedness is then read OUT: a foot is rising/falling by where its head sits; the
line head is the majority direction of its feet; the meter's foot size is the
majority foot length.
"""

from collections import namedtuple, Counter

FOOT_LABELS = {
    "ws": "iamb", "sw": "trochee", "wws": "anapest", "sww": "dactyl",
    "wsw": "amphibrach", "sws": "cretic", "s": "bare", "w": "extrametrical",
    # disyllabic head (a strong RESOLUTION, still one beat):
    "ss": "spondee", "wss": "iamb-r", "ssw": "trochee-r", "wwss": "anapest-r",
    "ssww": "dactyl-r", "wssw": "amphibrach-r",
}


def _foot_cost(lead, head_len, trail, is_last=False, pref_size=2):
    """Cost of a foot = `lead` weaks + a strong-run head (`head_len` syllables,
    one beat) + `trail` weaks. One head per foot always; a disyllabic head is a
    strong resolution, not two beats. A bare foot (a lone head) is degenerate
    MID-line but legitimate at the LINE END — that's catalexis (a truncated final
    foot), so it's cheap there, not awful. `pref_size` is the line's dominant foot
    size (from period self-similarity): feet of that size are free, so a genuinely
    ternary line isn't broken into cheaper binary feet."""
    size = lead + head_len + trail
    if size == 1:
        return 0.5 if is_last else 10.0                  # catalexis vs mid-line degeneracy
    c = 0.0 if size == pref_size else (1.0 if size in (2, 3) else 4.0 + size)
    if lead > 0 and trail > 0:                            # head is medial (amphibrach/cretic)
        c += 2.0
    return c

Head = namedtuple("Head", ["direction", "confidence"])


class Foot:
    """A metrical foot: a VIEW grouping the syllables it spans (iamb/trochee/anapest/
    dactyl/spondee/bare/extrametrical). NOT a tree entity — a syllable keeps its one
    real parent (its WordForm) — so a Foot is an orthogonal grouping over a parse.
    **Iterating a Foot yields its syllable units**, duck-typed (`SyllData` from the
    parser, `Syllable` from a manual `Parse(line, scansion)`), so accessing feet never forces entity
    construction.

    Attributes: `pattern` ('wws'), `label` ('anapest'), `head` ('rising'/'falling'/
    'none'/'ambiguous'), `is_substituted` (inverts the line head), `slots`
    (ParseSlots), `sylls` (the syllable units)."""

    __slots__ = ("pattern", "label", "head", "is_substituted", "slots", "sylls")

    def __init__(self, pattern, label, head, is_substituted, slots, sylls):
        self.pattern = pattern
        self.label = label
        self.head = head
        self.is_substituted = is_substituted
        self.slots = slots
        self.sylls = sylls

    @property
    def txt(self) -> str:
        """The foot's text — its syllables joined."""
        return "".join(getattr(s, "txt", "") or "" for s in self.sylls)

    def to_html(self) -> str:
        """The foot as a labelled bracket of syllable spans (mtr_/str_ classes
        matching the web app); `*` in the title marks a substitution."""
        inner = "".join(
            f'<span class="mtr_{"s" if s.is_prom else "w"} '
            f'str_{"s" if getattr(s.unit, "is_stressed", False) else "w"}">'
            f'{getattr(s.unit, "txt", "")}</span>'
            for s in self.slots
        )
        cls = "foot foot_sub" if self.is_substituted else "foot"
        return f'<span class="{cls}" title="{self.label}{"*" if self.is_substituted else ""}">{inner}</span>'

    def __iter__(self):
        return iter(self.sylls)

    def __len__(self):
        return len(self.pattern)

    def __str__(self):
        return self.pattern + ("*" if self.is_substituted else "")

    def __repr__(self):
        return f"Foot({self.label}={self.pattern}{'*' if self.is_substituted else ''})"


class FootList(list):
    """A list of `Foot` with display helpers. `metrical_feet` returns this."""

    @property
    def labels(self):
        return [ft.label for ft in self]

    @property
    def patterns(self):
        return [ft.pattern for ft in self]

    @property
    def footed_scansion(self) -> str:
        """The feet as a pipe-delimited w/s string, e.g. `'wws|wws|wws|w'`."""
        return "|".join(ft.pattern for ft in self)

    def to_html(self) -> str:
        return "".join(ft.to_html() for ft in self)

    def __str__(self):
        """`'(w s)(w w s)(s w*)…'` — `*` marks a foot inverting the line head."""
        return foot_str(self)


def slot_proms(slots):
    """Per-SYLLABLE prominence (True where the syllable sits in a strong position).
    Feet are read over syllables, not positions, so a resolved juncture doesn't
    hide an inversion (see the ty·the case in the write-up)."""
    return [bool(s.is_prom) for s in slots]


def foot_head(pattern):
    """Direction of a foot from where its strong(s) sit: strong-last -> 'rising',
    strong-first -> 'falling', all-weak/all-strong -> 'none', else 'ambiguous'."""
    ns = pattern.count("s")
    if ns == 0 or ns == len(pattern):
        return "none"
    if pattern[-1] == "s" and pattern[0] != "s":
        return "rising"
    if pattern[0] == "s" and pattern[-1] != "s":
        return "falling"
    return "ambiguous"


EXTRAMETRICAL = 1.0  # cost of a line-edge lone-weak foot (anacrusis / feminine ending);
# tuned on the litlab foot-gold set: <0.5 over-peels (collapses to 67%), ~1.0-1.5 is
# the 97.5% plateau, too high stops peeling and reverts to the 93.3% no-edge baseline.


def _foot_dp(proms, pref_size):
    """Core DP: cut `proms` into exactly #strong-runs feet (one head each), the weak
    runs distributed to neighbouring feet to minimise total _foot_cost. Returns
    (spans, total_cost)."""
    n = len(proms)
    runs, i = [], 0                                  # maximal strong runs = heads
    while i < n:
        if proms[i]:
            j = i
            while j < n and proms[j]:
                j += 1
            runs.append((i, j))
            i = j
        else:
            i += 1
    if not runs:
        return ([(0, n)] if n else []), 0.0
    m = len(runs)
    hlen = [e - s for s, e in runs]
    # weak-run lengths: g[0] before run 0, g[k] between run k-1/k, g[m] after last
    g = [runs[0][0]] + [runs[k][0] - runs[k - 1][1] for k in range(1, m)] + [n - runs[-1][1]]

    def cost(lead, k, trail):
        return _foot_cost(lead, hlen[k], trail, is_last=(k == m - 1), pref_size=pref_size)

    INF = float("inf")
    dp = {g[0]: (0.0, None)}                          # foot 0's leading weaks are fixed = g[0]
    back = []
    for k in range(m - 1):
        g1, ndp, ch = g[k + 1], {}, {}
        for lead_next in range(g1 + 1):
            trail_k, best, bp = g1 - lead_next, INF, None
            for lead_k, (c0, _) in dp.items():
                c = c0 + cost(lead_k, k, trail_k)
                if c < best:
                    best, bp = c, lead_k
            ndp[lead_next], ch[lead_next] = (best, bp), bp
        dp, _ = ndp, back.append(ch)
    best, best_lead = INF, None
    for lead_k, (c0, _) in dp.items():
        c = c0 + cost(lead_k, m - 1, g[m])
        if c < best:
            best, best_lead = c, lead_k
    leads = [0] * m
    leads[m - 1] = best_lead
    for k in range(m - 2, -1, -1):
        leads[k] = back[k][leads[k + 1]]
    trails = [(g[k + 1] - leads[k + 1]) if k < m - 1 else g[m] for k in range(m)]
    return [(runs[k][0] - leads[k], runs[k][1] + trails[k]) for k in range(m)], best


def foot_parse(proms, pref_size=None, extrametrical=True):
    """Foot-parse by DP. Heads are strong RUNS (each maximal run of strongs = one
    beat = one position, 1-2 syllables); the weak runs between/around them are
    distributed to the neighbouring feet. So #feet = #strong-runs, exactly one head
    per foot — no pyrrhic, no two-head spondee. With `extrametrical` (default), a
    line-INITIAL lone weak (anacrusis) and/or line-FINAL lone weak (feminine ending)
    may be split off as their own headless edge feet (`w|…`, `…|w`) when that lets the
    interior feet be cleaner — a hand-scansion convention validated on the litlab
    foot-gold set (recovers `wws|wws|wws|w` over the forced `wws|wws|wwsw`). Returns
    (start, end) foot spans covering [0, len)."""
    proms = [bool(p) for p in proms]
    n = len(proms)
    if pref_size is None:
        # dominant foot size from period self-similarity (dactyl/anapest repeat with
        # period 3, iamb/trochee with period 2) — prefer it so the cost doesn't break
        # a genuinely-ternary line into cheaper binary feet.
        def _sim(k):
            return sum(proms[i] == proms[i - k] for i in range(k, n)) / (n - k) if n > k else 0.0
        pref_size = 3 if _sim(3) > _sim(2) else 2
    if not extrametrical:
        return _foot_dp(proms, pref_size)[0]
    best_spans, best_cost = None, float("inf")
    for ana in (0, 1):                               # peel a leading weak as anacrusis?
        for fem in (0, 1):                           # peel a trailing weak as feminine?
            if ana and (not n or proms[0]):
                continue                             # can only peel a WEAK edge
            if fem and (not n or proms[-1]):
                continue
            lo, hi = ana, n - fem
            interior = proms[lo:hi]
            if lo >= hi or not any(interior):
                continue                             # a head must remain in the interior
            spans, c = _foot_dp(interior, pref_size)
            c += EXTRAMETRICAL * (ana + fem)
            spans = [(a + lo, b + lo) for a, b in spans]
            if ana:
                spans = [(0, 1)] + spans
            if fem:
                spans = spans + [(n - 1, n)]
            if c < best_cost:
                best_cost, best_spans = c, spans
    return best_spans if best_spans is not None else _foot_dp(proms, pref_size)[0]


def line_head(patterns):
    """Line headedness = majority direction of the directional feet, with a
    confidence in [0,1]."""
    d = Counter(foot_head(p) for p in patterns)
    r, f = d.get("rising", 0), d.get("falling", 0)
    if r + f == 0:
        # no directional feet (all spondaic/pyrrhic/lone): honest "none", NOT a
        # false "rising" — so Parse.is_rising can report unknown rather than a
        # phantom iamb. ("none" ⇒ no foot is marked substituted, since none is
        # directional anyway.)
        return Head("none", 0.0)
    return Head("rising" if r >= f else "falling", abs(r - f) / (r + f))


def parse_feet(slots, head=None):
    """Foot-parse `slots` (variable size + headedness) into labelled Foot objects.
    A foot is `is_substituted` when its direction disagrees with the line head."""
    spans = foot_parse(slot_proms(slots))
    patterns = ["".join("s" if slots[k].is_prom else "w" for k in range(a, b)) for a, b in spans]
    if head is None:
        head = line_head(patterns).direction
    feet = FootList()
    for (a, b), pat in zip(spans, patterns):
        fh = foot_head(pat)
        chunk = slots[a:b]
        feet.append(Foot(pat, FOOT_LABELS.get(pat, pat), fh,
                         fh not in (head, "none", "ambiguous"),
                         chunk, [c.unit for c in chunk]))
    return feet


def foot_str(feet):
    """'(w s)(w w s)(s w*)…' — '*' marks a foot that inverts the line head."""
    return "".join(f"({' '.join(ft.pattern)}{'*' if ft.is_substituted else ''})" for ft in feet)
