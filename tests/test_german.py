"""German language support: espeak-driven pronunciation + word lists.

Stress expectations are hand-derived from standard German phonology
(Duden): inseparable prefixes (be-/ge-/ver-/er-/zer-/ent-) unstressed,
separable prefixes stressed, compounds head-initial with secondary stress
on the second stem, Romance loanwords in -ie/-ur final-stressed.

Test corpus: the Tell monologue (Schiller, Wilhelm Tell IV.3, 1804
orthography from Wikisource) — canonical Blankvers (iambic pentameter).
"""
import warnings

warnings.filterwarnings("ignore")

import os

import pytest

from prosodic.imports import *
from prosodic.langs.langs import Language

TELL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "corpora", "corppoetry_de", "de.schiller.tell.txt",
)


@pytest.fixture(scope="module")
def de():
    return Language("de")


@pytest.fixture(scope="module")
def tell_txt():
    with open(TELL_PATH, encoding="utf-8") as f:
        return f.read()


def _primary_stress_idx(lang, word):
    sylls_ll, _ = lang.get(word.lower())
    form = sylls_ll[0]
    stresses = [get_syll_ipa_stress(ipa) for ipa, _ in form]
    prim = [i for i, s in enumerate(stresses) if s == "P"]
    return prim[0] if prim else None, len(form)


def test_german_language_dispatch(de):
    from prosodic.langs.german import GermanLanguage
    assert isinstance(de, GermanLanguage)
    assert de.lang == "de"
    assert de.name == "german"


def test_german_stress_prefixes(de):
    # inseparable prefixes unstressed -> stress on root syllable
    for word in ["verstehen", "beginnen", "entdecken", "gefallen", "zerbrechen"]:
        idx, n = _primary_stress_idx(de, word)
        assert idx == 1, f"{word}: primary stress on syll {idx}, expected 1"
    # separable prefixes stressed
    for word in ["aufstehen", "ausgehen"]:
        idx, n = _primary_stress_idx(de, word)
        assert idx == 0, f"{word}: primary stress on syll {idx}, expected 0"


def test_german_stress_compounds_and_loans(de):
    idx, _ = _primary_stress_idx(de, "sonnenschein")
    assert idx == 0
    # famous exceptions and Romance loans
    idx, _ = _primary_stress_idx(de, "lebendig")
    assert idx == 1  # le-BEN-dig
    idx, n = _primary_stress_idx(de, "philosophie")
    assert idx == n - 1  # final stress


def test_german_dictionary_override(de):
    # espeak initial-stresses -ur loanwords; german.tsv overrides
    idx, n = _primary_stress_idx(de, "natur")
    assert (idx, n) == (1, 2)  # na-TUR


def test_german_syllabify_hiatus(de):
    # -ehen/-uhen verbs: the eː.ə hiatus must split (metrically critical)
    assert len(de.syllabify_ipa(de.get_sylls_ipa_str_tts("gehen"))) == 2
    assert len(de.syllabify_ipa(de.get_sylls_ipa_str_tts("aufstehen"))) == 3
    assert len(de.syllabify_ipa(de.get_sylls_ipa_str_tts("ausgehen"))) == 3


def test_german_function_words():
    t = TextModel("Durch diese hohle Gasse muß er kommen,", lang="de")
    df = t._syll_df
    first = df[df.form_idx == 0]
    func = set(first[first.is_functionword].word_txt.str.strip().str.lower())
    assert {"durch", "er"} <= func
    # content words stay stressed
    by_word = (
        first.assign(w=first.word_txt.str.strip())
        .groupby("w", sort=False)["is_stressed"].any()
    )
    assert by_word["Gasse"]
    assert by_word["kommen"]


def test_german_autodetect(tell_txt):
    # default lang is 'en'; explicit lang=None triggers langdetect
    t = TextModel(tell_txt, lang=None)
    assert t.lang == "de"


def test_schiller_blankvers(tell_txt):
    t = TextModel(tell_txt, lang="de")
    t.parse()
    meters = []
    for line in t.lines:
        bp = line.best_parse
        assert bp is not None
        meters.append(bp.meter_str)
    # Blankvers: 10 sylls (masculine) or 11 (feminine ending); Schiller
    # allows the occasional longer line ("Beschützen, Landvogt – Da, ...")
    lens = [len(m) for m in meters]
    assert all(10 <= n <= 12 for n in lens), lens
    # a majority of lines should scan as strict iambic pentameter
    strict = sum(1 for m in meters if m in ("-+-+-+-+-+", "-+-+-+-+-+-"))
    assert strict >= 15, f"only {strict}/30 strict iambic lines"
    mt = t.meter_type
    assert mt["foot"] == "binary"
    assert mt["type"] == "iambic"
