from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from .imports import *

class SimpleCache:
    """A simple file-based caching system.

    This class provides a dictionary-like interface for caching objects to disk.
    It uses a two-level directory structure to organize cached files.

    Attributes:
        root_dir (str): The root directory for storing cached files.
    """

    def __init__(self, root_dir: str = PATH_HOME_DATA_CACHE) -> None:
        """Initialize the SimpleCache.

        Args:
            root_dir: The root directory for storing cached files.
        """
        self.root_dir = root_dir
        os.makedirs(root_dir, exist_ok=True)

    def _get_file_path(self, key: str) -> str:
        """Get the file path for a given key.

        Args:
            key: The cache key.

        Returns:
            The file path for the given key.
        """
        # Use the first 2 characters for the first level directory
        # and the next 2 characters for the second level directory
        dir1 = key[:2]
        dir2 = key[2:4]
        file_name = key[4:]
        
        dir_path = os.path.join(self.root_dir, dir1, dir2)
        os.makedirs(dir_path, exist_ok=True)
        
        return os.path.join(dir_path, file_name)

    def __setitem__(self, key: str, value: Any) -> None:
        """Set an item in the cache.

        Args:
            key: The cache key.
            value: The value to cache.
        """
        file_path = self._get_file_path(key)
        with open(file_path, 'wb') as f:
            f.write(encode_cache(value))

    def __getitem__(self, key: str) -> Any:
        """Get an item from the cache.

        Args:
            key: The cache key.

        Returns:
            The cached value.

        Raises:
            KeyError: If the key is not found in the cache.
        """
        file_path = self._get_file_path(key)
        if not os.path.exists(file_path):
            raise KeyError(key)
        with open(file_path, 'rb') as f:
            return decode_cache(f.read())

    def __contains__(self, key: str) -> bool:
        """Check if a key exists in the cache.

        Args:
            key: The cache key.

        Returns:
            True if the key exists, False otherwise.
        """
        return os.path.exists(self._get_file_path(key))

    def get(self, key: str, default: Any = None) -> Any:
        """Get an item from the cache with a default value.

        Args:
            key: The cache key.
            default: The default value to return if the key is not found.

        Returns:
            The cached value or the default value.
        """
        try:
            return self[key]
        except KeyError:
            return default

def retry_on_io_error(max_attempts: int = 3, delay: float = 0.1) -> Callable:
    """Decorator to retry a function on IOError.

    Args:
        max_attempts: Maximum number of retry attempts.
        delay: Delay between retry attempts in seconds.

    Returns:
        A decorator function.
    """
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


def group_ents(l: List[Any], feat: str) -> List[List[Any]]:
    """Group entities based on a common feature.

    Args:
        l: List of entities to group.
        feat: The feature to group by.

    Returns:
        A list of grouped entities.
    """
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


def groupby(df: pd.DataFrame, groupby: Union[str, List[str]]) -> pd.core.groupby.DataFrameGroupBy:
    """Group a DataFrame by specified columns.

    Args:
        df: The DataFrame to group.
        groupby: Column name(s) to group by.

    Returns:
        A grouped DataFrame.

    Raises:
        Exception: If no valid grouping columns are found.
    """
    allcols = set(df.index.names) | {df.index.name} | set(df.columns)
    if type(groupby) == str:
        groupby = [groupby]
    gby = [g for g in groupby if g in allcols]
    if not gby:
        raise Exception("No group after filter")
    return df.groupby(gby)


def get_txt(txt: Optional[str], fn: Optional[str]) -> str:
    """Get text content from a string, file, or URL.

    Args:
        txt: Text content or None.
        fn: Filename or URL or None.

    Returns:
        The text content.
    """
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


# def clean_text(txt: str) -> str:
#     """Clean and normalize text.

#     Args:
#         txt: The input text.

#     Returns:
#         Cleaned and normalized text.
#     """
#     txt = txt.replace("\r\n", "\n").replace("\r", "\n")
#     txt = ftfy.fix_text(txt)
#     return txt


def get_attr_str(attrs: Dict[str, Any], sep: str = ", ", bad_keys: Optional[List[str]] = None) -> str:
    """Generate a string representation of attributes.

    Args:
        attrs: Dictionary of attributes.
        sep: Separator between attribute strings.
        bad_keys: List of keys to exclude.

    Returns:
        A string representation of the attributes.
    """
    strs = [
        f"{k}={repr(v)}"
        for k, v in attrs.items()
        if v is not None and (not bad_keys or not k in set(bad_keys))
    ]
    attrstr = sep.join(strs)
    return attrstr


def safesum(l: List[Union[int, float]]) -> Union[int, float]:
    """Safely sum a list of numbers, ignoring non-numeric values.

    Args:
        l: List of numbers to sum.

    Returns:
        The sum of the numeric values in the list.
    """
    l = [x for x in l if type(x) in {int, float, np.float64, np.float32}]
    return sum(l)


def setindex(df: pd.DataFrame, cols: List[str] = []) -> pd.DataFrame:
    """Set the index of a DataFrame to specified columns.

    Args:
        df: The input DataFrame.
        cols: List of column names to set as index.

    Returns:
        The DataFrame with the new index set.
    """
    if not cols:
        return df
    cols = [c for c in cols if c in set(df.columns)]
    return df.set_index(cols) if cols else df



def get_stress(ipa: str) -> str:
    """Get the stress level from an IPA string.

    Args:
        ipa: The IPA string.

    Returns:
        The stress level ('S', 'P', or 'U').
    """
    if not ipa:
        return ""
    if ipa[0] == "`":
        return "S"
    if ipa[0] == "'":
        return "P"
    return "U"


def get_initial_whitespace(xstr: str) -> str:
    """Get the initial whitespace from a string.

    Args:
        xstr: The input string.

    Returns:
        The initial whitespace.
    """
    o = []
    for i, x in enumerate(xstr):
        if x == x.strip():
            break
        o.append(x)
    return "".join(o)


def unique(l: List[Any]) -> List[Any]:
    """Get unique elements from a list while preserving order.

    Args:
        l: The input list.

    Returns:
        A list of unique elements.
    """
    from ordered_set import OrderedSet

    return list(OrderedSet(l))


def hashstr(*inputs: Any, length: int = HASHSTR_LEN) -> str:
    """Generate a hash string from inputs.

    Args:
        *inputs: Input values to hash.
        length: Length of the output hash string.

    Returns:
        A hash string.
    """
    import hashlib
    input_string = str(inputs)
    sha256_hash = hashlib.sha256(str(input_string).encode()).hexdigest()
    return sha256_hash[:length]


def read_json(fn: str) -> Dict[str, Any]:
    """Read a JSON file.

    Args:
        fn: The filename.

    Returns:
        The parsed JSON data as a dictionary.
    """
    if not os.path.exists(fn):
        return {}
    with open(fn, encoding='utf-8') as f:
        return orjson.loads(f.read())


def from_json(json_d: Union[str, Dict[str, Any]], **kwargs: Any) -> Any:
    """Create an object from JSON data.

    Args:
        json_d: JSON data or filename.
        **kwargs: Additional keyword arguments.

    Returns:
        The created object.

    Raises:
        Exception: If the JSON data doesn't contain a '_class' key.
    """
    from .imports import GLOBALS

    if type(json_d) == str:
        json_d = read_json(json_d)
    if not "_class" in json_d:
        pprint(json_d)
        raise Exception
    classname = json_d["_class"]
    classx = GLOBALS[classname]
    return classx.from_json(json_d, **kwargs)


def load(fn: str, **kwargs: Any) -> Any:
    """Load an object from a JSON file.

    Args:
        fn: The filename.
        **kwargs: Additional keyword arguments.

    Returns:
        The loaded object.
    """
    return from_json(fn, **kwargs)


def to_json(obj: Any, fn: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Convert an object to JSON and optionally save to a file.

    Args:
        obj: The object to convert.
        fn: The filename to save to (optional).

    Returns:
        The JSON data if fn is None, otherwise None.
    """
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


def ensure_dir(fn: str) -> None:
    """Ensure that the directory for a file exists.

    Args:
        fn: The filename.
    """
    dirname = os.path.dirname(fn)
    if dirname:
        os.makedirs(dirname, exist_ok=True)



def encode_cache(x: Any) -> bytes:
    """Encode an object for caching.

    Args:
        x: The object to encode.

    Returns:
        The encoded object as bytes.
    """
    return b64encode(
        zlib.compress(
            orjson.dumps(
                x,
                option=orjson.OPT_SERIALIZE_NUMPY,
            )
        )
    )


def decode_cache(x: bytes) -> Any:
    """Decode a cached object.

    Args:
        x: The encoded object.

    Returns:
        The decoded object.
    """
    return orjson.loads(
        zlib.decompress(
            b64decode(
                x,
            ),
        ),
    )


def to_html(html: Union[str, Any], as_str: bool = False, **kwargs: Any) -> Union[str, Any]:
    """Convert an object to HTML.

    Args:
        html: The object to convert.
        as_str: Whether to return as a string.
        **kwargs: Additional keyword arguments.

    Returns:
        The HTML representation of the object.
    """
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


def enable_caching() -> None:
    """Enable caching."""
    global USE_CACHE
    USE_CACHE = True


def caching_is_enabled() -> bool:
    """Check if caching is enabled.

    Returns:
        True if caching is enabled, False otherwise.
    """
    return USE_CACHE


def disable_caching() -> None:
    """Disable caching."""
    global USE_CACHE
    USE_CACHE = False


@contextmanager
def caching_enabled() -> Iterator[None]:
    """Context manager for temporarily enabling caching."""
    was_loud = caching_is_enabled()
    enable_caching()
    yield
    if not was_loud:
        disable_caching()


@contextmanager
def caching_disabled() -> Iterator[None]:
    """Context manager for temporarily disabling caching."""
    was_loud = caching_is_enabled()
    disable_caching()
    yield
    if was_loud:
        enable_caching()


@contextmanager
def logging_disabled() -> Iterator[None]:
    """Context manager for temporarily disabling logging."""
    was_quiet = logmap.is_quiet
    logmap.is_quiet = True
    yield
    logmap.is_quiet = was_quiet


@contextmanager
def logging_enabled() -> Iterator[None]:
    """Context manager for temporarily enabling logging."""
    was_quiet = logmap.is_quiet
    logmap.is_quiet = False
    yield
    logmap.is_quiet = was_quiet


def force_int(x: Any, errors: int = 0) -> int:
    """Convert the input to an integer.

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

def tokenize_agnostic(txt: str) -> List[str]:
    """Tokenize text in a language-agnostic way.

    Args:
        txt: The input text.

    Returns:
        A list of tokens.
    """
    return re.findall(r"[\w']+|[.,!?; -—–'\n]", txt)



def clean_text(txt):
    txt=txt.replace('\r\n','\n').replace('\r','\n')
    replacements={
        '&eacute':'é',
        '&hyphen;':'-',
        '&sblank;':'--',
        '&mdash;':' -- ',
        '&ndash;':' - ',
        '&longs;':'s',
        '&wblank':' -- ',
        '\u2223':'',
        '\u2014':' -- ',
        '&ldquo;':'“',
        '&rdquo;':'”',
        '&lsquo;':'‘’',
        '&rsquo;':'’',
        '&indent;':'     ',
        '&amp;':'&',
        '&euml;':'ë',
        '&uuml;':'ü',
        '&auml;':'ä',
    }
    for k,v in list(replacements.items()):
        txt=txt.replace(k,v)
        # elif k.startswith('&') and k.endswith(';') and k[:-1] in txt:
            # txt=txt.replace(k[:-1],v)

    import ftfy
    txt=ftfy.fix_text(txt)
    return txt
