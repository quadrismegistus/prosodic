from ..langs import LanguageModel, cache

# English verse-elision rules, ported from Prosodic v1 (`add_elisions`). Each maps
# a two-syllable IPA sequence (``.`` = syllable boundary) to its one-syllable
# synaeresis. Applied to a word's pronunciation to add a reduced-syllable variant
# ("sweet as love, which overflows her bow'r"; "scattering unbeholden"). On by
# default via ``use_elision``; ``pool_forms`` then uses the elided reading only
# where it scans better, so it is an option, never forced.
ELISION_RULES = {
    "aʊ.ɛː": "aʊr",   # -OWER: tower, hour, bower, flower
    "ə.nəs": "nəs",   # -INOUS: ominous
    "ɛː.əs": "rəs",   # -EROUS: ponderous, adventurous
    "iː.ə":  "jə",    # -IA-: plutonian, indian, assyrian, idea
    "iː.ɛː": "ɪr",    # -IER: happier
    "ɛː.ɪŋ": "rɪŋ",   # -ERING: scattering, wondering, watering, tottering
    "ə.nɪŋ": "nɪŋ",   # -ENING: opening
    "ə.nɛː": "nɛː",   # -ENER: gardener
    "ɪ.ɛː":  "ɪr",    # -IRE: fire, fiery, attire, hired
    "uː.əl": "uːl",   # -EL/-UAL: jewel
    "ɛ.vən": "ɛvn",   # -EVN: heaven, seven
    "eɪ.ʌ":  "eɪʌ",   # -EER: sincerest, incommodiously
}


class EnglishLanguage(LanguageModel):
    lang = 'en'
    name = 'english'
    lang_espeak = 'en-us'
    use_g2p_alignment = True
    use_elision = True

    def get_elided_pronunciations(self, sylls_ipa_l):
        """One elided variant per matching rule (independent, as in v1)."""
        ipa = ".".join(sylls_ipa_l)
        out = []
        for k, v in ELISION_RULES.items():
            if k in ipa:
                elided = ipa.replace(k, v)
                if elided != ipa:
                    out.append(elided.split("."))
        return out


@cache
def English(): return EnglishLanguage()
