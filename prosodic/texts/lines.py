from ..imports import *
from ..words.wordtokenlist import WordTokenList

class GridMethods:
    """Hayes-grid delegates shared by any parse-bearing unit (Line, LinePart)."""

    def _grid_phrasal(self, kwargs):
        """Auto-supply gradient phrasal prominence (syntax=True) to the grid."""
        if 'phrasal' not in kwargs:
            from ..analysis.grid import phrasal_values
            kwargs['phrasal'] = phrasal_values(self.best_parse, self.text)
        return kwargs

    def grid_str(self, **kwargs) -> str:
        """Hayes-style metrical grid of the best parse as monospace text.

        With ``syntax=True`` on the text, phrasal-prominence rows extend
        the grid above the word level (nuclear stress = tallest column).
        """
        return self.best_parse.grid_str(**self._grid_phrasal(kwargs))

    def grid_df(self, **kwargs):
        """Metrical grid of the best parse as a per-syllable DataFrame."""
        return self.best_parse.grid_df(**self._grid_phrasal(kwargs))

    def grid_plot(self, **kwargs):
        """Metrical grid of the best parse as a plotnine figure."""
        return self.best_parse.grid_plot(**self._grid_phrasal(kwargs))


class Line(GridMethods, WordTokenList):
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

        # Both entity- and DF-path parses render directly: wordtoken2slots keys by
        # the tokenizer word number (WordToken.num == SyllData.word_num), so a
        # DF-path parse no longer needs an entity-path re-parse to map slots to
        # words. (Was AUDIT T9's eager re-parse; now entity-free.)
        output = []

        for i, wordtoken in enumerate(self.wordtokens):
            prefstr = get_initial_whitespace(wordtoken.txt)
            if prefstr:
                odx = {"txt": prefstr}
                output.append(odx)

            wordtoken_slots = parse.wordtoken2slots[wordtoken.num]
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
        odf = odf.ffill()

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

    @property
    def metrical_parse(self):
        """Among the co-optimal (min-score, unbounded) parses, the one with the
        most UNIFORM footing — fewest distinct foot types, then fewest feet.
        best_parse merely tie-breaks arbitrarily among co-optimal parses (so it can
        return a ragged reading when a clean one is equally optimal). A regular line
        is metrically uniform (all iambs, all trochees, all anapests, …), so
        preferring the fewest-distinct-feet co-optimal parse recovers the regular
        scansion — LINE-LOCALLY, with no poem-level meter and no prior, and
        meter-agnostically (it doesn't assume iambic). E.g. 'His tender heir might
        bear his memory' -> 5 iambs even parsed in isolation."""
        pl = self.parses
        unb = list(pl.unbounded) if pl is not None else []
        if not unb:
            return self.best_parse
        ms = min(p.score for p in unb)
        ties = [p for p in unb if p.score == ms]
        if len(ties) == 1:
            return ties[0]
        # count DISTINCT full feet — a trailing bare foot (catalectic/extrametrical
        # stub, e.g. 'sw sw sw s' = 3 trochees + a stub) shouldn't inflate the
        # distinctness of an otherwise-uniform line.
        return min(ties, key=lambda p: (len({ft.label for ft in p.metrical_feet if ft.label != "bare"}),
                                        len(p.metrical_feet)))

    @cache
    def rime_distance(self, line: 'Line', max_dist=RHYME_MAX_DIST) -> float:
        """
        Calculate the rime distance between this line and another line.

        Args:
            line (Line): The line to compare with.

        Returns:
            float: The rime distance between the two lines.
        """
        if not self.wordforms_nopunc or not line.wordforms_nopunc:
            return np.nan
        return self.wordforms_nopunc[-1].rime_distance(line.wordforms_nopunc[-1], max_dist=max_dist)

    def rime_type(self, line: 'Line', **kwargs):
        """Classify the end-rhyme between this line and another as
        'perfect', 'slant', 'assonance', or None (2-D Walker-calibrated
        nucleus/coda regions; see WordForm.rime_type for the taxonomy
        and threshold kwargs)."""
        if not self.wordforms_nopunc or not line.wordforms_nopunc:
            return None
        return self.wordforms_nopunc[-1].rime_type(
            line.wordforms_nopunc[-1], **kwargs
        )

    @property
    def parts(self):
        return LinePartList.from_wordtokens(self.wordtokens, parent=self)

    @property
    def linepart_parses(self):
        """LazyParseList per linepart for this line. Populated by the prose
        fallback when the line exceeds MAX_SYLL_IN_PARSE_UNIT. Returns a list
        aligned with self.parts; entries may be None if a linepart was itself
        too long to parse.
        """
        results = getattr(self.text, '_linepart_parse_results', None)
        if not results:
            return []
        latest_key = next(reversed(results))
        lp_results = results[latest_key]
        lp_nums = sorted({wt.linepart_num for wt in self.wordtokens if not wt.is_punc})
        return [lp_results.get(lp_num) for lp_num in lp_nums]



class LineList(EntityList):
    @classmethod
    def from_wordtokens(cls, wordtokens, text=None):
        return WordTokenList._from_wordtokens(wordtokens, 'line', 'line_num', text=text)

    def get_rhyming_lines(self, max_dist=RHYME_MAX_DIST):
        line2rhyme = defaultdict(list)
        for line_i, line in enumerate(self.data):
            prev_lines = self.data[:line_i]
            if not prev_lines:
                continue
            for line2 in prev_lines:
                dist = line.rime_distance(line2, max_dist=max_dist)
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

class LinePart(GridMethods, WordTokenList):
    prefix = 'linepart'

class LinePartList(EntityList):
    @classmethod
    def from_wordtokens(cls, wordtokens, text=None):
        return WordTokenList._from_wordtokens(wordtokens, 'linepart', 'linepart_num', text=text)