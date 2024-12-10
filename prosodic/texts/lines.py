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
    prefix = 'line'

    def __repr__(self, **kwargs):
        return f"Line(num={self.num}, txt={repr(self.txt)})"

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

        for i, wordtoken in enumerate(self.wordtokens):
            prefstr = get_initial_whitespace(wordtoken.txt)
            if prefstr:
                odx = {"txt": prefstr}
                output.append(odx)

            wordtoken_slots = parse.wordtoken2slots[wordtoken.key]
            if wordtoken_slots:
                for slot in wordtoken_slots:
                    pos = slot.position
                    spclass = f"mtr_{'s' if slot.is_prom else 'w'}"
                    stclass = f"str_{'s' if slot.unit.is_stressed else 'w'}"
                    
                    # Get position-level violations
                    violations = list(slot.violset)
                    
                    # Add parse-wide violations to last slot
                    is_last_slot = (i == len(self.wordtokens) - 1 and 
                                  slot is wordtoken_slots[-1])
                    if is_last_slot:
                        violations.extend(parse.parse_viold.keys())
                    
                    vclass = f"viol_{'y' if violations else 'n'}"
                    
                    odx = {
                        "txt": slot.unit.txt,
                        "meter": spclass,
                        "stress": stclass,
                        "viol": vclass,
                        "viols": violations,
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

    @property
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
    
    @property
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
    
    @property
    def rhyming(self):
        return self.get_rhyming_lines()
    
    @property
    def num_rhyming(self) -> int:
        """
        Get the number of rhyming lines in the stanza.

        Returns:
            int: The number of rhyming lines.
        """
        return len(self.rhyming)

    @property
    def is_rhyming(self) -> bool:
        """
        Check if the stanza contains rhyming lines.

        Returns:
            bool: True if the stanza contains rhyming lines, False otherwise.
        """
        return self.num_rhyming > 0

class LinePart(WordTokenList): 
    prefix = 'linepart'
    pass

class LinePartList(EntityList):
    @classmethod
    def from_wordtokens(cls, wordtokens, text=None):
        return WordTokenList._from_wordtokens(wordtokens, 'linepart', 'linepart_num', text=text)