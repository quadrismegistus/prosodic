from pprint import pprint
import pytest
from prosodic.texts import Text, Stanza
from prosodic.lines import Line
from prosodic.words import WordForm, Word
from prosodic.syllables import Syllable

@pytest.fixture
def sample_text():
    return Text("The cat\nsat on the mat.\nThe dog\nlay on the log.")

@pytest.fixture
def sample_stanza():
    return Stanza("The cat\nsat on the mat.\nThe dog\nlay on the log.")

@pytest.fixture
def sample_lines():
    return [
        Line("The cat"),
        Line("sat on the mat"),
        Line("The dog"),
        Line("lay on the log.")
    ]

@pytest.fixture
def sample_wordforms():
    return [
        # WordForm("mat", sylls_ipa=["mæt"], sylls_text=["mat"]),
        # WordForm("cat", sylls_ipa=["kæt"], sylls_text=["cat"]),
        # WordForm("log", sylls_ipa=["lɔg"], sylls_text=["log"]),
        # WordForm("dog", sylls_ipa=["dɔg"], sylls_text=["dog"])
        Word('silver').wordforms[0],
        Word('blur').wordforms[0],
        Word('log').wordforms[0],
        Word('dog').wordforms[0],
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
    
    # Test similar rimes
    assert mat.rime_distance(cat) < mat.rime_distance(log), "Distance between 'mat' and 'cat' should be less than 'mat' and 'log'"
    assert log.rime_distance(dog) < log.rime_distance(mat), "Distance between 'log' and 'dog' should be less than 'log' and 'mat'"

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