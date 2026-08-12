from pprint import pprint
import pytest
from prosodic.imports import *

@pytest.fixture
def sample_text():
    return TextModel("The cat\nsat on the mat.\nThe dog\nlay on the log.")

@pytest.fixture
def sample_stanza():
    return TextModel("The cat\nsat on the mat.\nThe dog\nlay on the log.").stanza1

@pytest.fixture
def sample_lines():
    return [
        TextModel("The cat").line1,
        TextModel("sat on the mat").line1,
        TextModel("The dog").line1,
        TextModel("lay on the log.").line1,
    ]

@pytest.fixture
def sample_wordforms():
    return [
        TextModel('mat').wordform1,
        TextModel('cat').wordform1,
        TextModel('log').wordform1,
        TextModel('dog').wordform1,
    ]

def test_text_get_rhyming_lines(sample_text):
    rhyming_lines = sample_text.get_rhyming_lines()
    assert len(rhyming_lines) == 2, "Expected 2 rhyming lines"
    assert all(isinstance(line, Line) for line in rhyming_lines.keys()), "All keys should be Line instances"
    assert all(isinstance(item, tuple) for item in rhyming_lines.values()), "All values should be tuples"
    assert all(len(item) == 2 for item in rhyming_lines.values()), "Each tuple should have 2 elements"
    assert all(isinstance(item[0], (float,int)) and isinstance(item[1], Line) for item in rhyming_lines.values()), "Each tuple should contain a float and a Line"

def test_stanza_get_rhyming_lines(sample_stanza):
    rhyming_lines = sample_stanza.get_rhyming_lines()
    assert len(rhyming_lines) == 2, "Expected 2 rhyming lines"
    assert all(isinstance(line, Line) for line in rhyming_lines.keys()), "All keys should be Line instances"
    assert all(isinstance(item, tuple) for item in rhyming_lines.values()), "All values should be tuples"
    assert all(len(item) == 2 for item in rhyming_lines.values()), "Each tuple should have 2 elements"
    assert all(isinstance(item[0], (float,int)) and isinstance(item[1], Line) for item in rhyming_lines.values()), "Each tuple should contain a float and a Line"


def test_line_rime_distance(sample_lines):
    line1, line2 = sample_lines[:2]
    distance = line1.rime_distance(line2)
    assert isinstance(distance, (float,int)), "Rime distance should be a float"
    assert 0 <= distance <= 1, "Rime distance should be between 0 and 1"  # Assuming the distance is normalized

def test_wordform_rime_distance(sample_wordforms):
    mat, cat, log, dog = sample_wordforms

    # Test with feature distance (max_dist=None for gradient distances)
    assert mat.rime_distance(cat, max_dist=None) < mat.rime_distance(log, max_dist=None), \
        "Distance between 'mat' and 'cat' should be less than 'mat' and 'log'"
    assert log.rime_distance(dog, max_dist=None) < log.rime_distance(mat, max_dist=None), \
        "Distance between 'log' and 'dog' should be less than 'log' and 'mat'"

    # Test exact-match mode (default max_dist=0)
    assert mat.rime_distance(cat) == 0, "'mat' and 'cat' should have identical rimes"
    assert log.rime_distance(dog) == 0, "'log' and 'dog' should have identical rimes"

def test_syllable_rime(sample_wordforms):
    mat = sample_wordforms[0]
    syll = mat.syllables[0]
    
    rime = syll.rime
    assert len(rime) > 0, "Rime should not be empty"
    assert all(phon.is_rime for phon in rime), "All phonemes in rime should have is_rime=True"
    assert rime[-1].is_coda, "Last phoneme in rime should be coda"
    assert rime[0].is_nucleus, "First phoneme in rime should be nucleus"

def test_text_is_rhyming(sample_text):
    assert sample_text.is_rhyming, "Sample text should be rhyming"

def test_stanza_is_rhyming(sample_stanza):
    assert sample_stanza.is_rhyming, "Sample stanza should be rhyming"

def test_text_num_rhyming_lines(sample_text):
    assert sample_text.num_rhyming_lines == 2, "Sample text should have 2 rhyming lines"

def test_stanza_num_rhyming_lines(sample_stanza):
    assert sample_stanza.num_rhyming_lines == 2, "Sample stanza should have 2 rhyming lines"

def _wf(word):
    return TextModel(word).wordtokens[0].wordform


def test_rime_type_bands():
    """2-D Walker-calibrated regions (scripts/rime_eval.py): perfect =
    nucleus match + near-coda; slant = coda identity (consonance);
    assonance = nucleus identity + coda mismatch. Hand-verified (dn, dc):
    day/may (0,0), love/prove (.33,0), gone/alone (.58,0),
    day/night (.08,1.0), day/late (0,1.0), cat/dog (.42,.46)."""
    # perfect
    assert _wf("day").rime_type(_wf("may")) == "perfect"
    assert _wf("night").rime_type(_wf("light")) == "perfect"
    # classic slant rhymes: coda identical, nucleus free
    assert _wf("love").rime_type(_wf("prove")) == "slant"
    assert _wf("blood").rime_type(_wf("good")) == "slant"
    assert _wf("gone").rime_type(_wf("alone")) == "slant"
    # the 1-D scalar tied day/night with gone/alone at 0.389; the 2-D
    # decomposition separates them (coda mismatch vs coda identity)
    assert _wf("day").rime_type(_wf("night")) is None
    # assonance: nucleus identical, coda differs (weaker, Walker-unvalidated)
    assert _wf("day").rime_type(_wf("late")) == "assonance"
    assert _wf("deep").rime_type(_wf("beat")) == "assonance"
    # non-rhymes
    assert _wf("cat").rime_type(_wf("dog")) is None
    assert _wf("table").rime_type(_wf("running")) is None
    # identical words do not rhyme with themselves
    assert _wf("day").rime_type(_wf("day")) is None
    # thresholds overridable per call
    assert _wf("day").rime_type(_wf("late"), assonance_nuc_max=-1) is None


def test_rime_distance_nc():
    dn, dc = _wf("gone").rime_distance_nc(_wf("alone"))
    assert dc == 0.0 and dn > 0.3          # consonance signature
    dn, dc = _wf("day").rime_distance_nc(_wf("night"))
    assert dc == 1.0 and dn < 0.15         # open-vs-closed coda mismatch
    dn, dc = _wf("day").rime_distance_nc(_wf("may"))
    assert (dn, dc) == (0.0, 0.0)


def test_glides_are_onsets_not_nuclei():
    """A glide is [-cons] exactly as every vowel is, so classifying phonemes by
    `cons` made /w/ and /j/ vowels: "warm" put its own onset in the nucleus and
    carried it into the rime. Syllabicity is what separates the two."""
    warm = _wf("warm")
    syll = warm.syllables[0]
    phons = list(syll.rime)  # accessing .rime is what annotates onset/rime
    assert [p.txt for p in syll.children] == ["w", "ɔː", "r", "m"]
    assert syll.children[0].is_vowel is False, "/w/ is a glide, not a vowel"
    assert syll.children[0].is_onset, "/w/ opens the syllable"
    assert [p.txt for p in phons] == ["ɔː", "r", "m"], "rime excludes the onset"
    assert phons[0].is_nucleus and phons[-1].is_coda


def test_glide_onset_does_not_demote_a_perfect_rhyme():
    """What the misclassification cost: with half the nucleus apparently missing,
    every perfect rhyme with a glide on one side came back 'slant'."""
    for first, second in [
        ("warm", "storm"),
        ("way", "day"),
        ("win", "sin"),
        ("young", "sung"),
        ("wing", "sing"),
        ("yearn", "burn"),
    ]:
        pair = f"{first}/{second}"
        assert _wf(first).rime_type(_wf(second)) == "perfect", pair
        assert _wf(first).rime_distance_nc(_wf(second)) == (0.0, 0.0), pair


def test_glides_do_not_make_a_diphthong():
    """Syllable weight reads the same classification, so a glide counted as a
    vowel also invented diphthongs: /wʌn/ and /mjə/ have one vowel each, and an
    open short /mjə/ is light."""
    assert _wf("one").syllables[0].has_dipthong is False
    assert _wf("way").syllables[0].has_dipthong is True, "/eɪ/ is a real diphthong"
    assert [s.weight for s in _wf("accumulate").syllables] == ["L", "H", "L", "H"]


def test_line_rime_type():
    t = TextModel(
        "Shall I compare thee to a summer's day?\n"
        "Thou art more lovely and more temperate:\n"
        "Rough winds do shake the darling buds of May,\n"
    )
    lines = t.lines
    assert lines[0].rime_type(lines[2]) == "perfect"   # day / May
    assert lines[0].rime_type(lines[1]) is None        # day / temperate


def test_rime_type_sonnet_scheme_validation():
    """Real-verse validation: sonnet rhyme scheme (ABAB CDCD EFEF GG)
    supplies both positives and TRUE negatives. Full-corpus numbers
    (scripts/rime_eval.py): bands F1 0.912, FPR 0.041. This pins a
    25-sonnet subset with slack for pronunciation drift."""
    import os
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "corpora", "corppoetry_en", "en.shakespeare.txt")
    with open(path) as f:
        stanzas = f.read().split("\n\n")
    t = TextModel("\n\n".join(stanzas[:25]))
    POS = [(0, 2), (1, 3), (4, 6), (5, 7), (8, 10), (9, 11), (12, 13)]
    NEG = [(0, 1), (1, 2), (2, 3), (4, 5), (5, 6), (6, 7),
           (8, 9), (9, 10), (10, 11)]
    pos, neg = [], []
    for st in t.stanzas:
        lines = st.lines
        if len(lines) != 14:
            continue
        for idxs, bucket in ((POS, pos), (NEG, neg)):
            for i, j in idxs:
                a = lines[i].wordforms_nopunc[-1]
                b = lines[j].wordforms_nopunc[-1]
                if a.txt != b.txt:
                    bucket.append((a, b))
    assert len(pos) > 100 and len(neg) > 150

    def is_rhyme(a, b):
        return a.rime_type(b) in ("perfect", "slant")

    tpr = sum(1 for a, b in pos if is_rhyme(a, b)) / len(pos)
    fpr = sum(1 for a, b in neg if is_rhyme(a, b)) / len(neg)
    assert tpr > 0.80, f"TPR {tpr:.3f}"
    assert fpr < 0.10, f"FPR {fpr:.3f}"


def test_rhyme_ids_band_mode_fixes_sonnet_106():
    """Sonnet 106's third quatrain rhymes prophecies/eyes and
    prefiguring/sing — consonance the legacy scalar mode couldn't hear
    (it classified 106 as 'Sonnet A'). Band mode detects them; the
    legacy path stays available via an explicit max_dist."""
    import os
    from prosodic.analysis.rhyme_scheme import compute_rhyme_ids
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "corpora", "corppoetry_en", "en.shakespeare.txt")
    with open(path) as f:
        stanzas = f.read().split("\n\n")
    t = TextModel(stanzas[105])
    rs = t.rhyme_scheme
    assert rs["form"].replace(" ", "") == "ababcdcdefefgg", rs
    ids_legacy = compute_rhyme_ids(t, max_dist=0.35)
    ids_bands = compute_rhyme_ids(t)
    assert ids_bands != ids_legacy
