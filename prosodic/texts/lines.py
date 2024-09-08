from ..imports import *
from ..words.wordtokenlist import WordTokenList

class Line(WordTokenList):
    """
    A class representing a line of text in a poem or prose.

    This class inherits from Text and represents a single line, typically containing
    words or tokens. It provides methods for parsing, analyzing, and rendering the line.

    Attributes:
        line_sep (str): Separator string used between lines. Default is "\n".
        sep (str): Separator string used between words. Default is "\n".
        child_type (str): The type of child entities. Default is "WordToken".
        is_parseable (bool): Whether the line can be parsed. Default is True.
        prefix (str): Prefix used for identification. Default is "line".
        use_cache (bool): Whether to use caching. Default is False.
    """

    # line_sep: str = "\n"
    # sep: str = "\n"
    # child_type: str = "WordToken"
    # is_parseable: bool = True
    # prefix: str = "line"
    # use_cache: bool = False

    # @log.debug
    # def __init__(
    #     self,
    #     txt: str = "",
    #     children: List[Any] = [],
    #     parent: Optional[Any] = None,
    #     tokens_df: Optional[pd.DataFrame] = None,
    #     lang: str = DEFAULT_LANG,
    #     **kwargs
    # ) -> None:
    #     """
    #     Initialize a Line object.

    #     Args:
    #         txt (str): The text content of the line.
    #         children (List[Any]): List of child entities (usually WordTokens).
    #         parent (Optional[Any]): The parent entity of this line.
    #         tokens_df (Optional[pd.DataFrame]): DataFrame containing tokenized data.
    #         lang (str): The language of the line. Defaults to DEFAULT_LANG.
    #         **kwargs: Additional keyword arguments.

    #     Raises:
    #         Exception: If neither txt, children, nor tokens_df is provided.
    #     """
    #     from ..words import WordToken
    #     log.debug("Importing WordToken")

    #     if not txt and not children and tokens_df is None:
    #         log.debug("No input provided")
    #         raise Exception("Must provide either txt, children, or tokens_df")

    #     txt = txt.strip()
    #     log.debug(f"Stripped text: {txt}")

    #     if not children:
    #         log.debug("No children provided")
    #         if tokens_df is None:
    #             log.debug("No tokens_df provided, tokenizing text")
    #             tokens_df = tokenize_sentwords_df(txt)
            
    #         log.debug("Creating children from tokens_df")
    #         children = [
    #             WordToken(
    #                 txt=word_d.get("word_str", ""),
    #                 lang=lang,
    #                 parent=self,
    #                 sent_num=word_d.get("sent_i"),
    #                 sentpart_num=word_d.get("sentpart_i"),
    #             )
    #             for word_d in tokens_df.to_dict("records")
    #             if "word_str" in word_d
    #         ]
    #         log.debug(f"Created {len(children)} children")

    #     log.debug("Initializing Entity")
    #     if not txt:
    #         txt=''.join(x._txt for x in children)
    #     super().__init__(txt=txt, children=children, parent=parent, **kwargs)

    #     log.debug("Setting up parses and parseable flag")
    #     self._parses = []
    #     self.is_parseable = True
    #     log.debug("Line initialization complete")
    #     log.debug(f"Line text: {self._txt}")

    # @stash.stashed_result
    # def parse(self, meter=None, defaults=False, **meter_kwargs):
    #     if meter is None:
    #         if defaults:
    #             meter_kwargs = {**DEFAULT_METER_KWARGS, **meter_kwargs}
    #         meter = self.get_meter(meter=meter, **meter_kwargs)
        
    #     return meter.parse_line(self, **meter_kwargs)

    # def to_dict(self) -> Dict[str, Any]:
    #     """
    #     Convert the Line object to a JSON-serializable dictionary.

    #     Returns:
    #         Dict[str, Any]: A dictionary representation of the Line object.
    #     """
    #     return super().to_dict(self, txt=self.txt)

    def to_html(self, parse: Optional[Any] = None, as_str: bool = False, css: str = HTML_CSS, tooltip: bool = False, **kwargs) -> Any:
        """
        Generate an HTML representation of the Line.

        Args:
            parse (Optional[Any]): The parse to use for rendering. If None, uses the minimum parse.
            as_str (bool): If True, return the result as a string. Default is False.
            css (str): CSS styles to include in the HTML. Default is HTML_CSS.
            tooltip (bool): Whether to include tooltips. Default is False.
            **kwargs: Additional keyword arguments.

        Returns:
            Any: HTML representation of the Line.
        """
        if parse is None:
            parse = min(self._parses)

        output = []

        for wordtoken in self.wordtokens:
            prefstr = get_initial_whitespace(wordtoken.txt)
            if prefstr:
                odx = {"txt": prefstr}
                output.append(odx)

            wordtoken_slots = parse.wordtoken2slots[wordtoken]
            if wordtoken_slots:
                for slot in wordtoken_slots:
                    pos = slot.parent
                    spclass = f"mtr_{'s' if slot.is_prom else 'w'}"
                    stclass = f"str_{'s' if slot.unit.is_stressed else 'w'}"
                    vclass = f"viol_{'y' if pos.violset else 'n'}"
                    odx = {
                        "txt": slot.unit.txt,
                        "meter": spclass,
                        "stress": stclass,
                        "viol": vclass,
                        "viols": list(slot.violset),
                    }
                    output.append(odx)
            else:
                odx = {"txt": wordtoken.txt}
                output.append(odx)

        odf = pd.DataFrame(output)
        odf = odf.fillna(method="ffill")

        def htmlx(row, tooltip=tooltip):
            if not row.txt.strip() or not row.txt[0].isalpha():
                return row.txt

            if tooltip and row.viols:
                viol_strs = [f"<li>{viol}</li>" for viol in sorted(row.viols)]
                viol_str = f'<ol>{"".join(viol_strs)}</ol>'
                viol_title = f"Violated {len(row.viols)} constraints: {viol_str}"
                rowtxt = f'{row.txt}<span class="tooltip">{viol_title}</span>'
                tooltip = " tooltip"
            else:
                tooltip = ""
                rowtxt = row.txt

            return f'<span class="{row.meter} {row.stress} {row.viol}{tooltip}">{rowtxt}</span>'

        spans = odf.apply(htmlx, axis=1)
        out = "".join(spans)
        out = f'<style>{css}</style><div class="parse">{out}</div>'
        return to_html(out, as_str=as_str)

    def stats(self, by: str = "parse", **kwargs) -> pd.DataFrame:
        """
        Get statistics for the line's parses.

        Args:
            by (str): The grouping criterion for statistics. Default is "parse".
            **kwargs: Additional keyword arguments.

        Returns:
            pd.DataFrame: A DataFrame containing parse statistics.
        """
        return self.parses.stats(by=by, **kwargs)

    def stats_d(self, by: str = "parse", **kwargs) -> Dict[str, Any]:
        """
        Get statistics for the line's parses as a dictionary.

        Args:
            by (str): The grouping criterion for statistics. Default is "parse".
            **kwargs: Additional keyword arguments.

        Returns:
            Dict[str, Any]: A dictionary containing parse statistics.
        """
        return self.parses.stats_d(by=by, **kwargs)

    @cached_property
    def num_sylls(self) -> int:
        """
        Get the number of syllables in the line.

        Returns:
            int: The number of syllables.
        """
        return len(self.syllables)

    @cache
    def rime_distance(self, line: 'Line') -> float:
        """
        Calculate the rime distance between this line and another line.

        Args:
            line (Line): The line to compare with.

        Returns:
            float: The rime distance between the two lines.
        """
        if not self.wordforms_nopunc or not line.wordforms_nopunc:
            return np.nan
        return self.wordforms_nopunc[-1].rime_distance(line.wordforms_nopunc[-1])
    
    @cached_property
    def parts(self):
        return LinePartList.from_wordtokens(self.wordtokens, parent=self)
    


class LineList(EntityList):
    @classmethod
    def from_wordtokens(cls, wordtokens, text=None):
        return WordTokenList._from_wordtokens(wordtokens, 'line', 'line_num', text=text)

    def get_rhyming_lines(self, max_dist=RHYME_MAX_DIST):
        line2rhyme = defaultdict(list)
        for line in self.data:
            prev_lines = self.data[: line.i]
            if not prev_lines:
                continue
            for line2 in prev_lines:
                dist = line.rime_distance(line2)
                if max_dist is None or dist <= max_dist:
                    line2rhyme[line].append((dist, line2))
        return {i: min(v) for i, v in line2rhyme.items()}

class LinePart(WordTokenList): pass

class LinePartList(EntityList):
    @classmethod
    def from_wordtokens(cls, wordtokens, text=None):
        return WordTokenList._from_wordtokens(wordtokens, 'linepart', 'linepart_num', text=text)