from ..imports import *
from ..words import WordTokenList, WordToken

NUMBUILT = 0
DEFAULT_COMBINE_BY = 'line'

class TextModel(WordTokenList):
    """
    A class that represents a text structure, comprised of WordTokens.
    """
    is_text = True
    prefix = "text"

    # @#log.debug
    def __init__(
        self,
        children: Optional[list] = [],
        txt: str = None,
        fn: str = None,
        lang: Optional[str] = DEFAULT_LANG,
        parent: Optional[Entity] = None,
        tokens_df: Optional[pd.DataFrame] = None,
        **kwargs,
    ):
        """
        Initializes an instance of the class.

        Args:
            txt (str): The text string. Default is an empty string.
            fn (str): A path or URL to a text file to read
            lang (Optional[str]): The language of the text. Default is DEFAULT_LANG.
            parent (Optional[Entity]): The parent entity. Default is None.
            children (Optional[list]): The list of child entities. Default is an empty list.
            tokens_df (Optional[pd.DataFrame]): The token dataframe. Default is None.
            use_cache (bool): Whether to use cache. Default is USE_CACHE.
            force (bool): Force parsing regardless of current state. Default is False.
            **kwargs: Additional keyword arguments.

        Raises:
            Exception: If neither txt string, filename, nor token dataframe is provided.

        Returns:
            None
        """
        if isinstance(children,str):
            txt = children
            children = []

        if not txt and not fn and not children and tokens_df is None:
            raise ValueError(
                "must provide either txt string or filename or token dataframe"
            )
        self._text = None

        #log.debug("Cleaning and getting text")
        txt = clean_text(get_txt(txt, fn)).strip()

        #log.debug(f"Cleaned text: {txt[:100]}...")

        self._txt = txt
        self._fn = fn

        #log.debug(f"Setting language: {lang}")

        self.lang = lang if lang else detect_lang(txt)
        #log.debug(f"Language set to: {self.lang}")

        was_quiet = logmap.quiet
        #log.debug(f"Was quiet: {was_quiet}")

        if not children:
            #log.debug("No children provided, processing text")

            numwords = len(txt.split())
            #log.debug(f"Number of words: {numwords}")

            if was_quiet and numwords > 1000:
                #log.debug("Setting logmap to not quiet due to large text")
                logmap.quiet = False

            #log.debug(f"building text with {numwords:,} words")
            if tokens_df is None:
                #log.debug("Tokenizing text into DataFrame")
                tokens_df = tokenize_sentwords_df(txt)
            children = [
                WordToken(lang=self.lang, parent=self, text=self, **row.to_dict())
                for _, row in progress_bar(
                    list(tokens_df.iterrows()),
                    progress=len(tokens_df)>=1000, 
                    desc='Building long text'
                )
            ]
        #log.debug("Initializing parent class")
        super().__init__(children=children, parent=parent, **kwargs)

    

    @cached_property
    def stanzas(self):
        from ..texts.stanzas import StanzaList
        return StanzaList.from_wordtokens(self, text=self)
    
    @cached_property
    def lines(self):
        from ..texts.lines import LineList
        return LineList.from_wordtokens(self, text=self)
    
    @cached_property
    def lineparts(self):
        from ..texts.lines import LinePartList
        return LinePartList.from_wordtokens(self, text=self)
    
    @cached_property
    def sents(self):
        from ..sents.sents import SentenceList
        return SentenceList.from_wordtokens(self, text=self)
    
    @cached_property
    def sentparts(self):
        from ..sents.sents import SentPartList
        return SentPartList.from_wordtokens(self, text=self)

    def to_hash(self) -> str:
        """
        Generate a hash string for the text.

        Returns:
            str: A hash string representation of the text.
        """
        return hashstr(self._txt)

    @property
    def hash(self):
        return encode_hash(serialize({'txt':self.txt, 'lang':self.lang}))

    @cached_property
    def key(self):
        return f'{self.nice_type_name}({self.hash})'

    def parse(self, combine_by: Literal['line','sent'] = DEFAULT_COMBINE_BY, num_proc=None, lim=None, force=False, meter=None, **meter_kwargs):
        """
        Parse the text.

        Args:
            **kwargs: Keyword arguments for parsing configuration.

        Returns:
            Any: The parsed result.
        """
        from ..parsing.parselists import ParseListList
        self._parses = ParseListList(
            self.parse_iter(
                combine_by=combine_by,
                num_proc=num_proc,
                force=force,
                meter=meter,
                lim=lim,
                **meter_kwargs,
            ),
            parent=self
        )
        return self._parses

    def parse_iter(self, combine_by: Literal['line','sent'] = DEFAULT_COMBINE_BY, num_proc=None, lim=None, force=False, meter=None, **meter_kwargs):
        from ..parsing.parselists import ParseList
        meter = self.get_meter(meter=meter, **meter_kwargs)
        if combine_by and meter.parse_unit == combine_by:
            combine_by = None
        
        last_unit = None
        units=[]
        for parse_list in meter.parse_text_iter(self, num_proc=num_proc, force=force, lim=lim):
            parsed_ent = self.match(parse_list.parent)
            parse_list.parent = parsed_ent
            parsed_ent._parses = parse_list
            if not combine_by:
                yield parse_list
            else:
                this_unit = getattr(parsed_ent, combine_by)
                if units and not last_unit.equals(this_unit):
                    new_parselist = ParseList.from_combinations(units, parent=this_unit)
                    this_unit._parses = new_parselist
                    yield new_parselist
                    units=[]
                units.append(parse_list)
                last_unit = this_unit

        if units:
            new_parselist = ParseList.from_combinations(units, parent=this_unit)
            this_unit._parses = new_parselist
            yield new_parselist
        

        

# @stash.stashed_result
def Text(
    txt: str = "",
    fn: str = "",
    lang: Optional[str] = DEFAULT_LANG,
    parent: Optional[Entity] = None,
    children: Optional[list] = [],
    tokens_df: Optional[pd.DataFrame] = None,
):
    return TextModel(txt=txt, fn=fn, lang=lang, parent=parent, children=children, tokens_df=tokens_df)


class TextList(EntityList):
    pass
