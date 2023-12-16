from .imports import *


def get_txt(txt, fn):
    if txt:
        return txt
    if fn and os.path.exists(fn):
        with open(fn) as f:
            return f.read()
    return ""


def clean_text(txt):
    txt = txt.replace("\r\n", "\n").replace("\r", "\n")
    txt = ftfy.fix_text(txt)
    return txt


def get_attr_str(attrs, sep=", ", bad_keys=None):
    strs = [
        f"{k}={repr(v)}"
        for k, v in attrs.items()
        if v is not None and (not bad_keys or not k in set(bad_keys))
    ]
    attrstr = sep.join(strs)
    return attrstr


# @profile


def safesum(l):
    # o=pd.Series(pd.to_numeric(l,errors='coerce')).sum()
    # o_int=int(o)
    # o_float = float(o)
    # return o_int if o_int==o_float else o_float
    l = [x for x in l if type(x) in {int, float, np.float64, np.float32}]
    return sum(l)


def setindex(df, cols=[]):
    if not cols:
        return df
    cols = [c for c in cols if c in set(df.columns)]
    return df.set_index(cols) if cols else df


def split_scansion(wsws: str) -> list:
    positions = []
    position = []
    last_x = None
    for x in wsws:
        if last_x and last_x != x and position:
            positions.append(position)
            position = []
        position.append(x)
        last_x = x
    if position:
        positions.append(position)
    return ["".join(pos) for pos in positions]


@cache
def get_possible_scansions(nsyll, max_s=METER_MAX_S, max_w=METER_MAX_W):
    if max_s is None:
        max_s = nsyll
    if max_w is None:
        max_w = nsyll
    return [
        l for l in iter_mpos(nsyll, max_s=max_s, max_w=max_w) if getlenparse(l) == nsyll
    ]


def getlenparse(l):
    return sum(len(x) for x in l)


def iter_mpos(nsyll, starter=[], pos_types=None, max_s=METER_MAX_S, max_w=METER_MAX_W):
    if pos_types is None:
        wtypes = ["w" * n for n in range(1, max_w + 1)]
        stypes = ["s" * n for n in range(1, max_s + 1)]
        pos_types = [[x] for x in wtypes + stypes]

    news = []
    for pos_type in pos_types:
        if starter and starter[-1][-1] == pos_type[0][0]:
            continue
        new = starter + pos_type
        # if starter: print(starter[-1][-1], pos_type[0][0], new)
        # if not is_ok_parse(new): continue
        if getlenparse(new) <= nsyll:
            news.append(new)

    # news = battle_parses(news)
    if news:
        yield from news
    # print('\n'.join('|'.join(x) for x in news))
    for new in news:
        yield from iter_mpos(nsyll, starter=new, pos_types=pos_types)


# class representing the potential bounding relations between to parses
class Bounding:
    bounds = 0  # first parse harmonically bounds the second
    bounded = 1  # first parse is harmonically bounded by the second
    equal = 2  # the same constraint violation scores
    unequal = 3  # unequal scores; neither set of violations is a subset of the other


def get_stress(ipa):
    if not ipa:
        return ""
    if ipa[0] == "`":
        return "S"
    if ipa[0] == "'":
        return "P"
    return "U"


def get_initial_whitespace(xstr):
    o = []
    for i, x in enumerate(xstr):
        if x == x.strip():
            break
        o.append(x)
    return "".join(o)


def unique(l):
    from ordered_set import OrderedSet

    return list(OrderedSet(l))


def hashstr(*inputs, length=HASHSTR_LEN):
    import hashlib

    input_string = str(inputs)
    sha256_hash = hashlib.sha256(str(input_string).encode()).hexdigest()
    return sha256_hash[:length]


def from_json(json_d, **kwargs):
    from .imports import GLOBALS

    if not "_class" in json_d:
        pprint(json_d)
        raise Exception
    classname = json_d["_class"]
    classx = GLOBALS[classname]
    return classx.from_json(json_d, **kwargs)


def to_json(obj, fn=None):
    data = obj.to_json()
    if not fn:
        return data

    os.makedirs(os.path.dirname(fn), exist_ok=True)
    with open(fn, "wb") as of:
        of.write(
            orjson.dumps(data, option=orjson.OPT_INDENT_2 | orjson.OPT_SERIALIZE_NUMPY)
        )


def ensure_dir(fn):
    dirname = os.path.dirname(fn)
    if dirname:
        os.makedirs(dirname, exist_ok=True)


def encode_cache(x):
    return zlib.compress(orjson.dumps(x, option=orjson.OPT_SERIALIZE_NUMPY))


def decode_cache(x):
    return orjson.loads(zlib.decompress(x))


def CompressedSqliteDict(fn, *args, flag="c", **kwargs):
    from sqlitedict import SqliteDict

    ensure_dir(fn)
    kwargs["encode"] = encode_cache
    kwargs["decode"] = decode_cache
    return SqliteDict(fn, *args, flag=flag, **kwargs)


def to_html(html, as_str=False, **kwargs):
    if type(html) is not str:
        if hasattr(html, "to_html"):
            return html.to_html(as_str=as_str, **kwargs)
        logger.error(f"what type of data is this? {html}")
        return

    if as_str:
        return html

    try:
        from IPython.display import HTML, Markdown, display

        return HTML(html)
    except ModuleNotFoundError:
        return html
