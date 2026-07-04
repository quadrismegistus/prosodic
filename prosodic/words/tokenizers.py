from typing import List, Dict, Any, Callable, Optional, Iterator
from ..imports import *


@cache
def get_sent_tokenizer() -> Callable[[str], List[str]]:
    """
    Get a sentence tokenizer function.

    Returns:
        A function that tokenizes text into sentences.

    Raises:
        Exception: If NLTK punkt tokenizer fails to load.
    """
    try:
        nltk.sent_tokenize('hello')
    except Exception as e:
        nltk.download("punkt", quiet=True)
        nltk.download("punkt_tab", quiet=True)
    return nltk.sent_tokenize


def normalize_dashes(txt: str) -> str:
    """Normalize ASCII double/triple hyphens to em-dash so they trigger
    phrase splitting (SEPS_PHRASE includes — but not --)."""
    return re.sub(r'-{2,}', '\u2014', txt)


# A pure-number token: digits with an optional decimal part. Thousands-separator
# commas are stripped upstream by normalize_number_commas() so "1,000" arrives
# here as "1000".
NUMERAL_RE = re.compile(r'^\d+(?:\.\d+)?$')


def normalize_number_commas(txt: str) -> str:
    """Remove thousands-separator commas inside numbers ("1,000" -> "1000")
    so a numeral tokenizes as a single token (the word tokenizer otherwise
    splits on the comma). Only commas grouping runs of exactly three digits are
    removed, so list-style "3,4" is left untouched."""
    return re.sub(r'(?<=\d),(?=\d{3}(?:,\d{3})*(?:\D|$))', '', txt)


def is_numeral(token: str) -> bool:
    """True if the (stripped) token is a plain number: digits with an optional
    decimal part, e.g. "3", "1867", "3.5"."""
    return bool(NUMERAL_RE.match(token.strip()))


def numeral_to_words(token: str, lang: str = DEFAULT_LANG) -> Optional[str]:
    """Convert a numeric token to its spoken word form via num2words
    ("3" -> "three", "1867" -> "one thousand, eight hundred and sixty-seven").

    Returns None if num2words is unavailable or the conversion fails (non-numeric,
    too large, unsupported language) so the caller can fall back to the previous
    behavior of treating the token as punctuation. Imported lazily so a missing
    install degrades to the old drop-behavior instead of breaking import."""
    try:
        from num2words import num2words
    except ImportError:
        return None
    s = token.strip()
    try:
        n = float(s) if '.' in s else int(s)
        return num2words(n, lang=lang)
    except Exception:
        return None


def tokenize_sents_txt(txt: str, **y: Any) -> List[str]:
    """
    Tokenize text into sentences.

    Args:
        txt: The input text to tokenize.
        **y: Additional keyword arguments.

    Returns:
        A list of sentences.
    """
    txt = normalize_dashes(txt)
    txt = normalize_number_commas(txt)
    sents = get_sent_tokenizer()(txt)
    lastoffset = 0
    osents = []
    for sent in sents:
        offset = txt.find(sent, lastoffset)
        newpref = txt[lastoffset:offset]
        lastoffset = offset + len(sent)
        newsent = newpref + sent
        osents.append(newsent)
    return osents


def tokenize_words_txt(txt: str) -> List[str]:
    """
    Tokenize text into words.

    Args:
        txt: The input text to tokenize.

    Returns:
        A list of words.
    """
    l = tokenize_agnostic(txt)
    o = []
    x0 = ""
    for x in l:
        if not x.strip():
            x0 += x
        else:
            o += [x0 + x]
            x0 = ""
        # if o and not x.strip():# and not o[-1].strip():
        #     o[-1]+=x
        # else:
        #     o+=[x]
    return o


def tokenize_sentwords_df(txt: str) -> pd.DataFrame:
    """
    Tokenize text into sentences and words, returning a DataFrame.

    Args:
        txt: The input text to tokenize.

    Returns:
        A DataFrame containing tokenized sentences and words.
    """
    with logmap("tokenizing", level='trace'):
        return pd.DataFrame(tokenize_sentwords_iter(txt))


def tokenize_sentwords_iter(
    txt: str,
    sents: Optional[List[str]] = None,
    sep_line: str = SEP_LINE,
    sep_stanza: str = SEP_STANZA,
    seps_phrase: List[str] = SEPS_PHRASE,
    para_i: Optional[int] = None,
    lang: str = DEFAULT_LANG,
    **kwargs: Any
) -> Iterator[Dict[str, Any]]:
    """
    Tokenize text into sentences and words, yielding dictionaries.

    Args:
        txt: The input text to tokenize.
        sents: Optional pre-tokenized sentences.
        sep_line: Line separator.
        sep_stanza: Stanza separator.
        seps_phrase: Phrase separators.
        para_i: Optional paragraph index.
        **kwargs: Additional keyword arguments.

    Yields:
        Dictionaries containing tokenized word information.
    """
    tok_i = 0
    line_i = 1
    para_i = 1
    sentpart_i = 1
    linepart_i = 1
    start_offset = 0
    # txt = clean_text(txt)
    if sents is None:
        sents = tokenize_sents_txt(txt)
    for sent_i, sent in enumerate(sents):
        tokens = tokenize_words_txt(sent)
        for word_str in tokens:
            numlinebreaks = word_str.count(sep_line)
            if numlinebreaks > 1:
                para_i += 1
            if numlinebreaks:
                line_i += 1
                linepart_i+=1

            # Number normalization: a pure-number token ("3", "1867") would be
            # classified as punctuation (no alpha chars) and dropped from the
            # scansion. Instead spell it out via num2words and re-tokenize the
            # spoken form into normal words so each becomes scannable. If
            # conversion is unavailable/fails, fall back to the old behavior.
            sub_strs = [word_str]
            core = word_str.strip()
            if core and is_numeral(core):
                spoken = numeral_to_words(core, lang=lang)
                if spoken:
                    spoken_toks = tokenize_words_txt(spoken)
                    if spoken_toks:
                        prefix = word_str[:len(word_str) - len(word_str.lstrip())]
                        spoken_toks[0] = prefix + spoken_toks[0]
                        sub_strs = spoken_toks

            for sub_str in sub_strs:
                tok_i+=1
                is_punc = int(not any(x.isalpha() for x in sub_str))
                odx_word = dict(
                    txt=sub_str,
                    num=tok_i,
                    para_num=para_i,
                    line_num=line_i,
                    sent_num=sent_i + 1,
                    sentpart_num=sentpart_i,
                    linepart_num=linepart_i,
                    is_punc=is_punc
                )
                yield odx_word
                if set(sub_str) & set(seps_phrase):
                    sentpart_i += 1
                    linepart_i += 1