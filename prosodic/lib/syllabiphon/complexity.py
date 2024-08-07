def onsetless_syls(parse):
    return len(list(filter(lambda s: s.ons == '', parse)))

def complex_onsets(parse):
    return len(list(filter(lambda s: len(s.ons) > 1, parse)))

def codas(parse):
    return len(list(filter(lambda s: s.cod, parse)))

def complex_codas(parse):
    return len(list(filter(lambda s: len(s.cod) > 1, parse)))

FEATURES = [
    onsetless_syls,
    complex_onsets,
    codas,
    complex_codas
]

def extract_features(parse, features=FEATURES):
    return [f(parse) for f in features]