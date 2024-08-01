from .imports import *

class SimpleCache:
    def __init__(self, root_dir = PATH_HOME_DATA_CACHE):
        self.root_dir = root_dir
        os.makedirs(root_dir, exist_ok=True)

    def _get_file_path(self, key):
        # Use the first 2 characters for the first level directory
        # and the next 2 characters for the second level directory
        dir1 = key[:2]
        dir2 = key[2:4]
        file_name = key[4:]
        
        dir_path = os.path.join(self.root_dir, dir1, dir2)
        os.makedirs(dir_path, exist_ok=True)
        
        return os.path.join(dir_path, file_name)

    def __setitem__(self, key, value):
        file_path = self._get_file_path(key)
        with open(file_path, 'wb') as f:
            f.write(encode_cache(value))

    def __getitem__(self, key):
        file_path = self._get_file_path(key)
        if not os.path.exists(file_path):
            raise KeyError(key)
        with open(file_path, 'rb') as f:
            return decode_cache(f.read())

    def __contains__(self, key):
        return os.path.exists(self._get_file_path(key))

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

def retry_on_io_error(max_attempts=3, delay=0.1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except IOError as e:
                    if attempt < max_attempts - 1:
                        time.sleep(delay)
                    else:
                        raise
        return wrapper
    return decorator


def group_ents(l, feat):
    val = None
    ol = []
    lx = []
    for x in l:
        valx = getattr(x, feat)
        if valx is not val and lx:
            ol.append(lx)
            lx = []
        lx.append(x)
        val = valx
    if lx:
        ol.append(lx)
    return ol


def groupby(df: pd.DataFrame, groupby: list):
    allcols = set(df.index.names) | {df.index.name} | set(df.columns)
    if type(groupby) == str:
        groupby = [groupby]
    gby = [g for g in groupby if g in allcols]
    if not gby:
        raise Exception("No group after filter")
    return df.groupby(gby)


def get_txt(txt, fn):
    if txt:
        if txt.startswith("http") or os.path.exists(txt):
            return get_txt(None, txt)

        return txt

    if fn:
        if fn.startswith("http"):
            response = requests.get(fn)
            return response.text.strip()

        if os.path.exists(fn):
            with open(fn, encoding='utf-8') as f:
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
    wsws = wsws.replace("-", "w").replace("+", "s")
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


def read_json(fn):
    if not os.path.exists(fn):
        return {}
    with open(fn, encoding='utf-8') as f:
        return orjson.loads(f.read())


def from_json(json_d, **kwargs):
    from .imports import GLOBALS

    if type(json_d) == str:
        json_d = read_json(json_d)
    if not "_class" in json_d:
        pprint(json_d)
        raise Exception
    classname = json_d["_class"]
    classx = GLOBALS[classname]
    return classx.from_json(json_d, **kwargs)


def load(fn, **kwargs):
    return from_json(fn, **kwargs)


def to_json(obj, fn=None):
    if hasattr(obj, "to_json"):
        data = obj.to_json()
    else:
        data = obj

    if not fn:
        return data
    else:
        fdir = os.path.dirname(fn)
        if fdir:
            os.makedirs(fdir, exist_ok=True)
        with open(fn, "wb") as of:
            of.write(
                orjson.dumps(
                    data, option=orjson.OPT_INDENT_2 | orjson.OPT_SERIALIZE_NUMPY
                )
            )


def ensure_dir(fn):
    dirname = os.path.dirname(fn)
    if dirname:
        os.makedirs(dirname, exist_ok=True)



def encode_cache(x):
    return b64encode(
        zlib.compress(
            orjson.dumps(
                x,
                option=orjson.OPT_SERIALIZE_NUMPY,
            )
        )
    )


def decode_cache(x):
    return orjson.loads(
        zlib.decompress(
            b64decode(
                x,
            ),
        ),
    )


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


def enable_caching():
    global USE_CACHE
    USE_CACHE = True


def caching_is_enabled():
    return USE_CACHE


def disable_caching():
    global USE_CACHE
    USE_CACHE = False


@contextmanager
def caching_enabled():
    was_loud = caching_is_enabled()
    enable_caching()
    yield
    if not was_loud:
        disable_caching()


@contextmanager
def caching_disabled():
    was_loud = caching_is_enabled()
    disable_caching()
    yield
    if was_loud:
        enable_caching()


@contextmanager
def logging_disabled():
    was_quiet = logmap.is_quiet
    logmap.is_quiet = True
    yield
    logmap.is_quiet = was_quiet


@contextmanager
def logging_enabled():
    was_quiet = logmap.is_quiet
    logmap.is_quiet = False
    yield
    logmap.is_quiet = was_quiet


def force_int(x, errors=0) -> int:
    """Converts the input to an integer.

    Args:
        x: The input value to be converted to an integer.
        errors: The value to be returned in case of an error. Defaults to 0.

    Returns:
        The input value converted to an integer if successful, otherwise the specified error value.
    """
    try:
        return int(x)
    except (ValueError, TypeError):
        return errors
