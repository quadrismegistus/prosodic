from .imports import *


def tokenize_agnostic(txt):
    return re.findall(r"[\w']+|[.,!?; -—–'\n]", txt)


@cache
def get_sent_tokenizer():
    try:
        nltk.sent_tokenize('hello')
    except Exception as e:
        nltk.download("punkt", quiet=True)
    return nltk.sent_tokenize


def tokenize_sents_txt(txt, **y):
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


def tokenize_words_txt(txt):
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


def tokenize_sentwords_df(txt):
    with logmap("tokenizing"):
        return pd.DataFrame(tokenize_sentwords_iter(txt))


def tokenize_sentwords_iter(
    txt,
    sents=None,
    sep_line=SEP_LINE,
    sep_stanza=SEP_STANZA,
    seps_phrase=SEPS_PHRASE,
    para_i=None,
    **kwargs
):
    char_i = 0
    line_i = 1
    stanza_i = 1
    linepart_i = 1
    linepart_ii = 0
    start_offset = 0
    txt = clean_text(txt)
    if sents is None:
        sents = tokenize_sents_txt(txt)
    for sent_i, sent in enumerate(sents):
        tokens = tokenize_words_txt(sent)
        for tok_i, word_str in enumerate(tokens):
            # word_tok=to_token(word_str)
            numlinebreaks = word_str.count(sep_line)
            if numlinebreaks > 1:
                stanza_i += 1
            if numlinebreaks:
                line_i += 1
            is_punc = int(not any(x.isalpha() for x in word_str))
            odx_word = dict(
                **(dict(para_i=para_i) if para_i is not None else {}),
                sent_i=sent_i + 1,
                sentpart_i=linepart_i,
                stanza_i=stanza_i,
                line_i=line_i,
                word_i=tok_i + 1,
                word_str=word_str,
                # word_tok=word_tok,
                word_ispunc=is_punc
            )
            yield odx_word
            if set(word_str) & set(seps_phrase):
                linepart_i += 1
