"""Grapheme-to-phoneme alignment for orthographic syllable labels.

The syllable *text* shown for a word (e.g. the "wit"/"hin" of "within") has
historically come from NLTK's sonority syllabifier, which splits the spelling
with no knowledge of the pronunciation — so its boundaries routinely disagree
with the IPA syllabification they're displayed next to (issue #47: "within"
rendered as wit|hin against wɪ|ðɪn).

This module instead aligns the token's letters to its IPA phones with a small
dynamic program, then cuts the spelling at the letter positions where the IPA
syllables begin: "within" → wi|thin, "thereby" → there|by.

align_syllable_text() returns None whenever it can't produce a confident,
non-degenerate split; callers fall back to the legacy heuristic path.
"""

from functools import lru_cache

# Letter spans that can spell each phone. Keys are gruut-segmented phone
# strings as they appear in the English dictionary/TTS pipeline (see
# _parse_ipa_cached: stress marks and combining diacritics are stripped, so
# syllabic n̩ arrives as plain "n"). Order within a tuple doesn't matter; the
# DP tries every entry. Vowel phones are handled generically (see below) and
# only need listing here when they take consonant-looking spellings.
PHONE_SPELLINGS = {
    "p": ("p", "pp", "pe"),
    "b": ("b", "bb", "be"),
    "t": ("t", "tt", "te", "ed", "bt", "th"),
    "d": ("d", "dd", "de", "ed"),
    "k": ("k", "c", "ck", "cc", "ch", "q", "qu", "que", "ke", "kh", "lk"),
    "ɡ": ("g", "gg", "gh", "gue", "gu"),
    "m": ("m", "mm", "me", "mb", "mn", "gm", "lm"),
    "n": ("n", "nn", "ne", "kn", "gn", "pn"),
    "ŋ": ("ng", "n", "ngue"),
    "f": ("f", "ff", "ph", "gh", "fe"),
    "v": ("v", "ve", "vv", "f", "ph"),
    "θ": ("th",),
    "ð": ("th", "the"),
    "s": ("s", "ss", "c", "sc", "ce", "se", "ps", "st", "ts"),
    "z": ("z", "zz", "s", "se", "ze", "ss", "es"),
    "ʃ": ("sh", "ti", "ci", "si", "ssi", "ss", "s", "ch", "sci", "ce", "sch", "sc"),
    "ʒ": ("si", "s", "g", "ge", "z", "zi", "j", "ti"),
    "h": ("h", "wh", "j"),
    "ʧ": ("ch", "tch", "t", "ti", "tu", "c", "cz"),
    "ʤ": ("j", "g", "dg", "dge", "ge", "gg", "d", "di", "dj"),
    "l": ("l", "ll", "le", "sl"),
    "r": ("r", "rr", "wr", "re", "rh", "rrh"),
    "ɹ": ("r", "rr", "wr", "re", "rh", "rrh"),
    "w": ("w", "wh", "u", "o", "ou"),
    "j": ("y", "i", "j", "ll", "e"),
    "ɾ": ("t", "tt", "d", "dd"),  # espeak flap
    "ʔ": ("t", "tt"),             # espeak glottal stop (button, glutton)
    "x": ("ch", "gh"),            # loch
}

# Phone pairs that a single letter span can spell (one-to-many): "x" is /k s/,
# vowel+glide onsets like the /j uː/ of "use", the /w ʌ/ of "one".
PAIR_SPELLINGS = {
    ("k", "s"): ("x", "xe", "cc", "xc"),
    ("ɡ", "z"): ("x", "xh"),
    ("k", "ʃ"): ("x", "xi"),
    ("j", "uː"): ("u", "ue", "ew", "eu", "iew", "you"),
    ("j", "ʊ"): ("u",),
    ("j", "ə"): ("u", "ia", "io"),
    ("w", "ʌ"): ("o",),
    ("w", "ɪ"): ("ui",),
}

# Phones that behave as vowels for the generic matching rules. Includes the
# monophthong/length variants seen in the dictionary and espeak output, plus
# the bare "a"/"e"/"o" left when gruut splits a diphthong into two units.
VOWEL_PHONES = frozenset({
    "a", "e", "i", "o", "u", "y",
    "ɪ", "ʊ", "ɛ", "æ", "ʌ", "ə", "ɑ", "ɒ", "ɔ",
    "iː", "uː", "ɔː", "ɑː", "ɛː", "ɜː", "əː", "aː", "eː", "oː",
    "ɚ", "ɝ", "ɜ",
    "aɪ", "eɪ", "ɔɪ", "aʊ", "oʊ", "əʊ", "ɪə", "eə", "ʊə",
})

VOWEL_LETTERS = frozenset("aeiouy")

# Multi-letter spans a vowel phone (or a gruut-split diphthong pair) may
# consume in one step. Single vowel letters are always tried.
VOWEL_DIGRAPHS = (
    "eigh", "aigh", "ough", "augh", "igh",
    "ea", "ee", "ai", "ay", "ei", "ey", "ie", "oa", "oo", "ou", "ow",
    "oi", "oy", "au", "aw", "eu", "ew", "ue", "ui", "oe", "ao", "eo",
    "ia", "io", "ua", "uo", "ye", "aye", "eye",
)

# Long vowels that swallow a written r in r-less dictionary pronunciations
# ("galleria" ɡæ.lɛː.iː.ə — the "ller" letters must land on lɛː). The DP
# tries these as vowel+r digraphs at the same cost as other digraphs.
R_COLORED_VOWELS = frozenset({"ɛː", "ɑː", "ɔː", "əː", "ɜː", "ɚ", "ɝ", "ɜ"})

# DP operation costs. Table matches are free so the aligner prefers them;
# everything else is a progressively grudging concession. Tuned against the
# full English dictionary (see tests/test_g2p_align.py for the acceptance
# examples and scripts in the PR for the corpus sweep).
COST_GENERIC_VOWEL = 0.25      # vowel phone ↔ single vowel letter
COST_VOWEL_DIGRAPH = 0.35      # vowel phone/pair ↔ vowel digraph
COST_SILENT_FINAL_E = 0.2      # trailing silent e
COST_SILENT_VOWEL = 0.6        # other unspoken vowel letter
COST_SILENT_CONSONANT = 1.0    # unspoken consonant letter
COST_UNSPELLED_PHONE = 1.5     # phone with no letters at all
MAX_COST_PER_PHONE = 1.0       # reject alignments worse than this on average


def _phone_units(sylls_ipa_l):
    """Flatten syllable IPA strings to (phone, syll_idx) units via gruut."""
    from prosodic.words.syllables import _parse_ipa_cached

    units = []
    for syll_idx, syll_ipa in enumerate(sylls_ipa_l):
        phones = _parse_ipa_cached(syll_ipa)
        if not phones:
            return None
        units.extend((p, syll_idx) for p in phones)
    return units


@lru_cache(maxsize=None)
def align_syllable_text(token, sylls_ipa_l):
    """Split `token`'s spelling at its IPA syllable boundaries.

    Args:
        token: the word as written (case and apostrophes preserved).
        sylls_ipa_l: tuple of per-syllable IPA strings (stress marks ok).

    Returns:
        List of orthographic syllables (joining back to `token` exactly,
        one per input syllable), or None if no confident alignment exists.
    """
    if not token or not sylls_ipa_l:
        return None
    if len(sylls_ipa_l) == 1:
        return [token]

    letters = token.lower()
    units = _phone_units(sylls_ipa_l)
    if not units:
        return None

    L, U = len(letters), len(units)
    INF = float("inf")
    # dp[i][j] = min cost aligning letters[:i] with units[:j]
    dp = [[INF] * (U + 1) for _ in range(L + 1)]
    # back[i][j] = (prev_i, prev_j) for reconstruction
    back = [[None] * (U + 1) for _ in range(L + 1)]
    dp[0][0] = 0.0

    def relax(i, j, ni, nj, cost):
        c = dp[i][j] + cost
        if c < dp[ni][nj]:
            dp[ni][nj] = c
            back[ni][nj] = (i, j)

    for i in range(L + 1):
        for j in range(U + 1):
            if dp[i][j] == INF:
                continue
            rest = letters[i:]
            # --- silent / non-letter characters (apostrophes, hyphens) ---
            if i < L:
                ch = letters[i]
                if not ch.isalpha():
                    relax(i, j, i + 1, j, 0.0)
                elif ch == "e" and i == L - 1:
                    relax(i, j, i + 1, j, COST_SILENT_FINAL_E)
                elif ch in VOWEL_LETTERS:
                    relax(i, j, i + 1, j, COST_SILENT_VOWEL)
                else:
                    relax(i, j, i + 1, j, COST_SILENT_CONSONANT)
            if j < U:
                phone = units[j][0]
                # --- phone with no letters ---
                relax(i, j, i, j + 1, COST_UNSPELLED_PHONE)
                # --- table match ---
                for sp in PHONE_SPELLINGS.get(phone, ()):
                    if rest.startswith(sp):
                        relax(i, j, i + len(sp), j + 1, 0.0)
                # --- generic vowel matches ---
                if phone in VOWEL_PHONES:
                    if rest[:1] in VOWEL_LETTERS:
                        relax(i, j, i + 1, j + 1, COST_GENERIC_VOWEL)
                    for dg in VOWEL_DIGRAPHS:
                        if rest.startswith(dg):
                            relax(i, j, i + len(dg), j + 1, COST_VOWEL_DIGRAPH)
                    if phone in R_COLORED_VOWELS:
                        for vl in VOWEL_LETTERS:
                            for tail in (vl + "r", vl + "rr", vl + "re"):
                                if rest.startswith(tail):
                                    relax(i, j, i + len(tail), j + 1, COST_VOWEL_DIGRAPH)
                # --- phone-pair spellings (same-syllable only: a shared
                # letter span across a syllable boundary would leave that
                # boundary with no letter position to cut at) ---
                if j + 1 < U and units[j][1] == units[j + 1][1]:
                    pair = (phone, units[j + 1][0])
                    for sp in PAIR_SPELLINGS.get(pair, ()):
                        if rest.startswith(sp):
                            relax(i, j, i + len(sp), j + 2, 0.0)
                    # two gruut-split diphthong halves sharing one vowel span
                    if phone in VOWEL_PHONES and pair[1] in VOWEL_PHONES:
                        if rest[:1] in VOWEL_LETTERS:
                            relax(i, j, i + 1, j + 2, COST_GENERIC_VOWEL)
                        for dg in VOWEL_DIGRAPHS:
                            if rest.startswith(dg):
                                relax(i, j, i + len(dg), j + 2, COST_VOWEL_DIGRAPH)

    if dp[L][U] == INF or dp[L][U] > MAX_COST_PER_PHONE * U:
        return None

    # Walk back to find, for each unit, the letter span it consumed.
    # unit_start[j] = letter index where unit j's span begins.
    unit_start = [None] * U
    i, j = L, U
    while (i, j) != (0, 0):
        pi, pj = back[i][j]
        for jj in range(pj, j):
            unit_start[jj] = pi
        i, j = pi, pj

    # Letter boundary before each syllable = start of its first unit.
    n_sylls = len(sylls_ipa_l)
    bounds = [0]
    for s in range(1, n_sylls):
        first_unit = next(k for k, (_, si) in enumerate(units) if si == s)
        b = unit_start[first_unit]
        if b is None:
            return None
        # Geminate aesthetics: cut doubled consonants (and "ck") down the
        # middle — nig|gar, glut|ton, tuc|ker — rather than before the pair.
        if (
            0 < b < L - 1
            and letters[b].isalpha()
            and letters[b] not in VOWEL_LETTERS
            and (letters[b] == letters[b + 1] or letters[b : b + 2] == "ck")
        ):
            b += 1
        bounds.append(b)
    bounds.append(L)

    # Boundaries must be strictly increasing: every syllable needs letters.
    if any(b2 <= b1 for b1, b2 in zip(bounds, bounds[1:])):
        return None

    return [token[a:b] for a, b in zip(bounds, bounds[1:])]
