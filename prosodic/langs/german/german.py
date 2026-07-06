from ..langs import LanguageModel, cache


class GermanLanguage(LanguageModel):
    """German via espeak TTS with dictionary overrides.

    espeak-ng's German lexical stress is highly reliable (validated on
    inseparable prefixes be-/ge-/ver-/er-/zer-/ent-, separable prefixes,
    compounds, and Romance loanwords; see tests/test_german.py), so unlike
    Finnish there is no rule engine here — pronunciation flows through the
    standard dict → TTS pipeline. german.tsv seeds the dictionary with the
    few systematic espeak misses (final-stressed -ur loanwords: Natur,
    Kultur, ...). unstressed_words.txt / ambig_stress_words.txt mark
    function words for metrical flexibility, mirroring English.

    The g2p syllable-text aligner is English-only, so orthographic
    syllable labels fall back to the NLTK sonority split.
    """
    lang = 'de'
    name = 'german'
    cache_fn = 'german_wordtypes'


@cache
def German():
    return GermanLanguage()
