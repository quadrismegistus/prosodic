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


def tokenize_sents_txt(txt: str, **y: Any) -> List[str]:
    """
    Tokenize text into sentences.

    Args:
        txt: The input text to tokenize.
        **y: Additional keyword arguments.

    Returns:
        A list of sentences.
    """
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
            tok_i+=1
            # word_tok=to_token(word_str)
            numlinebreaks = word_str.count(sep_line)
            if numlinebreaks > 1:
                para_i += 1
            if numlinebreaks:
                line_i += 1
                linepart_i+=1
            is_punc = int(not any(x.isalpha() for x in word_str))
            odx_word = dict(
                txt=word_str,
                num=tok_i,
                para_num=para_i,
                line_num=line_i,
                sent_num=sent_i + 1,
                sentpart_num=sentpart_i,
                linepart_num=linepart_i,
                is_punc=is_punc
            )
            yield odx_word
            if set(word_str) & set(seps_phrase):
                sentpart_i += 1
                linepart_i += 1